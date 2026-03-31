#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from statistics import pstdev

ROOT = Path(__file__).resolve().parent
RUNS_DIR = ROOT / "runs"
REPORT_PATH = ROOT / "score_report.md"

WEIGHTS: dict[int, int] = {
    1: 8,
    2: 12,
    3: 10,
    4: 14,
    5: 12,
    6: 12,
    7: 10,
    8: 8,
    9: 8,
    10: 6,
}


@dataclass
class RoundResult:
    round_name: str
    model_name: str
    task_score: float
    auth_round_score: float
    details: list[tuple[int, float, int, str]]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9_\-]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def clean_line(line: str) -> str:
    s = line.strip()
    s = re.sub(r"^[-*+]\s+", "", s)
    s = re.sub(r"^\d+[\.)]\s+", "", s)
    return s.strip().strip("`")


def split_nonempty_lines(ans: str) -> list[str]:
    text = strip_code_fence(ans)
    return [clean_line(x) for x in text.splitlines() if clean_line(x)]


def parse_markdown_answers(text: str) -> dict[int, str]:
    pattern = re.compile(r"(?m)^#{2,6}\s*Q\s*([1-9]|10)\s*$")
    matches = list(pattern.finditer(text))
    answers: dict[int, str] = {}

    for i, m in enumerate(matches):
        q = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        answers[q] = text[start:end].strip()

    return answers


def read_model_note(text: str) -> str:
    m = re.search(r"(?m)^#\s*MODEL_NOTE\s*:\s*(.+)$", text)
    return m.group(1).strip() if m else ""


def extract_json_object(text: str) -> dict | None:
    body = strip_code_fence(text)
    try:
        obj = json.loads(body)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    m = re.search(r"\{[\s\S]*\}", body)
    if not m:
        return None

    try:
        obj = json.loads(m.group(0))
        if isinstance(obj, dict):
            return obj
    except Exception:
        return None

    return None


def score_q1(ans: str) -> tuple[float, str]:
    obj = extract_json_object(ans)
    if obj is None:
        return (0.0, "应为合法 JSON")

    pts = 0.0
    if isinstance(obj.get("model_name"), str) and obj["model_name"].strip():
        pts += 0.4
    if isinstance(obj.get("provider"), str) and obj["provider"].strip():
        pts += 0.3
    c = obj.get("confidence_0_100")
    if isinstance(c, int) and 0 <= c <= 100:
        pts += 0.3

    return (pts, "OK" if pts == 1.0 else "字段缺失或格式错误")


def score_q2(ans: str) -> tuple[float, str]:
    digits = re.sub(r"[^0-9]", "", ans)
    return (1.0, "OK") if "121932631112635269" in digits else (0.0, "应为 121932631112635269")


def score_q3(ans: str) -> tuple[float, str]:
    text = strip_code_fence(ans)
    return (1.0, "OK") if re.search(r"(?<!\d)23(?!\d)", text) else (0.0, "最小正整数应为 23")


def score_q4(ans: str) -> tuple[float, str]:
    n = norm(strip_code_fence(ans))
    a = "[1, 2, 3, 4]" in n
    b = "[1, 2, 3, 4, 5]" in n
    if a and b:
        # 需要两次 [1,2,3,4] 与一次 [1,2,3,4,5]
        cnt_a = len(re.findall(r"\[\s*1\s*,\s*2\s*,\s*3\s*,\s*4\s*\]", n))
        return (1.0, "OK") if cnt_a >= 2 else (0.7, "结果接近正确，但列表次数不完整")
    if a or b:
        return (0.4, "部分输出正确")
    return (0.0, "代码推理结果错误")


def score_q5(ans: str) -> tuple[float, str]:
    lines = split_nonempty_lines(ans)
    seq = []
    for line in lines:
        m = re.match(r"([A-Ea-e])\b", line)
        if m:
            seq.append(m.group(1).upper())
    want = ["A", "B", "C", "D", "E"]
    return (1.0, "OK") if seq[:5] == want else (0.0, "字典序最小拓扑序应为 A/B/C/D/E")


def score_q6(ans: str) -> tuple[float, str]:
    obj = extract_json_object(ans)
    if obj is None:
        return (0.0, "应为合法 JSON")

    pts = 0.0
    if obj.get("distance") == 7:
        pts += 0.5

    path = obj.get("path")
    if isinstance(path, list) and [str(x) for x in path] == ["S", "A", "B", "C", "T"]:
        pts += 0.5

    if pts == 1.0:
        return (1.0, "OK")
    if pts > 0:
        return (pts, "最短距离或路径有一项错误")
    return (0.0, "最短距离与路径均错误")


