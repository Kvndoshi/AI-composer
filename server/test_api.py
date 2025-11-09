"""
Simple test script for the AI Message Composer API
Run this to verify your backend is working correctly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_test(name, passed, details=""):
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"  {details}")
    print()

def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            data.get("status") == "healthy" and
            data.get("neo4j_connected") == True and
            data.get("llm_available") == True
        )
        
        print_test(
            "Health Check",
            passed,
            f"Status: {data.get('status')}, Neo4j: {data.get('neo4j_connected')}, LLM: {data.get('llm_available')}"
        )
        return passed
    except Exception as e:
        print_test("Health Check", False, f"Error: {str(e)}")
        return False

def test_rewrite():
    """Test message rewrite endpoint"""
    print("Testing message rewrite...")
    try:
        payload = {
            "platform": "linkedin",
            "user_input": "hey can we meet tomorrow to discuss the project?",
            "conversation_context": [],
            "recipient": "Test User",
            "tone": "professional"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/rewrite",
            json=payload,
            timeout=10
        )
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            "rewritten_message" in data and
            len(data["rewritten_message"]) > 0 and
            data["rewritten_message"] != payload["user_input"]
        )
        
        details = f"Original: {payload['user_input'][:50]}...\nRewritten: {data.get('rewritten_message', '')[:100]}..."
        print_test("Message Rewrite", passed, details)
        return passed
    except Exception as e:
        print_test("Message Rewrite", False, f"Error: {str(e)}")
        return False

def test_store_conversation():
    """Test conversation storage"""
    print("Testing conversation storage...")
    try:
        payload = {
            "platform": "linkedin",
            "recipient": "Test User",
            "message": "This is a test message for storage",
            "is_outgoing": True,
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{BASE_URL}/api/store-conversation",
            json=payload,
            timeout=5
        )
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            data.get("status") == "success"
        )
        
        print_test("Store Conversation", passed, f"Message: {data.get('message')}")
        return passed
    except Exception as e:
        print_test("Store Conversation", False, f"Error: {str(e)}")
        return False

def test_get_conversation_history():
    """Test retrieving conversation history"""
    print("Testing conversation history retrieval...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/conversation-history/Test%20User",
            params={"platform": "linkedin", "limit": 10},
            timeout=5
        )
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            "recipient" in data and
            "messages" in data and
            isinstance(data["messages"], list)
        )
        
        details = f"Found {len(data.get('messages', []))} messages for {data.get('recipient')}"
        print_test("Get Conversation History", passed, details)
        return passed
    except Exception as e:
        print_test("Get Conversation History", False, f"Error: {str(e)}")
        return False

def test_rewrite_with_context():
    """Test message rewrite with conversation context"""
    print("Testing message rewrite with context...")
    try:
        payload = {
            "platform": "linkedin",
            "user_input": "sounds good, lets do it",
            "conversation_context": [
                {
                    "text": "Would you like to meet tomorrow at 2pm?",
                    "is_outgoing": False,
                    "timestamp": "2024-01-01T10:00:00Z"
                }
            ],
            "recipient": "Test User",
            "tone": "professional"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/rewrite",
            json=payload,
            timeout=10
        )
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            data.get("context_used") == True and
            len(data.get("rewritten_message", "")) > 0
        )
        
        details = f"Context used: {data.get('context_used')}\nRewritten: {data.get('rewritten_message', '')[:100]}..."
        print_test("Rewrite with Context", passed, details)
        return passed
    except Exception as e:
        print_test("Rewrite with Context", False, f"Error: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("AI Message Composer - API Test Suite")
    print("=" * 60)
    print()
    
    # Check if server is reachable
    try:
        requests.get(BASE_URL, timeout=2)
    except:
        print("✗ ERROR: Cannot reach server at", BASE_URL)
        print("  Make sure the server is running: python main.py")
        return
    
    # Run tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Message Rewrite", test_rewrite()))
    results.append(("Store Conversation", test_store_conversation()))
    results.append(("Get History", test_get_conversation_history()))
    results.append(("Rewrite with Context", test_rewrite_with_context()))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

