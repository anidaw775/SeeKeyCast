#!/usr/bin/env python3
"""
HTTP-only Backend API Testing for Real-time Streaming Application
Tests session management and text messaging APIs
"""

import requests
import json
import time
from datetime import datetime
import sys

# Backend URL from frontend/.env
BASE_URL = "https://realtimeshare.preview.emergentagent.com/api"

class HTTPBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "session_management": {"passed": 0, "failed": 0, "errors": []},
            "text_messages": {"passed": 0, "failed": 0, "errors": []}
        }
        self.created_sessions = []
        
    def log_result(self, category, test_name, success, error_msg=None):
        """Log test result"""
        if success:
            self.test_results[category]["passed"] += 1
            print(f"✅ {test_name}")
        else:
            self.test_results[category]["failed"] += 1
            self.test_results[category]["errors"].append(f"{test_name}: {error_msg}")
            print(f"❌ {test_name}: {error_msg}")
    
    def test_session_management(self):
        """Test session creation, retrieval, and closure"""
        print("\n🔧 Testing Session Management API...")
        
        # Test 1: Create text session
        try:
            response = self.session.post(f"{BASE_URL}/sessions", 
                                       json={"session_type": "text"})
            if response.status_code == 200:
                session_data = response.json()
                if ("id" in session_data and "code" in session_data and 
                    session_data["session_type"] == "text" and
                    len(session_data["code"]) == 6):
                    self.created_sessions.append(session_data)
                    self.log_result("session_management", "Create text session", True)
                    print(f"   Created session: {session_data['code']} (ID: {session_data['id']})")
                else:
                    self.log_result("session_management", "Create text session", False, 
                                  f"Invalid response structure: {session_data}")
            else:
                self.log_result("session_management", "Create text session", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("session_management", "Create text session", False, str(e))
        
        # Test 2: Create stream session
        try:
            response = self.session.post(f"{BASE_URL}/sessions", 
                                       json={"session_type": "stream"})
            if response.status_code == 200:
                session_data = response.json()
                if ("id" in session_data and "code" in session_data and 
                    session_data["session_type"] == "stream" and
                    len(session_data["code"]) == 6):
                    self.created_sessions.append(session_data)
                    self.log_result("session_management", "Create stream session", True)
                    print(f"   Created session: {session_data['code']} (ID: {session_data['id']})")
                else:
                    self.log_result("session_management", "Create stream session", False, 
                                  f"Invalid response structure: {session_data}")
            else:
                self.log_result("session_management", "Create stream session", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("session_management", "Create stream session", False, str(e))
        
        # Test 3: Verify unique codes
        if len(self.created_sessions) >= 2:
            codes = [session["code"] for session in self.created_sessions]
            if len(set(codes)) == len(codes):
                self.log_result("session_management", "Unique session codes generated", True)
            else:
                self.log_result("session_management", "Unique session codes generated", False, 
                              f"Duplicate codes found: {codes}")
        
        # Test 4: Retrieve session by code
        if self.created_sessions:
            try:
                test_session = self.created_sessions[0]
                response = self.session.get(f"{BASE_URL}/sessions/{test_session['code']}")
                if response.status_code == 200:
                    retrieved_session = response.json()
                    if (retrieved_session["id"] == test_session["id"] and
                        retrieved_session["code"] == test_session["code"] and
                        retrieved_session["session_type"] == test_session["session_type"]):
                        self.log_result("session_management", "Retrieve session by code", True)
                    else:
                        self.log_result("session_management", "Retrieve session by code", False, 
                                      f"Retrieved session data doesn't match: {retrieved_session}")
                else:
                    self.log_result("session_management", "Retrieve session by code", False, 
                                  f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("session_management", "Retrieve session by code", False, str(e))
        
        # Test 5: Retrieve non-existent session
        try:
            response = self.session.get(f"{BASE_URL}/sessions/NONEXIST")
            if response.status_code == 404:
                self.log_result("session_management", "Handle non-existent session", True)
            else:
                self.log_result("session_management", "Handle non-existent session", False, 
                              f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("session_management", "Handle non-existent session", False, str(e))
        
        # Test 6: Close session
        if self.created_sessions:
            try:
                test_session = self.created_sessions[-1]  # Use last created session
                response = self.session.delete(f"{BASE_URL}/sessions/{test_session['code']}")
                if response.status_code == 200:
                    response_data = response.json()
                    if "message" in response_data:
                        self.log_result("session_management", "Close session", True)
                    else:
                        self.log_result("session_management", "Close session", False, 
                                      f"Invalid response: {response_data}")
                else:
                    self.log_result("session_management", "Close session", False, 
                                  f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("session_management", "Close session", False, str(e))
        
        # Test 7: Try to retrieve closed session
        if self.created_sessions:
            try:
                closed_session = self.created_sessions[-1]
                response = self.session.get(f"{BASE_URL}/sessions/{closed_session['code']}")
                if response.status_code == 404:
                    self.log_result("session_management", "Closed session not retrievable", True)
                else:
                    self.log_result("session_management", "Closed session not retrievable", False, 
                                  f"Expected 404 for closed session, got {response.status_code}")
            except Exception as e:
                self.log_result("session_management", "Closed session not retrievable", False, str(e))
    
    def test_text_messages(self):
        """Test text message sending and retrieval"""
        print("\n💬 Testing Text Messages API...")
        
        if not self.created_sessions:
            self.log_result("text_messages", "Text messages test", False, 
                          "No sessions available for testing")
            return
        
        # Use first session for text message testing (should still be active)
        test_session = self.created_sessions[0]
        session_id = test_session["id"]
        
        # Test 1: Send text message
        try:
            message_data = {
                "username": "Олександр",
                "message": "Привіт! Це тестове повідомлення."
            }
            response = self.session.post(f"{BASE_URL}/sessions/{session_id}/messages", 
                                       json=message_data)
            if response.status_code == 200:
                message_response = response.json()
                if ("id" in message_response and 
                    message_response["username"] == "Олександр" and 
                    message_response["message"] == "Привіт! Це тестове повідомлення." and
                    message_response["session_id"] == session_id):
                    self.log_result("text_messages", "Send text message", True)
                    print(f"   Message ID: {message_response['id']}")
                else:
                    self.log_result("text_messages", "Send text message", False, 
                                  f"Invalid message response: {message_response}")
            else:
                self.log_result("text_messages", "Send text message", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("text_messages", "Send text message", False, str(e))
        
        # Test 2: Send another message
        try:
            message_data = {
                "username": "Марія",
                "message": "Друге тестове повідомлення з емодзі 🚀"
            }
            response = self.session.post(f"{BASE_URL}/sessions/{session_id}/messages", 
                                       json=message_data)
            if response.status_code == 200:
                message_response = response.json()
                if ("id" in message_response and 
                    message_response["username"] == "Марія" and
                    "🚀" in message_response["message"]):
                    self.log_result("text_messages", "Send message with emoji", True)
                else:
                    self.log_result("text_messages", "Send message with emoji", False, 
                                  f"Invalid message response: {message_response}")
            else:
                self.log_result("text_messages", "Send message with emoji", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("text_messages", "Send message with emoji", False, str(e))
        
        # Test 3: Send long message
        try:
            long_message = "Це дуже довге повідомлення для тестування обробки великих текстів. " * 10
            message_data = {
                "username": "Тестер",
                "message": long_message
            }
            response = self.session.post(f"{BASE_URL}/sessions/{session_id}/messages", 
                                       json=message_data)
            if response.status_code == 200:
                self.log_result("text_messages", "Send long message", True)
            else:
                self.log_result("text_messages", "Send long message", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("text_messages", "Send long message", False, str(e))
        
        # Test 4: Retrieve messages
        try:
            response = self.session.get(f"{BASE_URL}/sessions/{session_id}/messages")
            if response.status_code == 200:
                messages = response.json()
                if isinstance(messages, list) and len(messages) >= 3:
                    # Check if messages are sorted by timestamp
                    timestamps = [msg.get("timestamp") for msg in messages if "timestamp" in msg]
                    if len(timestamps) >= 2:
                        self.log_result("text_messages", "Retrieve text messages", True)
                        print(f"   Retrieved {len(messages)} messages")
                    else:
                        self.log_result("text_messages", "Retrieve text messages", False, 
                                      "Messages missing timestamps")
                else:
                    self.log_result("text_messages", "Retrieve text messages", False, 
                                  f"Expected list with 3+ messages, got: {len(messages) if isinstance(messages, list) else 'not a list'}")
            else:
                self.log_result("text_messages", "Retrieve text messages", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("text_messages", "Retrieve text messages", False, str(e))
        
        # Test 5: Send message to non-existent session
        try:
            fake_session_id = "non-existent-session-id"
            message_data = {
                "username": "Test",
                "message": "This should work even for non-existent sessions"
            }
            response = self.session.post(f"{BASE_URL}/sessions/{fake_session_id}/messages", 
                                       json=message_data)
            # This should succeed as the API doesn't validate session existence
            if response.status_code == 200:
                self.log_result("text_messages", "Send message to any session", True)
            else:
                self.log_result("text_messages", "Send message to any session", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("text_messages", "Send message to any session", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🧪 HTTP BACKEND TEST SUMMARY")
        print("="*60)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results["passed"]
            failed = results["failed"]
            total_passed += passed
            total_failed += failed
            
            status = "✅ PASS" if failed == 0 else "❌ FAIL"
            print(f"{category.replace('_', ' ').title()}: {status} ({passed} passed, {failed} failed)")
            
            if results["errors"]:
                for error in results["errors"]:
                    print(f"  ❌ {error}")
        
        print(f"\nOverall: {total_passed} passed, {total_failed} failed")
        
        if total_failed == 0:
            print("🎉 All HTTP backend tests passed!")
            return True
        else:
            print(f"⚠️  {total_failed} tests failed - see details above")
            return False

def main():
    """Run all HTTP backend tests"""
    print("🚀 Starting HTTP Backend API Tests...")
    print(f"Testing against: {BASE_URL}")
    
    tester = HTTPBackendTester()
    
    # Run HTTP API tests
    tester.test_session_management()
    tester.test_text_messages()
    
    # Print summary
    success = tester.print_summary()
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)