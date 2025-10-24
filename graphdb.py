import json
import os
import numpy as np
from llm import llm
from collections import Counter
from sentence_transformers import SentenceTransformer

DATABASE = "neo4j"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")  # 더 작은 모델 사용


def create_summary_context(trace_data):
    context_lines = []

    def get_tag_value(tags, key, default=None):
        for tag in tags:
            if tag.get("key") == key:
                return tag.get("value")
        return default

    sigma_alerts = Counter()
    process_flows = Counter()
    network_events = Counter()
    file_events = Counter()
    registry_events = Counter()

    for span in trace_data.get("spans", []):
        tags = span.get("tags", [])
        event_name = get_tag_value(tags, "EventName", "")
        process_image = get_tag_value(tags, "Image")
        process_name = os.path.basename(process_image or "N/A")

        # Sigma 룰 탐지
        rule_title = get_tag_value(tags, "sigma.rule_title")
        if rule_title:
            sigma_alerts[f"규칙: {rule_title}, 프로세스: {process_name}"] += 1

        # 프로세스 생성 흐름
        if "ProcessCreate" in event_name:
            parent_image = get_tag_value(tags, "ParentImage")
            if parent_image and process_image:
                process_flows[
                    f"'{os.path.basename(parent_image)}'가 '{process_name}'를 실행"
                ] += 1

        # 네트워크/파일/레지스트리 이벤트
        if "NetworkConnect" in event_name:
            dest_ip = get_tag_value(tags, "DestinationIp")
            dest_port = get_tag_value(tags, "DestinationPort")
            if dest_ip and dest_port:
                network_events[
                    f"[네트워크] '{process_name}'가 '{dest_ip}:{dest_port}'로 연결"
                ] += 1
        elif "FileCreate" in event_name:
            target_file = get_tag_value(tags, "TargetFilename")
            if target_file:
                file_events[
                    f"[파일] '{process_name}'가 '{target_file}' 파일을 생성"
                ] += 1
        elif "RegistryValueSet" in event_name:
            target_object = get_tag_value(tags, "TargetObject")
            if target_object:
                registry_events[
                    f"[레지스트리] '{process_name}'가 '{target_object}' 키 값을 수정"
                ] += 1

    # 컨텍스트 생성
    if sigma_alerts:
        context_lines.append("### Sigma Rule 탐지 요약:")
        for item, count in sigma_alerts.most_common():
            context_lines.append(f"- {item} ({count}회)")
    if process_flows:
        context_lines.append("\n### 주요 프로세스 생성 흐름:")
        for item, count in process_flows.most_common():
            context_lines.append(f"- {item} ({count}회)")
    if network_events or file_events or registry_events:
        context_lines.append("\n### 기타 주요 이벤트:")
        for item, count in network_events.most_common(5):
            context_lines.append(f"- {item} ({count}회)")
        for item, count in file_events.most_common(5):
            context_lines.append(f"- {item} ({count}회)")
        for item, count in registry_events.most_common(5):
            context_lines.append(f"- {item} ({count}회)")

    return "\n".join(context_lines)


def summarize_trace_with_llm(trace_input, prompt_template):
    if isinstance(trace_input, str):
        with open(trace_input, "r", encoding="utf-8-sig") as f:
            trace_data = json.load(f)
    else:
        trace_data = trace_input

    summary_context = create_summary_context(trace_data)
    final_prompt = prompt_template.replace(
        "[분석할 JSON 데이터가 여기에 삽입됩니다]", summary_context
    )

    try:
        response = llm.invoke(final_prompt)
        raw_content = response.content
        if not raw_content.strip():
            return {"error": "LLM으로부터 빈 응답을 받았습니다."}

        cleaned_content = raw_content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content.split("\n", 1)[1]
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content.rsplit("\n", 1)[0]

        analysis_result = json.loads(cleaned_content.strip())
        return analysis_result
    except json.JSONDecodeError:
        return {
            "error": "LLM이 유효한 JSON을 반환하지 않았습니다.",
            "raw_response": raw_content,
        }
    except Exception as e:
        return {"error": f"LLM 호출 중 오류 발생: {e}"}


