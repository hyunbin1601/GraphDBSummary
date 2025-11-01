"""
OpenAI API 응답 테스트 스크립트
여러 모델(gpt-5, gpt-4o 등)의 API 응답을 테스트할 수 있습니다.
"""

import os
import json
import time
from datetime import datetime
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 테스트할 모델 목록
TEST_MODELS = [
    "gpt-5",
    "gpt-4o",
    "gpt-4o-mini",
    "o3-pro",
    "o3-mini",
]

# API 키 확인
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다!")
    print("💡 .env 파일에 OPENAI_API_KEY=your-key-here 추가하세요.")
    exit(1)

print(f"✅ OpenAI API 키 확인됨: {openai_key[:10]}...\n")


def test_simple_prompt(model_name: str):
    """간단한 프롬프트로 기본 응답 테스트"""
    print(f"\n{'='*60}")
    print(f"📝 테스트 1: 간단한 프롬프트 - {model_name}")
    print(f"{'='*60}")

    try:
        # 모델 초기화
        if model_name in ["o3-pro", "o3-mini"]:
            llm = ChatOpenAI(model=model_name, timeout=600)
        else:
            llm = ChatOpenAI(
                model=model_name,
                temperature=0.1,
                max_tokens=1000,
                top_p=0.95,
                timeout=120,
            )

        prompt = "안녕하세요. 간단히 자기소개를 한 문장으로 해주세요."

        print(f"프롬프트: {prompt}")
        print("응답 대기 중...")

        start_time = time.time()
        response = llm.invoke(prompt)
        elapsed_time = time.time() - start_time

        print(f"✅ 응답 시간: {elapsed_time:.2f}초")
        print(f"응답 내용:\n{response.content[:200]}")

        return {"success": True, "time": elapsed_time, "response": response.content}

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return {"success": False, "error": str(e)}


def test_json_output(model_name: str):
    """구조화된 JSON 출력 테스트"""
    print(f"\n{'='*60}")
    print(f"📝 테스트 2: JSON 출력 테스트 - {model_name}")
    print(f"{'='*60}")

    try:
        # 모델 초기화
        if model_name in ["o3-pro", "o3-mini"]:
            llm = ChatOpenAI(model=model_name, timeout=600)
        else:
            llm = ChatOpenAI(
                model=model_name,
                temperature=0.1,
                max_tokens=2000,
                top_p=0.95,
                timeout=120,
            )

        prompt = """다음 정보를 JSON 형식으로 출력해주세요:
{
  "name": "테스트",
  "description": "이것은 테스트입니다",
  "items": ["항목1", "항목2"]
}

마크다운 코드 블록 없이 순수 JSON만 출력하세요."""

        print(f"프롬프트: JSON 형식 요청")
        print("응답 대기 중...")

        start_time = time.time()
        response = llm.invoke(prompt)
        elapsed_time = time.time() - start_time

        print(f"✅ 응답 시간: {elapsed_time:.2f}초")
        print(f"응답 내용:\n{response.content}")

        # JSON 파싱 테스트
        try:
            cleaned = response.content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("\n", 1)[0]

            parsed_json = json.loads(cleaned)
            print("✅ JSON 파싱 성공!")
            return {
                "success": True,
                "time": elapsed_time,
                "json_parseable": True,
                "response": response.content,
            }
        except json.JSONDecodeError:
            print("⚠️ JSON 파싱 실패 - 응답이 유효한 JSON이 아닙니다.")
            return {
                "success": True,
                "time": elapsed_time,
                "json_parseable": False,
                "response": response.content,
            }

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return {"success": False, "error": str(e)}


