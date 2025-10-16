#!/usr/bin/env bash
set -euo pipefail

# 환경변수 설정
export NEO4J_URI="neo4j+s://bd07fa08.databases.neo4j.io"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="5d3Jlb3abtyNANIDQcvJERS9ndXdtL8hFw5oiSZrWew"
export NEO4J_DATABASE="neo4j"

export KAFKA_BOOTSTRAP_SERVERS="172.31.11.219:19092"
export KAFKA_INPUT_TOPIC="ensemble_predict"
export KAFKA_OUTPUT_TOPIC="llm_result"

export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -U pip
pip install -r requirements.txt

# 애플리케이션 실행
python producer.py
