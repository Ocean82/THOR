import requests
import json

# Base URL
base_url = "http://0.0.0.0:5000"

# Start a session to maintain cookies
session = requests.Session()

# Log in
login_data = {
    "username": "testuser",
    "password": "testpassword"
}

login_response = session.post(f"{base_url}/login", data=login_data)
print(f"Login status: {login_response.status_code}")

# Test code generation
code_gen_data = {
    "description": "A Python function to calculate Fibonacci sequence up to n terms",
    "language": "python"
}
code_gen_response = session.post(f"{base_url}/api/thor/generate-code", json=code_gen_data)
print(f"Code generation status: {code_gen_response.status_code}")
print("Response content:")
try:
    print(json.dumps(code_gen_response.json(), indent=2))
except:
    print(code_gen_response.text)