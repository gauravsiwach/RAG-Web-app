# Multi-Modal Input Architecture

This document details the architecture for voice and image input features in the RAG Web App.

## 🏗️ Overview

The application supports three input modalities:
- **Text**: Traditional typed input
- **Voice**: Speech-to-text conversion using Azure Speech Service
- **Image**: OCR and analysis using Azure Computer Vision

All modalities follow a common pattern but have specialized components for their unique requirements.

## 🎤 Voice Input Architecture

### Flow Diagram
```
┌─────────────────┐
│   🎤 Voice      │
│   Input Button  │
└────────┬────────┘
         │
┌────────▼────────┐
│  VoiceInput     │
│  Component      │
│  - Mic button   │
│  - State mgmt   │
└────────┬────────┘
         │
┌────────▼────────┐
│azureSpeechService│
│  - Recognize    │
│  - Transcribe   │
│  - Error handling│
└────────┬────────┘
         │
┌────────▼────────┐
│handleVoiceMessage│
│  - Create msg   │
│  - Remove listening│
│  - Add to chat  │
└────────┬────────┘
         │
┌────────▼────────┐
│  sendQueryToRAG │
│  - API call     │
│  - Error handling│
│  - Bot response │
└────────┬────────┘
         │
┌────────▼────────┐
│   RAG Backend   │
│  (PDF/JSON/Web) │
└─────────────────┘
```

### Components

#### VoiceInput.jsx
```javascript
// UI Component Responsibilities:
- Render microphone button
- Manage recording state
- Handle click events
- Show visual feedback (🎤/🔄)
- Call azureSpeechService
```

#### azureSpeechService.js
```javascript
// Service Responsibilities:
- Initialize Azure Speech SDK
- Handle microphone permissions
- Perform speech recognition
- Return transcribed text
- Handle errors gracefully
```

#### handleVoiceMessage()
```javascript
// Handler Responsibilities:
- Create voice message object
- Add isVoice: true flag
- Remove listening indicator
- Add message to chat history
- Call sendQueryToRAG()
```

### Message Structure
```javascript
{
  id: timestamp,
  sender: "user",
  text: "transcribed speech",
  isVoice: true
}
```

## 🖼️ Image Input Architecture

### Flow Diagram
```
┌─────────────────┐
│   🖼️ Image      │
│   Input Button  │
└────────┬────────┘
         │
┌────────▼────────┐
│ ImageQueryInput │
│   Component     │
│  - File upload  │
│  - Validation   │
│  - Preview      │
└────────┬────────┘
         │
┌────────▼────────┐
│azureVisionService│
│  - OCR          │
│  - Caption      │
│  - Object Detect│
│  - Text extract │
└────────┬────────┘
         │
┌────────▼────────┐
│handleImageMessage│
│  - Create msg   │
│  - Add thumbnail│
│  - Add to chat  │
└────────┬────────┘
         │
┌────────▼────────┐
│  sendQueryToRAG │
│  - API call     │
│  - Error handling│
│  - Bot response │
└────────┬────────┘
         │
┌────────▼────────┐
│   RAG Backend   │
│  (PDF/JSON/Web) │
└─────────────────┘
```

### Components

#### ImageQueryInput.jsx
```javascript
// UI Component Responsibilities:
- Render image upload button
- Handle file selection
- Validate file type/size
- Create preview URL
- Show loading state
- Call azureVisionService
```

#### azureVisionService.js
```javascript
// Service Responsibilities:
- Initialize Azure Vision SDK
- Perform OCR (text extraction)
- Generate image captions
- Detect objects/tags
- Return structured analysis
- Handle errors gracefully
```

#### handleImageMessage()
```javascript
// Handler Responsibilities:
- Create image message object
- Add imageUrl for thumbnail
- Add message to chat history
- Call sendQueryToRAG()
```

### Message Structure
```javascript
{
  id: timestamp,
  sender: "user",
  text: "extracted text from image",
  imageUrl: "blob:http://..."
}
```

## 🔗 Common Architecture Pattern

### Shared Flow
```
┌─────────────────┐
│  Input Handler  │
│  (Voice/Image)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Create  │
    │ Message │
    │ Object  │
    └────┬────┘
         │
    ┌────┴────┐
    │ Add to  │
    │ Chat    │
    │ History │
    └────┬────┘
         │
    ┌────┴────┐
    │sendQuery│
    │ToRAG()   │
    └────┬────┘
         │
    ┌────┴────┐
    │ API Call │
    │ to RAG   │
    └────┬────┘
         │
    ┌────┴────┐
    │ Display │
    │ Response│
    └─────────┘
```

### sendQueryToRAG() - Common Method
```javascript
// Shared Responsibilities:
- Set sending state
- Determine endpoint based on mode
- Prepare request body
- Call backend API
- Handle bot response
- Manage errors
- Reset sending state
```

## 📊 Method Comparison

| Method | Input | Output | Special Features |
|--------|-------|--------|------------------|
| `handleVoiceMessage()` | text | voice message | `isVoice: true`, removes listening indicator |
| `handleImageMessage()` | text, imageUrl | image message | `imageUrl` for thumbnail display |
| `handleSendMessage()` | text | text message | Standard text input |

## 🎨 UI/UX Considerations

### Voice Input
- **Visual Feedback**: Button changes during recording
- **Listening Indicator**: "🎤 Listening..." message
- **Auto-Send**: Seamless experience
- **Error Handling**: Clear error messages

### Image Input
- **Thumbnail Display**: Image shown in chat
- **Clean Text**: Only extracted text as query
- **Loading State**: 🔄 during processing
- **Validation**: File type/size checks

## 🔧 Technical Implementation

### State Management
```javascript
// DashboardLayout.jsx State
const [chatHistory, setChatHistory] = useState([]);
const [isFileProcessed, setIsFileProcessed] = useState(false);
const [sending, setSending] = useState(false);
const [isListeningToVoice, setIsListeningToVoice] = useState(false);
```

### Error Handling
```javascript
// Common Error Patterns
- Network errors: "Network error"
- Permission errors: "Microphone access denied"
- Credential errors: "Invalid API key"
- File errors: "Invalid file type/size"
```

### Performance Considerations
- **Debouncing**: Prevent rapid API calls
- **Cleanup**: Proper resource disposal
- **Caching**: Avoid redundant uploads
- **Optimistic UI**: Immediate feedback

## 🚀 Future Enhancements

### Voice Improvements
- Voice commands
- Multiple languages
- Voice synthesis for responses

### Image Improvements
- Multiple image upload
- Image editing tools
- Handwritten text recognition

### Architecture Improvements
- Plugin system for new modalities
- Unified input processor
- Advanced error recovery

## 📝 Code Examples

### Voice Message Creation
```javascript
const userMessage = {
  id: Date.now(),
  sender: "user",
  text: text.trim(),
  isVoice: true,
};
```

### Image Message Creation
```javascript
const userMessage = {
  id: Date.now(),
  sender: "user",
  text: text.trim(),
  imageUrl: imageUrl,
};
```

### Common API Call
```javascript
const sendQueryToRAG = async (queryText) => {
  setSending(true);
  try {
    // API call logic
  } catch (error) {
    // Error handling
  } finally {
    setSending(false);
  }
};
```

This architecture ensures clean separation of concerns while maintaining consistency across all input modalities.
