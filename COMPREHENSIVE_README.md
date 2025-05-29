# 🚗 LiveKit AI Car Call Centre - Comprehensive Setup & Run Guide

## 🌟 Overview

The LiveKit AI Car Call Centre is an intelligent voice assistant system designed for automotive customer service. It combines real-time voice conversations, automatic call recording, vehicle VIN lookup, and comprehensive monitoring capabilities to provide a complete call center solution.

## ✨ Key Features

- **🎤 Real-time Voice Conversations** - Natural AI voice interactions using LiveKit WebRTC
- **📹 Automatic Call Recording** - Every conversation saved as high-quality audio files  
- **🚗 Smart VIN Lookup** - Intelligent vehicle identification and database integration
- **📊 Live Monitoring** - Real-time conversation analytics and admin dashboard
- **🌐 Professional Web Interface** - Two frontend options (Vite + Next.js)
- **☁️ Cloud-Ready** - Seamless integration with LiveKit Cloud infrastructure
- **🗄️ Local Storage** - MinIO-powered recording storage with web access

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, LiveKit Agents, OpenAI GPT-4, Azure Speech Services
- **Frontend**: 
  - Option 1: React + Vite (port 5173)
  - Option 2: Next.js (port 3000) with admin monitoring
- **Storage**: MinIO (S3-compatible), SQLite database
- **Infrastructure**: ngrok tunneling, WebRTC, Real-time audio processing

