import os

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

# Gemini API 사용을 위한 langchain_google_genai 임포트
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    print("❌ langchain-google-genai가 설치되지 않았습니다!")
    print("💡 다음 명령어로 설치하세요: pip install langchain-google-genai")
    raise

# Gemini API 키 확인
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    print(f"✅ Gemini API 키 설정됨: {gemini_key[:10]}...")
else:
    print("❌ GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수가 설정되지 않았습니다!")
    print("💡 다음 방법 중 하나를 사용하세요:")
    print("   1. .env 파일에 GEMINI_API_KEY=your-key-here 추가")
    print("   2. .env 파일에 GOOGLE_API_KEY=your-key-here 추가")
    print("   3. 환경변수 직접 설정: set GEMINI_API_KEY=your-key-here (Windows)")
    print("   4. 환경변수 직접 설정: export GEMINI_API_KEY='your-key-here' (Linux/Mac)")

# 사용 가능한 Gemini 모델 (2025년 최신):
# - "gemini-2.5-pro": 최신 고성능 모델 (최신, 권장)
# - "gemini-2.0-flash-exp": 실험 버전 빠른 모델
# - "gemini-1.5-pro": 안정적인 고성능 모델
# - "gemini-1.5-flash": 빠른 응답 모델
# - "gemini-1.5-pro-latest": 최신 1.5 프로 버전
# - "gemini-pro": 범용 모델 (구버전)
# - "gemini-pro-vision": 이미지 처리 지원 모델

try:

    # Gemini 모델 초기화
    # 최신 Gemini 모델은 max_output_tokens 파라미터 사용
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        google_api_key=gemini_key,  # API 키 명시적 전달 (ADC 오류 방지)
        temperature=0.1,  # 사실 기반, 정확한 출력을 위해 낮게 설정
        convert_system_message_to_human=True,  # 시스템 메시지 변환
    )

    print("✅ ChatGoogleGenerativeAI 클라이언트 초기화 완료")
    print("   - Temperature: 0.1 (정확성 중심)")
    print("   💡 Gemini는 구조화된 JSON 출력을 지원합니다.")

except Exception as e:
    print(f"❌ ChatGoogleGenerativeAI 클라이언트 초기화 실패: {e}")
    print("   ⚠️ Gemini API 키가 유효하지 않거나 모델이 사용 불가능할 수 있습니다.")
    print(
        "   💡 API 키는 Google AI Studio (https://makersuite.google.com/app/apikey)에서 발급받을 수 있습니다."
    )
    raise
