# -*- coding: utf-8 -*-
"""
Script chạy kiểm thử tự động 1.000 kịch bản Phân tích liên bài (Cross-Article Analysis).
Usage:
    python backend/scripts/run_1000_cross_tests.py [--limit N] [--category CAT]
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

def main():
    parser = argparse.ArgumentParser(description="Chạy kiểm thử 1.000 bài test phân tích liên bài Acamind")
    parser.add_argument("--limit", type=int, default=20, help="Số lượng test case muốn chạy (mặc định 20, dùng 1000 để chạy hết)")
    parser.add_argument("--category", type=str, default="", help="Lọc theo category cụ thể")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="Địa chỉ backend")
    args = parser.parse_args()

    test_file = r"data/operational_test_1000_cross_article.json"
    if not os.path.exists(test_file):
        print(f"[ERROR] Không tìm thấy file {test_file}")
        sys.exit(1)

    with open(test_file, "r", encoding="utf-8") as f:
        all_tests = json.load(f)

    if args.category:
        all_tests = [t for t in all_tests if t.get("category") == args.category]

    total_to_run = min(args.limit, len(all_tests))
    tests_to_run = all_tests[:total_to_run]

    print(f"\n{'='*70}")
    print(f"  ACAMIND SUITE: KIỂM THỬ THỰC NGHIỆM PHÂN TÍCH LIÊN BÀI")
    print(f"  Tổng số test case nạp: {len(all_tests)} | Sẽ chạy: {total_to_run} ca")
    print(f"  Target Server: {args.base_url}")
    print(f"{'='*70}\n")

    results = []
    passed = 0
    failed = 0
    total_latency_ms = 0

    for idx, test in enumerate(tests_to_run, 1):
        cid = test["case_id"]
        cat = test["category"]
        name = test["name"][:55]
        endpoint = test["target_endpoint"]
        url = args.base_url + endpoint
        payload_bytes = json.dumps(test["payload"]).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload_bytes,
            headers={"Content-Type": "application/json"}
        )

        t0 = time.time()
        status_code = None
        error_msg = None
        response_preview = ""

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status_code = resp.status
                latency = round((time.time() - t0) * 1000, 2)
                raw_body = resp.read()
                try:
                    data = json.loads(raw_body.decode("utf-8"))
                    response_preview = str(data)[:100]
                except Exception:
                    response_preview = raw_body.decode("utf-8", errors="ignore")[:100]
        except urllib.error.HTTPError as he:
            status_code = he.code
            latency = round((time.time() - t0) * 1000, 2)
            error_msg = f"HTTPError: {he.code}"
        except Exception as e:
            latency = round((time.time() - t0) * 1000, 2)
            error_msg = str(e)

        is_success = (status_code == test.get("expected_status", 200))
        if is_success:
            passed += 1
            mark = "PASS"
        else:
            failed += 1
            mark = "FAIL"

        total_latency_ms += latency
        print(f"[{idx:03d}/{total_to_run}] [{mark}] {cid} | {cat[:18]:<18} | {latency:7.1f}ms | {name}")

        results.append({
            "case_id": cid,
            "category": cat,
            "name": test["name"],
            "endpoint": endpoint,
            "status": status_code,
            "latency_ms": latency,
            "passed": is_success,
            "error": error_msg,
            "preview": response_preview
        })

    avg_latency = round(total_latency_ms / max(1, total_to_run), 2)
    pass_rate = round((passed / max(1, total_to_run)) * 100, 1)

    print(f"\n{'='*70}")
    print(f"  KẾT QUẢ KIỂM THỬ: {passed}/{total_to_run} PASSED ({pass_rate}%) | {failed} FAILED")
    print(f"  Độ trễ trung bình: {avg_latency} ms")
    print(f"{'='*70}\n")

    # Lưu báo cáo
    os.makedirs("outputs", exist_ok=True)
    report_file = r"outputs/cross_article_test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_executed": total_to_run,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "avg_latency_ms": avg_latency,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    print(f"Báo cáo chi tiết đã lưu tại: {os.path.abspath(report_file)}")

if __name__ == "__main__":
    main()
