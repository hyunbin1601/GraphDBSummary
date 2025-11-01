"""
OpenAI API와 Gemini API 테스트 결과 비교 스크립트
두 테스트 결과를 비교하여 어느 API가 더 나은 성능을 보이는지 분석합니다.
"""

import json
import os
from datetime import datetime
from pathlib import Path


def load_test_results():
    """테스트 결과 파일들을 로드"""
    results = {}

    # OpenAI 결과 로드
    if os.path.exists("api_test_results.json"):
        with open("api_test_results.json", "r", encoding="utf-8") as f:
            results["openai"] = json.load(f)
        print("✅ OpenAI 테스트 결과 로드 완료")
    else:
        print("⚠️ api_test_results.json 파일이 없습니다.")
        results["openai"] = None

    # Gemini 결과 로드
    if os.path.exists("gemini_api_test_results.json"):
        with open("gemini_api_test_results.json", "r", encoding="utf-8") as f:
            results["gemini"] = json.load(f)
        print("✅ Gemini 테스트 결과 로드 완료")
    else:
        print("⚠️ gemini_api_test_results.json 파일이 없습니다.")
        results["gemini"] = None

    return results


def compare_simple_prompt(openai_results, gemini_results):
    """간단한 프롬프트 비교"""
    print("\n" + "=" * 80)
    print("📝 테스트 1: 간단한 프롬프트 비교")
    print("=" * 80)

    if not openai_results or not gemini_results:
        print("⚠️ 비교할 결과가 없습니다.")
        return

    # 첫 번째 사용 가능한 모델 비교
    openai_model = None
    for model_name, data in openai_results.items():
        if data.get("simple_prompt", {}).get("success"):
            openai_model = model_name
            openai_data = data["simple_prompt"]
            break

    gemini_model = None
    for model_name, data in gemini_results.items():
        if data.get("simple_prompt", {}).get("success"):
            gemini_model = model_name
            gemini_data = data["simple_prompt"]
            break

    if not openai_model or not gemini_model:
        print("⚠️ 사용 가능한 모델을 찾을 수 없습니다.")
        return

    print(f"\nOpenAI ({openai_model}):")
    print(f"  응답 시간: {openai_data.get('time', 0):.2f}초")
    print(f"  응답 길이: {len(openai_data.get('response', ''))}자")

    print(f"\nGemini ({gemini_model}):")
    print(f"  응답 시간: {gemini_data.get('time', 0):.2f}초")
    print(f"  응답 길이: {len(gemini_data.get('response', ''))}자")

    # 성능 비교
    print("\n📊 성능 비교:")
    if openai_data.get("time", 0) < gemini_data.get("time", 0):
        faster = f"OpenAI ({openai_model})"
        time_diff = gemini_data.get("time", 0) - openai_data.get("time", 0)
    else:
        faster = f"Gemini ({gemini_model})"
        time_diff = openai_data.get("time", 0) - gemini_data.get("time", 0)

    print(f"  ⚡ 빠른 응답: {faster} ({time_diff:.2f}초 더 빠름)")

    if abs(openai_data.get("time", 0) - gemini_data.get("time", 0)) < 0.5:
        print("  📌 응답 시간이 거의 동일합니다.")


def compare_json_output(openai_results, gemini_results):
    """JSON 출력 비교"""
    print("\n" + "=" * 80)
    print("📝 테스트 2: JSON 출력 비교")
    print("=" * 80)

    if not openai_results or not gemini_results:
        print("⚠️ 비교할 결과가 없습니다.")
        return

    # 첫 번째 사용 가능한 모델 비교
    openai_model = None
    for model_name, data in openai_results.items():
        if data.get("json_output", {}).get("success"):
            openai_model = model_name
            openai_data = data["json_output"]
            break

    gemini_model = None
    for model_name, data in gemini_results.items():
        if data.get("json_output", {}).get("success"):
            gemini_model = model_name
            gemini_data = data["json_output"]
            break

    if not openai_model or not gemini_model:
        print("⚠️ 사용 가능한 모델을 찾을 수 없습니다.")
        return

    print(f"\nOpenAI ({openai_model}):")
    print(f"  응답 시간: {openai_data.get('time', 0):.2f}초")
    print(f"  JSON 파싱 성공: {'✅' if openai_data.get('json_parseable') else '❌'}")

    print(f"\nGemini ({gemini_model}):")
    print(f"  응답 시간: {gemini_data.get('time', 0):.2f}초")
    print(f"  JSON 파싱 성공: {'✅' if gemini_data.get('json_parseable') else '❌'}")

    print("\n📊 성능 비교:")

    # JSON 파싱 성공률
    openai_success = "✅ 성공" if openai_data.get("json_parseable") else "❌ 실패"
    gemini_success = "✅ 성공" if gemini_data.get("json_parseable") else "❌ 실패"

    print(f"  OpenAI: {openai_success}")
    print(f"  Gemini: {gemini_success}")

    if openai_data.get("time", 0) < gemini_data.get("time", 0):
        faster = f"OpenAI ({openai_model})"
        time_diff = gemini_data.get("time", 0) - openai_data.get("time", 0)
    else:
        faster = f"Gemini ({gemini_model})"
        time_diff = openai_data.get("time", 0) - gemini_data.get("time", 0)

    print(f"  ⚡ 빠른 응답: {faster} ({time_diff:.2f}초 더 빠름)")


