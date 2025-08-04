"""
Test script to verify API functionality and OpenAI key
"""

import requests
import os
from openai import OpenAI

# Configuration
API_BASE_URL = "https://vigilore-api.onrender.com"
LOCAL_API_URL = "http://localhost:9999"

def test_health_check(base_url):
    """Test if API is running"""
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print(f"✅ API is running at {base_url}")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to API: {e}")
        return False

def test_openai_key():
    """Test if OpenAI key is valid"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        # Make a simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API key works!'"}],
            max_tokens=10
        )
        print(f"✅ OpenAI API key is valid")
        print(f"   Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI API key error: {e}")
        return False

def test_cors_headers(base_url):
    """Test CORS configuration"""
    try:
        response = requests.options(
            f"{base_url}/audits",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        cors_headers = response.headers.get("Access-Control-Allow-Origin")
        if cors_headers:
            print(f"✅ CORS is configured: {cors_headers}")
            return True
        else:
            print("❌ CORS headers not found")
            return False
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== VigilOre API Test Suite ===\n")
    
    # Test local API
    print("1. Testing Local API:")
    local_running = test_health_check(LOCAL_API_URL)
    
    print("\n2. Testing Render Deployment:")
    render_running = test_health_check(API_BASE_URL)
    
    print("\n3. Testing OpenAI Key:")
    test_openai_key()
    
    print("\n4. Testing CORS (for frontend access):")
    if local_running:
        test_cors_headers(LOCAL_API_URL)
    
    print("\n=== API Access Information ===")
    print("\nYour frontend developer can access the API in two ways:")
    print("\n1. Direct API Access (No Auth Required):")
    print("   - The API is public at your Render URL")
    print("   - No API key needed for the endpoints")
    print("   - OpenAI key is set in Render environment variables")
    
    print("\n2. If you want to add API authentication later:")
    print("   - You could add an API_KEY header requirement")
    print("   - Or use JWT tokens for user sessions")
    print("   - But currently, the API is open (which is fine for POC)")