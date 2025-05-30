# 📊 LiveKit AI Call Center - File Integration & Communication Map

## 🎯 **System Overview**
This document maps every file's role, who it talks to, what it sends/receives, and how components integrate together.

---

## 🤖 **Backend Core Files**

### **`enhanced_agent_fixed.py`** - Main AI Agent Controller
**Role**: Primary conversational AI agent that handles customer interactions with monitoring
**Integrates With**:
- **LiveKit Cloud** → Connects to rooms, manages participants
- **OpenAI LLM** → Sends conversation context, receives AI responses
- **Azure Speech (STT/TTS)** → Processes audio in/out
- **api.py functions** → Calls VIN lookup and car creation functions
- **streaming_conversation_monitor_fixed.py** → Real-time conversation monitoring
- **LiveKit Egress** → Records conversations

**Sends**:
- Audio responses to customer via LiveKit
- VIN lookup requests to api.py functions
- Conversation events to streaming monitor
- Recording start/stop commands to Egress

**Receives**:
- Customer audio from LiveKit room
- AI responses from OpenAI
- Speech-to-text from Azure
- Vehicle data from api.py functions
- Room connection events from LiveKit

**Communication Pattern**:
```
Customer Audio → LiveKit → enhanced_agent_fixed.py → OpenAI + api.py functions → AI Response
                     ↓
         streaming_conversation_monitor_fixed.py (real-time monitoring)
                     ↓
                LiveKit Egress (recordings)
```

### **`admin_monitor.py`** - Admin Room Monitoring Service
**Role**: Provides admin monitoring capabilities - joining rooms as hidden participants
**Integrates With**:
- **LiveKit Cloud** → Connects to rooms as hidden admin participants
- **server.py** → Provides admin monitoring endpoints
- **Admin Frontend** → Serves room monitoring data

**Sends**:
- Hidden participant tokens for admin access
- Room participant lists and status
- Live room connection capabilities
- Admin monitoring session data

**Receives**:
- Admin monitoring requests from server.py
- Room join requests for hidden participation
- LiveKit room events and participant updates

**Communication Pattern**:
```
Admin Request → server.py → admin_monitor.py → LiveKit Room (hidden) → Live Monitoring
```

### **`api.py`** - Vehicle Database Agent Functions
**Role**: Provides AI agent function tools for vehicle VIN operations during conversations
**Integrates With**:
- **enhanced_agent_fixed.py** → Used as function tools by AI agent
- **SQLite Database (db_driver.py)** → Stores and retrieves vehicle information
- **Customer Conversations** → Responds to VIN lookup requests in real-time

**Sends**:
- Vehicle information (make, model, year) to AI agent
- Car creation confirmations
- VIN validation results
- Formatted car detail strings

**Receives**:
- VIN lookup requests from AI agent during conversations
- Car creation requests with vehicle details
- Car detail retrieval requests

**Communication Pattern**:
```
Customer asks about VIN → enhanced_agent_fixed.py → api.py functions → SQLite DB → Vehicle Data → AI Response
```

### **`server.py`** - Flask Web Server
**Role**: Main web server that provides LiveKit token generation and admin monitoring endpoints
**Integrates With**:
- **Frontend (both old and new)** → Serves token requests and admin API
- **LiveKit Cloud** → Generates access tokens and manages rooms
- **admin_monitor.py** → Provides admin monitoring services
- **admin_auth.py** → Handles admin authentication

**Sends**:
- LiveKit JWT tokens for room access
- Admin room lists and status
- CORS headers for browser access
- Health check responses

**Receives**:
- Token generation requests from frontend
- Admin API requests
- Room listing requests
- Health check pings

**Communication Pattern**:
```
Frontend → /getToken → server.py → LiveKit JWT Token
Admin Dashboard → /admin/* → server.py → admin_monitor.py → Admin Data
```

---

## 🎨 **Frontend Files (frontend_new/)**

### **`app/page.js`** - Main Landing Page
**Role**: Customer-facing interface for joining voice calls
**Integrates With**:
- **LiveKit Cloud** → Connects customers to voice rooms
- **Enhanced Agent** → Triggers agent activation

**Sends**:
- Room connection requests to LiveKit
- Customer audio to voice room

**Receives**:
- LiveKit room URLs and tokens
- Agent audio responses

**Communication Pattern**:
```
Customer → page.js → LiveKit Room → enhanced_agent_fixed.py
```

### **`app/admin/page.js`** - Admin Dashboard
**Role**: Real-time monitoring interface for administrators
**Integrates With**:
- **admin_monitor.py** → Receives live conversation data
- **api.py** → Fetches conversation history and recordings

**Sends**:
- WebSocket connection requests
- API calls for data retrieval
- Admin commands and queries

**Receives**:
- Live transcripts via WebSocket
- Conversation metadata
- Recording file access URLs

**Communication Pattern**:
```
Admin Dashboard → WebSocket → admin_monitor.py → Live Updates
                → HTTP API → api.py → Historical Data
```

