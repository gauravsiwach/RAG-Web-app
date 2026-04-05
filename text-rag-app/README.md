# RAG Web App - Multi-Modal Chat Interface

A modern React-based RAG (Retrieval-Augmented Generation) application with support for text, voice, and image inputs. Built with Vite for fast development and deployment.

## 🚀 Features

### 📝 Text Input
- Type queries directly in the chat interface
- Real-time chat with RAG-powered responses

### 🎤 Voice Input
- **Global Language Selector**: Choose your preferred voice input language (English or Hindi) from the Source Configuration sidebar. This setting applies to all voice queries.
- **Speech-to-Text**: Convert voice queries to text using Azure Speech Service, with accurate transcription for both English and Hindi.
- **Auto-Send**: Automatically send transcribed queries to the RAG system.
- **Visual Feedback**: Shows "Listening..." indicator during voice capture.
- **Smart Integration**: Seamlessly integrates with the unified chat flow.

### 🖼️ Image Input
- **Visual Queries**: Upload images as query input
- **OCR & Analysis**: Extract text from images using Azure Computer Vision
- **Smart Captioning**: Generate image descriptions automatically
- **Thumbnail Display**: Show image preview in chat
- **Clean Queries**: Extracted text sent as query to RAG system

### 📚 Data Sources & Multi-Modal Chat
- **PDF Files**: Upload and index PDF documents
- **JSON Files**: Support for structured data queries
- **Web URLs**: Index web pages for Q&A
- **Existing Indexes**: Reuse previously indexed data
- **Unified Chat**: Text, voice, and image queries all use the same chat interface and retrieval pipeline.

## 🏗️ Architecture

### Voice Input Language Selection

- The language selector is located in the Source Configuration sidebar (left panel).
- Select either **English** or **Hindi** before using the microphone button.
- The selected language is used for all speech-to-text queries.

### Voice Input Architecture

```
┌─────────────────┐
│   🎤 Voice      │
│   Input Button  │
└────────┬────────┘
         │
┌────────▼────────┐
│  VoiceInput     │
│  Component      │
└────────┬────────┘
         │
┌────────▼────────┐
│azureSpeechService│
│  - Recognize    │
│  - Transcribe   │
└────────┬────────┘
         │
┌────────▼────────┐
│handleVoiceMessage│
│  - Create msg   │
│  - Remove listening│
└────────┬────────┘
         │
┌────────▼────────┐
│  sendQueryToRAG │
│  - API call     │
│  - Error handling│
└────────┬────────┘
         │
┌────────▼────────┐
│   RAG Backend   │
│  (PDF/JSON/Web) │
└─────────────────┘
```

#### Voice Components:
- **VoiceInput.jsx**: UI component with microphone button
- **azureSpeechService.js**: Azure Speech SDK integration
- **handleVoiceMessage()**: Voice-specific message handling
- **sendQueryToRAG()**: Common API call logic

### Image Input Architecture

```
┌─────────────────┐
│   🖼️ Image      │
│   Input Button  │
└────────┬────────┘
         │
┌────────▼────────┐
│ ImageQueryInput │
│   Component     │
└────────┬────────┘
         │
┌────────▼────────┐
│azureVisionService│
│  - OCR          │
│  - Caption      │
│  - Object Detect│
└────────┬────────┘
         │
┌────────▼────────┐
│handleImageMessage│
│  - Create msg   │
│  - Add thumbnail│
└────────┬────────┘
         │
┌────────▼────────┐
│  sendQueryToRAG │
│  - API call     │
│  - Error handling│
└────────┬────────┘
         │
┌────────▼────────┐
│   RAG Backend   │
│  (PDF/JSON/Web) │
└─────────────────┘
```

#### Image Components:
- **ImageQueryInput.jsx**: UI component with image upload button
- **azureVisionService.js**: Azure Computer Vision integration
- **handleImageMessage()**: Image-specific message handling
- **sendQueryToRAG()**: Common API call logic

