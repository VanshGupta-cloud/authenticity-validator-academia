"""
Certificate Field Extractor

Converts EasyOCR output into structured certificate fields.

Supports:

1. Label-based certificates

    Name: Rahul Kumar
    Institution: ABC University
    Course: Bachelor of Technology
    Roll No: 123456
    Marks: 450
    CGPA: 8.5

2. Layout-based certificates

    This is to certify that
    BHUMIKA THAKUR

    Roll No.
    17245572

    School
    CONVENT OF JESUS AND MARY

The extractor returns OCR-semantic fields.

Database/API-specific mapping should be handled by
the verification/backend layer.
"""

import re


# --------------------------------------------------
# OCR RESULTS -> TEXT
# --------------------------------------------------

def ocr_results_to_text(ocr_results):
    """
    Convert EasyOCR results into a single text string.

    EasyOCR format:

        [
            [bounding_box, detected_text, confidence],
            ...
        ]
    """

    lines = []

    for result in ocr_results:

        if len(result) < 2:
            continue

        text = str(result[1]).strip()

        if text:
            lines.append(text)

    return "\n".join(lines)


# --------------------------------------------------
# BASIC HELPERS
# --------------------------------------------------

def clean_value(value):
    """Clean extracted text."""

    if value is None:
        return None

    value = str(value).strip()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value if value else None


def get_lines(text):
    """Return cleaned OCR lines."""

    if not text:
        return []

    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


# --------------------------------------------------
# LABEL-BASED EXTRACTION
# --------------------------------------------------

def extract_labeled_field(text, labels):
    """
    Extract a value appearing after a label.

    Supports:

        Name: Rahul Kumar
        Institution: ABC University
        Course: Computer Science

    The colon/dash is optional.
    """

    lines = get_lines(text)

    for line in lines:

        for label in labels:

            pattern = (
                rf"^\s*{re.escape(label)}"
                rf"\s*(?::|-)\s*(.+?)\s*$"
            )

            match = re.search(
                pattern,
                line,
                re.IGNORECASE,
            )

            if match:
                return clean_value(
                    match.group(1)
                )

    return None


# --------------------------------------------------
# VALUE AFTER LABEL
# --------------------------------------------------

def extract_value_after_label(text, labels):
    """
    Extract a value from:

        Label: Value

    or:

        Label
        Value

    Example:

        Roll No.
        17245572
    """

    lines = get_lines(text)

    for index, line in enumerate(lines):

        for label in labels:

            label_pattern = re.escape(label)

            # ------------------------------------------
            # Exact label match
            # ------------------------------------------

            if re.fullmatch(
                rf"\s*{label_pattern}\s*[:\-]?\s*",
                line,
                re.IGNORECASE,
            ):

                if index + 1 < len(lines):

                    next_line = clean_value(
                        lines[index + 1]
                    )

                    if next_line:
                        return next_line

            # ------------------------------------------
            # Label + value on same line
            # ------------------------------------------

            same_line = re.search(
                rf"^\s*{label_pattern}"
                rf"\s*[:\-]\s*(.+?)\s*$",
                line,
                re.IGNORECASE,
            )

            if same_line:

                value = clean_value(
                    same_line.group(1)
                )

                if value:
                    return value

    return None


# --------------------------------------------------
# CERTIFICATE NUMBER
# --------------------------------------------------

