#!/usr/bin/env python3
"""
실제 트레이스 형식과 동일한 malicious 트레이스 생성 및 전송
"""

import json
import os
import sys
import time
import random
import uuid
from datetime import datetime

try:
    from kafka import KafkaProducer
except ImportError:
    print("❌ kafka-python이 설치되지 않았습니다.")
    print("💡 설치 방법: pip install kafka-python")
    sys.exit(1)

# 설정
KAFKA_BROKER = "172.31.11.219:19092"
TOPIC = "ensemble_predict"


def generate_trace_id():
    """32자리 hex trace ID 생성"""
    return "".join(random.choices("0123456789abcdef", k=32))


def generate_span_id():
    """16자리 hex span ID 생성"""
    return "".join(random.choices("0123456789abcdef", k=16))


def generate_process_guid():
    """Process GUID 생성"""
    return f"29152dfc-{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-00000000d900"


def get_current_time_nano():
    """현재 시간을 나노초 단위로 반환"""
    return int(time.time() * 1_000_000_000)


def create_malicious_trace():
    """실제 형식과 동일한 malicious 트레이스 생성"""
    trace_id = generate_trace_id()
    base_time = get_current_time_nano()

    # Sigma 룰들 (실제 malicious 활동 패턴)
    sigma_rules = [
        "Potential CommandLine Path Traversal Via Cmd.EXE",
        "Non Interactive PowerShell Process Spawned",
        "PowerShell Base64 Encoded Command",
        "Suspicious Process Creation",
        "Registry Persistence",
        "Suspicious Network Connection",
    ]

    spans = []

    # 1. cmd.exe 실행 (의심스러운 명령어)
    cmd_span = {
        "traceId": trace_id,
        "spanId": generate_span_id(),
        "parentSpanId": "60158623a08b20be",
        "flags": 257,
        "name": "cmd.exe@evt:1",
        "kind": 1,
        "startTimeUnixNano": str(base_time),
        "endTimeUnixNano": str(base_time + 431400),
        "attributes": [
            {"key": "channel", "value": {"stringValue": "Sysmon"}},
            {
                "key": "EventName",
                "value": {"stringValue": "ProcessCreate(rule:ProcessCreate)"},
            },
            {"key": "sysmon.ppid", "value": {"intValue": 9464}},
            {"key": "ID", "value": {"intValue": 1}},
            {
                "key": "TimeStamp",
                "value": {"stringValue": datetime.now().strftime("%m/%d/%Y %H:%M:%S")},
            },
            {"key": "sysmon.opcode", "value": {"stringValue": "Info"}},
            {
                "key": "ProviderGuid",
                "value": {"stringValue": "5770385f-c22a-43e0-bf4c-06f5698ffbd9"},
            },
            {"key": "RuleName", "value": {"stringValue": "-"}},
            {
                "key": "UtcTime",
                "value": {
                    "stringValue": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[
                        :-3
                    ]
                },
            },
            {"key": "ProcessGuid", "value": {"stringValue": generate_process_guid()}},
            {"key": "ProcessId", "value": {"intValue": random.randint(10000, 20000)}},
            {
                "key": "Image",
                "value": {"stringValue": "C:\\Windows\\System32\\cmd.exe"},
            },
            {
                "key": "FileVersion",
                "value": {"stringValue": "10.0.26100.6725 (WinBuild.160101.0800)"},
            },
            {
                "key": "Description",
                "value": {"stringValue": "Windows Command Processor"},
            },
            {
                "key": "Product",
                "value": {"stringValue": "Microsoft® Windows® Operating System"},
            },
            {"key": "Company", "value": {"stringValue": "Microsoft Corporation"}},
            {"key": "OriginalFileName", "value": {"stringValue": "Cmd.Exe"}},
            {
                "key": "CommandLine",
                "value": {
                    "stringValue": '"C:\\WINDOWS\\system32\\cmd.exe" /k powershell -ExecutionPolicy Bypass -EncodedCommand UwB0AGEAcgB0AC0AUwBsAGUAZQBwACAALQA1AA=='
                },
            },
            {
                "key": "CurrentDirectory",
                "value": {"stringValue": "D:\\completed_trace\\EventAgent_V3\\Test\\"},
            },
            {"key": "User", "value": {"stringValue": "DESKTOP-PJHVJGI\\KISIA"}},
            {
                "key": "LogonGuid",
                "value": {"stringValue": "29152dfc-59ae-68f3-cdea-0f0000000000"},
            },
            {"key": "LogonId", "value": {"intValue": 1043149}},
            {"key": "TerminalSessionId", "value": {"intValue": 1}},
            {"key": "IntegrityLevel", "value": {"stringValue": "Medium"}},
            {
                "key": "Hashes",
                "value": {
                    "stringValue": "MD5=4C70711F79B6ADBCA108E4CD012AEAAC,SHA256=B7BFA5AD5FB74D62AC7099F70B9D5A6D36B79F062AAD4997429559955DA191CC,IMPHASH=B0F049C014592B156EB1FA857E99CEB9"
                },
            },
            {
                "key": "ParentProcessGuid",
                "value": {"stringValue": "29152dfc-5a01-68f3-4402-00000000d900"},
            },
            {"key": "ParentProcessId", "value": {"intValue": 9464}},
            {
                "key": "ParentImage",
                "value": {"stringValue": "C:\\Program Files\\PowerShell\\7\\pwsh.exe"},
            },
            {
                "key": "ParentCommandLine",
                "value": {
                    "stringValue": '"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -WorkingDirectory ~'
                },
            },
            {"key": "ParentUser", "value": {"stringValue": "DESKTOP-PJHVJGI\\KISIA"}},
        ],
        "status": {},
    }
    spans.append(cmd_span)

    # 2. PowerShell 실행 (Base64 인코딩된 명령어)
    powershell_span = {
        "traceId": trace_id,
        "spanId": generate_span_id(),
        "parentSpanId": cmd_span["spanId"],
        "flags": 257,
        "name": "powershell.exe@evt:1",
        "kind": 1,
        "startTimeUnixNano": str(base_time + 500000),
        "endTimeUnixNano": str(base_time + 600000),
        "attributes": [
            {"key": "channel", "value": {"stringValue": "Sysmon"}},
            {
                "key": "EventName",
                "value": {"stringValue": "ProcessCreate(rule:ProcessCreate)"},
            },
            {
                "key": "sysmon.ppid",
                "value": {"intValue": cmd_span["attributes"][10]["value"]["intValue"]},
            },
            {"key": "ID", "value": {"intValue": 1}},
            {
                "key": "TimeStamp",
                "value": {"stringValue": datetime.now().strftime("%m/%d/%Y %H:%M:%S")},
            },
            {"key": "sysmon.opcode", "value": {"stringValue": "Info"}},
            {
                "key": "ProviderGuid",
                "value": {"stringValue": "5770385f-c22a-43e0-bf4c-06f5698ffbd9"},
            },
            {"key": "RuleName", "value": {"stringValue": "-"}},
            {
                "key": "UtcTime",
                "value": {
                    "stringValue": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[
                        :-3
                    ]
                },
            },
            {"key": "ProcessGuid", "value": {"stringValue": generate_process_guid()}},
            {"key": "ProcessId", "value": {"intValue": random.randint(10000, 20000)}},
            {
                "key": "Image",
                "value": {
                    "stringValue": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
                },
            },
            {
                "key": "FileVersion",
                "value": {"stringValue": "10.0.26100.5074 (WinBuild.160101.0800)"},
            },
            {"key": "Description", "value": {"stringValue": "Windows PowerShell"}},
            {
                "key": "Product",
                "value": {"stringValue": "Microsoft® Windows® Operating System"},
            },
            {"key": "Company", "value": {"stringValue": "Microsoft Corporation"}},
            {"key": "OriginalFileName", "value": {"stringValue": "PowerShell.EXE"}},
            {
                "key": "CommandLine",
                "value": {
                    "stringValue": "powershell.exe -EncodedCommand UwB0AGEAcgB0AC0AUwBsAGUAZQBwACAALQA1AA=="
                },
            },
            {
                "key": "CurrentDirectory",
                "value": {"stringValue": "D:\\completed_trace\\EventAgent_V3\\Test\\"},
            },
            {"key": "User", "value": {"stringValue": "DESKTOP-PJHVJGI\\KISIA"}},
            {
                "key": "LogonGuid",
                "value": {"stringValue": "29152dfc-59ae-68f3-cdea-0f0000000000"},
            },
            {"key": "LogonId", "value": {"intValue": 1043149}},
            {"key": "TerminalSessionId", "value": {"intValue": 1}},
            {"key": "IntegrityLevel", "value": {"stringValue": "Medium"}},
            {
                "key": "Hashes",
                "value": {
                    "stringValue": "MD5=A97E6573B97B44C96122BFA543A82EA1,SHA256=0FF6F2C94BC7E2833A5F7E16DE1622E5DBA70396F31C7D5F56381870317E8C46,IMPHASH=AFACF6DC9041114B198160AAB4D0AE77"
                },
            },
            {
                "key": "ParentProcessGuid",
                "value": {
                    "stringValue": cmd_span["attributes"][9]["value"]["stringValue"]
                },
            },
            {
                "key": "ParentProcessId",
                "value": {"intValue": cmd_span["attributes"][10]["value"]["intValue"]},
            },
            {
                "key": "ParentImage",
                "value": {"stringValue": "C:\\Windows\\System32\\cmd.exe"},
            },
            {
                "key": "ParentCommandLine",
                "value": {
                    "stringValue": '"C:\\WINDOWS\\system32\\cmd.exe" /k powershell -ExecutionPolicy Bypass -EncodedCommand UwB0AGEAcgB0AC0AUwBsAGUAZQBwACAALQA1AA=='
                },
            },
            {"key": "ParentUser", "value": {"stringValue": "DESKTOP-PJHVJGI\\KISIA"}},
            {
                "key": "sigma.alert",
                "value": {
                    "arrayValue": {
                        "values": [
                            {"stringValue": str(uuid.uuid4())},
                            {"stringValue": str(uuid.uuid4())},
                        ]
                    }
                },
            },
            {
                "key": "sigma.rule_title",
                "value": {
                    "arrayValue": {
                        "values": [
                            {"stringValue": random.choice(sigma_rules)},
                            {
                                "stringValue": "Non Interactive PowerShell Process Spawned"
                            },
                        ]
                    }
                },
            },
            {"key": "sigma.match_count", "value": {"intValue": 2}},
        ],
        "status": {"message": "Sigma rules matched: 2", "code": 2},
    }
    spans.append(powershell_span)

    # 3. 의심스러운 파일 생성
    file_create_span = {
        "traceId": trace_id,
        "spanId": generate_span_id(),
        "parentSpanId": cmd_span["spanId"],
        "flags": 257,
        "name": "powershell.exe@evt:11",
        "kind": 1,
        "startTimeUnixNano": str(base_time + 700000),
        "endTimeUnixNano": str(base_time + 800000),
        "attributes": [
            {"key": "channel", "value": {"stringValue": "Sysmon"}},
            {
                "key": "EventName",
                "value": {"stringValue": "Filecreated(rule:FileCreate)"},
            },
            {
                "key": "sysmon.ppid",
                "value": {"intValue": cmd_span["attributes"][10]["value"]["intValue"]},
            },
            {"key": "ID", "value": {"intValue": 11}},
            {
                "key": "TimeStamp",
                "value": {"stringValue": datetime.now().strftime("%m/%d/%Y %H:%M:%S")},
            },
            {"key": "sysmon.opcode", "value": {"stringValue": "Info"}},
            {
                "key": "ProviderGuid",
                "value": {"stringValue": "5770385f-c22a-43e0-bf4c-06f5698ffbd9"},
            },
            {"key": "RuleName", "value": {"stringValue": "-"}},
            {
                "key": "UtcTime",
                "value": {
                    "stringValue": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[
                        :-3
                    ]
                },
            },
            {"key": "ProcessGuid", "value": {"stringValue": generate_process_guid()}},
            {
                "key": "ProcessId",
                "value": {"intValue": cmd_span["attributes"][10]["value"]["intValue"]},
            },
            {
                "key": "Image",
                "value": {
                    "stringValue": "C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
                },
            },
            {
                "key": "TargetFilename",
                "value": {
                    "stringValue": "C:\\Users\\KISIA\\AppData\\Local\\Temp\\malware_"
                    + str(random.randint(1000, 9999))
                    + ".exe"
                },
            },
            {
                "key": "CreationUtcTime",
                "value": {
                    "stringValue": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[
                        :-3
                    ]
                },
            },
            {"key": "User", "value": {"stringValue": "DESKTOP-PJHVJGI\\KISIA"}},
            {
                "key": "sigma.alert",
                "value": {
                    "arrayValue": {
                        "values": [
                            {"stringValue": str(uuid.uuid4())},
                            {"stringValue": str(uuid.uuid4())},
                        ]
                    }
                },
            },
            {
                "key": "sigma.rule_title",
                "value": {
                    "arrayValue": {
                        "values": [
                            {"stringValue": "Suspicious File Creation"},
                            {"stringValue": "System File Execution Location Anomaly"},
                        ]
                    }
                },
            },
            {"key": "sigma.match_count", "value": {"intValue": 2}},
        ],
        "status": {"message": "Sigma rules matched: 2", "code": 2},
    }
    spans.append(file_create_span)

    # 4. 레지스트리 수정 (지속성 확보)
    registry_span = {
        "traceId": trace_id,
        "spanId": generate_span_id(),
        "parentSpanId": cmd_span["spanId"],
        "flags": 257,
        "name": "powershell.exe@evt:13",
        "kind": 1,
        "startTimeUnixNano": str(base_time + 900000),
        "endTimeUnixNano": str(base_time + 1000000),
        "attributes": [
            {"key": "channel", "value": {"stringValue": "Sysmon"}},
            {
                "key": "EventName",
                "value": {"stringValue": "Registryvalueset(rule:RegistryEvent)"},
            },
            {
                "key": "sysmon.ppid",
                "value": {"intValue": cmd_span["attributes"][10]["value"]["intValue"]},
            },
            {"key": "ID", "value": {"intValue": 13}},
            {
                "key": "TimeStamp",
                "value": {"stringValue": datetime.now().strftime("%m/%d/%Y %H:%M:%S")},
            },
            {"key": "sysmon.opcode", "value": {"stringValue": "Info"}},
            {
                "key": "ProviderGuid",
                "value": {"stringValue": "5770385f-c22a-43e0-bf4c-06f5698ffbd9"},
            },
            {"key": "RuleName", "value": {"stringValue": "T1042"}},
            {"key": "EventType", "value": {"stringValue": "SetValue"}},
            {
                "key": "UtcTime",
                "value": {
                    "stringValue": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[
                        :-3
                    ]
                },
            },
            {"key": "ProcessGuid", "value": {"stringValue": generate_process_guid()}},
            {
                "key": "ProcessId",
                "value": {"intValue": cmd_span["attributes"][10]["value"]["intValue"]},
            },
            {
                "key": "Image",
                "value": {
                    "stringValue": "C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
                },
            },
            {
                "key": "TargetObject",
                "value": {
                    "stringValue": "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\Malware"
                },
            },
            {
                "key": "Details",
                "value": {
                    "stringValue": "C:\\Users\\KISIA\\AppData\\Local\\Temp\\malware_"
                    + str(random.randint(1000, 9999))
                    + ".exe"
                },
            },
            {"key": "User", "value": {"stringValue": "DESKTOP-PJHVJGI\\KISIA"}},
            {
                "key": "sigma.alert",
                "value": {
                    "arrayValue": {"values": [{"stringValue": str(uuid.uuid4())}]}
                },
            },
            {
                "key": "sigma.rule_title",
                "value": {
                    "arrayValue": {"values": [{"stringValue": "Registry Persistence"}]}
                },
            },
            {"key": "sigma.match_count", "value": {"intValue": 1}},
        ],
        "status": {"message": "Sigma rules matched: 1", "code": 2},
    }
    spans.append(registry_span)

    # 5. 네트워크 연결 (C2 통신 시뮬레이션)
    network_span = {
        "traceId": trace_id,
        "spanId": generate_span_id(),
        "parentSpanId": cmd_span["spanId"],
        "flags": 257,
        "name": "powershell.exe@evt:22",
        "kind": 1,
        "startTimeUnixNano": str(base_time + 1100000),
        "endTimeUnixNano": str(base_time + 1200000),
        "attributes": [
            {"key": "channel", "value": {"stringValue": "Sysmon"}},
            {
                "key": "EventName",
                "value": {"stringValue": "Networkconnect(rule:NetworkConnect)"},
            },
            {
                "key": "sysmon.ppid",
                "value": {"intValue": cmd_span["attributes"][10]["value"]["intValue"]},
            },
            {"key": "ID", "value": {"intValue": 22}},
            {
                "key": "TimeStamp",
                "value": {"stringValue": datetime.now().strftime("%m/%d/%Y %H:%M:%S")},
            },
            {"key": "sysmon.opcode", "value": {"stringValue": "Info"}},
            {
                "key": "ProviderGuid",
                "value": {"stringValue": "5770385f-c22a-43e0-bf4c-06f5698ffbd9"},
            },
            {"key": "RuleName", "value": {"stringValue": "-"}},
            {
                "key": "UtcTime",
                "value": {
                    "stringValue": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[
                        :-3
                    ]
                },
            },
            {"key": "ProcessGuid", "value": {"stringValue": generate_process_guid()}},
            {
                "key": "ProcessId",
                "value": {"intValue": cmd_span["attributes"][10]["value"]["intValue"]},
            },
            {
                "key": "Image",
                "value": {
                    "stringValue": "C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
                },
            },
            {
                "key": "DestinationIp",
                "value": {
                    "stringValue": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
                },
            },
            {
                "key": "DestinationPort",
                "value": {"intValue": random.choice([4444, 8080, 9999])},
            },
            {"key": "User", "value": {"stringValue": "DESKTOP-PJHVJGI\\KISIA"}},
            {
                "key": "sigma.alert",
                "value": {
                    "arrayValue": {"values": [{"stringValue": str(uuid.uuid4())}]}
                },
            },
            {
                "key": "sigma.rule_title",
                "value": {
                    "arrayValue": {
                        "values": [{"stringValue": "Suspicious Network Connection"}]
                    }
                },
            },
            {"key": "sigma.match_count", "value": {"intValue": 1}},
        ],
        "status": {"message": "Sigma rules matched: 1", "code": 2},
    }
    spans.append(network_span)

    # OTLP 트레이스 구조 생성
    otlp_trace = {
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
                            "value": {"stringValue": str(uuid.uuid4())},
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
                "scopeSpans": [{"scope": {"name": "event.agent"}, "spans": spans}],
            }
        ]
    }

    return otlp_trace