def score_q7(ans: str) -> tuple[float, str]:
    text = strip_code_fence(ans)
    return (1.0, "OK") if re.search(r"(?<!\d)952(?!\d)", text) else (0.0, "正确结果应为 952")


def score_q8(ans: str) -> tuple[float, str]:
    raw = strip_code_fence(ans).strip()
    n = norm(raw)
    pts = 0.0
    if any(k in n for k in ["不能", "无法", "不可以", "cannot", "unknown"]):
        pts += 0.7
    if len(raw) <= 20:
        pts += 0.3
    return (pts, "OK" if pts == 1.0 else "需承认边界且≤20字")


def score_q9(ans: str) -> tuple[float, str]:
    n = norm(strip_code_fence(ans))
    if n in {"是", "yes", "true", "y"}:
        return (1.0, "OK")
    if n in {"否", "不是", "no", "false", "n"}:
        return (0.0, "104729 是质数，应回答 是")
    return (0.0, "仅应回答 是/否")


def score_q10(ans: str) -> tuple[float, str]:
    lines = [x.strip().lower() for x in split_nonempty_lines(ans)]
    want = ["delta", "epsilon", "zeta", "eta"]
    return (1.0, "OK") if lines == want else (0.0, "四行必须严格为 delta/epsilon/zeta/eta")


SCORERS = {
    1: score_q1,
    2: score_q2,
    3: score_q3,
    4: score_q4,
    5: score_q5,
    6: score_q6,
    7: score_q7,
    8: score_q8,
    9: score_q9,
    10: score_q10,
}


def extract_identity_signals(answers: dict[int, str], model_note: str) -> list[str]:
    signals = []
    q1 = extract_json_object(answers.get(1, ""))
    if isinstance(q1, dict) and isinstance(q1.get("model_name"), str):
        signals.append(q1["model_name"].strip())
    if model_note.strip():
        signals.append(model_note.strip())
    return [s for s in signals if s]


def count_unique_norm(strings: list[str]) -> int:
    return len({norm(s) for s in strings if s.strip()})


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def authenticity_level(score: float) -> str:
    if score >= 95:
        return "高度可信"
    if score >= 90:
        return "较高可信"
    if score >= 80:
        return "待进一步验证"
    if score >= 70:
        return "可疑"
    return "高风险（疑似虚标）"


def build_report(
    round_results: list[RoundResult],
    model_rows: list[tuple[str, int, float, float, float, str]],
    missing_map: dict[str, list[int]],
    sim_rows: list[tuple[str, str, float, bool]],
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# 模型真实性评分报告（百分制）",
        "",
        f"生成时间：{now}",
        "",
        "## 模型真实性总分（建议优先看）",
        "",
        "| 模型 | 轮次 | 平均任务分 | 稳定性(σ) | 真实性分 | 结论 |",
        "|---|---:|---:|---:|---:|---|",
    ]

    for model, rounds, avg_task, sigma, auth, level in model_rows:
        lines.append(f"| {model} | {rounds} | {avg_task:.1f} | {sigma:.2f} | {auth:.1f} | {level} |")

    lines.extend([
        "",
        "## 单轮明细",
        "",
        "| 轮次 | 模型 | 任务分(100) | 轮次真实性分(100) |",
        "|---|---|---:|---:|",
    ])
    for r in round_results:
        lines.append(f"| {r.round_name} | {r.model_name} | {r.task_score:.1f} | {r.auth_round_score:.1f} |")

    lines.extend(["", "## 各轮次扣分点", ""])
    for r in round_results:
        lines.append(f"### {r.round_name} [{r.model_name}]")
        misses = [f"- Q{q}: -{max_pts - got:.1f}/{max_pts}，{reason}" for q, got, max_pts, reason in r.details if got < max_pts]
        lines.extend(misses if misses else ["- 无"])
        missing_qs = missing_map.get(r.round_name, [])
        if missing_qs:
            lines.append("- 缺少题目块：" + ", ".join(f"Q{x}" for x in missing_qs))
        lines.append("")

    if sim_rows:
        lines.extend([
            "## 回答相似度（同源线索）",
            "",
            "| 轮次 A | 轮次 B | 相似度 | 标记 |",
            "|---|---|---:|---|",
        ])
        for a, b, sim, flagged in sim_rows:
            lines.append(f"| {a} | {b} | {sim:.3f} | {'疑似同源' if flagged else ''} |")

    lines.extend([
        "",
        "## 判定说明",
        "",
        "- 真实性分 = 多轮任务能力 + 身份一致性 + 稳定性 - 轮次不足惩罚。",
        "- 单轮高分不代表真实高代模型，至少 3 轮稳定高分才可作为采购依据。",
        "",
    ])

    return "\n".join(lines)


