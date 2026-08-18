import os

"""
Main SIH certificate verification pipeline.

PDF
↓
PDF → Image
↓
Image preprocessing
↓
EasyOCR
↓
Certificate field extraction
↓
RapidFuzz comparison
↓
VERIFIED / FLAGGED

Database integration will later replace the
temporary trusted certificate record.
"""

import sys
from pathlib import Path

# Ensure doc_processing directory is on path for direct script execution
_DOC_DIR = str(Path(__file__).resolve().parent)
if _DOC_DIR not in sys.path:
    sys.path.insert(0, _DOC_DIR)


import cv2

from pdf_processor import pdf_to_images
from image_preprocessing import preprocess_image
from ocr import extract_text
from field_extractor import extract_certificate_fields
from document_comparison import (
    compare_certificate,
    is_document_match,
)


# --------------------------------------------------
# TEMPORARY TRUSTED CERTIFICATE
# --------------------------------------------------
#
# This is only for local testing.
#
# Later:
# PostgreSQL → certificate_id → trusted record
#
# The field names here MUST match the
# field_extractor.py output.
# --------------------------------------------------

EXPECTED_CERTIFICATE = {
    "certificate_number": "17245572",
    "student_name": "BHUMIKA THAKUR",
    "student_roll_no": "17245572",
    "degree_name": "SECONDARY SCHOOL EXAMINATION, 2020",
    "issue_date": "27/03/2004",
    "institution": "43140-CONVENT OF JESUS AND MARY DISTT SHIMLA HP",
}


def process_certificate(
    pdf_path: str,
    trusted_certificate: dict | None = None,
):
    """
    Process a certificate PDF and compare the
    extracted certificate fields with trusted data.

    Parameters:
        pdf_path:
            Path to uploaded certificate PDF.

        trusted_certificate:
            Trusted certificate record.

            Currently this comes from the temporary
            local dictionary.

            Later this will come from PostgreSQL.
    """

    pdf_path = Path(pdf_path)

    if trusted_certificate is None:
        trusted_certificate = EXPECTED_CERTIFICATE

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Certificate PDF not found: {pdf_path}"
        )

    print("\n--- PDF PROCESSING ---")
    print(f"Input PDF: {pdf_path}")

    # --------------------------------------------------
    # PDF → IMAGES
    # --------------------------------------------------

    pages = pdf_to_images(
        str(pdf_path),
        dpi=200,
    )

    print(f"Pages found: {len(pages)}")

    all_results = []

    # --------------------------------------------------
    # PROCESS EACH PAGE
    # --------------------------------------------------

    for page_number, page_image in enumerate(
        pages,
        start=1,
    ):

        print(
            f"\n--- PROCESSING PAGE {page_number} ---"
        )

        raw_image_path = (
            pdf_path.parent
            / f"_page_{page_number}.png"
        )

        clean_image_path = (
            pdf_path.parent
            / f"_clean_page_{page_number}.png"
        )

        # --------------------------------------------------
        # SAVE PDF PAGE AS IMAGE
        # --------------------------------------------------

        success = cv2.imwrite(
            str(raw_image_path),
            page_image,
        )

        if not success:
            raise OSError(
                f"Could not save page image: "
                f"{raw_image_path}"
            )

        # --------------------------------------------------
        # IMAGE PREPROCESSING
        # --------------------------------------------------

        clean_image = preprocess_image(
            str(raw_image_path),
            str(clean_image_path),
        )

        # --------------------------------------------------
        # OCR
        # --------------------------------------------------

        ocr_results = extract_text(
            clean_image
        )

        # --------------------------------------------------
        # FIELD EXTRACTION
        # --------------------------------------------------

        certificate_data = (
            extract_certificate_fields(
                ocr_results
            )
        )

        certificate_data["page"] = page_number

        print(
            "\n--- EXTRACTED CERTIFICATE FIELDS ---"
        )

        for field, value in certificate_data.items():
            print(f"{field}: {value}")

        # --------------------------------------------------
        # RAPIDFUZZ COMPARISON
        # --------------------------------------------------

        comparison = compare_certificate(
            certificate_data,
            trusted_certificate,
        )

        print(
            "\n--- RAPIDFUZZ COMPARISON ---"
        )

        for field, score in (
            comparison["field_scores"].items()
        ):
            print(
                f"{field}: {score:.2f}%"
            )

        print(
            f"\nOverall Score: "
            f"{comparison['overall_score']:.2f}%"
        )

        print(
            f"Matched Fields: "
            f"{comparison['matched_fields']}/"
            f"{comparison['total_fields']}"
        )

        # --------------------------------------------------
        # DOCUMENT STATUS
        # --------------------------------------------------

        matched = is_document_match(
            comparison
        )

        status = (
            "VERIFIED"
            if matched
            else "FLAGGED"
        )

        print(
            f"\nDOCUMENT STATUS: {status}"
        )

        # --------------------------------------------------
        # STORE PAGE RESULT
        # --------------------------------------------------

        all_results.append(
            {
                "page": page_number,
                "certificate": certificate_data,
                "comparison": comparison,
                "status": status,
            }
        )

    return all_results


def main():
    """
    Local testing entry point.
    """

    # Test certificate PDF.
    pdf_path = "certificate.pdf" if os.path.exists("certificate.pdf") else str(Path(__file__).parent / "certificate.pdf")

    try:

        results = process_certificate(
            pdf_path
        )

        print(
            "\n===================================="
        )
        print(
            "SIH VERIFICATION COMPLETE"
        )
        print(
            "===================================="
        )

        for result in results:

            print(
                f"\nPage {result['page']}"
            )

            print(
                f"Status: "
                f"{result['status']}"
            )

            print(
                f"Overall similarity: "
                f"{result['comparison']['overall_score']:.2f}%"
            )

    except (
        FileNotFoundError,
        ValueError,
        OSError,
    ) as error:

        print(
            f"\nProcessing failed: {error}"
        )


if __name__ == "__main__":
    main()

