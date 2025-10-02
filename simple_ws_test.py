#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_simple_ws():
    # Test with a session that should exist
    session_id = "test-session-123"
    ws_url = f"wss://realtimeshare.preview.emergentagent.com/ws/text/{session_id}"
    
    print(f"Testing WebSocket connection to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url, timeout=10) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send ping
            ping_msg = {"type": "ping"}
            await websocket.send(json.dumps(ping_msg))
            print("📤 Sent ping message")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"📥 Received: {response}")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_ws())