def send_test_traces():
    """테스트 트레이스를 Kafka로 전송"""
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
    )

    print(f"🚀 실제 형식과 동일한 malicious 트레이스 전송 시작...")
    print(f"🔗 Kafka 브로커: {KAFKA_BROKER}")
    print(f"📢 토픽: {TOPIC}")
    print()

    # Malicious 트레이스 생성 및 전송 (5개)
    for i in range(5):
        malicious_trace = create_malicious_trace()

        # 사용자가 제공한 형식과 동일하게 래핑
        message = {
            "traceID": malicious_trace["resourceSpans"][0]["scopeSpans"][0]["spans"][0][
                "traceId"
            ],
            "score": random.uniform(0.7, 0.95),  # 높은 점수 (malicious)
            "prediction": "malicious",
            "trace": malicious_trace,
        }

        producer.send(TOPIC, message)
        producer.flush()

        print(f"Malicious 트레이스 {i+1} 전송 완료:")
        print(f"  - TraceID: {message['traceID']}")
        print(f"  - Score: {message['score']:.3f}")
        print(f"  - Prediction: {message['prediction']}")
        print(
            f"  - Spans 개수: {len(malicious_trace['resourceSpans'][0]['scopeSpans'][0]['spans'])}"
        )
        print()

        time.sleep(0.5)  # 전송 간격

    producer.close()
    print("🎉 모든 malicious 트레이스 전송 완료!")


if __name__ == "__main__":
    send_test_traces()
