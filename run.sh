#!/usr/bin/env bash

echo "🚀 GraphDB Summary 시스템 시작"
echo "================================"

# 환경변수 설정
export NEO4J_URI="neo4j+s://bd07fa08.databases.neo4j.io"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="5d3Jlb3abtyNANIDQcvJERS9ndXdtL8hFw5oiSZrWew"
export NEO4J_DATABASE="neo4j"

export KAFKA_BOOTSTRAP_SERVERS="172.31.11.219:19092"
export KAFKA_INPUT_TOPIC="ensemble_predict"
export KAFKA_OUTPUT_TOPIC="llm_result"

export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

echo "📋 환경 설정:"
echo "   Neo4j URI: $NEO4J_URI"
echo "   Kafka Broker: $KAFKA_BOOTSTRAP_SERVERS"
echo "   Input Topic: $KAFKA_INPUT_TOPIC"
echo "   Output Topic: $KAFKA_OUTPUT_TOPIC"
echo ""

echo "🔍 Kafka 토픽에서 트레이스 수신 대기 중..."
echo "   (Ctrl+C로 종료)"
echo ""

# 애플리케이션 실행(시스템 파이썬)
python3 producer.py
