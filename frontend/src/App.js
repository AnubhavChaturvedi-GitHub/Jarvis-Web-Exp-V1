import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Voice Wave Animation Component
const VoiceWave = ({ isListening, isProcessing }) => {
  return (
    <div className="voice-wave-container">
      <div className={`voice-wave ${isListening ? 'listening' : ''} ${isProcessing ? 'processing' : ''}`}>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
      </div>
    </div>
  );
};

// Main Jarvis Component
const JarvisAssistant = () => {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [commandHistory, setCommandHistory] = useState([]);
  const [error, setError] = useState('');
  
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  // Initialize Speech Recognition and Synthesis
  useEffect(() => {
    // Check if browser supports Speech Recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onstart = () => {
        setIsListening(true);
        setError('');
        setTranscript('');
      };

      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        setTranscript(finalTranscript || interimTranscript);

        if (finalTranscript) {
          processCommand(finalTranscript);
        }
      };

      recognitionRef.current.onerror = (event) => {
        setError(`Speech recognition error: ${event.error}`);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    } else {
      setError('Speech recognition not supported in this browser');
    }

    // Initialize Speech Synthesis
    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  // Process voice command
  const processCommand = async (command) => {
    setIsProcessing(true);
    try {
      const response = await axios.post(`${API}/process-command`, {
        command: command,
        timestamp: new Date().toISOString()
      });

      const result = response.data;
      setResponse(result.response);

      // Speak the response using StreamElements API
      await speakResponse(result.response);

      // Handle actions
      if (result.action === 'open_url' && result.url) {
        window.open(result.url, '_blank');
      }

      // Update command history
      setCommandHistory(prev => [{
        command,
        response: result.response,
        timestamp: new Date()
      }, ...prev.slice(0, 9)]);

    } catch (error) {
      console.error('Error processing command:', error);
      const errorMsg = 'Sorry sir, I encountered an error processing your request.';
      setResponse(errorMsg);
      await speakResponse(errorMsg);
    } finally {
      setIsProcessing(false);
    }
  };

  // Text-to-Speech using StreamElements API
  const speakResponse = async (text) => {
    try {
      const audioUrl = `https://api.streamelements.com/kappa/v2/speech?voice=Brian&text=${encodeURIComponent(text)}`;
      const audio = new Audio(audioUrl);
      
      return new Promise((resolve) => {
        audio.onended = resolve;
        audio.onerror = () => {
          // Fallback to browser TTS if StreamElements fails
          if (synthRef.current) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.9;
            utterance.pitch = 0.8;
            utterance.volume = 0.8;
            utterance.onend = resolve;
            synthRef.current.speak(utterance);
          } else {
            resolve();
          }
        };
        audio.play().catch(() => {
          // Fallback to browser TTS
          if (synthRef.current) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.9;
            utterance.pitch = 0.8;
            utterance.volume = 0.8;
            utterance.onend = resolve;
            synthRef.current.speak(utterance);
          } else {
            resolve();
          }
        });
      });
    } catch (error) {
      console.error('Error with text-to-speech:', error);
    }
  };

  // Start/Stop listening
  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      if (recognitionRef.current) {
        recognitionRef.current.start();
      } else {
        setError('Speech recognition not available');
      }
    }
  };

  // Handle manual command input
  const handleManualCommand = (e) => {
    if (e.key === 'Enter' && transcript.trim()) {
      processCommand(transcript.trim());
    }
  };

  return (
    <div className="jarvis-container">
      {/* Header */}
      <div className="jarvis-header">
        <div className="jarvis-logo">
          <div className="logo-circle">
            <div className="logo-inner"></div>
          </div>
          <h1>JARVIS</h1>
        </div>
        <p className="jarvis-subtitle">Personal AI Assistant</p>
      </div>

      {/* Main Interface */}
      <div className="jarvis-main">
        {/* Voice Wave Animation */}
        <VoiceWave isListening={isListening} isProcessing={isProcessing} />

        {/* Status Display */}
        <div className="status-display">
          {isListening && <p className="status listening">Listening...</p>}
          {isProcessing && <p className="status processing">Processing...</p>}
          {!isListening && !isProcessing && <p className="status ready">Ready for commands</p>}
        </div>

        {/* Transcript Display */}
        {transcript && (
          <div className="transcript-display">
            <p><strong>You said:</strong> "{transcript}"</p>
          </div>
        )}

        {/* Response Display */}
        {response && (
          <div className="response-display">
            <p><strong>Jarvis:</strong> {response}</p>
          </div>
        )}

        {/* Manual Input */}
        <div className="manual-input">
          <input
            type="text"
            placeholder="Type a command or click the microphone to speak..."
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            onKeyPress={handleManualCommand}
            className="command-input"
          />
        </div>

        {/* Control Buttons */}
        <div className="control-buttons">
          <button
            onClick={toggleListening}
            className={`mic-button ${isListening ? 'active' : ''}`}
            disabled={isProcessing}
          >
            {isListening ? '🛑 Stop' : '🎤 Talk to Jarvis'}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-display">
            <p className="error">{error}</p>
          </div>
        )}
      </div>

      {/* Command History */}
      {commandHistory.length > 0 && (
        <div className="command-history">
          <h3>Recent Commands</h3>
          <div className="history-list">
            {commandHistory.map((item, index) => (
              <div key={index} className="history-item">
                <div className="command">→ {item.command}</div>
                <div className="response">← {item.response}</div>
                <div className="timestamp">{item.timestamp.toLocaleTimeString()}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="jarvis-footer">
        <p>Say commands like "Open YouTube", "Search for cats on Google", or "Hello Jarvis"</p>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <JarvisAssistant />
    </div>
  );
}

export default App;