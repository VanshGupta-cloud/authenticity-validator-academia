"""
Certificate Field Extractor

Converts EasyOCR output into structured certificate fields.

Supports:
1. Label-based certificates
2. Layout-based certificates

Output is aligned with the AVFA certificate database schema.
"""

import re
from datetime import datetime


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

    value = re.sub(r"\s+", " ", value)

    return value if value else None


def get_lines(text):
    """Return cleaned OCR lines."""

    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def is_label_line(value):
    """
    Check whether a value looks like another certificate label.
    """

    if not value:
        return False

    return bool(
        re.search(
            r"\b("
            r"name|student|candidate|"
            r"roll|registration|enrollment|"
            r"institution|university|college|institute|school|"
            r"course|degree|program|programme|"
            r"marks|mark|percentage|"
            r"cgpa|gpa|"
            r"issue\s*date|date\s*of\s*issue|"
            r"certificate"
            r")\b",
            value,
            re.IGNORECASE,
        )
    )


# --------------------------------------------------
# LABEL-BASED EXTRACTION
# --------------------------------------------------

def extract_labeled_field(text, labels):
    """
    Extract a value appearing after a label.

    Examples:

        Name: Rahul Kumar
        Institution: ABC University
        Course: Computer Science
    """

    lines = get_lines(text)

    for line in lines:

        for label in labels:

            pattern = (
                rf"^\s*{re.escape(label)}"
                rf"\s*[:\-]\s*(.+?)\s*$"
            )

            match = re.search(
                pattern,
                line,
                re.IGNORECASE,
            )

            if match:
                return clean_value(match.group(1))

    return None


def extract_value_after_label(text, labels):
    """
    Extract a value appearing on the same line or
    immediately after a label.

    Example:

        Roll No.
        17245572
    """

    lines = get_lines(text)

    for index, line in enumerate(lines):

        for label in labels:

            if re.search(
                rf"\b{re.escape(label)}\b",
                line,
                re.IGNORECASE,
            ):

                # Same line
                same_line = re.search(
                    rf"{re.escape(label)}"
                    rf"\s*[:\-]?\s+(.+)$",
                    line,
                    re.IGNORECASE,
                )

                if same_line:

                    value = clean_value(
                        same_line.group(1)
                    )

                    if value and not is_label_line(value):
                        return value

                # Next line
                if index + 1 < len(lines):

                    next_line = clean_value(
                        lines[index + 1]
                    )

                    if (
                        next_line
                        and not is_label_line(next_line)
                    ):
                        return next_line

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
        return clean_value(match.group(1))

    return None