### Common Architecture Pattern

```javascript
// Reusable pattern for all input types
┌─────────────────┐
│  Input Handler  │
│  (Voice/Image)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Create  │
    │ Message │
    └────┬────┘
         │
    ┌────┴────┐
    │ Add to  │
    │ Chat    │
    └────┬────┘
         │
    ┌────┴────┐
    │sendQuery│
    │ToRAG()   │
    └─────────┘
```

## 🛠️ Setup & Installation

### Prerequisites
- Node.js 16+ 
- Azure Account (for Speech & Vision services)

### 1. Clone and Install
```bash
git clone <repository-url>
cd text-rag-app
npm install
```

### 2. Azure Services Setup

#### Azure Speech Service
1. Go to [Azure Portal](https://portal.azure.com)
2. Create Speech Service resource
3. Get API Key and Region
4. Add to `.env`:
```env
VITE_AZURE_SPEECH_KEY=your-speech-key
VITE_AZURE_SPEECH_REGION=your-region
```

#### Azure Computer Vision
1. Go to [Azure Portal](https://portal.azure.com)
2. Create Computer Vision resource
3. Get API Key and Endpoint
4. Add to `.env`:
```env
VITE_AZURE_VISION_KEY=your-vision-key
VITE_AZURE_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
```

### 3. Environment Variables
Create `.env` file:
```env
# Azure Speech Service
VITE_AZURE_SPEECH_KEY=your-speech-key
VITE_AZURE_SPEECH_REGION=your-region

# Azure Computer Vision
VITE_AZURE_VISION_KEY=your-vision-key
VITE_AZURE_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
```

### 4. Run Development Server
```bash
npm run dev
```

## 📁 Project Structure

```
src/
├── components/
│   ├── DashboardLayout.jsx    # Main layout and chat interface
│   ├── VoiceInput.jsx         # Voice input component
│   ├── ImageQueryInput.jsx    # Image input component
│   ├── PdfUploader.jsx        # PDF upload component
│   ├── WebUrlInput.jsx        # Web URL input component
│   └── JsonUploader.jsx       # JSON upload component
├── services/
│   ├── azureSpeechService.js  # Azure Speech SDK integration
│   └── azureVisionService.js  # Azure Vision SDK integration
├── config.js                  # API configuration
└── main.jsx                   # App entry point
```

## 🎯 Usage Guide

### Voice Input
1. Upload a data source (PDF/JSON/Web)
2. Click the 🎤 microphone button
3. Speak your query
4. Voice is transcribed and sent automatically
5. Get RAG-powered response

### Image Input
1. Upload a data source (PDF/JSON/Web)
2. Click the 🖼️ image button
3. Select an image file
4. Image is analyzed for text/caption
5. Extracted text sent as query
6. See image thumbnail in chat

### Text Input
1. Upload a data source (PDF/JSON/Web)
2. Type your query in the input box
3. Press Enter or click Send
4. Get RAG-powered response

## 🔧 Configuration

### Supported Image Formats
- JPG, PNG, GIF, BMP, WEBP
- Max file size: 20MB

### Voice Features
- Auto-send enabled by default
- Real-time transcription
- Visual listening indicator

### RAG Endpoints
- `/pdf_chat` - PDF document queries
- `/json_chat` - JSON data queries  
- `/web_url_chat` - Web page queries

## 🐛 Troubleshooting

### Voice Issues
- Check microphone permissions
- Verify Azure Speech credentials
- Ensure stable internet connection

### Image Issues
- Check image format and size
- Verify Azure Vision credentials
- Ensure proper CORS configuration

### Common Errors
- **401 Unauthorized**: Check Azure API keys
- **403 Forbidden**: Verify resource permissions
- **Network Error**: Check internet connection

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make your changes
4. Add tests if applicable
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🔗 Links

- [Azure Speech Service Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/)
- [Azure Computer Vision Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/)
- [React Documentation](https://reactjs.org/)
- [Vite Documentation](https://vitejs.dev/)
