#!/usr/bin/env python3

import json
import os
import sys
import time
import glob
from pathlib import Path

try:
    from kafka import KafkaProducer
except ImportError:
    print("❌ kafka-python이 설치되지 않았습니다.")
    print("💡 설치 방법: pip install kafka-python")
    sys.exit(1)

# 설정
KAFKA_BROKER = "172.31.11.219:19092"
TOPIC = "raw_trace"
TRACES_DIR = "./sample_traces/traces_eval"


def test_kafka_connection():
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode(
                "utf-8"
            ),
            request_timeout_ms=5000,
            api_version_auto_timeout_ms=5000,
        )
        producer.close()
        return True
    except Exception as e:
        print(f"❌ Kafka 연결 실패: {e}")
        return False


def create_otlp_trace(trace_id, span_count):
    # otlp 형식의 트레이스 생성
    return {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {
                            "key": "service.name",
                            "value": {"stringValue": "event-agent"},
                        },
                        {
                            "key": "service.instance.id",
                            "value": {"stringValue": "test-instance"},
                        },
                        {
                            "key": "telemetry.sdk.name",
                            "value": {"stringValue": "opentelemetry"},
                        },
                        {
                            "key": "telemetry.sdk.language",
                            "value": {"stringValue": "dotnet"},
                        },
                        {
                            "key": "telemetry.sdk.version",
                            "value": {"stringValue": "1.12.0"},
                        },
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "event.agent"},
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": f"span-{span_count:016x}",
                                "parentSpanId": None,
                                "flags": 257,
                                "name": "test-process@evt:1",
                                "kind": 1,
                                "startTimeUnixNano": "1760619370538127400",
                                "endTimeUnixNano": "1760619370539186600",
                                "attributes": [
                                    {
                                        "key": "channel",
                                        "value": {"stringValue": "Sysmon"},
                                    },
                                    {
                                        "key": "EventName",
                                        "value": {
                                            "stringValue": "ProcessCreate(rule:ProcessCreate)"
                                        },
                                    },
                                    {"key": "ProcessId", "value": {"intValue": 1234}},
                                    {
                                        "key": "Image",
                                        "value": {
                                            "stringValue": "C:\\Windows\\System32\\cmd.exe"
                                        },
                                    },
                                    {
                                        "key": "CommandLine",
                                        "value": {
                                            "stringValue": "cmd.exe /c echo test"
                                        },
                                    },
                                    {
                                        "key": "User",
                                        "value": {"stringValue": "DESKTOP-TEST\\USER"},
                                    },
                                    {
                                        "key": "sigma.rule_title",
                                        "value": {
                                            "arrayValue": {
                                                "values": [{"stringValue": "Test Rule"}]
                                            }
                                        },
                                    },
                                    {
                                        "key": "sigma.match_count",
                                        "value": {"intValue": 1},
                                    },
                                ],
                                "status": {
                                    "message": "Sigma rules matched: 1",
                                    "code": 2,
                                },
                            }
                        ],
                    }
                ],
            }
        ]
    }


def extract_trace_id(filename):
    # 트레이스 id 추출
    try:
        # trace-{traceid}.json 형식에서 traceID 추출
        if filename.startswith("trace-") and filename.endswith(".json"):
            return filename[6:-5]  # "trace-" 제거하고 ".json" 제거
        return None
    except:
        return None


def send_trace_to_kafka(producer, trace_data, trace_id):
    # kafka로 트레이스 전송
    try:
        future = producer.send(TOPIC, trace_data)
        record_metadata = future.get(timeout=10)
        return (
            True,
            f"파티션: {record_metadata.partition}, 오프셋: {record_metadata.offset}",
        )
    except Exception as e:
        return False, str(e)


def main():
    print("🚀 정확한 OTLP 형식으로 raw_trace 토픽으로 전송 시작...")
    print(f"📁 디렉토리: {TRACES_DIR}")
    print(f"🔗 Kafka 브로커: {KAFKA_BROKER}")
    print(f"📢 토픽: {TOPIC}")
    print()

    # 디렉토리 존재 확인
    if not os.path.exists(TRACES_DIR):
        print(f"❌ 디렉토리가 존재하지 않습니다: {TRACES_DIR}")
        return 1

    # 파일 목록 가져오기
    trace_files = glob.glob(os.path.join(TRACES_DIR, "trace-*.json"))
    if not trace_files:
        print(f"❌ trace-*.json 파일을 찾을 수 없습니다: {TRACES_DIR}")
        return 1

    file_count = len(trace_files)
    print(f"📊 총 파일 개수: {file_count}")
    print()

    # Kafka 연결 테스트
    print("🔍 Kafka 연결 테스트 중...")
    if not test_kafka_connection():
        print("💡 다음을 확인해주세요:")
        print("   - Kafka 브로커가 실행 중인지")
        print("   - 네트워크 연결 상태")
        print("   - 방화벽 설정")
        return 1
    print("✅ Kafka 브로커 연결 확인됨")
    print()

    # Kafka Producer 생성
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode(
                "utf-8"
            ),
            retries=3,
            retry_backoff_ms=1000,
        )
    except Exception as e:
        print(f"❌ Kafka Producer 생성 실패: {e}")
        return 1

    # 각 파일 처리
    success_count = 0
    for i, file_path in enumerate(trace_files, 1):
        filename = os.path.basename(file_path)
        print(f"[{i}/{file_count}] 처리 중: {filename}")

        # traceID 추출
        trace_id = extract_trace_id(filename)
        if not trace_id:
            print(f"⚠️  파일명에서 traceID를 추출할 수 없습니다: {filename}")
            continue

        print(f"🔍 추출된 traceID: {trace_id}")

        # OTLP 트레이스 생성
        try:
            trace_data = create_otlp_trace(trace_id, i)

            # JSON 유효성 검사
            json.dumps(trace_data)  # JSON 직렬화 테스트
            print("✅ JSON 유효성 검사 통과")
        except Exception as e:
            print(f"❌ JSON 생성/검사 실패: {e}")
            continue

        # Kafka로 전송
        success, message = send_trace_to_kafka(producer, trace_data, trace_id)
        if success:
            success_count += 1
            print(f"🎉 전송 성공! {message}")
        else:
            print(f"💥 전송 실패: {message}")

        print()
        time.sleep(0.1)  # 전송 간격

    # Producer 정리
    producer.close()

    # 결과 요약
    print("📊 전송 완료 요약:")
    print(f"   총 파일: {file_count}개")
    print(f"   성공: {success_count}개")
    print(f"   실패: {file_count - success_count}개")

    if success_count == file_count:
        print("🎉 모든 파일 전송 성공!")
        return 0
    else:
        print("⚠️  일부 파일 전송 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
