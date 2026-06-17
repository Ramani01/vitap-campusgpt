from pypdf import PdfReader
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pdf_folder = os.path.join(BASE_DIR, "data", "pdfs")
output_folder = os.path.join(BASE_DIR, "extracted")

os.makedirs(output_folder, exist_ok=True)

print("Starting extraction...")
for file in os.listdir(pdf_folder):
    if file.endswith(".pdf"):
        print(f"Extracting {file}...")
        try:
            reader = PdfReader(os.path.join(pdf_folder, file))
            text = ""
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    text += f"[Empty Page {idx + 1}]\n"

            output_file = os.path.join(
                output_folder,
                file.replace(".pdf", ".txt")
            )

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"Error extracting {file}: {e}")

print("Extraction Complete")