def compare_long_summary(openai_results, gemini_results):
    """Long Summary 프롬프트 비교 (가장 중요)"""
    print("\n" + "=" * 80)
    print("📝 테스트 4: Long Summary Prompt 비교 (비교 중요도: ⭐⭐⭐⭐⭐)")
    print("=" * 80)

    if not openai_results or not gemini_results:
        print("⚠️ 비교할 결과가 없습니다.")
        return

    # 첫 번째 사용 가능한 모델 비교
    openai_model = None
    for model_name, data in openai_results.items():
        if data.get("long_summary", {}).get("success"):
            openai_model = model_name
            openai_data = data["long_summary"]
            break

    gemini_model = None
    for model_name, data in gemini_results.items():
        if data.get("long_summary", {}).get("success"):
            gemini_model = model_name
            gemini_data = data["long_summary"]
            break

    if not openai_model or not gemini_model:
        print("⚠️ 사용 가능한 모델을 찾을 수 없습니다.")
        return

    print(f"\nOpenAI ({openai_model}):")
    print(f"  응답 시간: {openai_data.get('time', 0):.2f}초")
    print(f"  응답 길이: {openai_data.get('length', 0)}자")

    print(f"\nGemini ({gemini_model}):")
    print(f"  응답 시간: {gemini_data.get('time', 0):.2f}초")
    print(f"  응답 길이: {gemini_data.get('length', 0)}자")

    # 성능 비교
    print("\n📊 성능 비교:")
    if openai_data.get("time", 0) < gemini_data.get("time", 0):
        faster = f"OpenAI ({openai_model})"
        time_diff = gemini_data.get("time", 0) - openai_data.get("time", 0)
    else:
        faster = f"Gemini ({gemini_model})"
        time_diff = openai_data.get("time", 0) - gemini_data.get("time", 0)

    print(f"  ⚡ 빠른 응답: {faster} ({time_diff:.2f}초 더 빠름)")

    # 응답 길이 비교
    if abs(openai_data.get("length", 0) - gemini_data.get("length", 0)) < 100:
        print(f"  📌 응답 길이가 거의 동일합니다.")
    else:
        if openai_data.get("length", 0) > gemini_data.get("length", 0):
            longer = f"OpenAI ({openai_model})"
            length_diff = openai_data.get("length", 0) - gemini_data.get("length", 0)
        else:
            longer = f"Gemini ({gemini_model})"
            length_diff = gemini_data.get("length", 0) - openai_data.get("length", 0)
        print(f"  📝 더 긴 응답: {longer} ({length_diff}자 더 김)")

    # 응답 내용 미리보기
    print("\n📄 응답 내용 미리보기:")
    print(f"\n[OpenAI {openai_model}]")
    openai_resp = openai_data.get("response", "")
    print(openai_resp[:500] + "..." if len(openai_resp) > 500 else openai_resp)

    print(f"\n[Gemini {gemini_model}]")
    gemini_resp = gemini_data.get("response", "")
    print(gemini_resp[:500] + "..." if len(gemini_resp) > 500 else gemini_resp)


def save_comparison_report(results):
    """비교 결과를 파일로 저장"""
    comparison_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "openai_models": (
            list(results.get("openai", {}).keys()) if results.get("openai") else []
        ),
        "gemini_models": (
            list(results.get("gemini", {}).keys()) if results.get("gemini") else []
        ),
        "comparison": [],
    }

    with open("comparison_report.json", "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, ensure_ascii=False, indent=2)

    print("\n💾 비교 보고서가 comparison_report.json에 저장되었습니다.")


def main():
    """메인 비교 함수"""
    print("=" * 80)
    print("🔍 OpenAI vs Gemini API 성능 비교 리포트")
    print("=" * 80)
    print(f"비교 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 테스트 결과 로드
    results = load_test_results()

    if not results.get("openai") and not results.get("gemini"):
        print("\n❌ 비교할 테스트 결과가 없습니다.")
        print("💡 먼저 test_api.py와 test_gemini_api.py를 실행하세요.")
        return

    if not results.get("openai"):
        print("\n⚠️ OpenAI 테스트 결과가 없습니다.")
    if not results.get("gemini"):
        print("\n⚠️ Gemini 테스트 결과가 없습니다.")

    # 각 테스트별 비교
    compare_simple_prompt(results.get("openai"), results.get("gemini"))
    compare_json_output(results.get("openai"), results.get("gemini"))
    compare_long_summary(results.get("openai"), results.get("gemini"))

    # 종합 비교
    print("\n" + "=" * 80)
    print("📊 종합 비교 요약")
    print("=" * 80)

    if results.get("openai") and results.get("gemini"):
        openai_models = len(results["openai"])
        gemini_models = len(results["gemini"])
        print(f"\nOpenAI 테스트 모델 수: {openai_models}")
        print(f"Gemini 테스트 모델 수: {gemini_models}")

        # 전체 평균 시간 계산
        openai_times = []
        gemini_times = []

        for model_data in results["openai"].values():
            if model_data.get("simple_prompt", {}).get("success"):
                openai_times.append(model_data["simple_prompt"].get("time", 0))

        for model_data in results["gemini"].values():
            if model_data.get("simple_prompt", {}).get("success"):
                gemini_times.append(model_data["simple_prompt"].get("time", 0))

        if openai_times and gemini_times:
            avg_openai = sum(openai_times) / len(openai_times)
            avg_gemini = sum(gemini_times) / len(gemini_times)
            print(f"\n평균 응답 시간:")
            print(f"  OpenAI: {avg_openai:.2f}초")
            print(f"  Gemini: {avg_gemini:.2f}초")

            if avg_openai < avg_gemini:
                print(
                    f"  ⭐ 전반적으로 OpenAI가 {avg_gemini - avg_openai:.2f}초 더 빠릅니다."
                )
            else:
                print(
                    f"  ⭐ 전반적으로 Gemini가 {avg_openai - avg_gemini:.2f}초 더 빠릅니다."
                )

    # 비교 보고서 저장
    save_comparison_report(results)

    print("\n" + "=" * 80)
    print("✅ 비교 분석 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
