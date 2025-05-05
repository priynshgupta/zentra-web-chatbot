import requests

def test_backend():
    base_url = "http://localhost:4000"  # Use your PORT

    print("Testing backend server...")

    # 1. Check if server is running
    try:
        # Test root endpoint (add a basic GET handler if you don't have one)
        response = requests.get(f"{base_url}")
        print(f"✅ Server is online! Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Server is offline or not reachable!")
        return

    # 2. Test auth endpoint
    try:
        # You may need to adjust this for your specific auth endpoint
        auth_payload = {"email": "priyansh@gmail.com", "password": "password123"}
        auth_response = requests.post(f"{base_url}/api/auth/login", json=auth_payload)
        print(f"Auth endpoint response: {auth_response.status_code}")
    except Exception as e:
        print(f"❌ Error testing auth endpoint: {str(e)}")

    # 3. Test chat endpoint
    try:
        chat_payload = {"message": "Hello from Python test"}
        chat_response = requests.post(f"{base_url}/api/chat", json=chat_payload)
        print(f"Chat endpoint response: {chat_response.status_code}")
        if chat_response.status_code == 200:
            print(f"Response data: {chat_response.json()}")
    except Exception as e:
        print(f"❌ Error testing chat endpoint: {str(e)}")

if __name__ == "__main__":
    test_backend()