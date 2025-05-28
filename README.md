# LiveKit AI Car Call Centre

## 🚗 Intelligent Voice Assistant for Automotive Customer Service

An advanced AI-powered call center solution built with LiveKit, OpenAI, and real-time voice technology. This system provides intelligent customer service for automotive businesses with automatic call recording and VIN-based vehicle lookups.

## ✨ Key Features

- **🎤 Real-time Voice Conversations** - Natural AI voice interactions using LiveKit WebRTC
- **📹 Automatic Call Recording** - Every conversation saved as high-quality audio files  
- **🚗 Smart VIN Lookup** - Intelligent vehicle identification and database integration
- **📊 Live Monitoring** - Real-time conversation analytics and streaming insights
- **🌐 Web Interface** - Professional call center dashboard built with React
- **☁️ Cloud-Ready** - Seamless integration with LiveKit Cloud infrastructure
- **🗄️ Local Storage** - MinIO-powered recording storage with web access

## 🛠️ Technology Stack

- **Backend**: Python, LiveKit Agents, OpenAI GPT-4, Azure Speech Services
- **Frontend**: React, Vite, LiveKit React SDK
- **Storage**: MinIO (S3-compatible), SQLite database
- **Infrastructure**: ngrok tunneling, WebRTC, Real-time audio processing

## 🎯 Use Cases

- **Automotive Service Centers** - Handle customer inquiries about vehicle services
- **Car Dealerships** - Assist customers with vehicle information and appointments
- **Insurance Companies** - Process vehicle-related claims and inquiries
- **Fleet Management** - Support fleet operators with vehicle data and maintenance

## 🚀 Quick Start

> **See [SETUP_README.md](SETUP_README.md) for detailed installation and configuration instructions.**

1. **Clone & Install**
   ```bash
   git clone <repo-url>
   cd LiveKit-AI-Car-Call-Centre
   cd backend && pip install -r requirements.txt
   cd ../frontend && npm install
   ```

2. **Configure Environment**
   - Set up LiveKit Cloud credentials
   - Add OpenAI API key
   - Configure MinIO for recordings

3. **Start Services**
   ```bash
   # Terminal 1: MinIO Storage
   .\minio.exe server ./minio-data --console-address ":9001"
   
   # Terminal 2: ngrok Tunnel  
   .\ngrok.exe http 9000
   
   # Terminal 3: AI Agent
   cd backend && python -m livekit.agents.cli dev enhanced_agent_fixed.py
   
   # Terminal 4: Frontend
   cd frontend && npm run dev
   ```

4. **Test the System**
   - Open http://localhost:5173
   - Click "Join Call" and start talking
   - Check recordings at http://localhost:9001

## 📋 System Requirements

- **Python 3.11+**
- **Node.js 18+** 
- **LiveKit Cloud Account**
- **OpenAI API Access**
- **Windows OS** (current setup)

## 📁 Project Structure

```
LiveKit-AI-Car-Call-Centre/
├── backend/
│   ├── enhanced_agent_fixed.py     # Main AI agent with recording
│   ├── api.py                      # Vehicle database & VIN lookup
│   ├── prompts.py                  # AI conversation prompts
│   ├── streaming_conversation_monitor_fixed.py  # Real-time monitoring
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/components/             # React UI components
│   ├── SimpleVoiceAssistant.jsx    # Main voice interface
│   └── package.json                # Node.js dependencies
├── minio.exe                       # Local storage server
├── ngrok.exe                       # Public tunnel for recordings
└── SETUP_README.md                 # Detailed setup guide
```

## 🎬 Recording & Storage

- **Automatic Recording**: Every call automatically recorded in `.ogg` format
- **MinIO Storage**: S3-compatible local storage with web interface
- **ngrok Integration**: Secure public access for LiveKit Cloud uploads
- **Web Access**: Download and manage recordings via browser interface

## 🔧 Advanced Features

- **Enhanced Monitoring**: Real-time conversation analytics and performance metrics
- **Streaming Text Display**: Live transcript generation during conversations  
- **Function Tool Integration**: Dynamic VIN lookups and database queries
- **Graceful Shutdown**: Proper cleanup and recording finalization
- **Error Recovery**: Robust error handling and connection management

## 🐛 Troubleshooting

Common issues and solutions:

- **Recording failures**: Ensure ngrok is running and endpoint is updated in `.env`
- **Connection issues**: Verify LiveKit credentials and network connectivity  
- **Audio problems**: Check microphone permissions and browser compatibility
- **Storage access**: Confirm MinIO is running on port 9000

## 📚 Documentation

- **[Setup Guide](SETUP_README.md)** - Complete installation and configuration instructions
- **[Run Guide](RUN_GUIDE.md)** - Step-by-step instructions for running the system
- **[Troubleshooting](SETUP_README.md#troubleshooting)** - Common issues and solutions

## 🚀 Quick Start

1. **Setup**: Follow [SETUP_README.md](SETUP_README.md) for initial configuration
2. **Run**: Use [RUN_GUIDE.md](RUN_GUIDE.md) for daily operation
3. **Test**: Make a call and verify recording in MinIO console

## 📞 Support

For technical issues, check the terminal logs for detailed error messages.

---

**Built with ❤️ for the future of automotive customer service**
