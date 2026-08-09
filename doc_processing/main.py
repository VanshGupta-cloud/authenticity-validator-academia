
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
"""

from pathlib import Path

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
# EXPECTED CERTIFICATE
# --------------------------------------------------
# Temporary trusted certificate record.
#
# In the final SIH system, this data will come
# from the database.
# --------------------------------------------------

EXPECTED_CERTIFICATE = {
    "certificate_id": "17245572",
    "name": "BHUMIKA THAKUR",
    "institution": "43140-CONVENT OF JESUS AND MARY DISTT SHIMLA HP",
    "course": "Secondary School Examination",
    "date": "27/03/2004",
}


def process_certificate(pdf_path: str):
    """
    Process a certificate PDF and compare
    OCR-extracted fields with the trusted
    certificate record.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Certificate PDF not found: {pdf_path}"
        )

    print("\n--- PDF PROCESSING ---")
    print(f"Input PDF: {pdf_path}")

    pages = pdf_to_images(
        str(pdf_path),
        dpi=200
    )

    print(f"Pages found: {len(pages)}")

    all_results = []

    for page_number, page_image in enumerate(
        pages,
        start=1
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
        # PDF PAGE → IMAGE
        # --------------------------------------------------

        success = cv2.imwrite(
            str(raw_image_path),
            page_image
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
            str(clean_image_path)
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
            EXPECTED_CERTIFICATE
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
        # VERIFICATION STATUS
        # --------------------------------------------------

        matched = is_document_match(
            comparison
        )

        if matched:
            status = "VERIFIED"
        else:
            status = "FLAGGED"

        print(
            f"\nDOCUMENT STATUS: {status}"
        )

        # --------------------------------------------------
        # STORE RESULT
        # --------------------------------------------------

        all_results.append({
            "page": page_number,
            "certificate": certificate_data,
            "comparison": comparison,
            "status": status,
        })

    return all_results


def main():

    # Certificate PDF used for testing.
    pdf_path = "modified.pdf"

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
                f"Status: {result['status']}"
            )

            print(
                f"Overall similarity: "
                f"{result['comparison']['overall_score']:.2f}%"
            )

    except (
        FileNotFoundError,
        ValueError,
        OSError
    ) as error:

        print(
            f"\nProcessing failed: {error}"
        )


if __name__ == "__main__":
    main()

