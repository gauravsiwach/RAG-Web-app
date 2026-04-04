import React, { useState } from 'react';
import { recognizeSpeechFromMicrophone } from './services/azureSpeechService';

const VoiceInput = ({ onTranscript, onListeningChange, disabled, autoSend = false, userLanguage = "en-US" }) => {
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState(null);

  const handleVoiceInput = async () => {
    setIsListening(true);
    setError(null);
    
    // Notify parent component that listening started
    if (onListeningChange) {
      onListeningChange(true);
    }
    
    console.log("🎤 Starting voice input...");
    
    try {
      const transcript = await recognizeSpeechFromMicrophone(userLanguage);
      console.log("✅ Voice recognized:", transcript);
      
      // Pass transcript to parent with autoSend flag
      onTranscript(transcript, autoSend);
      
    } catch (err) {
      console.error('❌ Voice input error:', err);
      setError(err.message);
      
      // Show user-friendly error message
      if (err.message.includes('No speech could be recognized')) {
        alert('No speech detected. Please try again and speak clearly.');
      } else if (err.message.includes('credentials not configured')) {
        alert('Azure Speech Service not configured. Please check your .env file.');
      } else {
        alert(`Voice input failed: ${err.message}`);
      }
    } finally {
      setIsListening(false);
      
      // Notify parent that listening stopped
      if (onListeningChange) {
        onListeningChange(false);
      }
    }
  };

  return (
    <div className="voice-input-container" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <button
        onClick={handleVoiceInput}
        disabled={disabled || isListening}
        className={`voice-button ${isListening ? 'listening' : ''}`}
        title={isListening ? "Listening..." : "Click to speak"}
        style={{
          padding: '10px 15px',
          border: 'none',
          borderRadius: '4px',
          backgroundColor: isListening ? '#ef4444' : '#10b981',
          color: 'white',
          cursor: disabled || isListening ? 'not-allowed' : 'pointer',
          fontSize: '20px',
          transition: 'all 0.3s ease',
          opacity: disabled ? 0.5 : 1,
          minWidth: '50px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {isListening ? '🔴' : '🎤'}
      </button>
      {isListening && (
        <span style={{ marginLeft: '10px', color: '#666', fontSize: '14px', fontStyle: 'italic' }}>
          Listening...
        </span>
      )}
    </div>
  );
};

export default VoiceInput;
