"""
Certificate PDF Generator

Generates a certificate PDF from the AVFA certificate schema.

The certificate number is supplied by the certificate issuance system.
The PDF generator does not generate certificate numbers.

QR generation, SHA-256 hashing, digital signatures, and database
storage are handled by separate modules.
"""

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


@dataclass
class Certificate:
    """Represents the AVFA certificate database schema."""

    id: UUID
    certificate_number: str

    institution_id: UUID
    issuer_id: UUID

    student_name: str
    student_roll_no: str
    course_name: str
    issue_date: date

    marks: Optional[str] = None
    cgpa: Optional[str] = None

    sha256_hash: str = ""
    digital_signature: str = ""

    batch_id: Optional[UUID] = None

    qr_code_url: Optional[str] = None
    pdf_url: Optional[str] = None

    status: str = "ISSUED"

    revocation_reason: Optional[str] = None
    revoked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


def generate_certificate_pdf(
    certificate: Certificate,
    output_path: str,
    institution_name: str,
) -> str:
    """
    Generate a certificate PDF.

    The certificate_number must come from the actual issuance
    system, e.g. CERT-2026-F7BCAB87.

    Parameters
    ----------
    certificate:
        Certificate data.

    output_path:
        Path where the PDF will be saved.

    institution_name:
        Institution name displayed on the certificate.

    Returns
    -------
    str
        Path of the generated PDF.
    """

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    if certificate.status != "ISSUED":
        raise ValueError(
            f"Cannot generate PDF for certificate with status "
            f"'{certificate.status}'."
        )

    if not certificate.certificate_number:
        raise ValueError(
            "Certificate number cannot be empty."
        )

    # ---------------------------------------------------------
    # OUTPUT PATH
    # ---------------------------------------------------------

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # PDF DOCUMENT
    # ---------------------------------------------------------

    document = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=25 * mm,
        leftMargin=25 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # ---------------------------------------------------------
    # STYLES
    # ---------------------------------------------------------

    institution_style = ParagraphStyle(
        "Institution",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=15,
    )

    title_style = ParagraphStyle(
        "CertificateTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=24,
        leading=30,
        spaceAfter=15,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=13,
        leading=18,
        spaceAfter=12,
    )

    student_style = ParagraphStyle(
        "StudentName",
        parent=styles["Heading2"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=28,
        spaceBefore=8,
        spaceAfter=8,
    )

    normal_center = ParagraphStyle(
        "NormalCenter",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=12,
        leading=18,
    )

    course_style = ParagraphStyle(
        "Course",
        parent=normal_center,
        fontSize=16,
        leading=20,
        spaceBefore=8,
        spaceAfter=15,
    )

    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=11,
        leading=15,
    )

    footer_style = ParagraphStyle(
        "Footer",
        parent=normal_center,
        fontSize=8,
        leading=11,
    )

    # ---------------------------------------------------------
    # CERTIFICATE CONTENT
    # ---------------------------------------------------------

    story = []

    story.append(
        Paragraph(
            institution_name.upper(),
            institution_style,
        )
    )

    story.append(
        Paragraph(
            "CERTIFICATE OF ACHIEVEMENT",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "This is to certify that",
            subtitle_style,
        )
    )

    story.append(
        Paragraph(
            certificate.student_name.upper(),
            student_style,
        )
    )

    story.append(
        Paragraph(
            f"Roll Number: "
            f"<b>{certificate.student_roll_no}</b>",
            normal_center,
        )
    )

    story.append(
        Spacer(1, 10 * mm)
    )

    story.append(
        Paragraph(
            "has successfully completed the course",
            normal_center,
        )
    )

    story.append(
        Paragraph(
            f"<b>{certificate.course_name}</b>",
            course_style,
        )
    )

    # ---------------------------------------------------------
    # CERTIFICATE DETAILS
    # ---------------------------------------------------------

    details = [
        [
            Paragraph(
                "<b>Certificate Number</b>",
                label_style,
            ),
            certificate.certificate_number,
        ],
        [
            Paragraph(
                "<b>Issue Date</b>",
                label_style,
            ),
            certificate.issue_date.strftime("%d-%m-%Y"),
        ],
    ]

    if certificate.marks is not None:
        details.append(
            [
                Paragraph(
                    "<b>Marks</b>",
                    label_style,
                ),
                str(certificate.marks),
            ]
        )

    if certificate.cgpa is not None:
        details.append(
            [
                Paragraph(
                    "<b>CGPA</b>",
                    label_style,
                ),
                str(certificate.cgpa),
            ]
        )

    details_table = Table(
        details,
        colWidths=[
            60 * mm,
            80 * mm,
        ],
        hAlign="CENTER",
    )

    details_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    colors.black,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(details_table)

    story.append(
        Spacer(1, 20 * mm)
    )

    # ---------------------------------------------------------
    # SIGNATURE AREA
    # ---------------------------------------------------------

    signature_table = Table(
        [
            [
                "________________________",
                "________________________",
            ],
            [
                "Authorized Signatory",
                "Institution Authority",
            ],
        ],
        colWidths=[
            70 * mm,
            70 * mm,
        ],
        hAlign="CENTER",
    )

    signature_table.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    story.append(signature_table)

    story.append(
        Spacer(1, 12 * mm)
    )

    # ---------------------------------------------------------
    # CERTIFICATE ID
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            f"Certificate ID: "
            f"<b>{certificate.certificate_number}</b>",
            normal_center,
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    # ---------------------------------------------------------
    # FOOTER
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "This certificate is digitally verifiable through "
            "the Authenticity Validator for Academia (AVFA).",
            footer_style,
        )
    )

    # ---------------------------------------------------------
    # BUILD PDF
    # ---------------------------------------------------------

    document.build(story)

    return str(output_file)