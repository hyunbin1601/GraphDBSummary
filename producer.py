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
INPUT_TOPIC = os.getenv("KAFKA_INPUT_TOPIC", "trace_input")
OUTPUT_TOPIC = os.getenv("KAFKA_OUTPUT_TOPIC", "ensemble_predict")

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
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=os.getenv("KAFKA_CONSUMER_GROUP", "graphdb-summary-consumer"),
    )


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
            trace_input = extract_trace_input(message.value)
            results = analyze_structural_similarity_no_db(
                driver, trace_input, prompt_template, top_k=5
            )

            # 입력 트레이스의 traceID를 결과에 포함(상관관계용)
            source_trace_id = None
            if isinstance(trace_input, dict):
                source_trace_id = trace_input.get("traceID") or trace_input.get(
                    "traceId"
                )

            out_message = {
                "traceID": source_trace_id,
                "summary": results.get("summary", {}),
                "semantic_top_traces": results.get("semantic_top_traces", []),
                "structural_similarity": results.get("structural_similarity", []),
                "indirect_connections": results.get("indirect_connections", []),
                "mitigation_suggestions": results.get("mitigation_suggestions", ""),
            }

            producer.send(OUTPUT_TOPIC, out_message)
            producer.flush()
            print(f"분석 결과를 Kafka 토픽 '{OUTPUT_TOPIC}'로 전송했습니다.")
        except Exception as e:
            print(f"메시지 처리 중 오류: {e}")