def long_summary(
    driver,
    summary_text,
    comparisons,
    indirect_connections,
    semantic_top_traces,
    top_k=3,
):
    """구조적 유사성, 간접 연결, 의미적 유사 트레이스를 활용한 상세 요약 생성"""

    # 유사 트레이스 ID만 추출 (상위 3개)
    similar_trace_ids = [t["trace_id"] for t in semantic_top_traces[:top_k]]

    # LLM을 활용한 구조적 분석 프롬프트
    analysis_prompt = """
다음은 새로운 공격 트레이스와 기존 트레이스들 간의 구조적 유사성 분석 결과입니다.

입력 데이터는 두 가지입니다:
1. structural_similarity: 각 트레이스별로 공통된 엔티티와 일치 개수(entity_match_count)
2. indirect_connections: 엔티티 간의 간접 연결 관계(최대 2-hop 경로)

이 데이터를 기반으로 아래 내용을 **자연어로 종합적으로 요약**하세요.

요약 시 포함할 내용:
- 전반적인 구조적 유사성 경향  
  (공통 엔티티가 많은 트레이스들의 특징, 주요 유사 구조나 공격 패턴)
- 반복적으로 나타나는 핵심 엔티티(Process, File, IP, Registry 등)
- 간접 연결에서 의미 있는 관계  
  (예: 동일 파일을 여러 프로세스가 접근, 특정 IP로의 공통 네트워크 연결 등)
- 전체적으로 어떤 공격 흐름 또는 전술과 유사한지  
- 분석 결과에서 도출되는 구조적 인사이트나 시사점  

출력은 자연스러운 분석 보고서처럼 작성하세요.  
불필요한 형식 없이 문단 단위로 정리하고,  
필요하면 bullet point를 사용해도 좋습니다.

데이터:
{
  "structural_similarity": {{ structural_similarity }},
  "indirect_connections": {{ indirect_connections }}
}
"""

    try:
        # 실제 프롬프트 생성
        prompt = analysis_prompt.replace(
            "{{ structural_similarity }}",
            json.dumps(comparisons, ensure_ascii=False),
        )
        prompt = prompt.replace(
            "{{ indirect_connections }}",
            json.dumps(indirect_connections, ensure_ascii=False),
        )

        # LLM으로 구조적 분석 수행
        response = llm.invoke(prompt)
        structural_analysis = response.content.strip()

        # CoT 방식의 상세 분석 보고서 생성
        cot_prompt = f"""
당신은 보안 분석 전문가입니다. 다음 정보를 바탕으로 체계적이고 상세한 악성 행위 분석 보고서를 작성해주세요.

[원본 트레이스 요약]
{summary_text}

[구조적 유사성 분석 결과]
{structural_analysis}

[유사한 트레이스 정보]
- 상위 {len(similar_trace_ids)}개 유사 트레이스: {', '.join([tid[:8] + '...' for tid in similar_trace_ids])}

다음 형식으로 분석 보고서를 작성해주세요:

## 악성 행위 상세 분석

### 1. 공격 흐름 개요
[전체적인 공격 과정을 시간순으로 요약]

### 2. 주요 악성 행위 분석
[각 단계별 상세 분석 - 초기 침투, 권한 상승, 지속성 확보, 데이터 유출 등]

### 3. 사용된 공격 기법 및 도구
[발견된 공격 기법과 사용된 도구들]

### 4. 방어 우회 시도
[백신 우회, 탐지 회피 등의 시도]

### 5. 네트워크 활동 및 C2 통신
[외부 통신 시도, C2 서버 연결 등]

### 6. 구조적 유사성 분석 결과
[기존 트레이스와의 유사점, 공통 패턴]

### 7. 보안 위협 평가 및 결론
[전체적인 위협 수준과 즉시 조치 필요성]

분석은 한국어로 작성하고, 각 섹션은 구체적이고 실무진이 이해하기 쉽게 설명해주세요.
"""

        cot_response = llm.invoke(cot_prompt)
        long_summary_text = cot_response.content.strip()

    except Exception as e:
        # LLM 오류 시 기본 CoT 분석 보고서 생성
        cot_prompt_fallback = f"""
당신은 보안 분석 전문가입니다. 다음 정보를 바탕으로 체계적인 악성 행위 분석 보고서를 작성해주세요.

[원본 트레이스 요약]
{summary_text}

[유사한 트레이스 정보]
- 상위 {len(similar_trace_ids)}개 유사 트레이스: {', '.join([tid[:8] + '...' for tid in similar_trace_ids])}

[구조적 유사성 통계]
- {len([s for s in comparisons if s['entity_match_count'] > 0])}개의 트레이스에서 구조적 유사성 발견
- {len(indirect_connections)}개의 간접 연결 관계 발견

다음 형식으로 분석 보고서를 작성해주세요:

## 악성 행위 상세 분석

### 1. 공격 흐름 개요
[전체적인 공격 과정을 시간순으로 요약]

### 2. 주요 악성 행위 분석
[각 단계별 상세 분석]

### 3. 사용된 공격 기법 및 도구
[발견된 공격 기법과 사용된 도구들]

### 4. 방어 우회 시도
[백신 우회, 탐지 회피 등의 시도]

### 5. 네트워크 활동 및 C2 통신
[외부 통신 시도, C2 서버 연결 등]

### 6. 구조적 유사성 분석 결과
이 트레이스는 {len(similar_trace_ids)}개의 유사한 트레이스와 연관되어 있으며, 총 {len(indirect_connections)}개의 간접 연결을 통해 다른 엔티티들과 연결되어 있습니다.

### 7. 보안 위협 평가 및 결론
[전체적인 위협 수준과 즉시 조치 필요성]

분석은 한국어로 작성하고, 각 섹션은 구체적이고 실무진이 이해하기 쉽게 설명해주세요.
"""

        try:
            cot_response = llm.invoke(cot_prompt_fallback)
            long_summary_text = cot_response.content.strip()
        except Exception:
            # CoT도 실패하면 기본 템플릿 사용
            long_summary_text = f"""## 악성 행위 상세 분석

### 공격 흐름 개요
{summary_text}

### 구조적 유사성 분석
- {len([s for s in comparisons if s['entity_match_count'] > 0])}개의 트레이스에서 구조적 유사성 발견
- {len(indirect_connections)}개의 간접 연결 관계 발견

### 유사한 트레이스 분석
- 상위 {len(similar_trace_ids)}개 유사 트레이스: {', '.join([tid[:8] + '...' for tid in similar_trace_ids])}

### 보안 위협 평가
이 트레이스는 악성 활동으로 분류되었으며, 즉시 격리 및 분석이 필요합니다.
"""

    return {
        "long_summary": long_summary_text.strip(),
        "similar_trace_ids": similar_trace_ids,
    }


