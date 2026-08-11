
"""
Certificate Document Comparison

Compares OCR-extracted certificate fields with
trusted certificate fields using RapidFuzz.

The comparison fields are aligned with the
AVFA database certificate schema.

OCR fields:
    Data extracted from the uploaded document.

Trusted fields:
    Values retrieved from PostgreSQL.

Returns:
    Field-level similarity scores
    Overall similarity score
    Matched fields
    Total fields
"""

from rapidfuzz.fuzz import ratio


# --------------------------------------------------
# FIELDS USED FOR RAPIDFUZZ
# --------------------------------------------------

COMPARISON_FIELDS = [
    "student_name",
    "student_roll_no",
    "degree_name",
    "issue_date",
    "institution",
]


DEFAULT_THRESHOLD = 85.0


def normalize(value):
    """
    Normalize a field before comparison.

    - Convert to string
    - Lowercase
    - Remove leading/trailing whitespace
    - Normalize multiple spaces
    """

    if value is None:
        return ""

    return " ".join(
        str(value).lower().strip().split()
    )


def compare_field(
    extracted_value,
    stored_value,
):
    """
    Compare one extracted field against
    one trusted database field.

    Returns:
        Similarity score from 0 to 100.
    """

    extracted = normalize(extracted_value)
    stored = normalize(stored_value)

    if not extracted or not stored:
        return 0.0

    return float(
        ratio(
            extracted,
            stored,
        )
    )


def compare_certificate(
    extracted_certificate,
    stored_certificate,
):
    """
    Compare OCR-extracted certificate data
    against trusted certificate data.

    Both dictionaries should use the same
    field names as COMPARISON_FIELDS.

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

        extracted_value = (
            extracted_certificate.get(field)
        )

        stored_value = (
            stored_certificate.get(field)
        )

        field_scores[field] = compare_field(
            extracted_value,
            stored_value,
        )

    # --------------------------------------------------
    # OVERALL SCORE
    # --------------------------------------------------
    #
    # Every required field participates in the score.
    # A missing field therefore contributes 0.
    # --------------------------------------------------

    overall_score = (
        sum(field_scores.values())
        / len(COMPARISON_FIELDS)
    )

    # --------------------------------------------------
    # MATCHED FIELDS
    # --------------------------------------------------

    matched_fields = sum(
        1
        for score in field_scores.values()
        if score >= DEFAULT_THRESHOLD
    )

    return {
        "field_scores": field_scores,
        "overall_score": round(
            overall_score,
            2,
        ),
        "matched_fields": matched_fields,
        "total_fields": len(COMPARISON_FIELDS),
    }


def is_document_match(
    comparison_result,
    threshold=DEFAULT_THRESHOLD,
):
    """
    Determine whether the certificate sufficiently
    matches the trusted certificate record.

    A document is considered matched only when:

    1. Overall score >= threshold
    2. Every required field matches
    """

    return (
        comparison_result["overall_score"]
        >= threshold
        and
        comparison_result["matched_fields"]
        ==
        comparison_result["total_fields"]
    )