### **`components/AudioMonitor.js`** - Live Audio Streaming
**Role**: Streams live audio from active calls to admin interface
**Integrates With**:
- **LiveKit Rooms** → Connects as hidden participant
- **Admin Dashboard** → Displays audio controls

**Sends**:
- Audio control commands
- Room join requests as hidden participant

**Receives**:
- Live audio streams from customer calls
- Audio metadata and participant info

**Communication Pattern**:
```
Active Call Room → AudioMonitor.js → Admin Audio Interface
```

### **`components/ConversationMonitor.js`** - Real-time Transcript Display
**Role**: Shows live conversation transcripts and participant activity
**Integrates With**:
- **admin_monitor.py** → Receives transcript updates
- **Admin Dashboard** → Displays conversation flow

**Sends**:
- WebSocket subscription requests
- UI interaction events

**Receives**:
- Real-time transcript chunks
- Participant join/leave notifications
- Conversation status changes

---

## 🔧 **Configuration & Utility Files**

### **`.env`** - Environment Configuration
**Role**: Stores API keys, endpoints, and service credentials
**Integrates With**:
- **ALL Backend Services** → Provides configuration values
- **Frontend Build** → Supplies public environment variables

**Contains**:
- LiveKit API credentials
- OpenAI API keys
- Azure Speech service keys
- MinIO storage configuration
- ngrok tunnel URLs

### **`package.json` (Frontend)**
**Role**: Defines frontend dependencies and build scripts
**Integrates With**:
- **Next.js Framework** → App structure and routing
- **LiveKit SDK** → Real-time communication
- **Tailwind CSS** → UI styling

**Dependencies**:
- `@livekit/components-react` → Room components
- `livekit-client` → WebRTC connection
- `next` → React framework
- `tailwindcss` → Styling system

### **`requirements.txt` (Backend)**
**Role**: Defines Python dependencies for backend services
**Integrates With**:
- **LiveKit Agents** → Voice AI framework
- **OpenAI SDK** → Language model integration
- **Azure SDK** → Speech services
- **MinIO Client** → Object storage

**Key Dependencies**:
- `livekit-agents` → Core agent framework
- `livekit-plugins-openai` → AI integration
- `livekit-plugins-azure` → Speech services
- `minio` → Storage client

---

## 🌐 **External Service Integration**

### **LiveKit Cloud**
**Role**: Real-time communication infrastructure
**Connects To**:
- `enhanced_agent_fixed.py` → Agent workers
- `app/page.js` → Customer interface
- `AudioMonitor.js` → Admin monitoring

**Provides**:
- WebRTC room management
- Audio/video streaming
- Participant management
- Recording egress services

### **OpenAI API**
**Role**: Conversational AI processing
**Connects To**:
- `enhanced_agent_fixed.py` → Conversation processing

**Provides**:
- GPT-4 language responses
- Conversation context understanding
- Real-time text generation

### **Azure Speech Services**
**Role**: Speech-to-text and text-to-speech processing
**Connects To**:
- `enhanced_agent_fixed.py` → Audio processing

**Provides**:
- Real-time speech recognition
- Natural voice synthesis
- Multiple language support

### **MinIO Storage**
**Role**: S3-compatible object storage for recordings
**Connects To**:
- `enhanced_agent_fixed.py` → Stores conversation recordings
- `api.py` → Serves recording file access

**Provides**:
- Persistent file storage
- Pre-signed URL generation
- Recording archival

---

## 🔄 **Data Flow Patterns**

### **Customer Call Flow**
```
1. Customer → app/page.js → LiveKit Room Creation
2. LiveKit → enhanced_agent_fixed.py → Agent Joins Room
3. Customer Audio → Agent → OpenAI Processing → AI Response
4. Conversation Data → admin_monitor.py → Admin Dashboard
5. Call Recording → MinIO Storage → Available via api.py
```

### **Admin Monitoring Flow**
```
1. Admin → app/admin/page.js → Dashboard Interface
2. Dashboard → WebSocket → admin_monitor.py → Live Updates
3. Admin → AudioMonitor.js → LiveKit Room → Live Audio
4. Admin → HTTP API → api.py → Historical Data
```

### **Real-time Communication**
```
enhanced_agent_fixed.py ←→ LiveKit ←→ Customer Interface
        ↓
admin_monitor.py ←→ WebSocket ←→ Admin Dashboard
        ↓
Recording Pipeline → MinIO → api.py → Admin Access
```

## 🎯 **Integration Summary**

**Core Communication Hub**: `enhanced_agent_fixed.py`
- Orchestrates all customer interactions
- Triggers recording and monitoring
- Integrates with all AI services

**Admin Data Hub**: `admin_monitor.py`
- Broadcasts real-time updates
- Connects agent activity to admin interfaces
- Manages WebSocket communications

**API Gateway**: `api.py`
- Serves administrative data
- Provides recording access
- Handles vehicle information queries

**Frontend Coordination**: Next.js App Router
- Customer interface (`app/page.js`)
- Admin monitoring (`app/admin/page.js`)
- Real-time components (AudioMonitor, ConversationMonitor)
