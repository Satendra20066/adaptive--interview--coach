"""
Post-Session Analytics Module
"""


def compute_answer_quality(answer_text: str, question_text: str) -> float:
    if not answer_text or len(answer_text.strip()) < 10:
        return 20.0
    text = answer_text.lower().strip()
    score = 40.0
    word_count = len(text.split())
    score += min(25, word_count * 0.8)
    quality_keywords = [
        "because", "therefore", "example", "specifically",
        "achieved", "result", "learned", "improved", "team",
        "project", "solution", "problem", "experience"
    ]
    score += min(20, sum(1 for kw in quality_keywords if kw in text) * 4)
    fillers = ["um", "uh", "like", "you know", "basically", "literally"]
    score -= min(15, sum(text.count(f) for f in fillers) * 3)
    return round(min(100, max(10, score)), 1)


def generate_session_data(session_log: list) -> dict:
    if not session_log:
        return {}
    stress_scores = [s["stress_score"] for s in session_log]
    quality_scores = [s["answer_quality"] for s in session_log]
    max_stress_idx = stress_scores.index(max(stress_scores))
    mid = len(stress_scores) // 2
    first_half_avg = sum(stress_scores[:mid]) / max(1, mid)
    second_half_avg = sum(stress_scores[mid:]) / max(1, len(stress_scores) - mid)
    return {
        "total_questions": len(session_log),
        "avg_stress": round(sum(stress_scores) / len(stress_scores), 1),
        "max_stress": round(max(stress_scores), 1),
        "min_stress": round(min(stress_scores), 1),
        "avg_quality": round(sum(quality_scores) / len(quality_scores), 1),
        "stress_at_max_question": session_log[max_stress_idx]["question"][:60] + "...",
        "stress_improved": second_half_avg < first_half_avg,
        "first_half_avg_stress": round(first_half_avg, 1),
        "second_half_avg_stress": round(second_half_avg, 1),
        "session_log": session_log,
    }
