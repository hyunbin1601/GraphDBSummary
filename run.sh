#!/usr/bin/env bash

# 환경변수 설정
export NEO4J_URI="neo4j+s://bd07fa08.databases.neo4j.io"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="5d3Jlb3abtyNANIDQcvJERS9ndXdtL8hFw5oiSZrWew"
export NEO4J_DATABASE="neo4j"

export KAFKA_BOOTSTRAP_SERVERS="172.31.11.219:19092"
export KAFKA_INPUT_TOPIC="ensemble_predict"
export KAFKA_OUTPUT_TOPIC="llm_result"

export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"


# 애플리케이션 실행(시스템 파이썬)
python3 producer.py
