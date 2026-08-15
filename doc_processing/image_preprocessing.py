"""
Image preprocessing module for document OCR.

Pipeline:
1. Convert the input image to grayscale.
2. Normalize the grayscale image.
3. Apply unsharp masking to sharpen text.
"""

import cv2
import numpy as np


def preprocess_image(input_path: str, output_path: str = "clean_output.jpg") -> np.ndarray:
    """Preprocess a document image and return the processed image."""

    img = cv2.imread(input_path)

    if img is None:
        raise FileNotFoundError(
            f"Could not read image at path: {input_path}"
        )

    # 1. Grayscale Conversion
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Dynamic Range Normalization
    normalized = cv2.normalize(
        gray,
        None,
        alpha=0,
        beta=255,
        norm_type=cv2.NORM_MINMAX
    )

    # 3. Unsharp Masking / Sharpening
    gaussian_3 = cv2.GaussianBlur(
        normalized,
        (0, 0),
        sigmaX=2.0
    )

    sharp_text = cv2.addWeighted(
        normalized,
        1.5,
        gaussian_3,
        -0.5,
        0
    )

    # 4. Save processed image
    cv2.imwrite(output_path, sharp_text)

    return sharp_text


if __name__ == "__main__":

    processed_img = preprocess_image(
        "input_document.jpg",
        "clean_output.jpg"
    )

    print("Preprocessing complete.")