
"""
Certificate Field Extractor

Converts EasyOCR output into structured certificate fields.

The extractor supports:
1. Label-based certificates
   Example: Name: Rahul Kumar

2. Layout-based certificates
   Example:
       This is to certify that
       BHUMIKA THAKUR

       Roll No.
       17245572

       School
       CONVENT OF JESUS AND MARY

The output structure is aligned with the AVFA
certificate database fields.
"""

import re


# --------------------------------------------------
# OCR RESULTS → TEXT
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
                re.IGNORECASE
            )

            if match:
                return clean_value(match.group(1))

    return None


def extract_value_after_label(text, labels):
    """
    Extract a value that appears on the line immediately
    after a label.

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
                re.IGNORECASE
            ):

                # First check if the value is on
                # the same line.
                same_line = re.search(
                    rf"{re.escape(label)}"
                    rf"\s*[:\-]?\s+(.+)$",
                    line,
                    re.IGNORECASE
                )

                if same_line:

                    value = clean_value(
                        same_line.group(1)
                    )

                    if value:
                        return value

                # Otherwise check the next line.
                if index + 1 < len(lines):

                    next_line = clean_value(
                        lines[index + 1]
                    )

                    if next_line:

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

    Important:
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
        re.IGNORECASE
    )

    if match:
        return clean_value(match.group(1))

    return None


# --------------------------------------------------
# NAME
# --------------------------------------------------

def extract_name(text):
    """
    Extract student/candidate name.

    Supports:

        Name: Rahul Kumar

    and CBSE-style layout:

        This is to certify that
        BHUMIKA THAKUR
    """

    # Normal labelled format
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

    lines = get_lines(text)

    # CBSE-style certificate:
    # "This is to certify that"
    # followed by student name.
    for index, line in enumerate(lines):

        if re.search(
            r"this\s+is\s+to\s+certif",
            line,
            re.IGNORECASE
        ):

            if index + 1 < len(lines):

                candidate = clean_value(
                    lines[index + 1]
                )

                if candidate:

                    # Avoid obvious labels.
                    if not re.search(
                        r"roll|mother|father|date|school",
                        candidate,
                        re.IGNORECASE
                    ):
                        return candidate

    return None


# --------------------------------------------------
# ROLL NUMBER
# --------------------------------------------------

def extract_roll_number(text):
    """
    Extract student roll / registration number.

    Examples:

        Roll Number: 17245572
        Roll No. 17245572
        Registration No: ABC123
    """

    value = extract_labeled_field(
        text,
        [
            "Roll Number",
            "Roll No",
            "Roll No.",
            "Registration Number",
            "Registration No",
            "Registration No.",
            "Enrollment Number",
            "Enrollment No",
            "Enrollment No.",
        ],
    )

    if value:
        return value

    value = extract_value_after_label(
        text,
        [
            "Roll Number",
            "Roll No",
            "Roll No.",
            "Registration Number",
            "Registration No",
            "Registration No.",
            "Enrollment Number",
            "Enrollment No",
            "Enrollment No.",
        ],
    )

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

    and layout:

        ABC UNIVERSITY
        School
    """

    value = extract_labeled_field(
        text,
        [
            "Institution",
            "University",
            "College",
            "Institute",
        ],
    )

    if value:
        return value

    lines = get_lines(text)

    # Look for a line immediately before:
    # School / College / University / Institute
    institution_words = (
        "school",
        "college",
        "university",
        "institute",
    )

    for index, line in enumerate(lines):

        if line.lower().strip() in institution_words:

            if index > 0:

                candidate = clean_value(
                    lines[index - 1]
                )

                if candidate:

                    # Ignore generic headings.
                    if not re.search(
                        r"marks|certificate|examination|subject",
                        candidate,
                        re.IGNORECASE
                    ):
                        return candidate

    return None


# --------------------------------------------------
# DEGREE / COURSE
# --------------------------------------------------

def extract_degree(text):
    """
    Extract degree/course/program.

    Supports:

        Degree: Bachelor of Technology
        Course: Computer Science

    Also supports examination-style certificates:

        SECONDARY SCHOOL EXAMINATION, 2020
    """

    value = extract_labeled_field(
        text,
        [
            "Degree",
            "Course",
            "Program",
            "Programme",
            "Course Name",
        ],
    )

    if value:
        return value

    lines = get_lines(text)

    # Search for common academic examination names.
    for line in lines:

        if re.search(
            r"(secondary school examination|"
            r"senior school certificate examination|"
            r"higher secondary|"
            r"bachelor|master|diploma|"
            r"b\.?tech|b\.?e\.?|m\.?tech|"
            r"b\.?sc|m\.?sc|b\.?com|m\.?com)",
            line,
            re.IGNORECASE
        ):

            return clean_value(line)

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
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            value
        )

        if match:
            return match.group(0)

    return None


def extract_date(text):
    """
    Extract an explicitly labelled issue date.

    Important:
        Do NOT blindly take the first date in the document.

    This prevents a student's Date of Birth from
    accidentally becoming the certificate issue date.
    """

    lines = get_lines(text)

    date_labels = [
        "Issue Date",
        "Date of Issue",
        "Certificate Date",
        "Date Issued",
    ]

    # First look for explicitly labelled issue date.
    value = extract_labeled_field(
        text,
        date_labels,
    )

    date = extract_date_from_value(value)

    if date:
        return date

    # Check value on the next line.
    value = extract_value_after_label(
        text,
        date_labels,
    )

    date = extract_date_from_value(value)

    if date:
        return date

    # Finally look for a generic "Date:" label.
    for index, line in enumerate(lines):

        if re.match(
            r"^\s*date\s*[:\-]",
            line,
            re.IGNORECASE
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

    # Do NOT return an arbitrary date from the document.
    return None


# --------------------------------------------------
# GPA / PERCENTAGE
# --------------------------------------------------

def extract_gpa(text):
    """
    Extract GPA / CGPA / percentage when explicitly labelled.
    """

    return extract_labeled_field(
        text,
        [
            "CGPA",
            "GPA",
            "Percentage",
        ],
    )


# --------------------------------------------------
# BUILD CERTIFICATE STRUCTURE
# --------------------------------------------------

def build_certificate_fields(text):
    """
    Build the structured AVFA certificate record.

    Field names are aligned with the database:

        certificate_number
        student_name
        student_roll_no
        degree_name
        issue_date

    Compatibility aliases are also returned for
    the current RapidFuzz prototype.
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

    gpa = extract_gpa(
        text
    )

    return {

        # ------------------------------------------
        # Database-aligned fields
        # ------------------------------------------

        "certificate_number": certificate_number,

        "student_name": student_name,

        "student_roll_no": student_roll_no,

        "degree_name": degree_name,

        "issue_date": issue_date,

        "institution": institution,

        "gpa": gpa,

        # ------------------------------------------
        # Compatibility fields
        # ------------------------------------------

        "certificate_id": certificate_number,

        "name": student_name,

        "roll_number": student_roll_no,

        "degree": degree_name,

        "course": degree_name,

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
    Certificate of Achievement

    Name: Rahul Kumar

    Institution: ABC University

    Course: Bachelor of Technology

    Certificate ID: CERT-2026-00125

    Roll No: 123456

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