def test_security_analysis(model_name: str):
    """보안 분석 보고서 스타일 테스트"""
    print(f"\n{'='*60}")
    print(f"📝 테스트 3: 보안 분석 보고서 테스트 - {model_name}")
    print(f"{'='*60}")

    try:
        # 모델 초기화
        if model_name in ["o3-pro", "o3-mini"]:
            llm = ChatOpenAI(model=model_name, timeout=600)
        else:
            llm = ChatOpenAI(
                model=model_name,
                temperature=0.1,
                max_tokens=3000,
                top_p=0.95,
                timeout=120,
            )

        prompt = """다음 공격 정보를 분석하여 JSON 형식으로 출력해주세요:

공격 정보:
- 프로세스: setup.exe가 cmd.exe를 실행
- 파일: C:\\Users\\Test\\malware.exe 파일 생성
- 네트워크: 192.168.1.100:8080으로 연결

다음 형식의 JSON 객체를 출력하세요:
{
  "summary": "공격 요약 (최소 100자)",
  "key_entities": [
    {"type": "Process", "value": "프로세스명"},
    {"type": "File", "value": "파일경로"},
    {"type": "IP Address", "value": "IP주소"}
  ],
  "attack_techniques": [
    {"id": "T1059", "name": "Command and Scripting Interpreter"}
  ]
}

마크다운 코드 블록 없이 순수 JSON만 출력하세요."""

        print(f"프롬프트: 보안 분석 보고서 형식 요청")
        print("응답 대기 중...")

        start_time = time.time()
        response = llm.invoke(prompt)
        elapsed_time = time.time() - start_time

        print(f"✅ 응답 시간: {elapsed_time:.2f}초")
        print(f"응답 내용:\n{response.content[:500]}...")

        # JSON 파싱 테스트
        try:
            cleaned = response.content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("\n", 1)[0]

            parsed_json = json.loads(cleaned)
            print("✅ JSON 파싱 성공!")
            print(f"   - Summary 길이: {len(parsed_json.get('summary', ''))} 문자")
            print(f"   - Key Entities: {len(parsed_json.get('key_entities', []))}개")
            print(
                f"   - Attack Techniques: {len(parsed_json.get('attack_techniques', []))}개"
            )

            return {
                "success": True,
                "time": elapsed_time,
                "json_parseable": True,
                "response": response.content,
            }
        except json.JSONDecodeError:
            print("⚠️ JSON 파싱 실패 - 응답이 유효한 JSON이 아닙니다.")
            return {
                "success": True,
                "time": elapsed_time,
                "json_parseable": False,
                "response": response.content,
            }

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return {"success": False, "error": str(e)}


