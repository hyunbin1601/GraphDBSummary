#!/usr/bin/env python3
"""
ensemble_predict 토픽으로 malicious 트레이스 전송
OTLP 형식 + score, prediction 포함
"""

import json
from kafka import KafkaProducer

# 설정
KAFKA_BROKER = "172.31.11.219:19092"
TOPIC = "ensemble_predict"

# OTLP 형식의 트레이스 데이터 (schtasks.exe 스케줄 작업 생성)
otlp_trace_data = {
    "resourceSpans": [
        {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "event-agent"}},
                    {
                        "key": "service.instance.id",
                        "value": {"stringValue": "test-instance-123"},
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
                            "traceId": "c19a22b8c43401e6f23e483321b01490",
                            "spanId": "b4ef5bba22ae7a27",
                            "parentSpanId": "0769d93d20730ad3",
                            "flags": 257,
                            "name": "schtasks.exe@evt:1",
                            "kind": 1,
                            "startTimeUnixNano": "1761370892721736000",
                            "endTimeUnixNano": "1761370892721827000",
                            "attributes": [
                                {"key": "channel", "value": {"stringValue": "Sysmon"}},
                                {
                                    "key": "EventName",
                                    "value": {
                                        "stringValue": "ProcessCreate(rule:ProcessCreate)"
                                    },
                                },
                                {"key": "sysmon.ppid", "value": {"intValue": 6164}},
                                {"key": "ID", "value": {"intValue": 1}},
                                {
                                    "key": "TimeStamp",
                                    "value": {"stringValue": "10/24/2025 22:41:31"},
                                },
                                {
                                    "key": "sysmon.opcode",
                                    "value": {"stringValue": "Info"},
                                },
                                {
                                    "key": "ProviderGuid",
                                    "value": {
                                        "stringValue": "5770385f-c22a-43e0-bf4c-06f5698ffbd9"
                                    },
                                },
                                {"key": "RuleName", "value": {"stringValue": "-"}},
                                {
                                    "key": "UtcTime",
                                    "value": {"stringValue": "2025-10-25 05:41:31.254"},
                                },
                                {
                                    "key": "ProcessGuid",
                                    "value": {
                                        "stringValue": "c068fd60-630b-68fc-e401-000000000300"
                                    },
                                },
                                {"key": "ProcessId", "value": {"intValue": 4672}},
                                {
                                    "key": "Image",
                                    "value": {
                                        "stringValue": "C:\\Windows\\System32\\schtasks.exe"
                                    },
                                },
                                {
                                    "key": "FileVersion",
                                    "value": {
                                        "stringValue": "10.0.26100.1 (WinBuild.160101.0800)"
                                    },
                                },
                                {
                                    "key": "Description",
                                    "value": {
                                        "stringValue": "Task Scheduler Configuration Tool"
                                    },
                                },
                                {
                                    "key": "Product",
                                    "value": {
                                        "stringValue": "Microsoft® Windows® Operating System"
                                    },
                                },
                                {
                                    "key": "Company",
                                    "value": {"stringValue": "Microsoft Corporation"},
                                },
                                {
                                    "key": "OriginalFileName",
                                    "value": {"stringValue": "schtasks.exe"},
                                },
                                {
                                    "key": "CommandLine",
                                    "value": {
                                        "stringValue": 'schtasks.exe /create /tn "jaeger-all-in-onej" /sc MINUTE /mo 8 /tr "\'C:\\Recovery\\jaeger-all-in-one.exe\'" /rl HIGHEST /f'
                                    },
                                },
                                {
                                    "key": "CurrentDirectory",
                                    "value": {"stringValue": "C:\\WINDOWS\\system32\\"},
                                },
                                {
                                    "key": "User",
                                    "value": {
                                        "stringValue": "WIN-JAJPKDF4PHH\\Administrator"
                                    },
                                },
                                {
                                    "key": "LogonGuid",
                                    "value": {
                                        "stringValue": "c068fd60-5aba-68fc-01f2-030000000000"
                                    },
                                },
                                {"key": "LogonId", "value": {"intValue": 258561}},
                                {"key": "TerminalSessionId", "value": {"intValue": 1}},
                                {
                                    "key": "IntegrityLevel",
                                    "value": {"stringValue": "High"},
                                },
                                {
                                    "key": "Hashes",
                                    "value": {
                                        "stringValue": "MD5=92A282ECC1B59F1BAF83FD14B9EF6007,SHA256=7E606B6F3E7AA961B62885B05E2C1EE9701CFA8E666534359B65BF8000CB4747,IMPHASH=A7B2338D5533AE221C0EB231BBEC0787"
                                    },
                                },
                                {
                                    "key": "ParentProcessGuid",
                                    "value": {
                                        "stringValue": "c068fd60-62bd-68fc-cc01-000000000300"
                                    },
                                },
                                {"key": "ParentProcessId", "value": {"intValue": 6164}},
                                {
                                    "key": "ParentImage",
                                    "value": {
                                        "stringValue": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe"
                                    },
                                },
                                {
                                    "key": "ParentCommandLine",
                                    "value": {
                                        "stringValue": "C:\\WINDOWS\\system32\\wbem\\wmiprvse.exe -secured -Embedding"
                                    },
                                },
                                {
                                    "key": "ParentUser",
                                    "value": {
                                        "stringValue": "NT AUTHORITY\\NETWORK SERVICE"
                                    },
                                },
                                {
                                    "key": "sigma.alert",
                                    "value": {
                                        "arrayValue": {
                                            "values": [
                                                {
                                                    "stringValue": "92626ddd-662c-49e3-ac59-f6535f12d189"
                                                }
                                            ]
                                        }
                                    },
                                },
                                {"key": "sigma.match_count", "value": {"intValue": 1}},
                                {
                                    "key": "sigma.rule_title",
                                    "value": {
                                        "arrayValue": {
                                            "values": [
                                                {
                                                    "stringValue": "Scheduled Task Creation Via Schtasks.EXE"
                                                }
                                            ]
                                        }
                                    },
                                },
                                {"key": "user_id", "value": {"stringValue": "qwer"}},
                            ],
                            "status": {"message": "Sigma rules matched: 1", "code": 2},
                        },
                        {
                            "traceId": "c19a22b8c43401e6f23e483321b01490",
                            "spanId": "880e86a4f8a2916a",
                            "parentSpanId": "b4ef5bba22ae7a27",
                            "flags": 257,
                            "name": "schtasks.exe@evt:5",
                            "kind": 1,
                            "startTimeUnixNano": "1761370892722639000",
                            "endTimeUnixNano": "1761370892722696000",
                            "attributes": [
                                {"key": "channel", "value": {"stringValue": "Sysmon"}},
                                {
                                    "key": "EventName",
                                    "value": {
                                        "stringValue": "ProcessTerminate(rule:ProcessTerminate)"
                                    },
                                },
                                {"key": "sysmon.ppid", "value": {"intValue": 6164}},
                                {"key": "ID", "value": {"intValue": 5}},
                                {
                                    "key": "TimeStamp",
                                    "value": {"stringValue": "10/24/2025 22:41:31"},
                                },
                                {
                                    "key": "sysmon.opcode",
                                    "value": {"stringValue": "Info"},
                                },
                                {
                                    "key": "ProviderGuid",
                                    "value": {
                                        "stringValue": "5770385f-c22a-43e0-bf4c-06f5698ffbd9"
                                    },
                                },
                                {"key": "RuleName", "value": {"stringValue": "-"}},
                                {
                                    "key": "UtcTime",
                                    "value": {"stringValue": "2025-10-25 05:41:31.291"},
                                },
                                {
                                    "key": "ProcessGuid",
                                    "value": {
                                        "stringValue": "c068fd60-630b-68fc-e401-000000000300"
                                    },
                                },
                                {"key": "ProcessId", "value": {"intValue": 4672}},
                                {
                                    "key": "Image",
                                    "value": {
                                        "stringValue": "C:\\Windows\\System32\\schtasks.exe"
                                    },
                                },
                                {"key": "user_id", "value": {"stringValue": "qwer"}},
                            ],
                            "status": {},
                        },
                    ],
                }
            ],
        }
    ]
}


