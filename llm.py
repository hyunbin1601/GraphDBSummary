import os
from langchain_openai import ChatOpenAI

# .env 파일 로드 (python-dotenv 패키지 필요)
try:
    from dotenv import load_dotenv

    load_dotenv()
    print(".env 파일 로드 성공")
except ImportError:
    print(
        "⚠️ python-dotenv가 설치되지 않았습니다. pip install python-dotenv로 설치하세요."
    )
except Exception as e:
    print(f"⚠️ .env 파일 로드 실패: {e}")

# OPENAI_API_KEY가 설정되어 있을 때만 환경변수에 설정
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    os.environ["OPENAI_API_KEY"] = openai_key
    print(f"✅ OpenAI API 키 설정됨: {openai_key[:10]}...")
else:
    print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다!")
    print("💡 다음 방법 중 하나를 사용하세요:")
    print("   1. .env 파일에 OPENAI_API_KEY=your-key-here 추가")
    print("   2. 환경변수 직접 설정: set OPENAI_API_KEY=your-key-here (Windows)")
    print("   3. 환경변수 직접 설정: export OPENAI_API_KEY='your-key-here' (Linux/Mac)")

# o3-pro 모델 사용
# o3-pro는 OpenAI의 최신 reasoning 모델로, 복잡한 추론 작업에 특화되어 있습니다.
# 특징:
# - temperature, top_p, max_tokens 등 파라미터를 지원하지 않음 (reasoning 모델 특성)
# - 응답 시간이 길 수 있으므로 timeout을 충분히 설정
# - 복잡한 보안 분석 및 추론 작업에 강함

try:
    # o3-pro 모델 초기화
    # reasoning 모델이므로 파라미터 조정 불가
    llm = ChatOpenAI(
        model="o3-pro",
        # timeout=300,  # reasoning 모델은 응답 시간이 길 수 있으므로 타임아웃 확대
    )

    print("✅ ChatOpenAI 클라이언트 초기화 완료")
    print("   - 모델: o3-pro (Reasoning 모델)")
    print("   - Timeout: 300초 (긴 추론 시간 고려)")
    print("   ⚠️ Reasoning 모델은 temperature/top_p 파라미터를 지원하지 않습니다.")
except Exception as e:
    print(f"❌ ChatOpenAI 클라이언트 초기화 실패: {e}")
    raise