def extract_certificate_id(text):
    """
    Extract certificate number / ID.

    Examples:

        Certificate ID: CERT-2026-00125
        Certificate No: CERT-2026-00125
        Certificate Number: CERT-2026-00125

    Roll number is NOT treated as certificate ID.
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
        re.IGNORECASE,
    )

    if match:
        return clean_value(
            match.group(1)
        )

    return None


# --------------------------------------------------
# NAME
# --------------------------------------------------

def extract_name(text):
    """
    Extract student/candidate name.

    Supports:

        Name: Rahul Kumar

    and:

        This is to certify that
        BHUMIKA THAKUR
    """

    value = extract_labeled_field(
        text,
        [
            "Student Name",
            "Candidate Name",
            "Recipient Name",
            "Holder Name",
            "Name",
        ],
    )

    if value:
        return value

    value = extract_value_after_label(
        text,
        [
            "Student Name",
            "Candidate Name",
            "Recipient Name",
            "Holder Name",
            "Name",
        ],
    )

    if value:
        return value

    lines = get_lines(text)

    for index, line in enumerate(lines):

        if re.search(
            r"this\s+is\s+to\s+certif",
            line,
            re.IGNORECASE,
        ):

            if index + 1 < len(lines):

                candidate = clean_value(
                    lines[index + 1]
                )

                if candidate and not re.search(
                    r"roll|mother|father|date|school|"
                    r"certificate|institution|university",
                    candidate,
                    re.IGNORECASE,
                ):
                    return candidate

    return None


# --------------------------------------------------
# ROLL NUMBER
# --------------------------------------------------

ROLL_LABELS = [
    "Roll Number",
    "Roll No",
    "Roll No.",
    "Registration Number",
    "Registration No",
    "Registration No.",
    "Enrollment Number",
    "Enrollment No",
    "Enrollment No.",
]


def extract_roll_number(text):
    """
    Extract student roll / registration number.
    """

    value = extract_labeled_field(
        text,
        ROLL_LABELS,
    )

    if value:
        return value

    return extract_value_after_label(
        text,
        ROLL_LABELS,
    )


# --------------------------------------------------
# INSTITUTION
# --------------------------------------------------

INSTITUTION_LABELS = [
    "Institution",
    "University",
    "College",
    "Institute",
]


def extract_institution(text):
    """
    Extract institution / school / university.

    Supports:

        Institution: ABC University

    and layout:

        ABC UNIVERSITY
        School

    Returns the institution NAME as a string.

    IMPORTANT:
        This function does not return institution_id.
    """

    value = extract_labeled_field(
        text,
        INSTITUTION_LABELS,
    )

    if value:
        return value

    value = extract_value_after_label(
        text,
        INSTITUTION_LABELS,
    )

    if value:
        return value

    lines = get_lines(text)

    institution_words = {
        "school",
        "college",
        "university",
        "institute",
    }

    for index, line in enumerate(lines):

        if line.lower().strip() in institution_words:

            if index > 0:

                candidate = clean_value(
                    lines[index - 1]
                )

                if candidate and not re.search(
                    r"marks|certificate|examination|"
                    r"subject|roll|registration|"
                    r"course|degree",
                    candidate,
                    re.IGNORECASE,
                ):
                    return candidate

    return None


# --------------------------------------------------
# DEGREE / COURSE
# --------------------------------------------------

DEGREE_LABELS = [
    "Degree Name",
    "Degree",
    "Course Name",
    "Course",
    "Program Name",
    "Program",
    "Programme Name",
    "Programme",
]


def looks_like_degree(value):
    """
    Check whether a candidate looks like an academic
    degree/course rather than a roll number, institution,
    date, or unrelated certificate text.
    """

    if not value:
        return False

    value = clean_value(value)

    # Reject obvious numeric identifiers.
    if re.fullmatch(
        r"[\d\s\-\/]+",
        value,
    ):
        return False

    # Reject obvious labels/metadata.
    if re.search(
        r"roll\s*(number|no)?|"
        r"registration|"
        r"enrollment|"
        r"certificate\s*(id|no|number)?|"
        r"issue\s*date|"
        r"date\s*of\s*issue|"
        r"marks|"
        r"cgpa|"
        r"gpa",
        value,
        re.IGNORECASE,
    ):
        return False

    # Accept common academic terms.
    if re.search(
        r"\b("
        r"bachelor|"
        r"master|"
        r"diploma|"
        r"degree|"
        r"b\.?\s*tech|"
        r"b\.?\s*e\.?|"
        r"m\.?\s*tech|"
        r"m\.?\s*e\.?|"
        r"b\.?\s*sc|"
        r"m\.?\s*sc|"
        r"b\.?\s*com|"
        r"m\.?\s*com|"
        r"bca|"
        r"mca|"
        r"ph\.?\s*d|"
        r"secondary school examination|"
        r"senior school certificate examination|"
        r"higher secondary"
        r")\b",
        value,
        re.IGNORECASE,
    ):
        return True

    return False


def extract_degree(text):
    """
    Extract degree/course/program.

    Explicit labels are preferred.

    Falls back to common academic degree phrases.
    """

    value = extract_labeled_field(
        text,
        DEGREE_LABELS,
    )

    if value and looks_like_degree(value):
        return value

    value = extract_value_after_label(
        text,
        DEGREE_LABELS,
    )

    if value and looks_like_degree(value):
        return value

    lines = get_lines(text)

    for line in lines:

        candidate = clean_value(line)

        if looks_like_degree(candidate):
            return candidate

    return None


# --------------------------------------------------
# DATE
# --------------------------------------------------

def extract_date_from_value(value):
    """
    Extract a date from a supplied value.
    """

    if not value:
        return None

    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b\d{1,2}\s+"
        r"(?:Jan|January|Feb|February|Mar|March|"
        r"Apr|April|May|Jun|June|Jul|July|"
        r"Aug|August|Sep|September|Oct|October|"
        r"Nov|November|Dec|December)"
        r"\s+\d{4}\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            value,
            re.IGNORECASE,
        )

        if match:
            return clean_value(
                match.group(0)
            )

    return None


def extract_date(text):
    """
    Extract the certificate issue date.

    Does NOT blindly take the first date in the document.
    This prevents Date of Birth from being used as issue_date.
    """

    lines = get_lines(text)

    date_labels = [
        "Issue Date",
        "Date of Issue",
        "Certificate Date",
        "Date Issued",
    ]

    value = extract_labeled_field(
        text,
        date_labels,
    )

    date = extract_date_from_value(
        value
    )

    if date:
        return date

    value = extract_value_after_label(
        text,
        date_labels,
    )

    date = extract_date_from_value(
        value
    )

    if date:
        return date

    for index, line in enumerate(lines):

        if re.match(
            r"^\s*date\s*[:\-]",
            line,
            re.IGNORECASE,
        ):

            date = extract_date_from_value(
                line
            )

            if date:
                return date

            if index + 1 < len(lines):

                date = extract_date_from_value(
                    lines[index + 1]
                )

                if date:
                    return date

    return None


# --------------------------------------------------
# MARKS
# --------------------------------------------------

MARKS_LABELS = [
    "Total Marks",
    "Marks Obtained",
    "Marks",
    "Score",
]


def extract_marks(text):
    """
    Extract marks when explicitly labelled.

    Examples:

        Marks: 450
        Total Marks: 500
        Marks Obtained: 450
    """

    value = extract_labeled_field(
        text,
        MARKS_LABELS,
    )

    if value:
        return value

    value = extract_value_after_label(
        text,
        MARKS_LABELS,
    )

    if value:
        return value

    return None


# --------------------------------------------------
# CGPA / GPA
# --------------------------------------------------

CGPA_LABELS = [
    "CGPA",
    "C.G.P.A",
    "GPA",
    "G.P.A",
]


def extract_cgpa(text):
    """
    Extract CGPA/GPA when explicitly labelled.

    Examples:

        CGPA: 8.5
        GPA: 8.5
    """

    value = extract_labeled_field(
        text,
        CGPA_LABELS,
    )

    if value:
        return value

    value = extract_value_after_label(
        text,
        CGPA_LABELS,
    )

    if value:
        return value

    return None


# --------------------------------------------------
# BUILD CERTIFICATE STRUCTURE
# --------------------------------------------------

def build_certificate_fields(text):
    """
    Build the structured certificate record.

    OCR-semantic fields:

        certificate_number
        student_name
        student_roll_no
        degree_name
        course_name
        issue_date
        institution
        marks
        cgpa

    Compatibility aliases are also returned.
    """

    certificate_number = extract_certificate_id(
        text
    )

    student_name = extract_name(
        text
    )

    student_roll_no = extract_roll_number(
        text
    )

    degree_name = extract_degree(
        text
    )

    issue_date = extract_date(
        text
    )

    institution = extract_institution(
        text
    )

    marks = extract_marks(
        text
    )

    cgpa = extract_cgpa(
        text
    )

   return {
    "certificate_number": certificate_number,
    "student_name": student_name,
    "student_roll_no": student_roll_no,

    "degree_name": degree_name,
    "course_name": degree_name,

    "issue_date": issue_date,

    "institution": institution,
    "institution_name": institution,

    "marks": marks,
    "cgpa": cgpa,

    # Compatibility aliases
    "certificate_id": certificate_number,
    "name": student_name,
    "roll_number": student_roll_no,
    "degree": degree_name,
    "course": degree_name,
    "date": issue_date,
    "gpa": cgpa,
}


# --------------------------------------------------
# PUBLIC FUNCTIONS
# --------------------------------------------------

def extract_certificate_fields(ocr_results):
    """
    Extract certificate fields from EasyOCR results.
    """

    text = ocr_results_to_text(
        ocr_results
    )

    return build_certificate_fields(
        text
    )


def extract_from_ocr_text(text):
    """
    Extract certificate fields directly
    from an OCR text string.
    """

    return build_certificate_fields(
        text
    )


# --------------------------------------------------
# STANDALONE TEST
# --------------------------------------------------

if __name__ == "__main__":

    sample_text = """
    Certificate of Achievement

    Name: Rahul Kumar

    Institution: ABC University

    Course: Bachelor of Technology

    Certificate ID: CERT-2026-00125

    Roll No: 123456

    Marks: 450

    CGPA: 8.5

    Issue Date: 09/08/2026
    """

    result = extract_from_ocr_text(
        sample_text
    )

    print("\n--- EXTRACTED FIELDS ---")

    for field, value in result.items():

        print(
            f"{field}: {value}"
        )
