import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// Main App Component
function App() {
  const [currentView, setCurrentView] = useState('home');
  const [session, setSession] = useState(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-500 to-teal-400">
      {currentView === 'home' && (
        <HomePage 
          onCreateSession={(sessionData) => {
            setSession(sessionData);
            setCurrentView(sessionData.session_type === 'text' ? 'textSession' : 'streamSession');
          }}
          onJoinSession={(sessionData) => {
            setSession(sessionData);
            setCurrentView(sessionData.session_type === 'text' ? 'textViewer' : 'streamViewer');
          }}
        />
      )}
      
      {currentView === 'textSession' && (
        <TextSession 
          session={session}
          onBack={() => setCurrentView('home')}
        />
      )}
      
      {currentView === 'textViewer' && (
        <TextViewer 
          session={session}
          onBack={() => setCurrentView('home')}
        />
      )}
      
      {currentView === 'streamSession' && (
        <StreamSession 
          session={session}
          onBack={() => setCurrentView('home')}
        />
      )}
      
      {currentView === 'streamViewer' && (
        <StreamViewer 
          session={session}
          onBack={() => setCurrentView('home')}
        />
      )}
    </div>
  );
}

// Home Page Component
function HomePage({ onCreateSession, onJoinSession }) {
  const [joinCode, setJoinCode] = useState('');
  const [loading, setLoading] = useState(false);

  const createSession = async (sessionType) => {
    setLoading(true);
    try {
      const response = await fetch(`${API}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_type: sessionType })
      });
      const sessionData = await response.json();
      onCreateSession(sessionData);
    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      setLoading(false);
    }
  };

  const joinSession = async () => {
    if (!joinCode.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API}/sessions/${joinCode}`);
      if (response.ok) {
        const sessionData = await response.json();
        onJoinSession(sessionData);
      } else {
        alert('Сесія не знайдена');
      }
    } catch (error) {
      console.error('Failed to join session:', error);
      alert('Помилка підключення');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Обмін в реальному часі</h1>
          <p className="text-gray-600">Оберіть режим або приєднайтеся до сесії</p>
        </div>

        <div className="space-y-4 mb-8">
          <button
            onClick={() => createSession('text')}
            disabled={loading}
            className="w-full bg-gradient-to-r from-green-400 to-blue-500 text-white py-4 rounded-xl font-semibold text-lg hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200 disabled:opacity-50"
          >
            📝 Створити текстову трансляцію
          </button>
          
          <button
            onClick={() => createSession('stream')}
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-400 to-pink-500 text-white py-4 rounded-xl font-semibold text-lg hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200 disabled:opacity-50"
          >
            📹 Створити відео трансляцію
          </button>
        </div>

        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">Приєднатися до сесії</h3>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Введіть код сесії"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              className="flex-1 p-3 border-2 border-gray-300 rounded-xl focus:border-blue-500 focus:outline-none"
              maxLength="6"
            />
            <button
              onClick={joinSession}
              disabled={loading || !joinCode.trim()}
              className="px-6 py-3 bg-blue-500 text-white rounded-xl font-semibold hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              Увійти
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Text Session Component (Host)
function TextSession({ session, onBack }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [username, setUsername] = useState('Ведучий');
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Load existing messages
    loadMessages();
    
    // Connect WebSocket
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    const ws = new WebSocket(`${WS_URL}/ws/text/${session.id}`);
    
    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'message') {
        setMessages(prev => [...prev, data.data]);
      }
    };
    
    ws.onclose = () => {
      setWsConnected(false);
      console.log('WebSocket disconnected');
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
    };
    
    wsRef.current = ws;
  };

  const loadMessages = async () => {
    try {
      const response = await fetch(`${API}/sessions/${session.id}/messages`);
      const messagesData = await response.json();
      setMessages(messagesData);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;
    
    try {
      await fetch(`${API}/sessions/${session.id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          message: newMessage
        })
      });
      
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const closeSession = async () => {
    try {
      await fetch(`${API}/sessions/${session.code}`, {
        method: 'DELETE'
      });
      onBack();
    } catch (error) {
      console.error('Failed to close session:', error);
    }
  };

  const copySessionCode = () => {
    navigator.clipboard.writeText(session.code);
    alert('Код скопійовано в буфер обміну');
  };

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-400 to-blue-500 p-6 text-white">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">Текстова трансляция</h2>
            <button
              onClick={onBack}
              className="px-4 py-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 transition-all"
            >
              ← Назад
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="bg-white bg-opacity-20 px-4 py-2 rounded-lg">
              <span className="text-sm">Код сесії:</span>
              <span className="font-bold text-lg ml-2">{session.code}</span>
              <button
                onClick={copySessionCode}
                className="ml-2 text-sm bg-white bg-opacity-20 px-2 py-1 rounded hover:bg-opacity-30"
              >
                Копіювати
              </button>
            </div>
            
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span className="text-sm">{wsConnected ? 'Підключено' : 'Відключено'}</span>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="h-96 overflow-y-auto p-6 bg-gray-50">
          {messages.map((message) => (
            <div key={message.id} className="mb-4">
              <div className="bg-white p-4 rounded-lg shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-semibold text-blue-600">{message.username}</span>
                  <span className="text-xs text-gray-500">
                    {new Date(message.timestamp).toLocaleTimeString('uk-UA')}
                  </span>
                </div>
                <p className="text-gray-800">{message.message}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 border-t">
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              placeholder="Ваше ім'я"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-32 p-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
            />
            <input
              type="text"
              placeholder="Введіть повідомлення..."
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              className="flex-1 p-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
            />
            <button
              onClick={sendMessage}
              disabled={!newMessage.trim()}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg font-semibold hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              Відправити
            </button>
          </div>
          
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">
              Глядачі можуть приєднатися, використовуючи код: <strong>{session.code}</strong>
            </span>
            <button
              onClick={closeSession}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              Закінчити сесію
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Text Viewer Component
function TextViewer({ session, onBack }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [username, setUsername] = useState('');
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Load existing messages
    loadMessages();
    
    // Connect WebSocket
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    const ws = new WebSocket(`${WS_URL}/ws/text/${session.id}`);
    
    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'message') {
        setMessages(prev => [...prev, data.data]);
      }
    };
    
    ws.onclose = () => {
      setWsConnected(false);
      console.log('WebSocket disconnected');
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
    };
    
    wsRef.current = ws;
  };

  const loadMessages = async () => {
    try {
      const response = await fetch(`${API}/sessions/${session.id}/messages`);
      const messagesData = await response.json();
      setMessages(messagesData);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !username.trim()) return;
    
    try {
      await fetch(`${API}/sessions/${session.id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          message: newMessage
        })
      });
      
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-400 to-purple-500 p-6 text-white">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">Перегляд текстової трансляції</h2>
            <button
              onClick={onBack}
              className="px-4 py-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 transition-all"
            >
              ← Назад
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="bg-white bg-opacity-20 px-4 py-2 rounded-lg">
              <span className="text-sm">Сесія:</span>
              <span className="font-bold text-lg ml-2">{session.code}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span className="text-sm">{wsConnected ? 'Підключено' : 'Відключено'}</span>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="h-96 overflow-y-auto p-6 bg-gray-50">
          {messages.map((message) => (
            <div key={message.id} className="mb-4">
              <div className="bg-white p-4 rounded-lg shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-semibold text-purple-600">{message.username}</span>
                  <span className="text-xs text-gray-500">
                    {new Date(message.timestamp).toLocaleTimeString('uk-UA')}
                  </span>
                </div>
                <p className="text-gray-800">{message.message}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 border-t">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Ваше ім'я"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-32 p-2 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none"
            />
            <input
              type="text"
              placeholder="Введіть повідомлення..."
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              className="flex-1 p-2 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none"
            />
            <button
              onClick={sendMessage}
              disabled={!newMessage.trim() || !username.trim()}
              className="px-6 py-2 bg-purple-500 text-white rounded-lg font-semibold hover:bg-purple-600 transition-colors disabled:opacity-50"
            >
              Відправити
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Stream Session Component (Host/Broadcaster)
function StreamSession({ session, onBack }) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamType, setStreamType] = useState('screen'); // 'screen', 'camera', 'both'
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState('');
  const [wsConnected, setWsConnected] = useState(false);
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const wsRef = useRef(null);
  const peerConnections = useRef(new Map());

  useEffect(() => {
    // Get available cameras
    getCameras();
    
    // Connect WebSocket for signaling
    connectWebSocket();
    
    return () => {
      stopStreaming();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const getCameras = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');
      setCameras(videoDevices);
      if (videoDevices.length > 0 && !selectedCamera) {
        setSelectedCamera(videoDevices[0].deviceId);
      }
    } catch (error) {
      console.error('Error getting cameras:', error);
    }
  };

  const connectWebSocket = () => {
    const ws = new WebSocket(`${WS_URL}/ws/stream/${session.id}/broadcaster`);
    
    ws.onopen = () => {
      setWsConnected(true);
      console.log('Stream WebSocket connected');
    };
    
    ws.onmessage = async (event) => {
      const signal = JSON.parse(event.data);
      await handleSignal(signal);
    };
    
    ws.onclose = () => {
      setWsConnected(false);
      console.log('Stream WebSocket disconnected');
    };
    
    ws.onerror = (error) => {
      console.error('Stream WebSocket error:', error);
      setWsConnected(false);
    };
    
    wsRef.current = ws;
  };

  const handleSignal = async (signal) => {
    const { type, viewerId, offer, answer, iceCandidate } = signal;
    
    if (type === 'viewer_joined') {
      await createPeerConnection(viewerId);
    } else if (type === 'answer' && viewerId) {
      const pc = peerConnections.current.get(viewerId);
      if (pc) {
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
      }
    } else if (type === 'ice_candidate' && viewerId) {
      const pc = peerConnections.current.get(viewerId);
      if (pc && iceCandidate) {
        await pc.addIceCandidate(new RTCIceCandidate(iceCandidate));
      }
    }
  };

  const createPeerConnection = async (viewerId) => {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    // Add local stream to peer connection
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        pc.addTrack(track, streamRef.current);
      });
    }

    // Handle ICE candidates
    pc.onicecandidate = (event) => {
      if (event.candidate && wsRef.current) {
        wsRef.current.send(JSON.stringify({
          type: 'ice_candidate',
          viewerId,
          iceCandidate: event.candidate
        }));
      }
    };

    // Create and send offer
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({
        type: 'offer',
        viewerId,
        offer
      }));
    }

    peerConnections.current.set(viewerId, pc);
  };

  const startStreaming = async () => {
    try {
      let mediaStream;

      if (streamType === 'screen') {
        mediaStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true
        });
      } else if (streamType === 'camera') {
        mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { deviceId: selectedCamera ? { exact: selectedCamera } : undefined },
          audio: true
        });
      } else if (streamType === 'both') {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true
        });
        const cameraStream = await navigator.mediaDevices.getUserMedia({
          video: { deviceId: selectedCamera ? { exact: selectedCamera } : undefined }
        });

        // For simplicity, we'll use screen stream as primary
        // In a real implementation, you might want to combine streams
        mediaStream = screenStream;
      }

      streamRef.current = mediaStream;
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }

      setIsStreaming(true);
      
      // Handle stream end (when user stops sharing screen)
      mediaStream.getVideoTracks()[0].addEventListener('ended', () => {
        stopStreaming();
      });

    } catch (error) {
      console.error('Error starting stream:', error);
      alert('Не вдалося почати трансляцію');
    }
  };

  const stopStreaming = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    
    // Close all peer connections
    peerConnections.current.forEach(pc => pc.close());
    peerConnections.current.clear();
    
    setIsStreaming(false);
  };

  const closeSession = async () => {
    try {
      await fetch(`${API}/sessions/${session.code}`, {
        method: 'DELETE'
      });
      onBack();
    } catch (error) {
      console.error('Failed to close session:', error);
    }
  };

  const copySessionCode = () => {
    navigator.clipboard.writeText(session.code);
    alert('Код скопійовано в буфер обміну');
  };

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-400 to-pink-500 p-6 text-white">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">Відео трансляція</h2>
            <button
              onClick={onBack}
              className="px-4 py-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 transition-all"
            >
              ← Назад
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="bg-white bg-opacity-20 px-4 py-2 rounded-lg">
              <span className="text-sm">Код сесії:</span>
              <span className="font-bold text-lg ml-2">{session.code}</span>
              <button
                onClick={copySessionCode}
                className="ml-2 text-sm bg-white bg-opacity-20 px-2 py-1 rounded hover:bg-opacity-30"
              >
                Копіювати
              </button>
            </div>
            
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span className="text-sm">{wsConnected ? 'Підключено' : 'Відключено'}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isStreaming ? 'bg-red-500' : 'bg-gray-400'}`}></div>
              <span className="text-sm">{isStreaming ? 'В ефірі' : 'Не в ефірі'}</span>
            </div>
          </div>
        </div>

        <div className="p-6">
          {/* Controls */}
          {!isStreaming && (
            <div className="mb-6 bg-gray-50 p-6 rounded-xl">
              <h3 className="text-lg font-semibold mb-4">Налаштування трансляції</h3>
              
              <div className="flex gap-4 mb-4">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="streamType"
                    value="screen"
                    checked={streamType === 'screen'}
                    onChange={(e) => setStreamType(e.target.value)}
                  />
                  Тільки екран
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="streamType"
                    value="camera"
                    checked={streamType === 'camera'}
                    onChange={(e) => setStreamType(e.target.value)}
                  />
                  Тільки камера
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="streamType"
                    value="both"
                    checked={streamType === 'both'}
                    onChange={(e) => setStreamType(e.target.value)}
                  />
                  Екран + Камера
                </label>
              </div>

              {(streamType === 'camera' || streamType === 'both') && cameras.length > 0 && (
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">Оберіть камеру:</label>
                  <select
                    value={selectedCamera}
                    onChange={(e) => setSelectedCamera(e.target.value)}
                    className="p-2 border rounded-lg"
                  >
                    {cameras.map(camera => (
                      <option key={camera.deviceId} value={camera.deviceId}>
                        {camera.label || `Камера ${camera.deviceId.slice(0, 10)}`}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              
              <button
                onClick={startStreaming}
                className="px-6 py-3 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-600 transition-colors"
              >
                🔴 Почати трансляцію
              </button>
            </div>
          )}

          {/* Video Preview */}
          <div className="mb-6">
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              className="w-full max-w-4xl mx-auto bg-black rounded-xl"
              style={{ maxHeight: '60vh' }}
            />
            {!isStreaming && (
              <div className="w-full max-w-4xl mx-auto bg-gray-200 rounded-xl flex items-center justify-center text-gray-500 text-lg" style={{ height: '400px' }}>
                Попередній перегляд з'явиться тут
              </div>
            )}
          </div>

          {/* Stream Controls */}
          {isStreaming && (
            <div className="text-center mb-6">
              <button
                onClick={stopStreaming}
                className="px-6 py-3 bg-red-500 text-white rounded-lg font-semibold hover:bg-red-600 transition-colors mr-4"
              >
                ⏹️ Зупинити трансляцію
              </button>
            </div>
          )}

          {/* Session Info */}
          <div className="bg-blue-50 p-4 rounded-xl text-center">
            <p className="text-gray-700">
              Глядачі можуть приєднатися, використовуючи код: <strong className="text-blue-600 text-lg">{session.code}</strong>
            </p>
            <button
              onClick={closeSession}
              className="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              Закінчити сесію
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Stream Viewer Component
function StreamViewer({ session, onBack }) {
  const [wsConnected, setWsConnected] = useState(false);
  const [streamConnected, setStreamConnected] = useState(false);
  
  const videoRef = useRef(null);
  const wsRef = useRef(null);
  const peerConnectionRef = useRef(null);
  const viewerIdRef = useRef(Math.random().toString(36).substr(2, 9));

  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const ws = new WebSocket(`${WS_URL}/ws/stream/${session.id}/viewer`);
    
    ws.onopen = () => {
      setWsConnected(true);
      console.log('Viewer WebSocket connected');
      
      // Signal that viewer joined
      ws.send(JSON.stringify({
        type: 'viewer_joined',
        viewerId: viewerIdRef.current
      }));
      
      // Setup peer connection
      setupPeerConnection();
    };
    
    ws.onmessage = async (event) => {
      const signal = JSON.parse(event.data);
      await handleSignal(signal);
    };
    
    ws.onclose = () => {
      setWsConnected(false);
      setStreamConnected(false);
      console.log('Viewer WebSocket disconnected');
    };
    
    ws.onerror = (error) => {
      console.error('Viewer WebSocket error:', error);
      setWsConnected(false);
    };
    
    wsRef.current = ws;
  };

  const setupPeerConnection = () => {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    // Handle remote stream
    pc.ontrack = (event) => {
      console.log('Received remote stream');
      if (videoRef.current && event.streams[0]) {
        videoRef.current.srcObject = event.streams[0];
        setStreamConnected(true);
      }
    };

    // Handle ICE candidates
    pc.onicecandidate = (event) => {
      if (event.candidate && wsRef.current) {
        wsRef.current.send(JSON.stringify({
          type: 'ice_candidate',
          viewerId: viewerIdRef.current,
          iceCandidate: event.candidate
        }));
      }
    };

    pc.onconnectionstatechange = () => {
      console.log('Connection state:', pc.connectionState);
      if (pc.connectionState === 'disconnected') {
        setStreamConnected(false);
      }
    };

    peerConnectionRef.current = pc;
  };

  const handleSignal = async (signal) => {
    const { type, offer, iceCandidate } = signal;
    const pc = peerConnectionRef.current;

    if (type === 'offer' && pc) {
      await pc.setRemoteDescription(new RTCSessionDescription(offer));
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      
      if (wsRef.current) {
        wsRef.current.send(JSON.stringify({
          type: 'answer',
          viewerId: viewerIdRef.current,
          answer
        }));
      }
    } else if (type === 'ice_candidate' && pc && iceCandidate) {
      await pc.addIceCandidate(new RTCIceCandidate(iceCandidate));
    }
  };

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-pink-400 to-red-500 p-6 text-white">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">Перегляд відео трансляції</h2>
            <button
              onClick={onBack}
              className="px-4 py-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 transition-all"
            >
              ← Назад
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="bg-white bg-opacity-20 px-4 py-2 rounded-lg">
              <span className="text-sm">Сесія:</span>
              <span className="font-bold text-lg ml-2">{session.code}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span className="text-sm">WebSocket: {wsConnected ? 'Підключено' : 'Відключено'}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${streamConnected ? 'bg-green-400' : 'bg-yellow-400'}`}></div>
              <span className="text-sm">Трансляція: {streamConnected ? 'Підключено' : 'Очікування...'}</span>
            </div>
          </div>
        </div>

        <div className="p-6">
          {/* Video Stream */}
          <div className="mb-6">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="w-full max-w-4xl mx-auto bg-black rounded-xl"
              style={{ maxHeight: '70vh' }}
            />
            {!streamConnected && (
              <div className="w-full max-w-4xl mx-auto bg-gray-200 rounded-xl flex items-center justify-center text-gray-500 text-lg" style={{ height: '400px' }}>
                {wsConnected ? 'Очікування трансляції...' : 'Підключення...'}
              </div>
            )}
          </div>

          {/* Status Info */}
          <div className="bg-gray-50 p-4 rounded-xl text-center">
            <p className="text-gray-700">
              {streamConnected ? 
                '🔴 Дивитесь трансляцію в реальному часі' : 
                '⏳ Очікуємо початку трансляції від ведучого'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;