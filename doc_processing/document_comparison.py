"""
Certificate Document Comparison

Compares OCR-extracted certificate fields with the
original certificate record using RapidFuzz.

Returns field-level similarity scores and an overall
similarity score.

"""

from rapidfuzz.fuzz import ratio


COMPARISON_FIELDS = [
    "name",
    "institution",
    "course",
    "date",
]


def normalize(value):
    """
    Normalize text before comparison.
    """

    if value is None:
        return ""

    return " ".join(str(value).lower().strip().split())


def compare_field(extracted_value, stored_value):
    """
    Compare two field values using RapidFuzz.

    Returns similarity from 0 to 100.
    """

    extracted = normalize(extracted_value)
    stored = normalize(stored_value)

    if not extracted or not stored:
        return 0.0

    return float(ratio(extracted, stored))


def compare_certificate(extracted_certificate, stored_certificate):
    """
    Compare OCR-extracted certificate data against
    the trusted certificate record.

    Returns:
        {
            "field_scores": {...},
            "overall_score": float,
            "matched_fields": int,
            "total_fields": int
        }
    """

    field_scores = {}

    for field in COMPARISON_FIELDS:

        extracted_value = extracted_certificate.get(field)
        stored_value = stored_certificate.get(field)

        field_scores[field] = compare_field(
            extracted_value,
            stored_value
        )

    valid_scores = [
        score
        for score in field_scores.values()
        if score > 0
    ]

    if valid_scores:
        overall_score = sum(valid_scores) / len(valid_scores)
    else:
        overall_score = 0.0

    matched_fields = sum(
        1
        for score in field_scores.values()
        if score >= 85
    )

    return {
        "field_scores": field_scores,
        "overall_score": round(overall_score, 2),
        "matched_fields": matched_fields,
        "total_fields": len(COMPARISON_FIELDS),
    }


def is_document_match(comparison_result, threshold=85.0):
    """
    Determine whether the certificate fields sufficiently match
    the trusted certificate record.

    Default threshold: 85%.
    """

    return comparison_result["overall_score"] >= threshold