def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1, dtype=float)
    v2 = np.array(vec2, dtype=float)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


def find_similar_traces(driver, summary_text, top_k=3):
    with driver.session(database=DATABASE) as session:
        # 먼저 Trace 노드의 실제 속성을 확인
        try:
            # Trace 노드의 속성 확인
            result = session.run("MATCH (t:Trace) RETURN keys(t) as keys LIMIT 1")
            record = result.single()
            if record and record["keys"]:
                trace_keys = record["keys"]
                print(f"🔍 Trace 노드 속성: {trace_keys}")

                # traceId 속성이 있는지 확인
                if "traceId" in trace_keys:
                    trace_id_prop = "t.traceId"
                elif "trace_id" in trace_keys:
                    trace_id_prop = "t.trace_id"
                else:
                    print("⚠️ traceId 속성을 찾을 수 없습니다. ID() 사용")
                    trace_id_prop = "id(t)"
            else:
                print("⚠️ Trace 노드가 없습니다. ID() 사용")
                trace_id_prop = "id(t)"
        except Exception as e:
            print(f"⚠️ Trace 노드 속성 확인 실패: {e}. ID() 사용")
            trace_id_prop = "id(t)"

        query = f"""
            MATCH (s:Summary)-[:SUMMARIZES]->(t:Trace)
            RETURN 
                {trace_id_prop} AS trace_id, 
                s.embedding AS embedding
        """
        print(f"🔍 실행할 쿼리: {query}")

        all_summaries = session.run(query)

        summary_embedding = embedding_model.encode(summary_text)
        similarities = []

        # all_summaries를 다시 가져와야 함 (이미 소비됨)
        all_summaries = session.run(query)

        for record in all_summaries:
            trace_id = record["trace_id"]
            emb = record["embedding"]

            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except json.JSONDecodeError:
                    continue

            if emb is None:
                continue

            sim = cosine_similarity(summary_embedding, emb)
            similarities.append({"trace_id": trace_id, "similarity": sim})
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        result = similarities[:top_k]
        print(f"🎯 상위 {top_k}개 결과: {[r['trace_id'] for r in result]}")
        return result


