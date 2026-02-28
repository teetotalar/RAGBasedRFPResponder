# main.py

import os
from dotenv import load_dotenv
from src.config_loader import load_config
from src.batch_processor import process_compliance_sheet
from src.proposal_generator import generate_proposal_from_sections
from src.pdf_section_parser import parse_pdf_sections


# -------------------------------
# File picker utility
# -------------------------------

def choose_file(folder_path, extensions):
    """
    Lists files in folder_path matching given extensions.
    Prompts user to select one. Validates input.
    """
    files = [
        f for f in os.listdir(folder_path)
        if any(f.lower().endswith(ext) for ext in extensions)
    ]

    if not files:
        print(f"No supported files found in {folder_path}")
        return None

    print("\nAvailable files:")
    for idx, file in enumerate(files, 1):
        print(f"  {idx}. {file}")

    while True:
        try:
            choice = int(input("Select file number: "))
            if 1 <= choice <= len(files):
                return os.path.join(folder_path, files[choice - 1])
            else:
                print(f"Please enter a number between 1 and {len(files)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


# -------------------------------
# Ensure output folder exists
# -------------------------------

os.makedirs("rfp_outputs", exist_ok=True)


# -------------------------------
# Load config
# -------------------------------

config = load_config()
default_provider = config.get("model_provider", "ollama")

print("=== RFP AI Framework ===")
print(f"Default provider from config: {default_provider}")

choice = input("Select model provider (ollama/gemini) or press Enter to keep default: ").strip().lower()

if choice in ["ollama", "gemini"]:
    provider = choice
else:
    provider = default_provider


# -------------------------------
# Gemini validation
# -------------------------------

if provider == "gemini":
    load_dotenv("config.env")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key:
        print("\n❌ Gemini selected but GEMINI_API_KEY not found in config.env")
        print("Please add GEMINI_API_KEY=your_key_here in config.env\n")
        exit(1)

    import google.generativeai as genai
    genai.configure(api_key=gemini_key)

print(f"\nUsing provider: {provider}\n")


# -------------------------------
# Mode selection
# -------------------------------

mode = input("Mode (excel/pdf): ").strip().lower()


# -------------------------------
# EXCEL MODE
# -------------------------------

if mode == "excel":
    input_file = choose_file("rfp_inputs", [".xlsx"])

    if not input_file:
        exit(1)

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join("rfp_outputs", f"{base_name}_filled.xlsx")
    word_output = os.path.join("rfp_outputs", f"{base_name}_responses.docx")

    process_compliance_sheet(input_file, output_file, word_output, provider)


# -------------------------------
# PDF MODE
# -------------------------------

elif mode == "pdf":
    pdf_file = choose_file("rfp_inputs", [".pdf"])

    if not pdf_file:
        exit(1)

    while True:
        try:
            start_page = int(input("Start page (1-based index): "))
            end_page = int(input("End page (1-based index): "))

            if start_page < 1:
                print("Start page must be at least 1.")
            elif end_page < start_page:
                print("End page must be greater than or equal to start page.")
            else:
                break

        except ValueError:
            print("Invalid input. Please enter a valid page number.")

    sections = parse_pdf_sections(pdf_file, start_page, end_page)

    if not sections:
        print("⚠ No sections detected in the selected page range. Exiting.")
        exit(1)

    base_name = os.path.splitext(os.path.basename(pdf_file))[0]
    output_path = os.path.join("rfp_outputs", f"{base_name}_proposal.docx")

    generate_proposal_from_sections(sections, output_path, provider=provider)


# -------------------------------
# INVALID MODE
# -------------------------------

else:
    print("Invalid mode. Please enter 'excel' or 'pdf'.")