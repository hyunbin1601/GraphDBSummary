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

try:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    print("✅ ChatOpenAI 클라이언트 초기화 완료")
except Exception as e:
    print(f"❌ ChatOpenAI 클라이언트 초기화 실패: {e}")
    raise
