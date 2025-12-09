# Detector Project

Autonomous Insurance Claims Processing Agent using Python. 

I have used antigravity(Gemini), Chatgpt for faster development

## How to Use

1. Install requirements:
   1. create virtual environment or venv -> using py -3.13 -m venv venv
   2. activate the virtual environment -> using venv\Scripts\Activate
   3. install -> using pip install -r requirements.txt

3. Run the program:
   **python main.py**

4. Output:
   A file named **output.json** is created in the project root.
   Output Format (JSON)
   {
   "extractedFields": {},
   "missingFields": [],
   "recommendedRoute": "",
   "reasoning": ""
   }

5. Input Files:
   Place .txt or .pdf files in the **data** folder.
   Sample test files included:
   - 5 sample .txt files
   - 1 empty file
   - 1 written sample file

**Short description of each files and their purpose:**
src/extractor.py -> Reads raw text from PDF/TXT claim documents and extracts structured fields.
src/validator.py -> Validates extracted claim data.
src/router.py -> Decides which processing route the claim should follow.
main.py -> Central controller of the entire project.
