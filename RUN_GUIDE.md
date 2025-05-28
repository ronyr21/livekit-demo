# 🚗 LiveKit AI Car Call Centre - Run Guide

This guide provides step-by-step instructions for running the LiveKit AI Car Call Centre system with automatic call recording functionality.

## 🏁 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Active internet connection
- LiveKit Cloud account
- OpenAI API key

### 1. Initial Setup (First Time Only)
```bash
# Clone the repository
git clone <your-repo-url>
cd LiveKit-AI-Car-Call-Centre

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### 2. Environment Configuration
```bash
# Navigate to backend directory
cd backend

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys and settings
```

**Required .env variables:**
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
OPENAI_API_KEY=your-openai-key
MINIO_ENDPOINT=https://your-ngrok-url.ngrok-free.app
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=livekit-recordings
```

## 🚀 Running the System

### Step 1: Start MinIO Storage Server
```bash
# In a new terminal (from project root)
minio server minio-data --console-address ":9001"
```
- **Web Console**: http://localhost:9001
- **API Endpoint**: http://localhost:9000
- **Login**: minioadmin / minioadmin

### Step 2: Start Ngrok Tunnel
```bash
# In a new terminal (from project root)
./ngrok http 9000
```
- Copy the HTTPS URL (e.g., `https://xxxx.ngrok-free.app`)
- Update `MINIO_ENDPOINT` in `.env` with this URL

### Step 3: Start the LiveKit Agent
```bash
# In backend directory
python enhanced_agent_fixed.py
```
The agent will:
- Connect to LiveKit Cloud
- Initialize MinIO bucket
- Start voice AI assistant
- Enable automatic call recording

### Step 4: Start the Frontend (Optional)
```bash
# In a new terminal
cd frontend
npm start
```
- Frontend available at: http://localhost:3000

## 📞 Making Test Calls

### Option 1: Using Frontend Interface
1. Open http://localhost:3000
2. Click "Join Call"
3. Start speaking to test the AI assistant

### Option 2: Using LiveKit Dashboard
1. Go to your LiveKit Cloud dashboard
2. Navigate to your project
3. Use the "Test Room" feature
4. Join with audio enabled

### Option 3: Using Mobile/Web Client
Use any WebRTC-compatible client with your LiveKit room credentials.

## 🎥 Recording Management

### Accessing Recordings
1. **MinIO Web Console**: http://localhost:9001
2. **Bucket**: `livekit-recordings`
3. **Format**: MP4 files with timestamps

### Recording Workflow
1. **Call Start**: Recording begins automatically
2. **Call End**: Recording stops and uploads to MinIO
3. **Storage**: Files saved in timestamp-based folders
4. **Access**: Download via MinIO console or API

## 🔧 System Monitoring

### Check System Status
```bash
# Check if MinIO is running
curl http://localhost:9000/minio/health/live

# Check ngrok tunnel status
curl https://your-ngrok-url.ngrok-free.app/minio/health/live

# View agent logs
tail -f backend/agent.log
```

### Common Commands
```bash
# Restart MinIO
pkill minio
minio server minio-data --console-address ":9001"

# Restart ngrok
pkill ngrok
./ngrok http 9000

# Restart agent
cd backend
python enhanced_agent_fixed.py
```

## 🛠️ Troubleshooting

### Recording Upload Failures
1. **Check ngrok tunnel**: Ensure ngrok is running and URL is updated in `.env`
2. **Verify MinIO**: Access http://localhost:9001 to confirm MinIO is running
3. **Check connectivity**: Test ngrok URL accessibility from external networks

### Agent Connection Issues
1. **Verify LiveKit credentials**: Check API key and secret in `.env`
2. **Network connectivity**: Ensure stable internet connection
3. **Firewall settings**: Allow outbound connections to LiveKit Cloud

### Audio Issues
1. **Browser permissions**: Grant microphone access
2. **HTTPS requirement**: Some browsers require HTTPS for audio
3. **Device compatibility**: Test with different devices/browsers

## 📊 Performance Tips

### For Production Use
1. **Use dedicated MinIO server**: Deploy MinIO on separate server
2. **Configure persistent storage**: Use external storage volumes
3. **Set up monitoring**: Implement health checks and alerts
4. **Scale agents**: Run multiple agent instances for high load

### Resource Requirements
- **Memory**: 2GB+ for agent + MinIO
- **Storage**: 1GB+ per hour of recordings
- **Bandwidth**: 64kbps+ per concurrent call

## 🔐 Security Notes

### For Production Deployment
1. **Change default credentials**: Update MinIO admin credentials
2. **Use HTTPS**: Configure SSL certificates for production
3. **Restrict access**: Implement proper authentication
4. **Secure storage**: Use encrypted storage for recordings

### Environment Variables
- Never commit `.env` files to version control
- Use secure credential management in production
- Rotate API keys regularly

## 📋 Maintenance

### Daily Tasks
- Monitor storage usage
- Check recording uploads
- Review agent logs

### Weekly Tasks
- Clean up old recordings
- Update dependencies
- Backup configurations

### Monthly Tasks
- Rotate API keys
- Review security settings
- Performance optimization

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review agent and system logs
3. Verify all services are running
4. Test with minimal configuration

---

**Last Updated**: $(date)
**Version**: 1.0.0
