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

# Function to test API endpoints and print results
def test_endpoint(name, endpoint, data, method="POST"):
    print(f"\n--- Testing {name} ---")
    if method == "POST":
        response = session.post(f"{base_url}{endpoint}", json=data)
    else:
        response = session.get(f"{base_url}{endpoint}", params=data)
        
    print(f"Status: {response.status_code}")
    print("Response content:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    return response

# Test basic chat
chat_data = {
    "message": "Tell me about your capabilities"
}
test_endpoint("Basic Chat", "/api/chat", chat_data)

# Test network scan (doesn't use OpenAI)
network_scan_data = {
    "target_description": "Scan local network for open ports"
}
test_endpoint("Network Scan", "/api/thor/network-scan", network_scan_data)

# Test cloning capability
clone_data = {
    "description": "A test clone with networking capabilities"
}
test_endpoint("Create Clone", "/api/thor/create-clone", clone_data)

# Test listing clones
test_endpoint("List Clones", "/api/thor/list-clones", {}, method="GET")

# Test activating a clone
activate_data = {
    "clone_name": "THOR1"
}
test_endpoint("Activate Clone", "/api/thor/activate-clone", activate_data)

# Test self-improvement suggestions
test_endpoint("Self-Improvement", "/api/thor/suggest-improvements", {})