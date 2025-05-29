# Frontend Integration Development Guide

## 🚀 Running the Integrated System

### Backend Setup (Terminal 1)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python server.py
```

### Frontend Setup (Terminal 2)
```bash
cd frontend_new
npm install
npm run dev
```

## 🎯 Features Implemented

### ✅ Real-time Admin Monitoring
- **Live Room Detection**: Automatically fetches active rooms from backend
- **Audio Streaming**: Hidden participant monitoring with LiveKit
- **Professional UI**: Modern design with responsive layout
- **Auto-refresh**: Room list updates every 10 seconds

### ✅ Smart Fallback System
- **Backend Available**: Shows real live calls from LiveKit backend
- **Backend Unavailable**: Gracefully falls back to demo data
- **Status Indicators**: Clear visual indication of system state

### ✅ Audio Monitoring Panel
- **Clean Interface**: Removed transcript, focus on audio only
- **Live Audio Stream**: Real-time audio from monitored calls
- **Participant Tracking**: See who's in the call
- **Stop Listening**: Easy disconnect with red button

## 🔧 Environment Configuration

Create `.env.local` in frontend_new/:
```
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000
NEXT_PUBLIC_DEVELOPMENT_MODE=true
```

## 🎵 How It Works

1. **Room Discovery**: Frontend polls `/admin/rooms` every 10 seconds
2. **Room Selection**: Click headphone icon to start monitoring
3. **Token Generation**: Backend creates hidden participant token
4. **Audio Connection**: LiveKit connects as invisible admin
5. **Live Streaming**: Audio streams through `RoomAudioRenderer`
6. **Stop Monitoring**: Red button disconnects cleanly

## 🏗️ Architecture

```
Frontend (Next.js)
├── LiveCalls.js - Main room listing
├── AudioMonitor.js - LiveKit integration  
├── ApiService - Backend communication
└── CSS Modules - Professional styling

Backend (Python/Flask)
├── server.py - Main API endpoints
├── admin_monitor.py - Monitoring service
└── admin_auth.py - Token generation
```

## 🎨 UI Components

### Main Dashboard
- **Grid Layout**: Clean cards for each active call
- **Search**: Filter calls by name/identifier
- **Status Indicators**: Live/Demo mode, connection status
- **Responsive**: Works on different screen sizes

### Monitoring Panel
- **Call Header**: Room name, identifier, duration
- **Audio Visualization**: Animated wave during playback
- **Participants List**: Shows who's in the call
- **Connection Status**: Connected/Connecting/Disconnected
- **Stop Button**: Prominent red disconnect button

## 🔍 Testing

### With Backend Running
1. Start backend server
2. Create test call rooms
3. Open frontend - should see real rooms
4. Click headphone icon - should hear audio
5. Check participants list updates

### Without Backend (Demo Mode)
1. Stop backend server
2. Frontend shows warning banner
3. Demo data displays instead
4. Monitoring shows "connection error" gracefully

## 🚨 Troubleshooting

### No Audio Heard
- Check browser permissions for audio
- Verify LiveKit server is running on port 7880
- Check console for connection errors

### Backend Connection Failed
- Verify backend is running on port 5000
- Check CORS settings allow frontend domain
- Review browser network tab for 404/500 errors

### Monitoring Token Error
- Check admin_monitor.py is properly configured
- Verify API keys in backend .env file
- Test `/admin/status` endpoint manually

## 🔄 Development Workflow

1. **Start Backend**: Always run backend first
2. **Start Frontend**: npm run dev in frontend_new/
3. **Test Integration**: Create calls, monitor them
4. **Check Logs**: Watch both frontend console and backend logs
5. **Iterate**: Make changes, hot reload handles updates

## 📝 Next Steps

- [ ] Add user authentication integration
- [ ] Implement call recording features  
- [ ] Add more advanced audio controls
- [ ] Create admin dashboard overview
- [ ] Add call analytics and metrics
