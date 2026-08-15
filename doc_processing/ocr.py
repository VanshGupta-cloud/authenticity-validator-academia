"""
OCR module using EasyOCR.

The preprocessed image is passed to EasyOCR,
which returns bounding boxes, detected text
and confidence scores.
"""

import easyocr


def extract_text(image) -> list:
    """Run EasyOCR on a preprocessed image."""

    reader = easyocr.Reader(["en"])

    results = reader.readtext(image)

    return results


def print_results(results: list) -> None:
    """Print OCR results in a readable format."""

    print("\n--- EXTRACTED TEXT ---")

    for result in results:

        # EasyOCR result format:
        # [bounding_box, detected_text, confidence]

        text = result[1]
        confidence = result[2]

        print(
            f"Text: {text} | "
            f"Confidence: {confidence:.2f}"
        )


if __name__ == "__main__":

    import cv2

    image_path = "clean_output.jpg"

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not read image at path: {image_path}"
        )

    reader = easyocr.Reader(["en"])

    results = reader.readtext(image)

    print_results(results)