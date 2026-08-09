from rapidfuzz.fuzz import ratio


def compare_fields(extracted_fields, stored_fields):
    results = {}

    for field, extracted_value in extracted_fields.items():
        stored_value = stored_fields.get(field, "")

        if not extracted_value or not stored_value:
            results[field] = {
                "score": 0,
                "match": False
            }
            continue

        score = ratio(
            str(extracted_value).lower().strip(),
            str(stored_value).lower().strip()
        )

        results[field] = {
            "score": round(score, 2),
            "match": score >= 80
        }

    return results


def calculate_overall_score(results):
    scores = [
        result["score"]
        for result in results.values()
        if result["score"] > 0
    ]

    if not scores:
        return 0

    return round(sum(scores) / len(scores), 2)