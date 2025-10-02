#!/usr/bin/env python3
"""
Backend API Testing for Real-time Streaming Application
Tests session management, text messaging, and WebSocket functionality
"""

import requests
import json
import asyncio
import websockets
import time
from datetime import datetime
import sys

# Backend URL from frontend/.env
BASE_URL = "https://realtimeshare.preview.emergentagent.com/api"
WS_BASE_URL = "wss://realtimeshare.preview.emergentagent.com"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "session_management": {"passed": 0, "failed": 0, "errors": []},
            "text_messages": {"passed": 0, "failed": 0, "errors": []},
            "websocket_text": {"passed": 0, "failed": 0, "errors": []},
            "websocket_stream": {"passed": 0, "failed": 0, "errors": []}
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
                if "id" in session_data and "code" in session_data and session_data["session_type"] == "text":
                    self.created_sessions.append(session_data)
                    self.log_result("session_management", "Create text session", True)
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
                if "id" in session_data and "code" in session_data and session_data["session_type"] == "stream":
                    self.created_sessions.append(session_data)
                    self.log_result("session_management", "Create stream session", True)
                else:
                    self.log_result("session_management", "Create stream session", False, 
                                  f"Invalid response structure: {session_data}")
            else:
                self.log_result("session_management", "Create stream session", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("session_management", "Create stream session", False, str(e))
        
        # Test 3: Retrieve session by code
        if self.created_sessions:
            try:
                test_session = self.created_sessions[0]
                response = self.session.get(f"{BASE_URL}/sessions/{test_session['code']}")
                if response.status_code == 200:
                    retrieved_session = response.json()
                    if retrieved_session["id"] == test_session["id"]:
                        self.log_result("session_management", "Retrieve session by code", True)
                    else:
                        self.log_result("session_management", "Retrieve session by code", False, 
                                      "Retrieved session ID doesn't match")
                else:
                    self.log_result("session_management", "Retrieve session by code", False, 
                                  f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("session_management", "Retrieve session by code", False, str(e))
        
        # Test 4: Retrieve non-existent session
        try:
            response = self.session.get(f"{BASE_URL}/sessions/NONEXIST")
            if response.status_code == 404:
                self.log_result("session_management", "Handle non-existent session", True)
            else:
                self.log_result("session_management", "Handle non-existent session", False, 
                              f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("session_management", "Handle non-existent session", False, str(e))
        
        # Test 5: Close session
        if self.created_sessions:
            try:
                test_session = self.created_sessions[-1]  # Use last created session
                response = self.session.delete(f"{BASE_URL}/sessions/{test_session['code']}")
                if response.status_code == 200:
                    self.log_result("session_management", "Close session", True)
                else:
                    self.log_result("session_management", "Close session", False, 
                                  f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("session_management", "Close session", False, str(e))
    
    def test_text_messages(self):
        """Test text message sending and retrieval"""
        print("\n💬 Testing Text Messages API...")
        
        if not self.created_sessions:
            self.log_result("text_messages", "Text messages test", False, 
                          "No sessions available for testing")
            return
        
        # Use first session for text message testing
        test_session = self.created_sessions[0]
        session_id = test_session["id"]
        
        # Test 1: Send text message
        try:
            message_data = {
                "username": "TestUser",
                "message": "Hello from backend test!"
            }
            response = self.session.post(f"{BASE_URL}/sessions/{session_id}/messages", 
                                       json=message_data)
            if response.status_code == 200:
                message_response = response.json()
                if ("id" in message_response and 
                    message_response["username"] == "TestUser" and 
                    message_response["message"] == "Hello from backend test!"):
                    self.log_result("text_messages", "Send text message", True)
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
                "username": "AnotherUser",
                "message": "Second test message"
            }
            response = self.session.post(f"{BASE_URL}/sessions/{session_id}/messages", 
                                       json=message_data)
            if response.status_code == 200:
                self.log_result("text_messages", "Send second text message", True)
            else:
                self.log_result("text_messages", "Send second text message", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("text_messages", "Send second text message", False, str(e))
        
        # Test 3: Retrieve messages
        try:
            response = self.session.get(f"{BASE_URL}/sessions/{session_id}/messages")
            if response.status_code == 200:
                messages = response.json()
                if isinstance(messages, list) and len(messages) >= 2:
                    self.log_result("text_messages", "Retrieve text messages", True)
                else:
                    self.log_result("text_messages", "Retrieve text messages", False, 
                                  f"Expected list with 2+ messages, got: {messages}")
            else:
                self.log_result("text_messages", "Retrieve text messages", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("text_messages", "Retrieve text messages", False, str(e))
    
    async def test_websocket_text(self):
        """Test WebSocket text connections"""
        print("\n🔌 Testing WebSocket Text Connections...")
        
        if not self.created_sessions:
            self.log_result("websocket_text", "WebSocket text test", False, 
                          "No sessions available for testing")
            return
        
        # Use first session for WebSocket testing
        test_session = self.created_sessions[0]
        session_id = test_session["id"]
        ws_url = f"{WS_BASE_URL}/ws/text/{session_id}"
        
        # Test 1: Basic WebSocket connection
        try:
            async with websockets.connect(ws_url, open_timeout=10) as websocket:
                # Send ping message
                ping_message = {"type": "ping"}
                await websocket.send(json.dumps(ping_message))
                
                # Wait for pong response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                if response_data.get("type") == "pong":
                    self.log_result("websocket_text", "WebSocket text connection and ping/pong", True)
                else:
                    self.log_result("websocket_text", "WebSocket text connection and ping/pong", False, 
                                  f"Expected pong, got: {response_data}")
        except Exception as e:
            self.log_result("websocket_text", "WebSocket text connection and ping/pong", False, str(e))
        
        # Test 2: Multiple connections (simulate real-time messaging)
        try:
            async def client_handler(client_id):
                async with websockets.connect(ws_url, open_timeout=10) as websocket:
                    # Keep connection alive for a short time
                    await asyncio.sleep(1)
                    return f"Client {client_id} connected successfully"
            
            # Create multiple concurrent connections
            tasks = [client_handler(i) for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for result in results if isinstance(result, str))
            if success_count == 3:
                self.log_result("websocket_text", "Multiple WebSocket text connections", True)
            else:
                self.log_result("websocket_text", "Multiple WebSocket text connections", False, 
                              f"Only {success_count}/3 connections succeeded")
        except Exception as e:
            self.log_result("websocket_text", "Multiple WebSocket text connections", False, str(e))
    
    async def test_websocket_stream(self):
        """Test WebSocket stream signaling connections"""
        print("\n📺 Testing WebSocket Stream Signaling...")
        
        if len(self.created_sessions) < 2:
            self.log_result("websocket_stream", "WebSocket stream test", False, 
                          "Need at least 2 sessions for stream testing")
            return
        
        # Use second session (should be stream type) for WebSocket testing
        test_session = self.created_sessions[1] if len(self.created_sessions) > 1 else self.created_sessions[0]
        session_id = test_session["id"]
        
        # Test 1: Broadcaster connection
        try:
            broadcaster_url = f"{WS_BASE_URL}/ws/stream/{session_id}/broadcaster"
            async with websockets.connect(broadcaster_url, open_timeout=10) as websocket:
                # Send a test signal
                test_signal = {"type": "offer", "data": "test_offer_data"}
                await websocket.send(json.dumps(test_signal))
                
                # Connection successful if no exception
                self.log_result("websocket_stream", "WebSocket stream broadcaster connection", True)
        except Exception as e:
            self.log_result("websocket_stream", "WebSocket stream broadcaster connection", False, str(e))
        
        # Test 2: Viewer connection
        try:
            viewer_url = f"{WS_BASE_URL}/ws/stream/{session_id}/viewer"
            async with websockets.connect(viewer_url, open_timeout=10) as websocket:
                # Send a test signal
                test_signal = {"type": "answer", "data": "test_answer_data"}
                await websocket.send(json.dumps(test_signal))
                
                # Connection successful if no exception
                self.log_result("websocket_stream", "WebSocket stream viewer connection", True)
        except Exception as e:
            self.log_result("websocket_stream", "WebSocket stream viewer connection", False, str(e))
        
        # Test 3: Signal forwarding between broadcaster and viewer
        try:
            broadcaster_url = f"{WS_BASE_URL}/ws/stream/{session_id}/broadcaster"
            viewer_url = f"{WS_BASE_URL}/ws/stream/{session_id}/viewer"
            
            async def broadcaster_client():
                async with websockets.connect(broadcaster_url) as websocket:
                    # Send signal from broadcaster
                    signal = {"type": "offer", "data": "broadcaster_signal"}
                    await websocket.send(json.dumps(signal))
                    await asyncio.sleep(2)  # Keep connection alive
            
            async def viewer_client():
                async with websockets.connect(viewer_url) as websocket:
                    try:
                        # Wait for signal from broadcaster
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        signal_data = json.loads(response)
                        return signal_data.get("type") == "offer"
                    except asyncio.TimeoutError:
                        return False
            
            # Run both clients concurrently
            broadcaster_task = asyncio.create_task(broadcaster_client())
            viewer_task = asyncio.create_task(viewer_client())
            
            # Wait for viewer to receive signal
            signal_received = await viewer_task
            await broadcaster_task
            
            if signal_received:
                self.log_result("websocket_stream", "WebSocket stream signal forwarding", True)
            else:
                self.log_result("websocket_stream", "WebSocket stream signal forwarding", False, 
                              "Viewer did not receive broadcaster signal")
        except Exception as e:
            self.log_result("websocket_stream", "WebSocket stream signal forwarding", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🧪 BACKEND TEST SUMMARY")
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
            print("🎉 All backend tests passed!")
            return True
        else:
            print(f"⚠️  {total_failed} tests failed - see details above")
            return False

async def main():
    """Run all backend tests"""
    print("🚀 Starting Backend API Tests...")
    print(f"Testing against: {BASE_URL}")
    print(f"WebSocket URL: {WS_BASE_URL}")
    
    tester = BackendTester()
    
    # Run HTTP API tests
    tester.test_session_management()
    tester.test_text_messages()
    
    # Run WebSocket tests
    await tester.test_websocket_text()
    await tester.test_websocket_stream()
    
    # Print summary
    success = tester.print_summary()
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)