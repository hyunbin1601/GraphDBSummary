from kafka import KafkaProducer, KafkaConsumer
import json
import os
from graphdb import analyze_structural_similarity_no_db
from neo4j_driver import driver

# 외부 Kafka 브로커 및 토픽 설정
# 환경변수로 덮어쓸 수 있게 하고, 기본값은 외부 브로커 / 토픽 사용
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "172.31.11.219:19092"
).split(",")
INPUT_TOPIC = os.getenv("KAFKA_INPUT_TOPIC", "ensemble_predict")
OUTPUT_TOPIC = os.getenv("KAFKA_OUTPUT_TOPIC", "llm_result")

# 프롬프트 파일은 프로젝트 루트의 summary_prompt.md를 기본으로 사용
PROMPT_FILE = os.path.join(os.path.dirname(__file__), "summary_prompt.md")


def load_prompt_template():
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"오류: '{os.path.abspath(PROMPT_FILE)}' 파일을 찾을 수 없습니다.")
        return None


def build_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
    )


def build_consumer():
    return KafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: safe_json_decode(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=os.getenv("KAFKA_CONSUMER_GROUP", "graphdb-summary-consumer"),
    )


def safe_json_decode(json_str):
    """JSON 파싱 오류를 안전하게 처리 - OTLP 형식도 처리"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류 (OTLP 형식일 수 있음): {e}")
        print(f"원본 문자열 길이: {len(json_str)}")
        # OTLP 형식으로 가정하고 원본 문자열을 dict로 래핑
        return {"raw_otlp_data": json_str}


def extract_trace_input(msg_value):
    # - dict 그대로 트레이스(JSON)일 수 있음
    # - {"trace": {...}} 래핑일 수 있음
    # - {"trace_path": "..."} 로 파일 경로가 올 수 있음
    # 입력 메세지에서 트레이스 추출
    if isinstance(msg_value, dict):
        if "trace" in msg_value and isinstance(msg_value["trace"], (dict, list)):
            return msg_value["trace"]
        if "trace_path" in msg_value and isinstance(msg_value["trace_path"], str):
            return msg_value["trace_path"]
        return msg_value
    return msg_value


def _extract_attr_value(attr_value_obj):
    """OTLP attribute value(JSON)에서 실제 값을 추출"""
    if not isinstance(attr_value_obj, dict):
        return attr_value_obj
    for k in ("stringValue", "intValue", "doubleValue", "boolValue"):
        if k in attr_value_obj:
            return attr_value_obj[k]
    if "arrayValue" in attr_value_obj and isinstance(
        attr_value_obj["arrayValue"], dict
    ):
        values = attr_value_obj["arrayValue"].get("values", [])
        return [_extract_attr_value(v) if isinstance(v, dict) else v for v in values]
    if "kvlistValue" in attr_value_obj and isinstance(
        attr_value_obj["kvlistValue"], dict
    ):
        items = attr_value_obj["kvlistValue"].get("values", [])
        return {
            i.get("key"): _extract_attr_value(i.get("value"))
            for i in items
            if isinstance(i, dict)
        }
    return attr_value_obj


def normalize_otlp_trace(otlp_trace):
    """OTLP(OpenTelemetry) 형식의 trace를 내부 처리형식({traceID, spans:[{tags:[]}]} )으로 변환"""
    norm = {"traceID": None, "spans": []}
    # traceId는 각 span에 존재하므로 첫 span에서 가져옵니다.
    if not isinstance(otlp_trace, dict):
        return otlp_trace

    # 먼저 최상위에서 traceID 찾기
    norm["traceID"] = otlp_trace.get("traceID") or otlp_trace.get("traceId")

    resource_spans = otlp_trace.get("resourceSpans", [])
    for rs in resource_spans:
        scope_spans = rs.get("scopeSpans", [])
        for ss in scope_spans:
            spans = ss.get("spans", [])
            for sp in spans:
                # span에서 traceID가 있으면 사용 (더 정확할 수 있음)
                if norm["traceID"] is None:
                    norm["traceID"] = sp.get("traceId")
                tags = []
                for attr in sp.get("attributes", []):
                    key = attr.get("key")
                    val_obj = attr.get("value")
                    val = _extract_attr_value(val_obj)
                    tags.append({"key": key, "value": val})
                # 기존 필드도 보존
                op_name = sp.get("name")
                if op_name:
                    tags.append({"key": "operationName", "value": op_name})
                span_entry = {
                    "traceID": sp.get("traceId"),
                    "spanID": sp.get("spanId"),
                    "operationName": op_name,
                    "tags": tags,
                }
                norm["spans"].append(span_entry)
    return norm


def _iter_traces_from_message(msg_value):
    """Kafka 메시지에서 OTLP 트레이스들을 순회합니다.
    - dict + resourceSpans: 단일 OTLP 트레이스
    - dict + trace(otlp): 래핑된 단일
    - list[dict]: 여러 트레이스
    - str: 라인단위 JSON들일 수 있어 각 라인 파싱 시도
    반환: (otlp_trace_dict, passthrough_dict)
    """

    def _passthrough_from(obj):
        if isinstance(obj, dict):
            out = {}
            if "score" in obj:
                out["score"] = obj["score"]
            if "prediction" in obj:
                out["prediction"] = obj["prediction"]
            if "traceID" in obj:
                out["traceID"] = obj["traceID"]
            return out
        return {}

    if isinstance(msg_value, dict):
        # JSON 파싱 실패한 OTLP 원본 데이터 처리
        if "raw_otlp_data" in msg_value:
            raw_data = msg_value["raw_otlp_data"]
            try:
                # 다시 JSON 파싱 시도
                parsed = json.loads(raw_data)
                yield from _iter_traces_from_message(parsed)
                return
            except json.JSONDecodeError:
                # 여전히 파싱 실패하면 원본 문자열을 그대로 처리
                print(f"OTLP 원본 데이터를 문자열로 처리합니다. 길이: {len(raw_data)}")
                yield {"raw_string": raw_data}, {}
                return

        # 사용자가 제공한 형식: {"traceID": "...", "score": ..., "prediction": "...", "trace": "..."}
        if "trace" in msg_value and isinstance(msg_value["trace"], str):
            try:
                # trace가 JSON 문자열인 경우 파싱
                parsed_trace = json.loads(msg_value["trace"])
                yield parsed_trace, _passthrough_from(msg_value)
                return
            except json.JSONDecodeError:
                # JSON 파싱 실패시 원본 문자열 그대로 처리
                yield {"raw_string": msg_value["trace"]}, _passthrough_from(msg_value)
                return

        # 사용자가 제공한 형식: {"traceID": "...", "score": ..., "prediction": "...", "trace": {...}}
        if "trace" in msg_value and isinstance(msg_value["trace"], dict):
            yield msg_value["trace"], _passthrough_from(msg_value)
            return

        if "resourceSpans" in msg_value:
            yield msg_value, _passthrough_from(msg_value)
            return

        # dict지만 명확치 않으면 그대로 시도
        yield msg_value, _passthrough_from(msg_value)
        return

    if isinstance(msg_value, list):
        for item in msg_value:
            if isinstance(item, dict):
                if "trace" in item and isinstance(item["trace"], dict):
                    yield item["trace"], _passthrough_from(item)
                elif "resourceSpans" in item:
                    yield item, _passthrough_from(item)
                else:
                    yield item, _passthrough_from(item)
        return

    if isinstance(msg_value, str):
        # 라인단위 JSON 파싱 시도
        for line in msg_value.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            yield from _iter_traces_from_message(obj)
        return

    # 기타 타입은 그대로 단일로 시도
    yield msg_value, {}


if __name__ == "__main__":
    prompt_template = load_prompt_template()
    if not prompt_template:
        exit(1)

    print(
        f"Kafka 연결: servers={KAFKA_BOOTSTRAP_SERVERS}, input='{INPUT_TOPIC}', output='{OUTPUT_TOPIC}'"
    )

    producer = build_producer()
    consumer = build_consumer()

    print("입력 토픽에서 트레이스를 수신하여 분석을 시작합니다...")
    for message in consumer:
        try:
            raw_value = message.value
            for otlp_trace, passthrough in _iter_traces_from_message(raw_value):
                # 모든 트레이스에 대해 정규화 수행
                trace_input = (
                    normalize_otlp_trace(otlp_trace)
                    if isinstance(otlp_trace, dict)
                    else otlp_trace
                )

                # 입력 트레이스의 traceID를 결과에 포함(상관관계용)
                source_trace_id = None
                # 먼저 passthrough에서 traceID 확인 (사용자 제공 형식)
                if passthrough.get("traceID"):
                    source_trace_id = passthrough.get("traceID")
                elif isinstance(trace_input, dict):
                    source_trace_id = trace_input.get("traceID") or trace_input.get(
                        "traceId"
                    )

                # 정상으로 판정된 트레이스는 간단한 요약으로 처리
                if passthrough.get("prediction") == "benign":
                    out_message = {
                        "traceID": source_trace_id,
                        "summary": {"summary": "정상 트레이스입니다."},
                        "long_summary": "## 상세 분석 요약\n\n### 분석 결과\n이 트레이스는 정상으로 분류되었습니다. 추가 분석이 필요하지 않습니다.",
                        "similar_trace_ids": [],
                        "mitigation_suggestions": "정상 트레이스로 판정되어 대응 조치가 필요하지 않습니다.",
                    }
                    # passthrough에서 traceID를 제외하고 업데이트 (traceID는 이미 설정됨)
                    passthrough_copy = passthrough.copy()
                    passthrough_copy.pop("traceID", None)
                    out_message.update(passthrough_copy)

                    producer.send(OUTPUT_TOPIC, out_message)
                    producer.flush()
                    print(f"정상 트레이스 처리 완료: traceID={source_trace_id}")
                    continue

                # 악성 트레이스는 LLM 분석 수행
                try:
                    results = analyze_structural_similarity_no_db(
                        driver, trace_input, prompt_template, top_k=3
                    )
                except Exception as e:
                    print(f"⚠️ Neo4j 연결 실패로 인한 오류: {e}")
                    print("🔄 Neo4j 없이 LLM 분석만 수행합니다...")

                    # Neo4j 없이 기본 분석 수행
                    from graphdb import summarize_trace_with_llm

                    summary_result = summarize_trace_with_llm(
                        trace_input, prompt_template
                    )

                    if "error" in summary_result:
                        print(f"❌ LLM 요약 실패: {summary_result['error']}")
                        results = {
                            "summary": {"summary": "분석 실패"},
                            "long_summary": "분석을 완료할 수 없습니다.",
                            "similar_trace_ids": [],
                            "mitigation_suggestions": "분석 실패로 인해 대응 방안을 제시할 수 없습니다.",
                        }
                    else:
                        summary_text = summary_result.get("summary", "")
                        results = {
                            "summary": summary_result,
                            "long_summary": f"## 상세 분석 요약\n\n### 원본 트레이스 요약\n{summary_text}\n\n### 분석 결과\n이 트레이스는 악성 활동으로 분류되었습니다.",
                            "similar_trace_ids": [],
                            "mitigation_suggestions": "## 보안 대응 방안\n\n1. **프로세스 격리**: 의심스러운 프로세스 즉시 종료\n2. **시스템 스캔**: 전체 시스템 악성코드 스캔 수행\n3. **로그 분석**: 시스템 로그 전체 분석을 통한 추가 위협 탐지",
                        }

                # summary에서 key_entities 제거하고 간단한 요약만 포함
                summary_data = results.get("summary", {})
                simple_summary = {
                    "summary": summary_data.get("summary", ""),
                    # "attack_techniques": summary_data.get("attack_techniques", []),
                }

                # 유사 트레이스 정보 출력
                similar_trace_ids = results.get("similar_trace_ids", [])
                print(f"\n🔍 구조적 연결성 분석 결과:")
                print(f"   📊 유사 트레이스 개수: {len(similar_trace_ids)}")
                if similar_trace_ids:
                    print(f"   📋 유사 트레이스 ID 목록:")
                    for i, trace_id in enumerate(similar_trace_ids, 1):
                        print(f"      {i}. {trace_id}")
                else:
                    print("   ⚠️ 유사한 트레이스를 찾을 수 없습니다.")

                # 요약 정보 출력
                summary_text = summary_data.get("summary", "")
                if summary_text:
                    print(
                        f"   📝 요약: {summary_text[:100]}{'...' if len(summary_text) > 100 else ''}"
                    )

                # 공격 기법 정보 출력
                attack_techniques = summary_data.get("attack_techniques", [])
                if attack_techniques:
                    print(f"   ⚔️ 탐지된 공격 기법: {', '.join(attack_techniques)}")

                out_message = {
                    "traceID": source_trace_id,
                    "summary": simple_summary,
                    "long_summary": results.get("long_summary", ""),
                    "similar_trace_ids": similar_trace_ids,
                    "mitigation_suggestions": results.get("mitigation_suggestions", ""),
                }
                # passthrough에서 traceID를 제외하고 업데이트 (traceID는 이미 설정됨)
                passthrough_copy = passthrough.copy()
                passthrough_copy.pop("traceID", None)
                out_message.update(passthrough_copy)

                producer.send(OUTPUT_TOPIC, out_message)
                producer.flush()
                print(
                    f"✅ 분석 결과를 Kafka 토픽 '{OUTPUT_TOPIC}'로 전송했습니다. traceID={source_trace_id}"
                )
                print("=" * 80)
        except Exception as e:
            print(f"메시지 처리 중 오류: {e}")
            print(f"메시지 내용: {str(message.value)[:200]}...")