# --------------------------------------------------
# STUDENT NAME
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
            "Name",
            "Student Name",
            "Candidate Name",
            "Recipient Name",
            "Holder Name",
        ],
    )

    if value:
        return value

    value = extract_value_after_label(
        text,
        [
            "Name",
            "Student Name",
            "Candidate Name",
            "Recipient Name",
            "Holder Name",
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
                    r"certificate|course|degree",
                    candidate,
                    re.IGNORECASE,
                ):
                    return candidate

    return None


# --------------------------------------------------
# ROLL NUMBER
# --------------------------------------------------

def extract_roll_number(text):
    """
    Extract student roll / registration number.
    """

    labels = [
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

    value = extract_labeled_field(text, labels)

    if value:
        return value

    value = extract_value_after_label(text, labels)

    if value:
        return value

    return None


# --------------------------------------------------
# INSTITUTION
# --------------------------------------------------

def extract_institution(text):
    """
    Extract institution / school / university.

    Supports:

        Institution: ABC University

    and layout-based certificates where the institution
    appears near the top of the certificate.
    """

    labels = [
        "Institution",
        "University",
        "College",
        "Institute",
        "School",
    ]

    # Label-based
    value = extract_labeled_field(
        text,
        labels,
    )

    if value:
        return value

    # Label followed by value
    value = extract_value_after_label(
        text,
        labels,
    )

    if value:
        return value

    lines = get_lines(text)

    institution_words = (
        "school",
        "college",
        "university",
        "institute",
    )

    # Example:
    #
    # ABC UNIVERSITY
    # School
    #
    for index, line in enumerate(lines):

        if line.lower().strip() in institution_words:

            if index > 0:

                candidate = clean_value(
                    lines[index - 1]
                )

                if candidate and not re.search(
                    r"marks|certificate|examination|subject|"
                    r"achievement|diploma",
                    candidate,
                    re.IGNORECASE,
                ):
                    return candidate

    # --------------------------------------------------
    # TOP-OF-CERTIFICATE FALLBACK
    # --------------------------------------------------

    ignored_headings = (
        "certificate",
        "certificate of achievement",
        "certificate of completion",
        "certificate of merit",
        "this is to certify",
        "award",
        "achievement",
    )

    # Inspect only the first few OCR lines.
    for line in lines[:6]:

        candidate = clean_value(line)

        if not candidate:
            continue

        lower = candidate.lower()

        if lower in ignored_headings:
            continue

        if re.search(
            r"\b(university|college|institute|school)\b",
            candidate,
            re.IGNORECASE,
        ):
            return candidate

    return None


# --------------------------------------------------
# COURSE / DEGREE
# --------------------------------------------------

def looks_like_course(value):
    """
    Determine whether an OCR value looks like a course/degree
    rather than another certificate field.
    """

    if not value:
        return False

    value = clean_value(value)

    # Never accept labels/fields as course names.
    if re.search(
        r"\b("
        r"roll|roll\s*no|roll\s*number|"
        r"registration|enrollment|"
        r"certificate\s*(id|no|number)|"
        r"issue\s*date|date\s*of\s*issue|"
        r"marks?|percentage|cgpa|gpa|"
        r"institution|university|college|institute|school"
        r")\b",
        value,
        re.IGNORECASE,
    ):
        return False

    # A pure number is not a course.
    if re.fullmatch(r"[\d\W_]+", value):
        return False

    return True


def extract_degree(text):
    """
    Extract course / degree / programme.

    Primary database field:
        course_name
    """

    labels = [
        "Degree",
        "Course",
        "Program",
        "Programme",
        "Course Name",
        "Degree Name",
    ]

    value = extract_labeled_field(
        text,
        labels,
    )

    if value and looks_like_course(value):
        return value

    value = extract_value_after_label(
        text,
        labels,
    )

    if value and looks_like_course(value):
        return value

    lines = get_lines(text)

    # Search for common academic names.
    for line in lines:

        if not looks_like_course(line):
            continue

        if re.search(
            r"(secondary school examination|"
            r"senior school certificate examination|"
            r"higher secondary|"
            r"bachelor|master|diploma|"
            r"b\.?\s*tech|"
            r"b\.?\s*e\.?|"
            r"m\.?\s*tech|"
            r"b\.?\s*sc|"
            r"m\.?\s*sc|"
            r"b\.?\s*com|"
            r"m\.?\s*com)",
            line,
            re.IGNORECASE,
        ):
            return clean_value(line)

    return None


# --------------------------------------------------
# DATE
# --------------------------------------------------

def extract_date_from_value(value):
    """
    Extract and normalize a date.

    Output is ALWAYS:

        YYYY-MM-DD

    Supported inputs:

        15-08-2026
        15/08/2026
        15.08.2026
        2026-08-15
        2026/08/15
    """

    if not value:
        return None

    value = str(value).strip()

    patterns = [
        (
            r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
            "%d/%m/%Y",
        ),
        (
            r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b",
            "%d.%m.%Y",
        ),
        (
            r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",
            "%Y-%m-%d",
        ),
        (
            r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2})\b",
            "%d/%m/%y",
        ),
    ]

    for pattern, date_format in patterns:

        match = re.search(
            pattern,
            value,
        )

        if not match:
            continue

        raw_date = match.group(0)

        # Normalize separators for parsing.
        if date_format == "%d/%m/%Y":
            raw_date = raw_date.replace("-", "/")

        elif date_format == "%Y-%m-%d":
            raw_date = raw_date.replace("/", "-")

        elif date_format == "%d/%m/%y":
            raw_date = raw_date.replace("-", "/")

        try:
            parsed_date = datetime.strptime(
                raw_date,
                date_format,
            )

            return parsed_date.strftime(
                "%Y-%m-%d"
            )

        except ValueError:
            continue

    return None


