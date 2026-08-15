"""
PDF processing module.

Converts PDF pages into OpenCV-compatible images.
"""

from pathlib import Path

import cv2
import pymupdf
import numpy as np


def pdf_to_images(pdf_path: str, dpi: int = 200) -> list:
    """
    Convert all pages of a PDF into OpenCV BGR images.
    """

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {pdf_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {pdf_path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Expected a PDF file: {pdf_path}"
        )

    document = pymupdf.open(str(path))

    images = []

    scale = dpi / 72.0
    matrix = pymupdf.Matrix(scale, scale)

    try:
        for page in document:

            pixmap = page.get_pixmap(
                matrix=matrix,
                alpha=False
            )

            image = np.frombuffer(
                pixmap.samples,
                dtype=np.uint8
            )

            image = image.reshape(
                pixmap.height,
                pixmap.width,
                pixmap.n
            )

            image = cv2.cvtColor(
                image,
                cv2.COLOR_RGB2BGR
            )

            images.append(image)

    finally:
        document.close()

    if not images:
        raise ValueError(
            f"No pages found in PDF: {pdf_path}"
        )

    return images