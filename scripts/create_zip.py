import os
import zipfile
from pathlib import Path

# Dynamic workspace base directory
BASE_DIR = Path(__file__).resolve().parent
ZIP_OUTPUT = BASE_DIR / "avfa-frontend-complete.zip"

INCLUDE_DIRS = ["static", "frontend", "src", "docs", "qr", "doc_processing", "hashing", "PDF"]
INCLUDE_FILES = [
    "test_e2e.py",
    "test_workflow.py",
    "test_verify_doc.py",
    "institution_private_key.pem",
    "institution_public_key.pem",
    "requirements.txt"
]

def create_zip():
    print(f"Creating ZIP archive at {ZIP_OUTPUT}...")
    with zipfile.ZipFile(ZIP_OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add directories
        for d in INCLUDE_DIRS:
            dir_path = BASE_DIR / d
            if dir_path.exists():
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith((".pyc", ".db", ".sqlite")):
                            continue
                        full_path = Path(root) / file
                        arcname = full_path.relative_to(BASE_DIR)
                        zipf.write(full_path, arcname)
                        print(f"  Added: {arcname}")

        # Add root files
        for f in INCLUDE_FILES:
            file_path = BASE_DIR / f
            if file_path.exists():
                zipf.write(file_path, f)
                print(f"  Added: {f}")

        # Add README
        readme_content = """# Authenticity Validator for Academia (AVFA) - Complete Suite (SIH25029)

## How to Run Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the local server:
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```

3. Open in browser:
   http://localhost:8000
"""
        zipf.writestr("README.md", readme_content)
        print("  Added: README.md")

    size_mb = os.path.getsize(ZIP_OUTPUT) / (1024 * 1024)
    print(f"\n[SUCCESS] ZIP created successfully! Size: {size_mb:.2f} MB")

if __name__ == "__main__":
    create_zip()
