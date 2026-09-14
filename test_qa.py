"""
test_qa.py - Automated test script.

Instead of asking questions by hand and judging the answers by eye, the
questions and the expected behavior are defined here; the script runs all
of them, reports PASS/FAIL, and writes a report to test_results.md.

Two categories:
  ANSWERABLE   - the answer exists in the regulation; certain key facts must appear in it
  UNANSWERABLE - the answer does NOT exist in the regulation; the system must say so, not guess

Usage: python test_qa.py
"""

from datetime import datetime

import rag_core

# Phrases we look for to recognize that the model said "I don't know"
REFUSAL_MARKERS = [
    "don't have that information",
    "do not have that information",
    "not present in the provided context",
    "not specified in the provided context",
    "does not specify",
    "does not provide",
    "not provided in the given context",
]

# (question, expected facts) - each fact is a list of alternative phrasings;
# AT LEAST ONE phrase from the list must appear in the answer. This way the
# test does not fail just because the model phrased it differently
# ("eligible" vs "can enroll").
ANSWERABLE = [
    ("How many courses can I withdraw from in one semester at most?", [["two"]]),
    ("What GPA do I need to be an honor student?", [["3.00"]]),
    ("By when do I need to apply for a leave of absence?", [["fourth week"]]),
    ("What is the maximum duration of an undergraduate program?", [["seven"]]),
    ("What cumulative GPA do I need to graduate?", [["2.00"]]),
    ("How many semesters of leave of absence can I get at most?", [["four"]]),
    # Long version of the same scenario - the detailed phrasing produces better retrieval
    (
        "Let's say I took Math 1, but I passed with a DC. Then I took the remedial course "
        "but failed with an F. I need to take Math 2 next semester, and Math 1 is a "
        "prerequisite for Math 2. In this case, can I take Math 2 next semester, or am I "
        "ineligible to take it because I most recently received an F in Math 1?",
        [["eligible", "can take", "can enroll", "may take", "may enroll"]],
    ),
    # Short version of the same scenario - kept intentionally to measure phrasing
    # sensitivity. The short version surfaces ARTICLE 15 (5); the long version
    # correctly surfaces ARTICLE 13 (11).
    (
        "Let's say I took Math 1 and passed with a DC. Then I retook it and got an F. "
        "Math 1 is a prerequisite for Math 2. Can I take Math 2?",
        [["eligible", "can take", "can enroll", "may take", "may enroll"]],
    ),
]

# Questions with no answer in the regulation - the system should refuse
UNANSWERABLE = [
    "What is the campus Wi-Fi password?",
    "What time does the library close?",
    "Which cafeteria on campus has the best food?",
    "How much is the annual tuition fee in Turkish Lira?",
    "What is the minimum number of credits I need to take at the beginning of the semester?",
]


def contains_refusal(answer):
    lowered = answer.lower()
    return any(marker in lowered for marker in REFUSAL_MARKERS)


def run_answerable(session, question, expected_groups):
    """
    expected_groups: a list of lists of alternative phrasings.
    For each group, at least one phrase in that group must appear in the answer.
    """
    result = rag_core.answer_query(session, question)
    lowered = result["answer"].lower()

    missing = [
        " / ".join(group)
        for group in expected_groups
        if not any(alt.lower() in lowered for alt in group)
    ]
    passed = not result["refused"] and not missing

    return {
        "category": "ANSWERABLE",
        "question": question,
        "passed": passed,
        "note": "eksik: " + "; ".join(missing) if missing else ("reddetti" if result["refused"] else ""),
        "result": result,
    }


def run_unanswerable(session, question):
    result = rag_core.answer_query(session, question)

    # Either the threshold refused (never reached the model) or the model said "I don't know"
    passed = result["refused"] or contains_refusal(result["answer"])

    return {
        "category": "UNANSWERABLE",
        "question": question,
        "passed": passed,
        "note": "" if passed else "reddetmedi - uydurma riski",
        "result": result,
    }


def write_report(cases, passed_count, total):
    lines = [
        "# Otomatik Test Sonuclari",
        "",
        f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Sonuc: **{passed_count}/{total} test gecti**",
        "",
        f"Ayarlar: model `{rag_core.CHAT_ALIAS}`, embedding `{rag_core.EMBEDDING_ALIAS}`, "
        f"esik {rag_core.MIN_SCORE}, top_k {rag_core.TOP_K}, komsu {rag_core.NEIGHBOR_COUNT}, "
        f"hibrit agirlik {rag_core.SEMANTIC_WEIGHT}",
        "",
        "| # | Kategori | Soru | Sonuc | Semantik | Grounding | Not |",
        "|---|----------|------|-------|----------|-----------|-----|",
    ]

    for i, case in enumerate(cases, 1):
        r = case["result"]
        status = "GECTI" if case["passed"] else "KALDI"
        ground = f"{r['grounding']:.2f} ({r['grounding_label']})" if r["grounding"] is not None else "-"
        question = case["question"].replace("|", "/")
        if len(question) > 70:
            question = question[:67] + "..."
        lines.append(
            f"| {i} | {case['category']} | {question} | {status} | "
            f"{r['top_semantic']:.3f} | {ground} | {case['note']} |"
        )

    lines += ["", "## Cevap Detaylari", ""]
    for i, case in enumerate(cases, 1):
        r = case["result"]
        lines += [
            f"### {i}. {case['question']}",
            "",
            f"**Sonuc:** {'GECTI' if case['passed'] else 'KALDI'}  ",
            f"**Kaynaklar:** {', '.join(r['sources']) if r['sources'] else r.get('reason', '-')}  ",
            "",
            f"> {r['answer']}",
            "",
        ]

    with open("test_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    session = rag_core.start_session(on_progress=lambda m: print(m))
    print("\nTestler basliyor...\n")

    cases = []
    try:
        for question, keywords in ANSWERABLE:
            case = run_answerable(session, question, keywords)
            cases.append(case)
            status = "GECTI" if case["passed"] else "KALDI"
            print(f"[ANSWERABLE] {status} - {question[:60]}")
            if case["note"]:
                print(f"    ({case['note']})")

        for question in UNANSWERABLE:
            case = run_unanswerable(session, question)
            cases.append(case)
            status = "GECTI" if case["passed"] else "KALDI"
            print(f"[UNANSWERABLE] {status} - {question[:60]}")
            if case["note"]:
                print(f"    ({case['note']})")
    finally:
        session.unload()

    passed_count = sum(1 for c in cases if c["passed"])
    print(f"\nSonuc: {passed_count}/{len(cases)} test gecti.")

    write_report(cases, passed_count, len(cases))
    print("Detayli rapor: test_results.md")


if __name__ == "__main__":
    main()
