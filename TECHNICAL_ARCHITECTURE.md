# LiveKit AI Call Center - Technical Architecture Deep Dive

## Table of Contents
1. [System Overview](#system-overview)
2. [LiveKit Integration Architecture](#livekit-integration-architecture)
3. [Transcription Pipeline](#transcription-pipeline)
4. [Recording Mechanism](#recording-mechanism)
5. [Room Joining & Participant Management](#room-joining--participant-management)
6. [Monitoring System Architecture](#monitoring-system-architecture)
7. [Admin Monitoring Features](#admin-monitoring-features)
8. [Frontend-Backend Integration](#frontend-backend-integration)
9. [Data Flow Diagrams](#data-flow-diagrams)
10. [Error Handling & Graceful Shutdown](#error-handling--graceful-shutdown)

## System Overview

The LiveKit AI Call Center is a sophisticated real-time communication system that integrates multiple technologies:

- **LiveKit Agents SDK**: Real-time WebRTC communication
- **OpenAI GPT-4**: AI conversation engine
- **Azure Speech Services**: Speech-to-Text transcription
- **MinIO**: S3-compatible storage for recordings
- **ngrok**: Secure tunneling for webhooks
- **React/Next.js**: Frontend interfaces

### Core Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   LiveKit       │
│   Voice UI      │◄──►│   AI Agent      │◄──►│   Cloud         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └─────────────►│   Monitoring    │◄─────────────┘
                        │   System        │
                        └─────────────────┘
```

## LiveKit Integration Architecture

### Agent Connection Process

The AI agent connects to LiveKit rooms through a sophisticated worker pattern implemented in `enhanced_agent_fixed.py`:

```python
class EnhancedAgent(VoiceAssistant):
    def __init__(self, *, vad: silero.VAD, stt: STT, llm: LLM, tts: TTS):
        super().__init__(vad=vad, stt=stt, llm=llm, tts=tts)
        self.conversation_id = str(uuid.uuid4())
        self.monitor = ConversationMonitor(self.conversation_id)
        self._egress_started = False
        self._recording_track_sid = None
```

#### Room Connection Flow

1. **Worker Initialization**: The `WorkerOptions` define how the agent connects:
   ```python
   worker = LiveKitWorker(
       WorkerOptions(
           entrypoint_fnc=entrypoint,
           prewarm_fnc=prewarm,
           worker_type=WorkerType.ROOM,
           host="0.0.0.0",
           port=8080,
       ),
   )
   ```

2. **Entrypoint Function**: Handles room joining logic:
   ```python
   async def entrypoint(ctx: JobContext):
       await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
       participant = EnhancedAgent(...)
       participant.start(ctx.room)
       await participant.say("Welcome to CME Auto Sales!")
   ```

3. **Room State Management**: The agent maintains room state through:
   - Participant tracking via `ctx.room.participants`
   - Audio track subscription for transcription
   - Real-time audio streaming for monitoring

### Participant Handling

The system distinguishes between different participant types:

- **Human Participants**: Customers calling in
- **AI Agent**: The voice assistant (hidden from customer view)
- **Admin Monitors**: Invisible participants for supervision

```python
async def on_participant_connected(self, participant: RemoteParticipant):
    """Handle new participant connections"""
    if participant.identity.startswith("admin_"):
        # Hide admin from customer view
        await self._setup_admin_monitoring(participant)
    else:
        # Regular customer participant
        await self._start_conversation_tracking(participant)
```

## Transcription Pipeline

### Real-time vs Final Transcripts

The system implements a dual transcription approach:

#### 1. Real-time Transcription (Streaming)
```python
class StreamingConversationMonitor:
    async def handle_speech_event(self, event):
        if event.type == SpeechEventType.INTERIM_TRANSCRIPT:
            # Real-time streaming to admin dashboard
            await self.broadcast_interim_transcript(event.alternatives[0].text)
        elif event.type == SpeechEventType.FINAL_TRANSCRIPT:
            # Store final transcript in conversation log
            await self.store_final_transcript(event.alternatives[0].text)
```

#### 2. Azure Speech Services Integration
```python
async def _setup_azure_stt(self):
    """Configure Azure Speech-to-Text with real-time capabilities"""
    speech_config = speechsdk.SpeechConfig(
        subscription=os.getenv("AZURE_SPEECH_KEY"),
        region=os.getenv("AZURE_SPEECH_REGION")
    )
    speech_config.speech_recognition_language = "en-US"
    speech_config.enable_dictation()
    speech_config.request_word_level_timestamps()
```

#### Transcription Data Flow
```
Audio Input → VAD Detection → Azure STT → Real-time Streaming → Final Storage
     │                                          │                      │
     └── LiveKit Audio Track ──────────────────┘              SQLite Database
```

### Conversation Logging

Transcripts are structured and stored with metadata:

```python
@dataclass
class ConversationEvent:
    timestamp: datetime
    speaker: str  # "customer" or "assistant"
    content: str
    confidence: float
    is_final: bool
    event_type: str  # "speech", "silence", "interruption"
```

## Recording Mechanism

### Egress-based Recording System

The recording system uses LiveKit's Egress service for high-quality audio capture:

#### 1. Egress Initialization
```python
async def start_egress_recording(self, room_name: str):
    """Start recording using LiveKit Egress"""
    egress_client = EgressServiceClient()
    
    # Configure room composite recording
    room_composite = RoomCompositeEgressRequest(
        room_name=room_name,
        layout="speaker",
        audio_only=True,
        file_outputs=[
            EncodedFileOutput(
                file_type=EncodedFileType.MP4,
                filepath=f"conversations/{self.conversation_id}.mp4"
            )
        ]
    )
    
    response = await egress_client.start_room_composite_egress(room_composite)
    self._egress_id = response.egress_id
```

#### 2. MinIO Storage Integration
```python
class MinIORecordingHandler:
    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False
        )
    
    async def upload_recording(self, file_path: str, conversation_id: str):
        """Upload completed recording to MinIO"""
        bucket_name = "livekit-recordings"
        object_name = f"conversations/{conversation_id}.mp4"
        
        self.client.fput_object(bucket_name, object_name, file_path)
```

#### 3. ngrok Webhook Tunneling
```python
# Egress webhook endpoint for recording completion
@app.post("/webhook/egress")
async def egress_webhook(request: EgressWebhookRequest):
    """Handle egress completion notifications"""
    if request.event == "egress_ended":
        # Download from LiveKit storage
        file_url = request.egress_info.file_results[0].download_url
        
        # Upload to MinIO for permanent storage
        await upload_to_minio(file_url, request.egress_info.egress_id)
        
        # Update conversation record
        await update_conversation_recording_status(
            request.egress_info.room_name,
            "completed"
        )
```

### Recording Lifecycle
```
Room Start → Egress Init → Audio Capture → File Generation → MinIO Upload → Cleanup
     │             │             │              │               │            │
     └─── Monitor Start ─────────┴── Real-time ─┴─── Webhook ───┴─── Database Update
```

## Room Joining & Participant Management

### Customer Room Joining

#### Frontend Connection Process
```javascript
// SimpleVoiceAssistant.jsx
const connectToRoom = async () => {
    const room = new Room({
        adaptiveStream: true,
        dynacast: true,
        publishDefaults: {
            audioPreset: AudioPresets.music,
        },
    });

    // Set up event handlers before connecting
    room.on(RoomEvent.Connected, handleRoomConnected);
    room.on(RoomEvent.TrackSubscribed, handleTrackSubscribed);
    room.on(RoomEvent.Disconnected, handleDisconnected);

    // Connect with authentication token
    await room.connect(LIVEKIT_URL, token, {
        autoSubscribe: false,
    });
};
```

#### Token Generation & Authentication
```python
# Backend token generation
def generate_room_token(room_name: str, participant_identity: str):
    """Generate JWT token for room access"""
    token = AccessToken(
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    token.with_identity(participant_identity)
    token.with_name(f"Customer {participant_identity}")
    token.with_grants(
        RoomGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        )
    )
    
    return token.to_jwt()
```

### Agent Room Joining

The AI agent joins rooms through the LiveKit Workers framework:

```python
async def entrypoint(ctx: JobContext):
    """Agent entrypoint when assigned to a room"""
    logger.info(f"Agent joining room: {ctx.room.name}")
    
    # Connect to room with audio-only subscription
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Initialize enhanced agent with monitoring
    agent = EnhancedAgent(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=cartesia.TTS(),
    )
    
    # Start agent and begin conversation
    agent.start(ctx.room)
    await agent.say("Welcome to CME Auto Sales! How can I help you today?")
    
    # Keep agent running until room closes
    await asyncio.sleep(0.1)
```

### Admin Monitoring Participants

Admin participants join as invisible observers:

```python
class AdminMonitoringParticipant:
    async def join_as_monitor(self, room_name: str):
        """Join room as invisible monitoring participant"""
        token = self._generate_admin_token(room_name)
        
        # Connect with monitoring-specific settings
        room_options = RoomOptions(
            auto_subscribe=AutoSubscribe.AUDIO_ONLY,
            adaptive_stream=False,
            publish_defaults=PublishOptions(
                video_codec=VideoCodec.NONE,  # No video
                audio_preset=AudioPresets.speech,
            )
        )
        
        await self.room.connect(LIVEKIT_URL, token, room_options)
        
        # Hide from participant list
        await self._set_invisible_metadata()
```

## Monitoring System Architecture

### Core Monitoring Components

#### 1. ConversationMonitor
```python
class ConversationMonitor:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.events = []
        self.metadata = {
            "start_time": datetime.utcnow(),
            "participants": [],
            "status": "active"
        }
        self.db = DatabaseDriver()
    
    async def log_event(self, event: ConversationEvent):
        """Log conversation events with real-time broadcasting"""
        self.events.append(event)
        await self.db.store_event(self.conversation_id, event)
        await self.broadcast_to_admins(event)
```

#### 2. StreamingConversationMonitor
```python
class StreamingConversationMonitor(ConversationMonitor):
    async def start_real_time_monitoring(self):
        """Begin real-time audio and transcript streaming"""
        self.audio_streamer = AudioStreamer()
        self.transcript_streamer = TranscriptStreamer()
        
        # Set up WebSocket connections for admin dashboard
        await self.setup_admin_websockets()
        
        # Start audio streaming
        asyncio.create_task(self.stream_audio_to_admins())
```

### Real-time Data Broadcasting

The monitoring system uses WebSockets for real-time updates:

```python
class AdminWebSocketManager:
    def __init__(self):
        self.connections = {}  # admin_id -> websocket
        
    async def broadcast_conversation_update(self, conversation_id: str, update: dict):
        """Broadcast updates to all connected admin clients"""
        message = {
            "type": "conversation_update",
            "conversation_id": conversation_id,
            "data": update,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = []
        for admin_id, websocket in self.connections.items():
            try:
                await websocket.send(json.dumps(message))
            except ConnectionClosed:
                disconnected.append(admin_id)
        
        # Clean up disconnected clients
        for admin_id in disconnected:
            del self.connections[admin_id]
```

### Database Schema

The monitoring system uses SQLite with the following schema:

```sql
-- Conversations table
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    room_name TEXT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status TEXT DEFAULT 'active',
    customer_info JSON,
    recording_url TEXT,
    metadata JSON
);

-- Conversation events table
CREATE TABLE conversation_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    speaker TEXT,
    content TEXT,
    confidence REAL,
    event_type TEXT,
    metadata JSON,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Vehicle lookups table
CREATE TABLE vehicle_lookups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT,
    vin TEXT,
    make TEXT,
    model TEXT,
    year INTEGER,
    lookup_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

## Admin Monitoring Features

### Real-time Audio Streaming

The admin monitoring system provides live audio streaming capabilities:

#### Audio Monitor Component
```javascript
// AudioMonitor.js
const AudioMonitor = ({ conversationId }) => {
    const [audioStream, setAudioStream] = useState(null);
    const [isListening, setIsListening] = useState(false);
    
    useEffect(() => {
        const connectToLiveKitRoom = async () => {
            const room = new Room();
            
            // Connect as admin monitor
            const token = await fetchAdminToken(conversationId);
            await room.connect(LIVEKIT_URL, token);
            
            // Subscribe to audio tracks
            room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
                if (track.kind === Track.Kind.Audio) {
                    track.attach(audioRef.current);
                    setAudioStream(track);
                }
            });
        };
        
        connectToLiveKitRoom();
    }, [conversationId]);
    
    return (
        <div className={styles.audioMonitor}>
            <audio ref={audioRef} autoPlay />
            <button onClick={toggleListening}>
                {isListening ? 'Stop Listening' : 'Start Listening'}
            </button>
        </div>
    );
};
```

#### Admin Dashboard Integration
```javascript
// AdminDashboard.jsx
const AdminDashboard = () => {
    const [activeConversations, setActiveConversations] = useState([]);
    const [selectedConversation, setSelectedConversation] = useState(null);
    
    useEffect(() => {
        // WebSocket connection for real-time updates
        const ws = new WebSocket(WS_ADMIN_URL);
        
        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            
            switch (update.type) {
                case 'conversation_started':
                    setActiveConversations(prev => [...prev, update.conversation]);
                    break;
                case 'conversation_update':
                    updateConversationInList(update.conversation_id, update.data);
                    break;
                case 'conversation_ended':
                    removeConversationFromList(update.conversation_id);
                    break;
            }
        };
        
        return () => ws.close();
    }, []);
};
```

### Hidden Participant Management

Admin monitors join rooms as invisible participants:

```python
async def setup_admin_monitoring(self, admin_id: str, room_name: str):
    """Set up admin as hidden monitoring participant"""
    
    # Generate admin token with special permissions
    token = AccessToken(
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET
    )
    
    token.with_identity(f"admin_{admin_id}")
    token.with_name("System Monitor")
    token.with_grants(RoomGrants(
        room_join=True,
        room=room_name,
        can_subscribe=True,
        can_publish=False,  # Admin cannot speak
        hidden=True,  # Hidden from participant list
    ))
    
    # Set metadata to mark as admin
    token.with_metadata({
        "role": "admin",
        "monitor_type": "supervisor",
        "permissions": ["audio_monitor", "transcript_view"]
    })
    
    return token.to_jwt()
```

## Frontend-Backend Integration

### API Communication Patterns

#### Vehicle Database Integration
```python
# api.py - Vehicle lookup service
@app.post("/api/lookup-vehicle")
async def lookup_vehicle(request: VehicleLookupRequest):
    """Look up vehicle information by VIN"""
    try:
        # Query vehicle database
        vehicle = await db.query_vehicle_by_vin(request.vin)
        
        if vehicle:
            return VehicleLookupResponse(
                vin=vehicle.vin,
                make=vehicle.make,
                model=vehicle.model,
                year=vehicle.year,
                found=True
            )
        else:
            return VehicleLookupResponse(found=False)
            
    except Exception as e:
        logger.error(f"Vehicle lookup error: {e}")
        raise HTTPException(status_code=500, detail="Lookup failed")
```

#### Real-time Conversation Updates
```javascript
// Frontend WebSocket integration
const useConversationUpdates = (conversationId) => {
    const [transcript, setTranscript] = useState([]);
    const [status, setStatus] = useState('connecting');
    
    useEffect(() => {
        const ws = new WebSocket(`${WS_URL}/conversation/${conversationId}`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'transcript_update':
                    setTranscript(prev => [...prev, data.content]);
                    break;
                case 'status_change':
                    setStatus(data.status);
                    break;
                case 'recording_complete':
                    handleRecordingComplete(data.recording_url);
                    break;
            }
        };
        
        return () => ws.close();
    }, [conversationId]);
    
    return { transcript, status };
};
```

### Authentication & Security

#### JWT Token Management
```python
class AuthManager:
    @staticmethod
    def generate_customer_token(room_name: str, customer_id: str):
        """Generate customer access token"""
        token = AccessToken(api_key=API_KEY, api_secret=API_SECRET)
        token.with_identity(customer_id)
        token.with_grants(RoomGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))
        return token.to_jwt()
    
    @staticmethod
    def generate_admin_token(room_name: str, admin_id: str):
        """Generate admin monitoring token"""
        token = AccessToken(api_key=API_KEY, api_secret=API_SECRET)
        token.with_identity(f"admin_{admin_id}")
        token.with_grants(RoomGrants(
            room_join=True,
            room=room_name,
            can_subscribe=True,
            can_publish=False,
            hidden=True,
        ))
        return token.to_jwt()
```

## Data Flow Diagrams

### Complete System Data Flow
```
Customer Call Flow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Customer   │    │  Frontend   │    │   Backend   │    │  LiveKit    │
│   Browser   │    │    App      │    │   Server    │    │   Cloud     │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │                  │
       │ 1. Load Page     │                  │                  │
       ├─────────────────►│                  │                  │
       │                  │ 2. Request Token │                  │
       │                  ├─────────────────►│                  │
       │                  │ 3. JWT Token     │                  │
       │                  │◄─────────────────┤                  │
       │                  │ 4. Connect Room  │                  │
       │                  ├─────────────────────────────────────►│
       │                  │                  │ 5. Agent Join    │
       │                  │                  ├─────────────────►│
       │ 6. Audio Stream  │                  │                  │
       ├─────────────────►│◄─────────────────────────────────────┤
       │                  │                  │                  │
```

### Monitoring & Recording Flow
```
Real-time Monitoring:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Admin    │    │   Monitor   │    │ Conversation│    │   MinIO     │
│ Dashboard   │    │  Service    │    │  Monitor    │    │  Storage    │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │                  │
       │ WebSocket        │ Audio Stream     │ Egress Start     │
       │◄─────────────────┤◄─────────────────┤─────────────────►│
       │ Transcript       │ STT Events       │ Recording        │
       │◄─────────────────┤◄─────────────────┤                  │
       │ Status Updates   │ Room Events      │ Upload Complete  │
       │◄─────────────────┤◄─────────────────┤◄─────────────────┤
```

## Error Handling & Graceful Shutdown

### Agent Error Recovery
```python
class EnhancedAgent(VoiceAssistant):
    async def handle_connection_error(self, error: Exception):
        """Handle LiveKit connection errors gracefully"""
        logger.error(f"Connection error: {error}")
        
        # Attempt reconnection with exponential backoff
        for attempt in range(3):
            try:
                await asyncio.sleep(2 ** attempt)
                await self.reconnect()
                break
            except Exception as e:
                logger.warning(f"Reconnection attempt {attempt + 1} failed: {e}")
        
        # If all reconnection attempts fail, gracefully shut down
        if not self.is_connected():
            await self.graceful_shutdown()
    
    async def graceful_shutdown(self):
        """Perform cleanup before shutdown"""
        try:
            # Stop recording if active
            if self._egress_started:
                await self.stop_recording()
            
            # Save conversation state
            await self.monitor.finalize_conversation()
            
            # Notify admin dashboard
            await self.broadcast_shutdown_event()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            # Ensure room disconnection
            if self.room:
                await self.room.disconnect()
```

### Database Transaction Safety
```python
class DatabaseDriver:
    async def safe_transaction(self, operations: List[Callable]):
        """Execute multiple database operations safely"""
        async with self.connection.begin() as transaction:
            try:
                for operation in operations:
                    await operation()
                await transaction.commit()
            except Exception as e:
                await transaction.rollback()
                logger.error(f"Database transaction failed: {e}")
                raise
    
    async def store_conversation_event(self, event: ConversationEvent):
        """Store event with automatic retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.execute_query(
                    "INSERT INTO conversation_events ...",
                    event.to_dict()
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(0.5 * (2 ** attempt))
```

### WebSocket Connection Management
```javascript
// Frontend error handling
class WebSocketManager {
    constructor(url) {
        this.url = url;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }
    
    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };
        
        this.ws.onclose = (event) => {
            if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.reconnectAttempts++;
                    this.connect();
                }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.handleConnectionError(error);
        };
    }
    
    handleConnectionError(error) {
        // Notify user of connection issues
        // Fall back to polling if WebSocket fails
        this.fallbackToPolling();
    }
}
```

This technical documentation provides a comprehensive deep dive into how the LiveKit AI Call Center system works under the hood, covering all major components, integration patterns, and operational procedures. The system demonstrates sophisticated real-time communication architecture with robust monitoring, recording, and error handling capabilities.