def send_test_trace():
    """ensemble_predict 토픽으로 malicious 트레이스 전송"""
    print(f"🚀 트레이스 데이터를 ensemble_predict 토픽으로 전송합니다...")
    print(f"🔗 Kafka 브로커: {KAFKA_BROKER}")
    print(f"📢 토픽: {TOPIC}")
    print()

    # Kafka 연결 테스트
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode(
                "utf-8"
            ),
            api_version=(0, 10, 1),
            request_timeout_ms=5000,
            metadata_max_age_ms=30000,
        )
        print("✅ Kafka Producer 연결 성공")
    except Exception as e:
        print(f"❌ Kafka 연결 실패: {e}")
        print(f"\n💡 해결 방법:")
        broker_ip = KAFKA_BROKER.split(":")[0]
        broker_port = KAFKA_BROKER.split(":")[1]
        print(f"   1. Kafka 브로커가 실행 중인지 확인: {KAFKA_BROKER}")
        print(
            f"   2. 네트워크 연결 확인: ping {broker_ip} 또는 telnet {broker_ip} {broker_port}"
        )
        print(f"   3. 방화벽/보안 그룹에서 포트 {broker_port} 허용 확인")
        print(f"   4. 브로커 주소가 올바른지 확인")
        raise

    # ensemble_predict 형식으로 메시지 구성
    trace_id = otlp_trace_data["resourceSpans"][0]["scopeSpans"][0]["spans"][0][
        "traceId"
    ]

    message = {
        "traceID": trace_id,
        "score": 0.944,  # 높은 점수 (malicious)
        "prediction": "malicious",
        "trace": otlp_trace_data,
    }

    # 트레이스 데이터 전송
    producer.send(TOPIC, message)
    producer.flush()

    print(f"✅ 트레이스 데이터 전송 완료!")
    print(f"   - TraceID: {trace_id}")
    print(f"   - Score: {message['score']}")
    print(f"   - Prediction: {message['prediction']}")
    print(
        f"   - Spans 개수: {len(otlp_trace_data['resourceSpans'][0]['scopeSpans'][0]['spans'])}"
    )

    producer.close()
    print()
    print("🎉 전송 완료!")


if __name__ == "__main__":
    try:
        send_test_trace()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()