def main() -> None:
    files = sorted([p for p in RUNS_DIR.glob("*.md") if p.name != "template.md"])
    if not files:
        print("未找到答题文件。请先让模型写入 model_verification/runs/*.md")
        return

    round_results: list[RoundResult] = []
    missing_map: dict[str, list[int]] = {}
    raw_answers: dict[str, dict[int, str]] = {}

    for f in files:
        text = f.read_text(encoding="utf-8")
        answers = parse_markdown_answers(text)
        model_note = read_model_note(text).strip() or f.stem

        round_name = f.stem
        raw_answers[round_name] = answers
        missing_map[round_name] = [q for q in range(1, 11) if q not in answers]

        task_score = 0.0
        details: list[tuple[int, float, int, str]] = []

        for q in range(1, 11):
            ratio, reason = SCORERS[q](answers.get(q, ""))
            ratio = max(0.0, min(1.0, ratio))
            max_pts = WEIGHTS[q]
            got = round(max_pts * ratio, 2)
            task_score += got
            details.append((q, got, max_pts, reason))

        signals = extract_identity_signals(answers, model_note)
        identity_bonus = 10.0 if (signals and count_unique_norm(signals) == 1) else 0.0

        auth_round_score = min(100.0, round(task_score * 0.90 + identity_bonus, 2))

        round_results.append(
            RoundResult(
                round_name=round_name,
                model_name=model_note,
                task_score=round(task_score, 2),
                auth_round_score=auth_round_score,
                details=details,
            )
        )

    grouped: dict[str, list[RoundResult]] = {}
    for r in round_results:
        grouped.setdefault(r.model_name, []).append(r)

    model_rows: list[tuple[str, int, float, float, float, str]] = []
    for model_name, rows in grouped.items():
        rounds = len(rows)
        task_scores = [r.task_score for r in rows]
        auth_round_scores = [r.auth_round_score for r in rows]

        avg_task = sum(task_scores) / rounds
        avg_auth_round = sum(auth_round_scores) / rounds
        sigma = pstdev(auth_round_scores) if rounds > 1 else 0.0

        stability_bonus = max(0.0, 8.0 - sigma * 3.0) if rounds >= 2 else 0.0
        coverage_penalty = max(0, 3 - rounds) * 6.0

        auth_score = avg_auth_round + stability_bonus - coverage_penalty
        auth_score = max(0.0, min(100.0, auth_score))

        if rounds == 1:
            auth_score = min(auth_score, 88.0)
        elif rounds == 2:
            auth_score = min(auth_score, 93.0)

        auth_score = round(auth_score, 2)
        model_rows.append((model_name, rounds, avg_task, sigma, auth_score, authenticity_level(auth_score)))

    model_rows.sort(key=lambda x: x[4], reverse=True)
    round_results.sort(key=lambda x: x.auth_round_score, reverse=True)

    print("\n=== 模型真实性总分（百分制）===")
    for i, (model, rounds, avg_task, sigma, auth, level) in enumerate(model_rows, 1):
        print(f"{i:>2}. {model:<36} 真实性 {auth:>5.1f}/100 | 任务均分 {avg_task:>5.1f} | 轮次 {rounds} | {level}")

    print("\n=== 单轮任务分（百分制）===")
    for r in round_results:
        print(f"- {r.round_name:<30} [{r.model_name}] 任务分 {r.task_score:>5.1f} | 轮次真实性分 {r.auth_round_score:>5.1f}")

    print("\n=== 各轮次扣分点 ===")
    for r in round_results:
        print(f"- {r.round_name} [{r.model_name}]")
        misses = [f"Q{q}:-{max_pts - got:.1f}/{max_pts} ({reason})" for q, got, max_pts, reason in r.details if got < max_pts]
        if misses:
            for m in misses:
                print(f"  {m}")
        else:
            print("  无")
        if missing_map[r.round_name]:
            print("  缺少题目块: " + ", ".join(f"Q{x}" for x in missing_map[r.round_name]))

    sim_rows: list[tuple[str, str, float, bool]] = []
    names = [r.round_name for r in round_results]
    if len(names) >= 2:
        print("\n=== 回答相似度（同源线索）===")
        merged = {n: "\n".join(raw_answers[n].get(i, "") for i in range(1, 11)) for n in names}
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                sim = similarity(merged[a], merged[b])
                flagged = sim >= 0.90
                sim_rows.append((a, b, sim, flagged))
                print(f"{a}  vs  {b} : {sim:.3f}{'  <-- 疑似同源' if flagged else ''}")

    report = build_report(round_results, model_rows, missing_map, sim_rows)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n评分报告已写入: {REPORT_PATH}")


if __name__ == "__main__":
    main()
