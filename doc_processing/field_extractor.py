
"""
Extract structured certificate fields from OCR text.

Expected certificate fields:

- certificate_id
- name
- institution
- course
- date

This module receives OCR results from EasyOCR and converts
them into a structured dictionary for certificate verification.
"""

import re


def ocr_results_to_text(ocr_results):
    """
    Convert EasyOCR results into a single text string.

    EasyOCR result format:
    [
        [bounding_box, text, confidence],
        ...
    ]
    """

    return "\n".join(
        result[1].strip()
        for result in ocr_results
        if len(result) >= 2 and result[1].strip()
    )


def extract_labeled_field(text, labels):
    """
    Extract a field whose value appears after a label.

    Examples:
        Name: Rahul Kumar
        Institution: ABC University
        Course: Computer Science

    Returns the extracted value or None.
    """

    lines = text.splitlines()

    for line in lines:
        line = line.strip()

        for label in labels:

            pattern = (
                rf"^\s*{re.escape(label)}"
                rf"\s*[:\-]\s*(.+?)\s*$"
            )

            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                return match.group(1).strip()

    return None


def extract_certificate_id(text):
    """
    Extract certificate ID.

    Examples:
        Certificate ID: CERT-2026-00125
        Certificate No: CERT-2026-00125
        Certificate Number: CERT-2026-00125
    """

    pattern = (
        r"\bcertificate\s*"
        r"(?:id|no|number)"
        r"\s*[:\-]?\s*"
        r"([A-Za-z0-9][A-Za-z0-9_\-/]*)"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return None


def extract_date(text):
    """
    Extract common certificate date formats.

    Supported examples:
        09/08/2026
        09-08-2026
        09.08.2026
        2026-08-09
    """

    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(0)

    return None


def extract_certificate_fields(ocr_results):
    """
    Extract all required certificate fields
    from EasyOCR results.

    Returns:
        dict containing structured certificate information.
    """

    text = ocr_results_to_text(
        ocr_results
    )

    certificate = {
        "certificate_id": extract_certificate_id(
            text
        ),

        "name": extract_labeled_field(
            text,
            [
                "Name",
                "Student Name",
                "Candidate Name",
                "Recipient Name",
                "Holder Name",
            ],
        ),

        "institution": extract_labeled_field(
            text,
            [
                "Institution",
                "University",
                "College",
                "Institute",
            ],
        ),

        "course": extract_labeled_field(
            text,
            [
                "Course",
                "Program",
                "Programme",
                "Degree",
                "Course Name",
            ],
        ),

        "date": extract_date(
            text
        ),
    }

    return certificate


def extract_from_ocr_text(text):
    """
    Extract certificate fields directly from OCR text.

    Useful when OCR text has already been converted
    into a string elsewhere in the backend.
    """

    certificate = {
        "certificate_id": extract_certificate_id(
            text
        ),

        "name": extract_labeled_field(
            text,
            [
                "Name",
                "Student Name",
                "Candidate Name",
                "Recipient Name",
                "Holder Name",
            ],
        ),

        "institution": extract_labeled_field(
            text,
            [
                "Institution",
                "University",
                "College",
                "Institute",
            ],
        ),

        "course": extract_labeled_field(
            text,
            [
                "Course",
                "Program",
                "Programme",
                "Degree",
                "Course Name",
            ],
        ),

        "date": extract_date(
            text
        ),
    }

    return certificate


if __name__ == "__main__":

    # Standalone test only.
    # The actual application will call
    # extract_certificate_fields()
    # using results returned by EasyOCR.

    sample_text = """
    Certificate of Achievement
    Name: Rahul Kumar
    Institution: ABC University
    Course: Bachelor of Technology
    Certificate ID: CERT-2026-00125
    Date: 09/08/2026
    """

    result = extract_from_ocr_text(
        sample_text
    )

    print(result)