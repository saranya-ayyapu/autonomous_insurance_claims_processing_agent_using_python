import os
import json
import glob
from src.extractor import extract_fields
from src.validator import validate_fields
from src.router import determine_route
import pypdf

def read_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        try:
            reader = pypdf.PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return ""
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def process_claim(file_path):
    text = read_text(file_path)
    if not text:
        return {
            "file": os.path.basename(file_path),
            "error": "Could not extract text"
        }
    
    extracted_data = extract_fields(text)
    missing_fields = validate_fields(extracted_data)
    route, reasoning = determine_route(extracted_data, missing_fields)
    
    result = {
        "file": os.path.basename(file_path),
        "extractedFields": extracted_data,
        "missingFields": missing_fields,
        "recommendedRoute": route,
        "reasoning": reasoning
    }
    
    return result

def main():
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    files = glob.glob(os.path.join(data_dir, '*.txt')) + glob.glob(os.path.join(data_dir, '*.pdf'))
    
    all_results = []
    
    print(f"Processing {len(files)} documents in {data_dir}...\n")
    
    for file_path in files:
        result = process_claim(file_path)
        all_results.append(result)
        print(json.dumps(result, indent=2))
        print("-" * 40)

    output_path = os.path.join(os.path.dirname(__file__), "output.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n✔ output.json created at: {output_path}\n")


if __name__ == "__main__":
    main()
