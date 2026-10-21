
import requests
import json
import os
import time

# Create dummy extracted text file
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

dummy_filename = "test_resume_debug.pdf"
txt_path = os.path.join(UPLOAD_DIR, f"{dummy_filename}.txt")
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("Candidate Name: John Doe\nSkills: Python, FastAPI, JavaScript, React\nExperience: 5 years of full stack development.")

print(f"Created dummy text at {txt_path}")

# Hit the endpoint
url = "http://localhost:19440/api/v1/analyze-resume"
headers = {"Content-Type": "application/json"}
data = {"filename": dummy_filename}

print("Sending request to backend...")
try:
    response = requests.post(url, json=data, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
