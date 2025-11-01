#!/usr/bin/env bash

# nohup으로 실행될 때 출력이 파일로만 가기 때문에 콘솔 확인용
echo "🚀 GraphDB Summary 시스템 시작" >&2
echo "================================" >&2

# 이미 실행 중인 프로세스가 있는지 확인
EXISTING_PID=$(pgrep -f "python3 producer.py" | grep -v $$)
if [ ! -z "$EXISTING_PID" ]; then
    echo "⚠️  이미 실행 중인 프로세스가 있습니다:" >&2
    ps aux | grep "producer.py" | grep -v grep >&2
    echo "" >&2
    echo "🛑 기존 프로세스를 자동으로 종료합니다..." >&2
    pkill -f "python3 producer.py"
    sleep 2
    echo "✅ 종료 완료" >&2
fi

# 환경변수 설정
export NEO4J_URI="neo4j+s://bd07fa08.databases.neo4j.io"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="5d3Jlb3abtyNANIDQcvJERS9ndXdtL8hFw5oiSZrWew"
export NEO4J_DATABASE="neo4j"

export KAFKA_BOOTSTRAP_SERVERS="172.31.11.219:19092"
export KAFKA_INPUT_TOPIC="ensemble_predict"
export KAFKA_OUTPUT_TOPIC="llm_result"

export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

echo "📋 환경 설정:" >&2
echo "   Neo4j URI: $NEO4J_URI" >&2
echo "   Kafka Broker: $KAFKA_BOOTSTRAP_SERVERS" >&2
echo "   Input Topic: $KAFKA_INPUT_TOPIC" >&2
echo "   Output Topic: $KAFKA_OUTPUT_TOPIC" >&2
echo "" >&2

echo "🔍 Kafka 토픽에서 트레이스 수신 대기 중..." >&2
echo "   PID: $$" >&2
echo "" >&2

# 애플리케이션 실행(시스템 파이썬)
python3 producer.py 2>&1