def extract_date(text):
    """
    Extract the certificate issue date.

    Priority:

    1. Issue Date
    2. Date of Issue
    3. Certificate Date
    4. Date Issued
    5. Generic Date

    Result is always YYYY-MM-DD.
    """

    lines = get_lines(text)

    date_labels = [
        "Issue Date",
        "Date of Issue",
        "Certificate Date",
        "Date Issued",
    ]

    # Explicit label
    value = extract_labeled_field(
        text,
        date_labels,
    )

    date = extract_date_from_value(value)

    if date:
        return date

    # Label followed by value
    value = extract_value_after_label(
        text,
        date_labels,
    )

    date = extract_date_from_value(value)

    if date:
        return date

    # Generic Date:
    for index, line in enumerate(lines):

        if re.match(
            r"^\s*date\s*[:\-]",
            line,
            re.IGNORECASE,
        ):

            date = extract_date_from_value(line)

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

def extract_marks(text):
    """
    Extract marks / percentage.

    Examples:

        Marks: 85%
        Marks: 85
        Percentage: 85%
        Marks
        85%
    """

    labels = [
        "Marks",
        "Mark",
        "Percentage",
        "Percentage Marks",
        "Marks Obtained",
    ]

    value = extract_labeled_field(
        text,
        labels,
    )

    if value:
        return clean_value(value)

    value = extract_value_after_label(
        text,
        labels,
    )

    if value:
        return clean_value(value)

    return None


# --------------------------------------------------
# CGPA / GPA
# --------------------------------------------------

def extract_cgpa(text):
    """
    Extract CGPA / GPA.

    Examples:

        CGPA: 9.2
        GPA: 9.2
    """

    return extract_labeled_field(
        text,
        [
            "CGPA",
            "GPA",
        ],
    ) or extract_value_after_label(
        text,
        [
            "CGPA",
            "GPA",
        ],
    )


# --------------------------------------------------
# BUILD CERTIFICATE STRUCTURE
# --------------------------------------------------

def build_certificate_fields(text):
    """
    Build the structured AVFA certificate record.

    Primary fields match the certificate database schema.
    Compatibility aliases are retained for RapidFuzz.
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

    institution = extract_institution(
        text
    )

    course_name = extract_degree(
        text
    )

    issue_date = extract_date(
        text
    )

    marks = extract_marks(
        text
    )

    cgpa = extract_cgpa(
        text
    )

    return {

        # ------------------------------------------
        # DATABASE-ALIGNED FIELDS
        # ------------------------------------------

        "certificate_number": certificate_number,

        "student_name": student_name,

        "student_roll_no": student_roll_no,

        "institution": institution,

        "course_name": course_name,

        "issue_date": issue_date,

        "marks": marks,

        "cgpa": cgpa,

        # ------------------------------------------
        # COMPATIBILITY ALIASES
        # ------------------------------------------

        "certificate_id": certificate_number,

        "name": student_name,

        "roll_number": student_roll_no,

        "degree_name": course_name,

        "degree": course_name,

        "course": course_name,

        "gpa": cgpa,

        "date": issue_date,
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
    ABC UNIVERSITY

    CERTIFICATE OF ACHIEVEMENT

    This is to certify that
    Avika Srivastava

    Roll Number: 20260001

    Bachelor of Technology in Computer Science

    Certificate Number: CERT-2026-F7BCAB87

    Issue Date: 15-08-2026

    Marks: 85%

    CGPA: 9.2
    """

    result = extract_from_ocr_text(
        sample_text
    )

    print("\n--- EXTRACTED FIELDS ---")

    for field, value in result.items():

        print(
            f"{field}: {value}"
        )
