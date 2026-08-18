"""
Extract certificate verification ID from a QR code.
"""

from pathlib import Path

import cv2


def extract_qr_data(image_path: str) -> str:
    """
    Read QR code data from an image.

    Returns:
        QR code content as a string.
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {image_path}"
        )

    image = cv2.imread(str(path))

    if image is None:
        raise ValueError(
            f"Could not read image: {image_path}"
        )

    detector = cv2.QRCodeDetector()

    data, points, _ = detector.detectAndDecode(image)

    if data:
        return data.strip()

    raise ValueError(
        "No readable QR code found in the image."
    )


if __name__ == "__main__":

    sample_image = "sample_certificate_qr.png"

    try:
        certificate_id = extract_qr_data(
            sample_image
        )

        print("\n--- QR EXTRACTION ---")
        print(f"Image: {sample_image}")
        print(f"QR Data: {certificate_id}")

    except (
        FileNotFoundError,
        ValueError,
        OSError
    ) as error:

        print(
            f"Could not extract QR: {error}"
        )