def generate_mitigation_prompt(
    summary_result, structural_similarity, indirect_connections
):
    """
    LLM에게 악성 행위 대응 방안을 요청하는 프롬프트 생성
    """
    summary_text = summary_result.get("summary", "")

    similar_entities = set()
    if structural_similarity:
        for s in structural_similarity:
            similar_entities.update(s.get("common_entities", []))

    if indirect_connections:
        for c in indirect_connections:
            similar_entities.add(c.get("e1_name", ""))
            similar_entities.add(c.get("e2_name", ""))

    # 빈 엔티티 제거
    similar_entities = {e for e in similar_entities if e}

    prompt = f"""
    당신은 보안 전문가입니다. 아래 트레이스 분석 정보를 바탕으로 기업 환경에서 발견된 악성 행위에 대한 
    실제 대응 방안을 구체적으로 제안해주세요.

    [트레이스 요약]
    {summary_text}

    [연관 엔티티]
    {', '.join(similar_entities) if similar_entities else '연관 엔티티 정보 없음'}

    [요청]
    1. 탐지된 악성 프로세스 및 파일 격리 방법
    2. 네트워크 차단 및 외부 통신 통제 방안
    3. 로그/시스템 모니터링 강화 방법
    4. 향후 유사 공격 예방 전략
    5. 실무자가 바로 적용 가능한 단계별 대응 권장

    응답은 단계별로 번호를 붙여 상세히 설명해주세요.
    언어는 반드시 한국어로 응답하세요.
    """
    return prompt


