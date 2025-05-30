# LiveKit AI Call Center - Code Flow Analysis & Integration Details

## Table of Contents
1. [Complete Call Flow Walkthrough](#complete-call-flow-walkthrough)
2. [Recording Pipeline Deep Dive](#recording-pipeline-deep-dive)
3. [Real-time Monitoring Implementation](#real-time-monitoring-implementation)
4. [Admin Dashboard Integration](#admin-dashboard-integration)
5. [Error Recovery Mechanisms](#error-recovery-mechanisms)
6. [WebSocket Communication Patterns](#websocket-communication-patterns)
7. [Database Operations Flow](#database-operations-flow)

## Complete Call Flow Walkthrough

### 1. Customer Initiates Call

#### Frontend: SimpleVoiceAssistant.jsx
```javascript
// Customer clicks "Start Call" button
const handleStartCall = async () => {
    try {
        setIsConnecting(true);
        
        // Request room token from backend
        const response = await fetch('/api/get-token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                roomName: generateRoomName(),
                participantName: customerName || 'Customer'
            })
        });
        
        const { token, roomName } = await response.json();
        
        // Connect to LiveKit room
        await connectToRoom(token, roomName);
        
    } catch (error) {
        console.error('Failed to start call:', error);
        setError('Failed to connect to call center');
    }
};

const connectToRoom = async (token, roomName) => {
    const room = new Room({
        adaptiveStream: true,
        dynacast: true,
        publishDefaults: {
            audioPreset: AudioPresets.music,
            dtx: false, // Disable discontinuous transmission for call center
        },
    });

    // Critical: Set up event handlers BEFORE connecting
    room.on(RoomEvent.Connected, () => {
        console.log('Connected to room:', roomName);
        setIsConnected(true);
        setIsConnecting(false);
    });

    room.on(RoomEvent.TrackSubscribed, handleIncomingAudio);
    room.on(RoomEvent.Disconnected, handleDisconnection);
    room.on(RoomEvent.ParticipantConnected, handleAgentJoined);

    // Connect to room
    await room.connect(LIVEKIT_URL, token, {
        autoSubscribe: true, // Automatically subscribe to agent audio
    });

    setRoom(room);
    
    // Start publishing customer audio
    await enableMicrophone(room);
};
```

### 2. Backend Token Generation

#### API Route: Token Generation
```python
# api.py - Token generation endpoint
@app.post("/api/get-token")
async def get_token(request: TokenRequest):
    """Generate LiveKit access token for customer"""
    try:
        room_name = request.room_name or f"room_{uuid.uuid4()}"
        participant_name = request.participant_name or "Customer"
        
        # Generate customer token
        token = AccessToken(
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET")
        )
        
        token.with_identity(f"customer_{uuid.uuid4()}")
        token.with_name(participant_name)
        token.with_grants(RoomGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))
        
        # Store room info for monitoring
        await store_room_info(room_name, participant_name)
        
        return {
            "token": token.to_jwt(),
            "room_name": room_name,
            "participant_identity": token.identity
        }
        
    except Exception as e:
        logger.error(f"Token generation failed: {e}")
        raise HTTPException(status_code=500, detail="Token generation failed")
```

### 3. Agent Auto-Assignment

#### LiveKit Worker: Room Assignment
```python
# enhanced_agent_fixed.py - Worker entrypoint
async def entrypoint(ctx: JobContext):
    """Main entrypoint when agent is assigned to a room"""
    
    logger.info(f"Agent assigned to room: {ctx.room.name}")
    
    # Connect to room with audio-only subscription
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Initialize enhanced agent with full capabilities
    agent = EnhancedAgent(
        vad=silero.VAD.load(
            # Optimized for phone calls
            aggressiveness=2,
            min_silence_duration=0.8,
            min_speaking_duration=0.3,
        ),
        stt=deepgram.STT(
            # Real-time transcription
            model="nova-2",
            language="en-US",
            smart_format=True,
            interim_results=True,
        ),
        llm=openai.LLM(
            model="gpt-4",
            temperature=0.7,
            # Car dealership specific system prompt
            system_prompt=load_prompt("car_sales_agent"),
        ),
        tts=cartesia.TTS(
            model_id="sonic-english",
            voice_id="a0e99841-438c-4a64-b679-ae501e7d6091",
            # Low latency for real-time conversation
            experimental_real_time=True,
        ),
    )
    
    # Start agent in room
    agent.start(ctx.room)
    
    # Initial greeting
    await agent.say(
        "Hello! Welcome to CME Auto Sales. My name is Sarah, and I'm here to help you find the perfect vehicle. How can I assist you today?"
    )
    
    # Keep agent running
    await asyncio.sleep(0.1)
```

### 4. Audio Track Publication & Recording Start

#### Agent: Audio Track Detection
```python
# EnhancedAgent class - Track publication handler
async def on_track_published(self, publication: RemoteTrackPublication, participant: RemoteParticipant):
    """Critical: Start recording when customer audio is detected"""
    
    if publication.kind == TrackKind.AUDIO and not self._egress_started:
        logger.info(f"Customer audio track detected from {participant.identity}")
        
        # Store track info for recording
        self._recording_track_sid = publication.sid
        
        # Start egress recording immediately
        await self._start_egress_recording()
        
        # Initialize monitoring
        await self.monitor.start_audio_monitoring(publication)
        
        # Notify admin dashboard
        await self._notify_admin_call_started(participant)

async def _start_egress_recording(self):
    """Start LiveKit Egress recording for the room"""
    try:
        if self._egress_started:
            return
        
        egress_client = EgressServiceClient()
        
        # Configure room composite recording
        request = RoomCompositeEgressRequest(
            room_name=self.room.name,
            layout="speaker",  # Focus on active speaker
            audio_only=True,   # Audio-only for call center
            file_outputs=[
                EncodedFileOutput(
                    file_type=EncodedFileType.MP4,
                    filepath=f"recordings/{self.conversation_id}.mp4"
                )
            ],
            # Advanced egress options
            options=RoomCompositeOptions(
                audio_only=True,
                video_only=False,
            )
        )
        
        # Start recording
        response = await egress_client.start_room_composite_egress(request)
        self._egress_id = response.egress_id
        self._egress_started = True
        
        logger.info(f"Recording started - Egress ID: {self._egress_id}")
        
        # Update conversation record
        await self.monitor.update_recording_status("recording", self._egress_id)
        
    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        # Continue without recording rather than failing the call
```

## Recording Pipeline Deep Dive

### 1. Egress Service Integration

#### Egress Configuration & Management
```python
class EgressRecordingManager:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.egress_client = EgressServiceClient()
        self.egress_id = None
        self.recording_status = "pending"
    
    async def start_recording(self, room_name: str) -> str:
        """Start egress recording with comprehensive configuration"""
        
        # Build recording request
        request = RoomCompositeEgressRequest(
            room_name=room_name,
            layout="speaker",
            audio_only=True,
            
            # File output configuration
            file_outputs=[
                EncodedFileOutput(
                    file_type=EncodedFileType.MP4,
                    filepath=f"conversations/{self.conversation_id}.mp4",
                    # Audio-specific encoding
                    audio_codec=AudioCodec.OPUS,
                    audio_bitrate=128,  # High quality for transcription
                )
            ],
            
            # Advanced options
            options=RoomCompositeOptions(
                audio_only=True,
                # Custom layout for call center
                preset=EncodingOptionsPreset.H264_720P_30,
            )
        )
        
        try:
            response = await self.egress_client.start_room_composite_egress(request)
            self.egress_id = response.egress_id
            self.recording_status = "recording"
            
            logger.info(f"Egress recording started: {self.egress_id}")
            return self.egress_id
            
        except Exception as e:
            logger.error(f"Egress start failed: {e}")
            self.recording_status = "failed"
            raise
    
    async def stop_recording(self) -> Optional[str]:
        """Stop egress recording and return file URL"""
        if not self.egress_id:
            return None
        
        try:
            response = await self.egress_client.stop_egress(self.egress_id)
            self.recording_status = "stopped"
            
            # Return download URL for webhook processing
            return response.download_url if response.download_url else None
            
        except Exception as e:
            logger.error(f"Egress stop failed: {e}")
            self.recording_status = "error"
            raise
```

### 2. Webhook Processing for Recording Completion

#### ngrok Tunnel & Webhook Handler
```python
# Webhook endpoint for egress completion
@app.post("/webhook/egress")
async def handle_egress_webhook(webhook_data: dict):
    """Process egress webhook notifications"""
    
    event_type = webhook_data.get("event")
    egress_info = webhook_data.get("egress_info", {})
    
    logger.info(f"Egress webhook received: {event_type}")
    
    if event_type == "egress_ended":
        await process_recording_completion(egress_info)
    elif event_type == "egress_updated":
        await process_recording_update(egress_info)
    
    return {"status": "processed"}

async def process_recording_completion(egress_info: dict):
    """Process completed recording"""
    egress_id = egress_info.get("egress_id")
    room_name = egress_info.get("room_name")
    file_results = egress_info.get("file_results", [])
    
    if not file_results:
        logger.warning(f"No file results for egress {egress_id}")
        return
    
    for file_result in file_results:
        download_url = file_result.get("download_url")
        file_size = file_result.get("size")
        
        if download_url:
            # Download and store in MinIO
            await download_and_store_recording(
                download_url, 
                egress_id, 
                room_name,
                file_size
            )

async def download_and_store_recording(
    download_url: str, 
    egress_id: str, 
    room_name: str,
    file_size: int
):
    """Download recording from LiveKit and store in MinIO"""
    
    try:
        # Download file from LiveKit
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    file_content = await response.read()
                    
                    # Upload to MinIO
                    minio_client = Minio(
                        os.getenv("MINIO_ENDPOINT"),
                        access_key=os.getenv("MINIO_ACCESS_KEY"),
                        secret_key=os.getenv("MINIO_SECRET_KEY"),
                        secure=False
                    )
                    
                    bucket_name = "call-recordings"
                    object_name = f"conversations/{egress_id}.mp4"
                    
                    # Upload with metadata
                    minio_client.put_object(
                        bucket_name,
                        object_name,
                        io.BytesIO(file_content),
                        length=len(file_content),
                        content_type="video/mp4",
                        metadata={
                            "egress-id": egress_id,
                            "room-name": room_name,
                            "original-size": str(file_size),
                            "upload-timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    
                    # Update database
                    await update_conversation_recording(egress_id, object_name)
                    
                    logger.info(f"Recording stored: {object_name}")
                    
    except Exception as e:
        logger.error(f"Recording storage failed: {e}")
```

### 3. MinIO Storage Management

#### Storage Client with Lifecycle Management
```python
class RecordingStorageManager:
    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )
        self.bucket_name = "call-recordings"
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Ensure recording bucket exists"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                
                # Set lifecycle policy for old recordings
                lifecycle_config = {
                    "Rules": [
                        {
                            "ID": "DeleteOldRecordings",
                            "Status": "Enabled",
                            "Expiration": {"Days": 365},  # Keep for 1 year
                            "Filter": {"Prefix": "conversations/"}
                        }
                    ]
                }
                self.client.set_bucket_lifecycle(self.bucket_name, lifecycle_config)
                
        except Exception as e:
            logger.error(f"Bucket setup failed: {e}")
    
    async def store_recording(
        self, 
        file_data: bytes, 
        conversation_id: str,
        metadata: dict = None
    ) -> str:
        """Store recording with metadata"""
        
        object_name = f"conversations/{conversation_id}.mp4"
        
        # Prepare metadata
        storage_metadata = {
            "conversation-id": conversation_id,
            "upload-timestamp": datetime.utcnow().isoformat(),
            "content-type": "audio/mp4"
        }
        
        if metadata:
            storage_metadata.update(metadata)
        
        # Upload to MinIO
        self.client.put_object(
            self.bucket_name,
            object_name,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type="video/mp4",
            metadata=storage_metadata
        )
        
        # Generate presigned URL for access
        url = self.client.presigned_get_object(
            self.bucket_name, 
            object_name, 
            expires=timedelta(hours=24)
        )
        
        return url
    
    def get_recording_url(self, conversation_id: str, expires_hours: int = 24) -> str:
        """Get presigned URL for recording access"""
        object_name = f"conversations/{conversation_id}.mp4"
        
        return self.client.presigned_get_object(
            self.bucket_name,
            object_name,
            expires=timedelta(hours=expires_hours)
        )
```

## Real-time Monitoring Implementation

### 1. Streaming Conversation Monitor

#### Core Monitoring Class
```python
# streaming_conversation_monitor_fixed.py
class StreamingConversationMonitor(ConversationMonitor):
    def __init__(self, conversation_id: str):
        super().__init__(conversation_id)
        self.websocket_manager = AdminWebSocketManager()
        self.audio_streamer = AudioStreamer()
        self.transcript_buffer = []
        self.is_streaming = False
    
    async def start_real_time_monitoring(self):
        """Begin real-time monitoring with WebSocket broadcasting"""
        self.is_streaming = True
        
        # Start background tasks
        asyncio.create_task(self._stream_audio_to_admins())
        asyncio.create_task(self._broadcast_transcripts())
        asyncio.create_task(self._monitor_conversation_health())
        
        logger.info(f"Real-time monitoring started for {self.conversation_id}")
    
    async def handle_speech_event(self, event: SpeechEvent):
        """Process speech events with real-time broadcasting"""
        
        if event.type == SpeechEventType.INTERIM_TRANSCRIPT:
            # Broadcast interim results immediately
            await self.websocket_manager.broadcast_to_admins({
                "type": "interim_transcript",
                "conversation_id": self.conversation_id,
                "speaker": event.speaker,
                "text": event.alternatives[0].text,
                "confidence": event.alternatives[0].confidence,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        elif event.type == SpeechEventType.FINAL_TRANSCRIPT:
            # Store final transcript and broadcast
            transcript_event = ConversationEvent(
                timestamp=datetime.utcnow(),
                speaker=event.speaker,
                content=event.alternatives[0].text,
                confidence=event.alternatives[0].confidence,
                is_final=True,
                event_type="speech"
            )
            
            await self.log_event(transcript_event)
            
            await self.websocket_manager.broadcast_to_admins({
                "type": "final_transcript",
                "conversation_id": self.conversation_id,
                "event": transcript_event.to_dict()
            })
    
    async def _stream_audio_to_admins(self):
        """Stream live audio to admin dashboards"""
        while self.is_streaming:
            try:
                # Get audio chunks from room
                audio_chunk = await self.audio_streamer.get_next_chunk()
                
                if audio_chunk:
                    # Broadcast to connected admin clients
                    await self.websocket_manager.broadcast_audio_chunk(
                        self.conversation_id,
                        audio_chunk
                    )
                
                # Small delay to prevent overwhelming clients
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Audio streaming error: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_conversation_health(self):
        """Monitor conversation health and send alerts"""
        silence_start = None
        
        while self.is_streaming:
            try:
                # Check for prolonged silence
                last_activity = self.get_last_activity_time()
                silence_duration = (datetime.utcnow() - last_activity).total_seconds()
                
                if silence_duration > 30:  # 30 seconds of silence
                    if not silence_start:
                        silence_start = datetime.utcnow()
                        
                        # Alert admins of prolonged silence
                        await self.websocket_manager.broadcast_to_admins({
                            "type": "silence_alert",
                            "conversation_id": self.conversation_id,
                            "duration": silence_duration,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                else:
                    silence_start = None
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
```

### 2. WebSocket Management for Admin Dashboards

#### WebSocket Manager Implementation
```python
class AdminWebSocketManager:
    def __init__(self):
        self.admin_connections = {}  # admin_id -> websocket
        self.conversation_subscriptions = defaultdict(set)  # conversation_id -> set of admin_ids
    
    async def register_admin(self, admin_id: str, websocket: WebSocket):
        """Register admin WebSocket connection"""
        await websocket.accept()
        self.admin_connections[admin_id] = websocket
        
        # Send current active conversations
        active_conversations = await self.get_active_conversations()
        await websocket.send_json({
            "type": "initial_state",
            "conversations": active_conversations
        })
        
        logger.info(f"Admin {admin_id} connected")
    
    async def subscribe_to_conversation(self, admin_id: str, conversation_id: str):
        """Subscribe admin to specific conversation updates"""
        self.conversation_subscriptions[conversation_id].add(admin_id)
        
        # Send conversation history
        history = await self.get_conversation_history(conversation_id)
        
        if admin_id in self.admin_connections:
            await self.admin_connections[admin_id].send_json({
                "type": "conversation_history",
                "conversation_id": conversation_id,
                "history": history
            })
    
    async def broadcast_to_admins(self, message: dict):
        """Broadcast message to all relevant admin connections"""
        conversation_id = message.get("conversation_id")
        
        # Determine target admins
        if conversation_id:
            target_admins = self.conversation_subscriptions.get(conversation_id, set())
        else:
            target_admins = set(self.admin_connections.keys())
        
        # Send to target admins
        disconnected_admins = []
        for admin_id in target_admins:
            if admin_id in self.admin_connections:
                try:
                    await self.admin_connections[admin_id].send_json(message)
                except (ConnectionClosed, WebSocketDisconnect):
                    disconnected_admins.append(admin_id)
        
        # Clean up disconnected admins
        for admin_id in disconnected_admins:
            await self.remove_admin(admin_id)
    
    async def broadcast_audio_chunk(self, conversation_id: str, audio_chunk: bytes):
        """Broadcast audio chunk to subscribed admins"""
        target_admins = self.conversation_subscriptions.get(conversation_id, set())
        
        # Encode audio chunk for WebSocket transmission
        encoded_chunk = base64.b64encode(audio_chunk).decode('utf-8')
        
        message = {
            "type": "audio_chunk",
            "conversation_id": conversation_id,
            "audio_data": encoded_chunk,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for admin_id in target_admins:
            if admin_id in self.admin_connections:
                try:
                    await self.admin_connections[admin_id].send_json(message)
                except:
                    # Skip failed connections, cleanup happens elsewhere
                    pass
    
    async def remove_admin(self, admin_id: str):
        """Remove admin and clean up subscriptions"""
        if admin_id in self.admin_connections:
            del self.admin_connections[admin_id]
        
        # Remove from all conversation subscriptions
        for conversation_id in list(self.conversation_subscriptions.keys()):
            self.conversation_subscriptions[conversation_id].discard(admin_id)
            
            # Clean up empty subscription sets
            if not self.conversation_subscriptions[conversation_id]:
                del self.conversation_subscriptions[conversation_id]
```

## Admin Dashboard Integration

### 1. Audio Monitor Component

#### React Audio Streaming Component
```javascript
// AudioMonitor.js - Real-time audio monitoring
import React, { useEffect, useRef, useState } from 'react';
import { Room, RoomEvent, Track } from 'livekit-client';

const AudioMonitor = ({ conversationId, onAudioLevel }) => {
    const [room, setRoom] = useState(null);
    const [isListening, setIsListening] = useState(false);
    const [audioLevel, setAudioLevel] = useState(0);
    const audioRef = useRef(null);
    const audioContextRef = useRef(null);
    const analyzerRef = useRef(null);
    
    useEffect(() => {
        if (conversationId && isListening) {
            connectToRoom();
        }
        
        return () => {
            if (room) {
                room.disconnect();
            }
        };
    }, [conversationId, isListening]);
    
    const connectToRoom = async () => {
        try {
            // Get admin token for monitoring
            const response = await fetch('/api/admin/get-monitor-token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    conversationId,
                    adminId: 'admin_123' // Get from auth context
                })
            });
            
            const { token, roomName } = await response.json();
            
            // Connect as hidden monitoring participant
            const newRoom = new Room({
                publishDefaults: {
                    videoCodec: 'none', // Audio only
                },
                adaptiveStream: false, // Consistent quality for monitoring
            });
            
            // Set up audio monitoring
            newRoom.on(RoomEvent.TrackSubscribed, handleTrackSubscribed);
            newRoom.on(RoomEvent.Connected, () => {
                console.log('Admin connected to room for monitoring');
            });
            
            await newRoom.connect(LIVEKIT_URL, token, {
                autoSubscribe: true,
            });
            
            setRoom(newRoom);
            
        } catch (error) {
            console.error('Failed to connect for monitoring:', error);
        }
    };
    
    const handleTrackSubscribed = (track, publication, participant) => {
        if (track.kind === Track.Kind.Audio) {
            // Attach audio track
            track.attach(audioRef.current);
            
            // Set up audio level monitoring
            setupAudioAnalysis(track);
        }
    };
    
    const setupAudioAnalysis = (audioTrack) => {
        // Create audio context for level analysis
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const analyzer = audioContext.createAnalyser();
        
        // Connect track to analyzer
        const source = audioContext.createMediaStreamSource(audioTrack.mediaStream);
        source.connect(analyzer);
        
        analyzer.fftSize = 256;
        const bufferLength = analyzer.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        audioContextRef.current = audioContext;
        analyzerRef.current = analyzer;
        
        // Start level monitoring
        const updateAudioLevel = () => {
            if (analyzer) {
                analyzer.getByteFrequencyData(dataArray);
                
                // Calculate RMS level
                let sum = 0;
                for (let i = 0; i < bufferLength; i++) {
                    sum += dataArray[i] * dataArray[i];
                }
                const rms = Math.sqrt(sum / bufferLength);
                const level = Math.min(rms / 128, 1); // Normalize to 0-1
                
                setAudioLevel(level);
                onAudioLevel?.(level);
                
                requestAnimationFrame(updateAudioLevel);
            }
        };
        
        updateAudioLevel();
    };
    
    const toggleListening = () => {
        setIsListening(!isListening);
        
        if (isListening && room) {
            room.disconnect();
            setRoom(null);
        }
    };
    
    return (
        <div className="audio-monitor">
            <audio ref={audioRef} style={{ display: 'none' }} autoPlay />
            
            <div className="monitor-controls">
                <button 
                    onClick={toggleListening}
                    className={`listen-btn ${isListening ? 'active' : ''}`}
                >
                    {isListening ? 'Stop Listening' : 'Start Listening'}
                </button>
                
                <div className="audio-level-indicator">
                    <div 
                        className="level-bar"
                        style={{ 
                            width: `${audioLevel * 100}%`,
                            backgroundColor: audioLevel > 0.7 ? '#ff4444' : '#44ff44'
                        }}
                    />
                </div>
            </div>
            
            <div className="audio-info">
                <span>Audio Level: {Math.round(audioLevel * 100)}%</span>
            </div>
        </div>
    );
};

export default AudioMonitor;
```

### 2. Real-time Transcript Display

#### Transcript Component with Live Updates
```javascript
// TranscriptViewer.js
const TranscriptViewer = ({ conversationId }) => {
    const [transcript, setTranscript] = useState([]);
    const [interimText, setInterimText] = useState('');
    const [wsConnection, setWsConnection] = useState(null);
    const transcriptEndRef = useRef(null);
    
    useEffect(() => {
        // Establish WebSocket connection for real-time updates
        const connectWebSocket = () => {
            const ws = new WebSocket(`${WS_URL}/admin/conversation/${conversationId}`);
            
            ws.onopen = () => {
                console.log('WebSocket connected for transcript monitoring');
                setWsConnection(ws);
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = () => {
                console.log('WebSocket disconnected, attempting reconnect...');
                setTimeout(connectWebSocket, 3000); // Reconnect after 3 seconds
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        };
        
        connectWebSocket();
        
        return () => {
            if (wsConnection) {
                wsConnection.close();
            }
        };
    }, [conversationId]);
    
    const handleWebSocketMessage = (data) => {
        switch (data.type) {
            case 'interim_transcript':
                setInterimText(data.text);
                break;
                
            case 'final_transcript':
                // Add final transcript to history
                setTranscript(prev => [...prev, {
                    id: Date.now(),
                    timestamp: data.event.timestamp,
                    speaker: data.event.speaker,
                    content: data.event.content,
                    confidence: data.event.confidence,
                    isFinal: true
                }]);
                
                // Clear interim text
                setInterimText('');
                break;
                
            case 'conversation_history':
                // Load existing transcript history
                setTranscript(data.history.map(event => ({
                    id: event.id || Date.now(),
                    timestamp: event.timestamp,
                    speaker: event.speaker,
                    content: event.content,
                    confidence: event.confidence,
                    isFinal: true
                })));
                break;
                
            case 'silence_alert':
                // Show silence alert
                setTranscript(prev => [...prev, {
                    id: Date.now(),
                    timestamp: data.timestamp,
                    speaker: 'system',
                    content: `⚠️ Prolonged silence detected (${Math.round(data.duration)}s)`,
                    confidence: 1.0,
                    isFinal: true,
                    isAlert: true
                }]);
                break;
        }
    };
    
    // Auto-scroll to bottom when new content arrives
    useEffect(() => {
        transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [transcript, interimText]);
    
    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };
    
    const getSpeakerStyle = (speaker) => {
        const styles = {
            customer: { color: '#2196F3', fontWeight: 'bold' },
            assistant: { color: '#4CAF50', fontWeight: 'bold' },
            system: { color: '#FF9800', fontStyle: 'italic' }
        };
        return styles[speaker] || { color: '#666' };
    };
    
    return (
        <div className="transcript-viewer">
            <div className="transcript-header">
                <h3>Live Transcript</h3>
                <div className="connection-status">
                    <span className={`status-indicator ${wsConnection ? 'connected' : 'disconnected'}`} />
                    {wsConnection ? 'Connected' : 'Disconnected'}
                </div>
            </div>
            
            <div className="transcript-content">
                {transcript.map((entry) => (
                    <div 
                        key={entry.id} 
                        className={`transcript-entry ${entry.isAlert ? 'alert' : ''}`}
                    >
                        <div className="entry-header">
                            <span 
                                className="speaker"
                                style={getSpeakerStyle(entry.speaker)}
                            >
                                {entry.speaker.charAt(0).toUpperCase() + entry.speaker.slice(1)}
                            </span>
                            <span className="timestamp">
                                {formatTimestamp(entry.timestamp)}
                            </span>
                            <span className="confidence">
                                {Math.round(entry.confidence * 100)}%
                            </span>
                        </div>
                        <div className="entry-content">
                            {entry.content}
                        </div>
                    </div>
                ))}
                
                {/* Show interim results */}
                {interimText && (
                    <div className="transcript-entry interim">
                        <div className="entry-header">
                            <span className="speaker" style={{ color: '#999' }}>
                                Customer (interim)
                            </span>
                        </div>
                        <div className="entry-content interim-text">
                            {interimText}
                        </div>
                    </div>
                )}
                
                <div ref={transcriptEndRef} />
            </div>
        </div>
    );
};

export default TranscriptViewer;
```

This comprehensive documentation covers the complete technical architecture, implementation patterns, and code flows of the LiveKit AI Call Center system. It provides detailed insights into how each component works, how they integrate together, and the specific patterns used for real-time communication, monitoring, and recording.
