import os
from langchain_openai import ChatOpenAI

# OPENAI_API_KEY가 설정되어 있을 때만 환경변수에 설정
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    os.environ["OPENAI_API_KEY"] = openai_key

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
