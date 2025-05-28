# LiveKit AI Car Call Centre - Setup Guide

## 🚀 Quick Start Guide

This project is an AI-powered voice assistant for car call centers using LiveKit, OpenAI, and MinIO for call recording. Follow this guide to set up and run the system.

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- LiveKit Cloud account
- OpenAI API key
- Windows OS (for this setup)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```powershell
git clone <your-repo-url>
cd LiveKit-AI-Car-Call-Centre
```

### 2. Backend Setup

#### Install Python Dependencies
```powershell
cd backend
pip install -r requirements.txt
```

#### Configure Environment Variables
Create a `.env` file in the `backend` folder:

```properties
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-url.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key

# MinIO Configuration (for call recordings)
MINIO_ENDPOINT=https://your-ngrok-url.ngrok-free.app
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=livekit-recordings
MINIO_REGION=us-east-1
```

### 3. Frontend Setup

```powershell
cd frontend
npm install
```

Create a `.env` file in the `frontend` folder:
```properties
VITE_LIVEKIT_URL=wss://your-livekit-url.livekit.cloud
VITE_LIVEKIT_API_KEY=your_api_key
VITE_LIVEKIT_API_SECRET=your_api_secret
```

## 🎬 Setting Up Call Recording

### 1. Start MinIO Server

From the project root directory:
```powershell
.\minio.exe server ./minio-data --console-address ":9001"
```

**Important**: Keep this terminal window open while running the application.

### 2. Set Up ngrok Tunnel

In a **new terminal window**, from the project root:
```powershell
.\ngrok.exe http 9000
```

You'll see output like:
```
Forwarding    https://abcd-12-34-56-78.ngrok-free.app -> http://localhost:9000
```

**Copy the https ngrok URL** and update your `backend/.env` file:
```properties
MINIO_ENDPOINT=https://abcd-12-34-56-78.ngrok-free.app
```

**Important**: 
- Keep the ngrok terminal window open
- Update the `.env` file each time you restart ngrok (URL changes)

### 3. Verify MinIO Access

Visit http://localhost:9001 in your browser:
- Username: `minioadmin`
- Password: `minioadmin123`

You should see the MinIO console with a `livekit-recordings` bucket.

## 🚀 Running the Application

### Start the Backend Agent

```powershell
cd backend
python -m livekit.agents.cli dev enhanced_agent_fixed.py
```

You should see:
```
✅ Audio recording started successfully!
⏳ Waiting for a participant...
```

### Start the Frontend

In a new terminal:
```powershell
cd frontend  
npm run dev
```

Visit http://localhost:5173 to access the web interface.

## 📞 Testing the Call Center

1. **Open the web interface** at http://localhost:5173
2. **Click "Join Call"** to connect to the agent
3. **Allow microphone permissions** when prompted
4. **Start talking** - the AI agent will respond
5. **Check recordings** - Go to MinIO console (http://localhost:9001) → `livekit-recordings` → `conversations/`

## 🔧 Configuration Details

### LiveKit Setup

1. Create a LiveKit Cloud account at https://cloud.livekit.io
2. Create a new project
3. Copy the WebSocket URL, API Key, and API Secret
4. Update both `backend/.env` and `frontend/.env`

### OpenAI Setup

1. Get your API key from https://platform.openai.com/api-keys
2. Add to `backend/.env` as `OPENAI_API_KEY`

### Recording Features

- **Automatic call recording** - Every conversation is saved as `.ogg` files
- **MinIO storage** - Files stored in local MinIO instance
- **ngrok tunnel** - Allows LiveKit Cloud to upload recordings to your local MinIO
- **Web access** - Download recordings from MinIO console

## 🐛 Troubleshooting

### Recording Issues

**Problem**: "Failed to ensure MinIO bucket: path in endpoint is not allowed"
**Solution**: 
1. Ensure ngrok is running (`.\ngrok.exe http 9000`)
2. Update `MINIO_ENDPOINT` in `.env` with the current ngrok URL
3. Restart the backend agent

**Problem**: No files in MinIO after calls
**Solution**:
1. Check ngrok is still running (URLs expire)
2. Verify MinIO is accessible at http://localhost:9000
3. Check backend logs for egress errors

### Connection Issues

**Problem**: Agent not responding
**Solution**:
1. Verify all environment variables are set correctly
2. Check LiveKit credentials are valid
3. Ensure microphone permissions are granted

**Problem**: Frontend won't connect
**Solution**:
1. Check frontend `.env` has correct LiveKit URL
2. Verify backend agent is running and waiting for participants
3. Check browser console for WebRTC errors

## 📁 Project Structure

```
LiveKit-AI-Car-Call-Centre/
├── backend/
│   ├── enhanced_agent_fixed.py    # Main AI agent
│   ├── api.py                     # Car database functions
│   ├── prompts.py                 # AI prompts and instructions
│   └── .env                       # Backend configuration
├── frontend/
│   ├── src/components/            # React components
│   └── .env                       # Frontend configuration
├── minio.exe                      # MinIO server
├── ngrok.exe                      # ngrok tunnel
└── README.md
```

## 🎯 Features

- **Real-time voice conversation** with AI agent
- **Automatic call recording** (.ogg format)
- **Car VIN lookup** and database integration
- **Streaming conversation monitoring**
- **Professional call center interface**
- **Local storage** with MinIO
- **Cloud connectivity** via LiveKit

## 📝 Important Notes

1. **ngrok URL changes** every time you restart it - update `.env` accordingly
2. **Keep terminals open** - MinIO and ngrok must stay running
3. **Free ngrok limits** - Consider upgrading for production use
4. **Recording storage** - Files saved locally in MinIO, accessible via web console

## 🆘 Need Help?

- Check the terminal logs for detailed error messages
- Verify all services are running (MinIO, ngrok, backend agent)
- Ensure environment variables are correctly set
- Test MinIO connectivity at http://localhost:9001

---

🎉 **You're all set!** Your AI-powered call center with automatic recording is ready to use.