## 📋 Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed
- **Node.js 18+** installed
- **LiveKit Cloud Account** - [Sign up here](https://cloud.livekit.io)
- **OpenAI API Key** - [Get your key](https://platform.openai.com/api-keys)
- **Active internet connection**
- **Windows OS** (current setup optimized for Windows)

## 🚀 Complete Installation Guide

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd LiveKit-AI-Car-Call-Centre
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

The backend requires these key packages:
- `livekit-agents` - Core LiveKit agent framework
- `livekit-plugins-openai` - OpenAI integration
- `livekit-plugins-silero` - Speech recognition
- `python-dotenv` - Environment variable management
- `flask` & `flask-cors` - API server for admin monitoring
- `uvicorn` - ASGI server

#### Configure Backend Environment Variables

Create a `.env` file in the `backend` folder:

```properties
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key

# MinIO Configuration (for call recordings)
MINIO_ENDPOINT=https://your-ngrok-url.ngrok-free.app
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=livekit-recordings
MINIO_REGION=us-east-1

# Optional: Azure Speech Services
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=your_azure_region
```

### 3. Frontend Setup

You have two frontend options:

#### Option A: Vite Frontend (Recommended for basic usage)
```bash
cd frontend
npm install
```

Create `.env` file in `frontend` folder:
```properties
VITE_LIVEKIT_URL=wss://your-project.livekit.cloud
VITE_LIVEKIT_API_KEY=your_api_key
VITE_LIVEKIT_API_SECRET=your_api_secret
```

**Dependencies:**
- `@livekit/components-react` - LiveKit React components
- `livekit-client` - LiveKit client SDK
- `react` & `react-dom` - React framework
- `react-router-dom` - Client-side routing

#### Option B: Next.js Frontend (Advanced with admin monitoring)
```bash
cd frontend_new
npm install
```

Create `.env.local` file in `frontend_new` folder:
```properties
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**Dependencies:**
- `@livekit/components-react` - LiveKit React components
- `livekit-client` - LiveKit client SDK
- `next` - Next.js framework
- `tailwindcss` - Utility-first CSS framework
- `lucide-react` - Icon library

### 4. LiveKit Cloud Setup

1. **Create Account**: Visit [LiveKit Cloud](https://cloud.livekit.io)
2. **Create Project**: Set up a new project
3. **Get Credentials**: Copy your WebSocket URL, API Key, and API Secret
4. **Update Environment**: Add credentials to both backend and frontend `.env` files

### 5. OpenAI Setup

1. **Get API Key**: Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Create Key**: Generate a new API key
3. **Add to Environment**: Update `backend/.env` with `OPENAI_API_KEY`

## 🎬 Recording & Storage Setup

The system uses MinIO for local S3-compatible storage and ngrok for secure tunneling.

### 1. Start MinIO Storage Server

From the project root directory:
```bash
.\minio.exe server ./minio-data --console-address ":9001"
```

- **Web Console**: http://localhost:9001
- **API Endpoint**: http://localhost:9000
- **Default Login**: minioadmin / minioadmin
- **Keep this terminal open while running the application**

### 2. Set Up ngrok Tunnel

In a **new terminal window**:
```bash
.\ngrok.exe http 9000
```

You'll see output like:
```
Forwarding    https://abcd-12-34-56-78.ngrok-free.app -> http://localhost:9000
```

**Important Steps:**
- Copy the **https** ngrok URL
- Update `backend/.env` file: `MINIO_ENDPOINT=https://your-ngrok-url.ngrok-free.app`
- Keep ngrok terminal open (URL changes each restart)

### 3. Verify MinIO Setup

1. Visit http://localhost:9001
2. Login with: minioadmin / minioadmin
3. Confirm `livekit-recordings` bucket exists
4. If bucket doesn't exist, the agent will create it automatically

## 🚀 Running the Complete System

### Step 1: Start Storage & Tunnel Services

```bash
# Terminal 1: MinIO Storage
.\minio.exe server ./minio-data --console-address ":9001"

# Terminal 2: ngrok Tunnel  
.\ngrok.exe http 9000
```

### Step 2: Start the AI Agent

```bash
# Terminal 3: Backend Agent
cd backend
python enhanced_agent_fixed.py
```

**Expected Output:**
```
✅ Audio recording started successfully!
🔌 LiveKit URL: wss://your-project.livekit.cloud
⏳ Waiting for a participant...
```

### Step 3: Start Frontend

Choose one frontend option:

#### Option A: Vite Frontend
```bash
# Terminal 4: Vite Frontend
cd frontend
npm run dev
```
Access at: http://localhost:5173

#### Option B: Next.js Frontend (with admin monitoring)
```bash
# Terminal 4: Next.js Frontend
cd frontend_new
npm run dev
```
Access at: http://localhost:3000

### Step 4: Start Admin Monitoring (Optional)

For the Next.js frontend with admin capabilities:
```bash
# Terminal 5: Admin Backend
cd backend
python server.py
```
Admin backend runs on: http://localhost:8000

## 📞 Testing & Usage

### Making Test Calls

1. **Open Frontend**: Navigate to http://localhost:5173 or http://localhost:3000
2. **Join Call**: Click "Join Call" button
3. **Grant Permissions**: Allow microphone access when prompted
4. **Start Conversation**: Begin speaking to the AI assistant
5. **Test Features**: Try asking about vehicle VINs or service requests

### Admin Monitoring (Next.js Frontend)

1. **Live Calls Dashboard**: View all active calls in real-time
2. **Audio Monitoring**: Listen to ongoing conversations
3. **Call History**: Access previous conversation records
4. **Analytics**: View call duration, participant counts, and status

### Recording Management

1. **Access Recordings**: Visit MinIO console at http://localhost:9001
2. **Navigate to Bucket**: Open `livekit-recordings` bucket
3. **Download Files**: Recordings saved as `.ogg` files with timestamps
4. **File Structure**: `conversations/[room-name]/[timestamp]/audio.ogg`

## 📁 Project Structure

```
LiveKit-AI-Car-Call-Centre/
├── backend/
│   ├── enhanced_agent_fixed.py           # Main AI agent with recording
│   ├── server.py                         # Admin monitoring API server
│   ├── admin_monitor.py                  # Admin monitoring service
│   ├── admin_auth.py                     # Authentication service
│   ├── api.py                           # Vehicle database & VIN lookup
│   ├── prompts.py                       # AI conversation prompts
│   ├── streaming_conversation_monitor_fixed.py  # Real-time monitoring
│   ├── requirements.txt                 # Python dependencies
│   └── .env                            # Backend configuration
├── frontend/                           # Vite React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── SimpleVoiceAssistant.jsx # Main voice interface
│   │   │   ├── LiveKitModal.jsx         # LiveKit integration
│   │   │   └── AdminMonitor.jsx         # Admin monitoring
│   │   └── App.jsx                      # Main application
│   ├── package.json                    # Node.js dependencies
│   └── .env                           # Frontend configuration
├── frontend_new/                      # Next.js frontend with admin features
│   ├── app/
│   │   ├── components/
│   │   │   └── AudioMonitor.js         # Live audio monitoring
│   │   ├── content/sections/
│   │   │   └── LiveCalls.js           # Live calls dashboard
│   │   └── utils/
│   │       └── api.js                 # API service layer
│   ├── package.json                   # Node.js dependencies
│   └── .env.local                     # Next.js configuration
├── minio.exe                          # MinIO storage server
├── ngrok.exe                          # ngrok tunneling client
├── ngrok.yml                          # ngrok configuration
├── minio-data/                        # Local storage directory
└── Documentation/
    ├── README.md                      # Basic overview
    ├── SETUP_README.md               # Original setup guide
    ├── RUN_GUIDE.md                  # Original run guide
    └── COMPREHENSIVE_README.md       # This complete guide
```

## 🔧 Advanced Configuration

### Environment Variables Reference

#### Backend (.env)
```properties
# Required
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
OPENAI_API_KEY=your_openai_api_key

# Recording (Required for call recording)
MINIO_ENDPOINT=https://your-ngrok-url.ngrok-free.app
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=livekit-recordings
MINIO_REGION=us-east-1

# Optional
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=your_azure_region
```

#### Vite Frontend (.env)
```properties
VITE_LIVEKIT_URL=wss://your-project.livekit.cloud
VITE_LIVEKIT_API_KEY=your_api_key
VITE_LIVEKIT_API_SECRET=your_api_secret
```

#### Next.js Frontend (.env.local)
```properties
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   LiveKit       │
│   (React/Next)  │◄──►│   (Python)      │◄──►│   Cloud         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Browser  │    │   MinIO + ngrok │    │   OpenAI API    │
│   (WebRTC)      │    │   (Storage)     │    │   (AI Engine)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### Recording Upload Failures
**Problem**: "Failed to ensure MinIO bucket: path in endpoint is not allowed"
**Solutions**:
1. Ensure ngrok is running: `.\ngrok.exe http 9000`
2. Update `MINIO_ENDPOINT` in `backend/.env` with current ngrok URL
3. Restart the backend agent
4. Verify MinIO is accessible at http://localhost:9000

#### Agent Connection Issues
**Problem**: Agent not responding or connection failed
**Solutions**:
1. Verify LiveKit credentials in `backend/.env`
2. Check network connectivity and firewall settings
3. Ensure LiveKit Cloud project is active
4. Check terminal logs for detailed error messages

#### Frontend Connection Problems
**Problem**: Cannot connect to voice assistant
**Solutions**:
1. Verify frontend `.env` has correct LiveKit URL
2. Ensure backend agent is running and waiting for participants
3. Grant microphone permissions in browser
4. Check browser console for WebRTC errors
5. Try different browsers (Chrome recommended)

#### Audio Issues
**Problem**: No audio input/output
**Solutions**:
1. Grant microphone permissions in browser
2. Check microphone hardware and drivers
3. Test with different browsers
4. Ensure HTTPS for production (some browsers require it)

#### MinIO Storage Issues
**Problem**: Cannot access recordings or MinIO console
**Solutions**:
1. Verify MinIO is running on port 9000
2. Check MinIO console at http://localhost:9001
3. Confirm login credentials (minioadmin/minioadmin)
4. Restart MinIO server if needed

#### ngrok Tunnel Problems
**Problem**: ngrok URL not working or expired
**Solutions**:
1. Restart ngrok: `.\ngrok.exe http 9000`
2. Copy new HTTPS URL and update `backend/.env`
3. Restart backend agent after updating URL
4. Consider ngrok paid plan for stable URLs

### Debugging Tips

1. **Check All Terminals**: Ensure MinIO, ngrok, backend, and frontend are all running
2. **Monitor Logs**: Watch terminal outputs for error messages
3. **Verify Environment**: Double-check all `.env` files have correct values
4. **Test Connectivity**: 
   - MinIO: http://localhost:9001
   - Backend API: http://localhost:8000 (if running)
   - Frontend: http://localhost:5173 or http://localhost:3000
5. **Browser Developer Tools**: Check console for JavaScript errors

## 📊 Performance & Production Considerations

### Resource Requirements
- **Memory**: 2GB+ for agent + MinIO
- **Storage**: 1GB+ per hour of recordings
- **Bandwidth**: 64kbps+ per concurrent call
- **CPU**: Multi-core recommended for multiple concurrent calls

### Production Deployment Tips

1. **Security**:
   - Change MinIO default credentials
   - Use HTTPS/SSL certificates
   - Implement proper authentication
   - Secure API endpoints

2. **Scalability**:
   - Deploy MinIO on dedicated server
   - Use external storage volumes
   - Run multiple agent instances
   - Implement load balancing

3. **Monitoring**:
   - Set up health checks
   - Implement alerts for failures
   - Monitor storage usage
   - Track call quality metrics

4. **Backup**:
   - Regular backup of recordings
   - Database backup procedures
   - Configuration backup

## 🔐 Security Best Practices

1. **Environment Variables**: Never commit `.env` files to version control
2. **API Keys**: Rotate keys regularly and use secure storage
3. **Access Control**: Implement proper user authentication
4. **Network Security**: Use VPN for production deployments
5. **Data Protection**: Encrypt sensitive recordings and data

## 📋 Maintenance

### Daily Operations
- Monitor terminal outputs for errors
- Check storage usage in MinIO console
- Verify ngrok tunnel is active
- Review call logs and recordings

### Weekly Maintenance
- Clean up old recordings if needed
- Update ngrok URL if changed
- Check system resource usage
- Review error logs

### Updates & Upgrades
- Keep dependencies updated
- Monitor LiveKit SDK releases
- Update OpenAI models as available
- Backup before major updates

## 🆘 Support & Resources

### Getting Help
- **Terminal Logs**: Check detailed error messages in all terminals
- **Browser Console**: Use F12 to check for JavaScript errors
- **LiveKit Documentation**: [LiveKit Docs](https://docs.livekit.io)
- **OpenAI Documentation**: [OpenAI Docs](https://platform.openai.com/docs)

### Useful Commands
```bash
# Check Python version
python --version

# Check Node.js version
node --version

# Test network connectivity
ping google.com

# Check port usage
netstat -an | findstr :9000
netstat -an | findstr :5173
netstat -an | findstr :3000

# Kill processes if needed (Windows)
taskkill /f /im minio.exe
taskkill /f /im ngrok.exe
```

## 🎯 Use Cases & Applications

- **Automotive Service Centers**: Handle customer inquiries about vehicle services
- **Car Dealerships**: Assist customers with vehicle information and appointments  
- **Insurance Companies**: Process vehicle-related claims and inquiries
- **Fleet Management**: Support fleet operators with vehicle data and maintenance
- **Customer Support**: 24/7 automated assistance with human escalation
- **Appointment Scheduling**: Intelligent booking system integration

---

## 🎉 Conclusion

You now have a complete, production-ready AI-powered call center system with:

✅ **Real-time voice conversations** with intelligent AI  
✅ **Automatic call recording** with local storage  
✅ **Professional web interface** with admin monitoring  
✅ **Vehicle VIN lookup** and database integration  
✅ **Comprehensive monitoring** and analytics  
✅ **Scalable architecture** ready for production  

**Happy building! 🚗💬🤖**

---

*Built with ❤️ for the future of automotive customer service*