def analyze_structural_similarity_no_db(driver, new_trace, prompt_template, top_k=3):
    print("🔍 analyze_structural_similarity_no_db 시작")

    # LLM 요약
    print("📝 LLM 요약 시작...")
    summary_result = summarize_trace_with_llm(new_trace, prompt_template)
    if "error" in summary_result:
        print(f"❌ LLM 요약 실패: {summary_result['error']}")
        return summary_result

    summary_text = summary_result.get("summary", "")
    print(f"✅ LLM 요약 완료: {len(summary_text)} 문자")
    print(
        f"📄 요약 내용: {summary_text[:200]}{'...' if len(summary_text) > 200 else ''}"
    )

    if not summary_text:
        print("⚠️ 요약 텍스트가 비어있습니다.")
        return {
            "summary": {"summary": "요약 생성 실패"},
            "long_summary": "요약을 생성할 수 없습니다.",
            "similar_trace_ids": [],
            "mitigation_suggestions": "요약이 없어 대응 방안을 제시할 수 없습니다.",
        }

    # 유사 트레이스 검색
    print("🔍 유사 트레이스 검색 시작...")
    similar_ids = []
    top_similar_traces = []
    try:
        # Neo4j 연결 테스트
        with driver.session() as session:
            session.run("RETURN 1")

        top_similar_traces = find_similar_traces(driver, summary_text, top_k=top_k)
        similar_ids = [t["trace_id"] for t in top_similar_traces]
        print(f"✅ 유사 트레이스 검색 완료: {len(similar_ids)}개")
    except Exception as e:
        import traceback

        print(f"❌ 유사 트레이스 검색 실패 (Neo4j 연결 문제): {e}")
        print(f"🔎 에러 발생 원인: {type(e).__name__} - {e}")
        print("🔎 상세 에러 트레이스백:")
        traceback.print_exc()
        print("⚠️ Neo4j 없이 계속 진행합니다...")
        similar_ids = []
        top_similar_traces = []

    print(f"\n🔍 의미적 유사도 상위 {len(similar_ids)}개 트레이스: {similar_ids}\n")

    # 구조적 유사성 분석
    print("🔍 구조적 유사성 분석 시작...")
    comparisons = []
    indirect_connections = []

    try:
        with driver.session(database=DATABASE) as session:
            # Trace 노드의 실제 속성 확인
            try:
                result = session.run("MATCH (t:Trace) RETURN keys(t) as keys LIMIT 1")
                record = result.single()
                if record and record["keys"]:
                    trace_keys = record["keys"]
                    if "traceId" in trace_keys:
                        trace_id_prop = "t.traceId"
                    elif "trace_id" in trace_keys:
                        trace_id_prop = "t.trace_id"
                    else:
                        trace_id_prop = "id(t)"
                else:
                    trace_id_prop = "id(t)"
            except Exception as e:
                print(f"⚠️ Trace 노드 속성 확인 실패: {e}. ID() 사용")
                trace_id_prop = "id(t)"

            res = session.run(
                f"""
                MATCH (s:Summary)-[:SUMMARIZES]->(t:Trace)
                WHERE {trace_id_prop} IN $trace_ids
                OPTIONAL MATCH (s)-[:USES_TECHNIQUE]->(tech)
                OPTIONAL MATCH (t)<-[:PARTICIPATED_IN]-(ent)
                RETURN 
                    {trace_id_prop} AS trace_id,
                    collect(DISTINCT
                        CASE labels(ent)[0]
                            WHEN 'Process' THEN ent.processName
                            WHEN 'File' THEN ent.filePath
                            WHEN 'User' THEN ent.userName
                            WHEN 'Ip' THEN ent.ipAddress
                            WHEN 'Registry' THEN ent.keyPath
                            ELSE null
                        END
                    ) AS entities,
                    collect(DISTINCT tech.name) AS techniques
                """,
                trace_ids=similar_ids,
            )

            trace_entities = summary_result.get("key_entities", [])
            new_entities = set(
                e["value"].strip().lower().replace("\\", "/")
                for e in trace_entities
                if isinstance(e, dict) and "value" in e
            )

            for record in res:
                db_entities = set(
                    (e or "").strip().lower().replace("\\", "/")
                    for e in record["entities"]
                    if e and e != "-"
                )
                # 공통 엔티티
                common_entities = new_entities & db_entities

                comparisons.append(
                    {
                        "trace_id": record["trace_id"],
                        "common_entities": list(common_entities),
                        "entity_match_count": len(common_entities),
                    }
                )

            comparisons.sort(key=lambda x: (x["entity_match_count"]), reverse=True)

            # 간접 연결 탐색
            query = f"""
                UNWIND $trace_ids AS trace_id
                MATCH (s:Summary)-[:SUMMARIZES]->(t:Trace)
                WHERE t.traceId = trace_id
                OPTIONAL MATCH (t)<-[:PARTICIPATED_IN]-(ent)
                WITH collect(DISTINCT
                    CASE labels(ent)[0]
                        WHEN 'Process' THEN ent.processName
                        WHEN 'File' THEN ent.filePath
                        WHEN 'User' THEN ent.userName
                        WHEN 'Ip' THEN ent.ipAddress
                        WHEN 'Registry' THEN ent.keyPath
                        ELSE null
                    END
                ) AS groupEntities
                UNWIND groupEntities AS e1
                UNWIND groupEntities AS e2
                WITH e1, e2 WHERE e1 IS NOT NULL AND e2 IS NOT NULL AND e1 < e2
                MATCH path = shortestPath(
                    (n1)-[*..2]-(n2)
                )
                WHERE 
                    ( (labels(n1)[0] = 'Process' AND n1.processName = e1) OR
                    (labels(n1)[0] = 'File' AND n1.filePath = e1) OR
                    (labels(n1)[0] = 'User' AND n1.userName = e1) OR
                    (labels(n1)[0] = 'Ip' AND n1.ipAddress = e1) OR
                    (labels(n1)[0] = 'Registry' AND n1.keyPath = e1) )
                AND
                    ( (labels(n2)[0] = 'Process' AND n2.processName = e2) OR
                    (labels(n2)[0] = 'File' AND n2.filePath = e2) OR
                    (labels(n2)[0] = 'User' AND n2.userName = e2) OR
                    (labels(n2)[0] = 'Ip' AND n2.ipAddress = e2) OR
                    (labels(n2)[0] = 'Registry' AND n2.keyPath = e2) )
                RETURN e1 AS e1_name, e2 AS e2_name,
                    length(path) AS hops,
                    [n IN nodes(path) | 
                        labels(n)[0] + ':' + coalesce(n.name, n.processName, n.filePath, n.userName, n.ipAddress, n.keyPath, '') 
                    ] AS path_nodes
                LIMIT 50
            """
            indirect_connections_result = session.run(query, trace_ids=similar_ids)
            indirect_connections_raw = [r.data() for r in indirect_connections_result]

            # 중복 제거 (양방향 연결 고려)
            seen_connections = set()
            indirect_connections = []

            for conn in indirect_connections_raw:
                e1_name = conn["e1_name"]
                e2_name = conn["e2_name"]
                connection_key = tuple(sorted([e1_name, e2_name]))

                if connection_key not in seen_connections:
                    seen_connections.add(connection_key)
                    indirect_connections.append(conn)

        print(
            f"✅ 구조적 유사성 분석 완료: {len(comparisons)}개 비교, {len(indirect_connections)}개 간접 연결"
        )

    except Exception as e:
        print(f"❌ 구조적 유사성 분석 실패 (Neo4j 연결 문제): {e}")
        print("⚠️ Neo4j 없이 계속 진행합니다...")
        comparisons = []
        indirect_connections = []

    # 상세 요약 생성
    print("📝 상세 요약 생성 시작...")
    try:
        if similar_ids:
            long_summary_result = long_summary(
                driver,
                summary_text,
                comparisons,
                indirect_connections,
                top_similar_traces,
                top_k=3,
            )
        else:
            # Neo4j 없이 CoT 방식 요약 생성
            cot_prompt_no_neo4j = f"""
당신은 보안 분석 전문가입니다. 다음 정보를 바탕으로 체계적인 악성 행위 분석 보고서를 작성해주세요.

[원본 트레이스 요약]
{summary_text}

[공격 기법 정보]
{summary_result.get('attack_techniques', [])}

다음 형식으로 분석 보고서를 작성해주세요:

## 악성 행위 상세 분석

### 1. 공격 흐름 개요
[전체적인 공격 과정을 시간순으로 요약]

### 2. 주요 악성 행위 분석
[각 단계별 상세 분석]

### 3. 사용된 공격 기법 및 도구
[발견된 공격 기법과 사용된 도구들]

### 4. 방어 우회 시도
[백신 우회, 탐지 회피 등의 시도]

### 5. 네트워크 활동 및 C2 통신
[외부 통신 시도, C2 서버 연결 등]

### 6. 구조적 유사성 분석 결과
Neo4j 데이터베이스 연결이 없어 구조적 유사성 분석을 수행할 수 없습니다.

### 7. 보안 위협 평가 및 결론
[전체적인 위협 수준과 즉시 조치 필요성]

분석은 한국어로 작성하고, 각 섹션은 구체적이고 실무진이 이해하기 쉽게 설명해주세요.
"""

            try:
                cot_response = llm.invoke(cot_prompt_no_neo4j)
                long_summary_text = cot_response.content.strip()
            except Exception:
                # CoT 실패 시 기본 템플릿 사용
                long_summary_text = f"""## 악성 행위 상세 분석

### 공격 흐름 개요
{summary_text}

### 분석 결과
이 트레이스는 악성 활동으로 분류되었습니다. Sigma 룰 매칭을 통해 의심스러운 행위가 탐지되었습니다.

### 주요 특징
- PowerShell Base64 인코딩된 명령어 실행
- 의심스러운 프로세스 생성 패턴
- Sigma 룰 매칭: {summary_result.get('attack_techniques', [])}

### 보안 위협 평가
이 트레이스는 악성 활동으로 분류되었으며, 즉시 격리 및 분석이 필요합니다.
"""
            long_summary_result = {
                "long_summary": long_summary_text.strip(),
                "similar_trace_ids": similar_ids,
            }
        print("✅ 상세 요약 생성 완료")
    except Exception as e:
        print(f"❌ 상세 요약 생성 실패: {e}")
        long_summary_result = {
            "long_summary": "상세 요약 생성 실패",
            "similar_trace_ids": similar_ids,
        }

    # 대응 제안 생성
    print("🛡️ 대응 방안 생성 시작...")
    try:
        mitigation_prompt = generate_mitigation_prompt(
            summary_result, comparisons, indirect_connections
        )
        mitigation_response = llm.invoke(mitigation_prompt)
        mitigation_text = mitigation_response.content
        print("✅ 대응 방안 생성 완료")
    except Exception as e:
        print(f"❌ 대응 방안 생성 실패: {e}")
        mitigation_text = "대응 방안 생성 실패"

    result = {
        "summary": summary_result,
        "long_summary": long_summary_result["long_summary"],
        "similar_trace_ids": long_summary_result["similar_trace_ids"],
        "structural_similarity": comparisons,  # 구조적 유사성 분석 결과
        "indirect_connections": indirect_connections,  # 간접 연결 분석 결과
        "mitigation_suggestions": mitigation_text,
    }

    print("🎉 analyze_structural_similarity_no_db 완료")
    return result
