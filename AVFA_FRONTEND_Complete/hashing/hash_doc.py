"""Generate SHA-256 hashes for PDF documents."""

import hashlib
from pathlib import Path


def calculate_hash(file_path: str) -> str:
    """Calculate and return the SHA-256 hash of a file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(4096):
            sha256.update(chunk)

    return sha256.hexdigest()


if __name__ == "__main__":

    sample_pdf = "modified.pdf"

    try:
        document_hash = calculate_hash(
            sample_pdf
        )

        print("\n--- DOCUMENT HASH ---")
        print(f"File: {sample_pdf}")
        print(f"SHA-256: {document_hash}")

    except (
        FileNotFoundError,
        ValueError,
        OSError
    ) as error:

        print(
            f"Could not calculate hash: {error}"
        )