def test_long_summary_prompt(model_name: str):
    """GraphDB의 long_summary 프롬프트 테스트 (비교용)"""
    print(f"\n{'='*60}")
    print(f"📝 테스트 4: Long Summary Prompt 테스트 - {model_name}")
    print(f"{'='*60}")

    try:
        # 모델 초기화
        if model_name in ["o3-pro", "o3-mini"]:
            llm = ChatOpenAI(model=model_name, timeout=600)
        else:
            llm = ChatOpenAI(
                model=model_name,
                temperature=0.1,
                max_tokens=4000,
                top_p=0.95,
                timeout=120,
            )

        # graphdb.py의 실제 사용 프롬프트 사용
        summary_text = """악성 프로세스 riding.pif가 cmd.exe를 통해 여러 시스템 명령어를 실행했습니다.
주요 활동:
- tasklist.exe로 실행 중인 프로세스 목록 확인
- findstr.exe로 브라우저 비밀번호 데이터베이스 검색
- extrac32.exe로 파일 압축 해제
- 외부 IP 203.0.113.42:8080으로 네트워크 연결 시도"""

        similar_trace_ids = ["trace1234567890", "trace0987654321", "trace1122334455"]

        cot_prompt = f"""
당신은 지니언스(Genians)나 FireEye 같은 전문 보안 기관의 글로벌 위협 인텔리전스 분석가입니다.
제공된 정보를 바탕으로 EDR 제품에 수록될 수준의 전문 보안 분석 보고서를 작성해주세요.

[원본 트레이스 요약]
{summary_text}

[유사한 트레이스 정보]
- 상위 {len(similar_trace_ids)}개 유사 트레이스: {', '.join([tid[:8] + '...' for tid in similar_trace_ids])}

다음 구조로 전문 보안 보고서를 작성하세요:

## 악성 행위 상세 분석

### 1. 공격 흐름 개요 (Attack Flow)
공격 흐름 그래프를 그릴 수 있을 만큼 각 단계를 자세히, 정확하게 작성하세요.

필수 포함 사항:
- 호스트 정보: 호스트명, 도메인/워크그룹, 사용자 계정
- 단계별 프로세스 실행 체인: 각 프로세스 단계를 명확히 번호로 구분
- 부모-자식 프로세스 관계: 각 프로세스의 Real Parent Process, Parent Process 명시
- 공격 타임라인을 초기부터 시간순으로 단계별로 상세히 서술
- 각 단계의 프로세스 실행, 파일 조작, 네트워크 활동의 인과관계를 명확히 설명

### 2. 주요 악성 행위 분석
각 공격 단계를 다음과 같이 세분화하여 분석하세요:

2.1 초기 침투(Initial Access)
- 첫 번째 악성 프로세스 실행 방법과 트리거 메커니즘 상세 기술
- 부모 프로세스(Real Parent Process)와의 관계

2.2 실행(Execution)
- 악성코드 실행 방식과 사용된 실행 도구 상세 분석
- 각 실행 도구가 수행한 구체적인 작업

2.3 데이터 수집/유출
- 접근한 파일의 전체 경로, 파일 크기, 작업 유형
- 탈취 의도가 있는 데이터 범주와 구체적인 파일 정보

### 3. 사용된 공격 기법 및 도구
- MITRE ATT&CK 프레임워크에 매핑된 구체적인 테크닉 ID와 설명
- 관찰된 실행 도구와 각 도구의 악용 방식 상세 기술

### 4. 네트워크 활동 및 C2 통신
- 외부 IP 주소, 포트 번호, 통신 프로토콜 구체적 정보
- C2 인프라의 특징
- 통신 타이밍, 빈도, 데이터 전송 추정

작성 지침:
- 모든 단락은 구체적인 사실과 관찰된 증거만을 기반으로 자세히, 정확히 작성하세요.
- 전문 보안 산업 용어를 사용하되, 실무진이 이해할 수 있는 수준으로 설명하세요.
- 한국어로 작성하고, 지니언스 리포트와 같은 전문적이고 권위 있는 문체를 유지하세요.
- 코드를 작성할 때, 그 이외의 상황에서도 마크다운 코드의 블록 표시(```)나 코드 블록 닫기 표시를 사용하지 마세요
"""

        print(f"프롬프트: Long Summary 보안 보고서 형식 요청")
        print("응답 대기 중...")

        start_time = time.time()
        response = llm.invoke(cot_prompt)
        elapsed_time = time.time() - start_time

        print(f"✅ 응답 시간: {elapsed_time:.2f}초")
        print(f"응답 내용 (처음 1000자):\n{response.content[:1000]}...")
        print(f"전체 응답 길이: {len(response.content)} 문자")

        return {
            "success": True,
            "time": elapsed_time,
            "response": response.content,
            "length": len(response.content),
        }

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("🔬 OpenAI API 응답 테스트 시작")
    print("=" * 60)
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"테스트할 모델: {', '.join(TEST_MODELS)}")

    results = {}

    for model_name in TEST_MODELS:
        print(f"\n\n{'#'*60}")
        print(f"🧪 모델 테스트: {model_name}")
        print(f"{'#'*60}")

        model_results = {}

        # 테스트 1: 간단한 프롬프트
        try:
            result1 = test_simple_prompt(model_name)
            model_results["simple_prompt"] = result1
        except Exception as e:
            model_results["simple_prompt"] = {"success": False, "error": str(e)}

        # 간단한 테스트가 실패하면 다음 테스트 스킵
        if not model_results["simple_prompt"].get("success", False):
            print(
                f"⚠️ {model_name} 모델은 사용 불가능하거나 오류가 있습니다. 다음 모델로 넘어갑니다."
            )
            results[model_name] = model_results
            continue

        time.sleep(1)  # API 호출 간격

        # 테스트 2: JSON 출력
        try:
            result2 = test_json_output(model_name)
            model_results["json_output"] = result2
        except Exception as e:
            model_results["json_output"] = {"success": False, "error": str(e)}

        time.sleep(1)

        # 테스트 3: 보안 분석 보고서
        try:
            result3 = test_security_analysis(model_name)
            model_results["security_analysis"] = result3
        except Exception as e:
            model_results["security_analysis"] = {"success": False, "error": str(e)}

        time.sleep(1)

        # 테스트 4: Long Summary Prompt (비교용)
        try:
            result4 = test_long_summary_prompt(model_name)
            model_results["long_summary"] = result4
        except Exception as e:
            model_results["long_summary"] = {"success": False, "error": str(e)}

        results[model_name] = model_results

    # 결과 요약
    print("\n\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    for model_name, model_results in results.items():
        print(f"\n{model_name}:")
        if not model_results.get("simple_prompt", {}).get("success", False):
            print("  ❌ 모델 사용 불가능")
            continue

        simple_time = model_results.get("simple_prompt", {}).get("time", 0)
        json_success = model_results.get("json_output", {}).get("json_parseable", False)
        security_success = model_results.get("security_analysis", {}).get(
            "json_parseable", False
        )
        long_summary_time = model_results.get("long_summary", {}).get("time", 0)
        long_summary_length = model_results.get("long_summary", {}).get("length", 0)

        print(f"  ✅ 기본 응답 시간: {simple_time:.2f}초")
        print(
            f"  {'✅' if json_success else '❌'} JSON 출력: {'성공' if json_success else '실패'}"
        )
        print(
            f"  {'✅' if security_success else '❌'} 보안 분석 JSON: {'성공' if security_success else '실패'}"
        )
        print(
            f"  ✅ Long Summary 시간: {long_summary_time:.2f}초, 길이: {long_summary_length}자"
        )

    # 결과 저장
    with open("api_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 상세 결과가 api_test_results.json 파일에 저장되었습니다.")


if __name__ == "__main__":
    main()
