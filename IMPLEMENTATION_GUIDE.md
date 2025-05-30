# LiveKit AI Call Center - Implementation Guide & Code Patterns

## Table of Contents
1. [Agent Implementation Patterns](#agent-implementation-patterns)
2. [Audio Processing Pipeline](#audio-processing-pipeline)
3. [State Management Strategies](#state-management-strategies)
4. [Integration Patterns](#integration-patterns)
5. [Performance Optimizations](#performance-optimizations)
6. [Debugging & Troubleshooting](#debugging--troubleshooting)
7. [Deployment Considerations](#deployment-considerations)

## Agent Implementation Patterns

### Enhanced Agent Architecture

The `EnhancedAgent` class demonstrates sophisticated patterns for building AI voice agents:

#### Core Agent Structure
```python
class EnhancedAgent(VoiceAssistant):
    """Enhanced AI agent with recording, monitoring, and vehicle lookup capabilities"""
    
    def __init__(self, *, vad: silero.VAD, stt: STT, llm: LLM, tts: TTS):
        super().__init__(vad=vad, stt=stt, llm=llm, tts=tts)
        
        # Unique conversation tracking
        self.conversation_id = str(uuid.uuid4())
        self.monitor = ConversationMonitor(self.conversation_id)
        
        # Recording state management
        self._egress_started = False
        self._recording_track_sid = None
        self._egress_id = None
        
        # Conversation state
        self._conversation_started = False
        self._customer_name = None
        self._vehicle_info = {}
```

#### Event-Driven Architecture
The agent uses event handlers to respond to various LiveKit events:

```python
async def on_track_published(self, publication: RemoteTrackPublication, participant: RemoteParticipant):
    """Handle audio track publication - key for starting recording"""
    if publication.kind == TrackKind.AUDIO and not self._egress_started:
        logger.info(f"Audio track published by {participant.identity}, starting recording")
        await self._start_egress_recording()
        self._recording_track_sid = publication.sid

async def on_participant_connected(self, participant: RemoteParticipant):
    """Handle new participant connections"""
    logger.info(f"Participant connected: {participant.identity}")
    await self.monitor.log_participant_joined(participant.identity)

async def on_participant_disconnected(self, participant: RemoteParticipant):
    """Handle participant disconnections and cleanup"""
    logger.info(f"Participant disconnected: {participant.identity}")
    await self.monitor.log_participant_left(participant.identity)
    
    # Stop recording when customer leaves
    if not participant.identity.startswith("agent_"):
        await self._stop_recording_if_active()
```

### LLM Integration Patterns

#### Function Calling for Vehicle Lookup
```python
class VehicleLookupFunction(FunctionContext):
    """Function for looking up vehicle information by VIN"""
    
    @llm.ai_callable(description="Look up vehicle information using VIN number")
    async def lookup_vehicle_by_vin(self, vin: str) -> str:
        """
        Look up vehicle information by VIN number.
        
        Args:
            vin: The Vehicle Identification Number (17 characters)
            
        Returns:
            String containing vehicle information or error message
        """
        try:
            # Validate VIN format
            if len(vin) != 17:
                return "Invalid VIN number. VIN must be exactly 17 characters."
            
            # Call vehicle lookup API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8001/api/lookup-vehicle",
                    json={"vin": vin}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("found"):
                            self._vehicle_info = data
                            return f"Vehicle found: {data['year']} {data['make']} {data['model']}"
                        else:
                            return "Vehicle not found in our database."
                    else:
                        return "Error looking up vehicle information."
                        
        except Exception as e:
            logger.error(f"Vehicle lookup error: {e}")
            return "Sorry, there was an error looking up that vehicle."
```

#### Conversation Flow Management
```python
async def handle_user_speech(self, user_speech: str):
    """Process user speech and manage conversation flow"""
    
    # Log the customer's speech
    await self.monitor.log_event(ConversationEvent(
        timestamp=datetime.utcnow(),
        speaker="customer",
        content=user_speech,
        confidence=1.0,
        is_final=True,
        event_type="speech"
    ))
    
    # Update conversation context
    if not self._conversation_started:
        self._conversation_started = True
        await self.monitor.update_status("active")
    
    # Extract customer name if not already known
    if not self._customer_name:
        name_match = re.search(r"my name is (\w+)", user_speech.lower())
        if name_match:
            self._customer_name = name_match.group(1)
            await self.monitor.update_metadata({"customer_name": self._customer_name})
```

## Audio Processing Pipeline

### Voice Activity Detection (VAD)

The system uses Silero VAD for sophisticated voice activity detection:

```python
async def setup_vad(self):
    """Configure Voice Activity Detection"""
    vad = silero.VAD.load(
        # Aggressive VAD for noisy environments
        aggressiveness=3,
        # Quick response time
        min_silence_duration=0.5,
        # Prevent cutting off speech
        min_speaking_duration=0.3,
        # Handle phone call audio quality
        sample_rate=16000
    )
    return vad
```

### Speech-to-Text Configuration

#### Azure Speech Services Setup
```python
class AzureSTTProvider:
    def __init__(self):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.getenv("AZURE_SPEECH_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION")
        )
        
        # Optimize for phone calls
        self.speech_config.speech_recognition_language = "en-US"
        self.speech_config.enable_dictation()
        self.speech_config.request_word_level_timestamps()
        
        # Handle background noise
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EnableAudioLogging,
            "false"
        )
        
    async def create_recognizer(self, audio_stream):
        """Create speech recognizer with real-time capabilities"""
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        
        # Set up event handlers for real-time processing
        recognizer.recognizing.connect(self.handle_interim_result)
        recognizer.recognized.connect(self.handle_final_result)
        recognizer.session_stopped.connect(self.handle_session_stopped)
        
        return recognizer
```

### Text-to-Speech Optimization

#### Cartesia TTS Configuration
```python
class OptimizedTTS:
    def __init__(self):
        self.tts = cartesia.TTS(
            # Low-latency voice model
            model_id="sonic-english",
            # Optimized for phone calls
            voice_id="a0e99841-438c-4a64-b679-ae501e7d6091",
            # High quality audio
            sample_rate=24000,
            # Minimal buffering for real-time
            buffer_size=1024
        )
    
    async def synthesize_with_emotion(self, text: str, emotion: str = "friendly"):
        """Synthesize speech with emotional context"""
        # Add emotional markers to text
        emotional_text = self.add_emotional_markers(text, emotion)
        
        # Generate audio with streaming
        audio_stream = await self.tts.synthesize_stream(emotional_text)
        return audio_stream
    
    def add_emotional_markers(self, text: str, emotion: str) -> str:
        """Add SSML markers for emotional speech"""
        ssml_emotions = {
            "friendly": "<prosody rate='medium' pitch='+2st'>",
            "concerned": "<prosody rate='slow' pitch='-1st'>",
            "excited": "<prosody rate='fast' pitch='+3st'>",
        }
        
        marker = ssml_emotions.get(emotion, "")
        return f"<speak>{marker}{text}</prosody></speak>" if marker else text
```

## State Management Strategies

### Conversation State Tracking

#### State Machine Implementation
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

class ConversationState(Enum):
    INITIALIZING = "initializing"
    GREETING = "greeting"
    INFORMATION_GATHERING = "information_gathering"
    VEHICLE_LOOKUP = "vehicle_lookup"
    PROVIDING_DETAILS = "providing_details"
    CLOSING = "closing"
    ENDED = "ended"

@dataclass
class ConversationContext:
    state: ConversationState
    customer_name: Optional[str] = None
    contact_info: Dict[str, str] = None
    vehicle_interest: Dict[str, Any] = None
    vin_requests: List[str] = None
    follow_up_needed: bool = False
    
    def __post_init__(self):
        if self.contact_info is None:
            self.contact_info = {}
        if self.vehicle_interest is None:
            self.vehicle_interest = {}
        if self.vin_requests is None:
            self.vin_requests = []

class ConversationStateMachine:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.context = ConversationContext(state=ConversationState.INITIALIZING)
        self.state_handlers = {
            ConversationState.GREETING: self.handle_greeting,
            ConversationState.INFORMATION_GATHERING: self.handle_info_gathering,
            ConversationState.VEHICLE_LOOKUP: self.handle_vehicle_lookup,
            # ... other handlers
        }
    
    async def transition_to(self, new_state: ConversationState, **kwargs):
        """Transition to new state with validation"""
        logger.info(f"State transition: {self.context.state} -> {new_state}")
        
        # Validate transition
        if not self.is_valid_transition(self.context.state, new_state):
            logger.warning(f"Invalid transition attempted: {self.context.state} -> {new_state}")
            return False
        
        # Update context
        old_state = self.context.state
        self.context.state = new_state
        
        # Update context with provided data
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
        
        # Execute state handler
        if new_state in self.state_handlers:
            await self.state_handlers[new_state](old_state)
        
        return True
```

### Database State Persistence

#### SQLite with JSON State Storage
```python
class ConversationStateStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with JSON support"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_states (
                conversation_id TEXT PRIMARY KEY,
                current_state TEXT NOT NULL,
                context_data JSON,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    async def save_state(self, conversation_id: str, context: ConversationContext):
        """Save conversation state to database"""
        conn = sqlite3.connect(self.db_path)
        try:
            context_json = json.dumps(asdict(context), default=str)
            conn.execute("""
                INSERT OR REPLACE INTO conversation_states 
                (conversation_id, current_state, context_data, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (conversation_id, context.state.value, context_json))
            conn.commit()
        finally:
            conn.close()
    
    async def load_state(self, conversation_id: str) -> Optional[ConversationContext]:
        """Load conversation state from database"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT current_state, context_data FROM conversation_states 
                WHERE conversation_id = ?
            """, (conversation_id,))
            
            row = cursor.fetchone()
            if row:
                state_str, context_json = row
                context_data = json.loads(context_json)
                context_data['state'] = ConversationState(state_str)
                return ConversationContext(**context_data)
            
            return None
        finally:
            conn.close()
```

## Integration Patterns

### Microservices Communication

#### Vehicle API Integration
```python
class VehicleAPIClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={"Content-Type": "application/json"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def lookup_vehicle(self, vin: str) -> VehicleLookupResponse:
        """Lookup vehicle with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self.session.post(
                    f"{self.base_url}/api/lookup-vehicle",
                    json={"vin": vin}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return VehicleLookupResponse.from_dict(data)
                    elif response.status == 404:
                        return VehicleLookupResponse(found=False)
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

#### Event-Driven Communication
```python
class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type"""
        self.subscribers[event_type].append(handler)
    
    async def publish(self, event_type: str, data: Any):
        """Publish event to all subscribers"""
        handlers = self.subscribers.get(event_type, [])
        
        # Execute all handlers concurrently
        tasks = [handler(data) for handler in handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Usage in agent
class EnhancedAgent(VoiceAssistant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_bus = EventBus()
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Set up event handlers"""
        self.event_bus.subscribe("vehicle_lookup", self.handle_vehicle_lookup_event)
        self.event_bus.subscribe("customer_info_updated", self.handle_customer_info_event)
        self.event_bus.subscribe("conversation_ended", self.handle_conversation_end_event)
    
    async def handle_vehicle_lookup_event(self, data):
        """Handle vehicle lookup completion"""
        if data.get("found"):
            await self.say(f"I found that vehicle: {data['year']} {data['make']} {data['model']}")
        else:
            await self.say("I couldn't find that vehicle in our system.")
```

## Performance Optimizations

### Audio Processing Optimizations

#### Buffering and Streaming
```python
class OptimizedAudioProcessor:
    def __init__(self, buffer_size: int = 4096):
        self.buffer_size = buffer_size
        self.audio_queue = asyncio.Queue(maxsize=100)
        self.processing_task = None
    
    async def start_processing(self):
        """Start audio processing in background"""
        self.processing_task = asyncio.create_task(self._process_audio_stream())
    
    async def _process_audio_stream(self):
        """Process audio in chunks to reduce latency"""
        while True:
            try:
                # Get audio chunk with timeout
                chunk = await asyncio.wait_for(
                    self.audio_queue.get(), 
                    timeout=1.0
                )
                
                # Process chunk
                await self._process_chunk(chunk)
                
            except asyncio.TimeoutError:
                # No audio received, continue listening
                continue
            except Exception as e:
                logger.error(f"Audio processing error: {e}")
    
    async def add_audio_chunk(self, chunk: bytes):
        """Add audio chunk to processing queue"""
        try:
            self.audio_queue.put_nowait(chunk)
        except asyncio.QueueFull:
            # Drop oldest chunk if queue is full
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.put_nowait(chunk)
            except asyncio.QueueEmpty:
                pass
```

### Database Connection Pooling
```python
class DatabasePool:
    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self.pool = asyncio.Queue(maxsize=max_connections)
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        for _ in range(self.max_connections):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            self.pool.put_nowait(conn)
    
    async def get_connection(self):
        """Get connection from pool"""
        return await self.pool.get()
    
    async def return_connection(self, conn):
        """Return connection to pool"""
        await self.pool.put(conn)
    
    @asynccontextmanager
    async def connection(self):
        """Context manager for database connections"""
        conn = await self.get_connection()
        try:
            yield conn
        finally:
            await self.return_connection(conn)
```

### Memory Management
```python
class MemoryOptimizedAgent(EnhancedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conversation_buffer_size = 50  # Keep last 50 messages
        self.audio_chunk_cache = {}
        self.cache_cleanup_interval = 300  # 5 minutes
        
        # Start background cleanup
        asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Periodic memory cleanup"""
        while True:
            try:
                # Clean up old conversation events
                if len(self.monitor.events) > self.conversation_buffer_size:
                    # Keep most recent events
                    self.monitor.events = self.monitor.events[-self.conversation_buffer_size:]
                
                # Clean up audio cache
                current_time = time.time()
                expired_keys = [
                    key for key, (data, timestamp) in self.audio_chunk_cache.items()
                    if current_time - timestamp > self.cache_cleanup_interval
                ]
                
                for key in expired_keys:
                    del self.audio_chunk_cache[key]
                
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
```

## Debugging & Troubleshooting

### Comprehensive Logging
```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

class AgentLogger:
    def __init__(self, conversation_id: str):
        self.logger = structlog.get_logger().bind(conversation_id=conversation_id)
    
    def log_event(self, event_type: str, **kwargs):
        """Log structured event"""
        self.logger.info(f"Agent event: {event_type}", **kwargs)
    
    def log_error(self, error: Exception, context: dict = None):
        """Log error with context"""
        self.logger.error(
            "Agent error occurred",
            error=str(error),
            error_type=type(error).__name__,
            context=context or {}
        )
```

### Health Check Endpoints
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    checks = {}
    
    # Database connectivity
    try:
        async with DatabasePool().connection() as conn:
            cursor = conn.execute("SELECT 1")
            checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"
    
    # LiveKit connectivity
    try:
        room_service = RoomServiceClient()
        await room_service.list_rooms()
        checks["livekit"] = "healthy"
    except Exception as e:
        checks["livekit"] = f"unhealthy: {e}"
    
    # MinIO connectivity
    try:
        minio_client = Minio(os.getenv("MINIO_ENDPOINT"))
        minio_client.list_buckets()
        checks["storage"] = "healthy"
    except Exception as e:
        checks["storage"] = f"unhealthy: {e}"
    
    overall_health = "healthy" if all(
        "healthy" in status for status in checks.values()
    ) else "unhealthy"
    
    return {
        "status": overall_health,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Performance Monitoring
```python
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log performance metrics
            logger.info(
                f"Function {func.__name__} completed",
                execution_time=execution_time,
                args_count=len(args),
                kwargs_count=len(kwargs)
            )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed",
                execution_time=execution_time,
                error=str(e)
            )
            raise
    
    return wrapper

# Usage
class EnhancedAgent(VoiceAssistant):
    @monitor_performance
    async def handle_user_speech(self, user_speech: str):
        # Implementation here
        pass
```

## Deployment Considerations

### Docker Configuration
```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash agent
USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "livekit.agents.worker", "backend.enhanced_agent_fixed"]
```

### Environment Configuration
```bash
# Production environment variables
export LIVEKIT_URL="wss://your-livekit-instance.com"
export LIVEKIT_API_KEY="your-api-key"
export LIVEKIT_API_SECRET="your-api-secret"

export OPENAI_API_KEY="your-openai-key"
export AZURE_SPEECH_KEY="your-azure-key"
export AZURE_SPEECH_REGION="your-region"

export MINIO_ENDPOINT="minio:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"

export DATABASE_URL="sqlite:///conversations.db"
export LOG_LEVEL="INFO"
export ENVIRONMENT="production"
```

### Scaling Considerations
```python
# Load balancer configuration for multiple agents
class AgentLoadBalancer:
    def __init__(self):
        self.agents = []
        self.current_index = 0
    
    def add_agent(self, agent_endpoint: str):
        """Add agent to load balancer"""
        self.agents.append(agent_endpoint)
    
    def get_next_agent(self) -> str:
        """Get next available agent using round-robin"""
        if not self.agents:
            raise Exception("No agents available")
        
        agent = self.agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.agents)
        return agent
    
    async def assign_room(self, room_name: str) -> str:
        """Assign room to least loaded agent"""
        # In production, this would check actual agent load
        agent_endpoint = self.get_next_agent()
        
        # Notify agent of room assignment
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{agent_endpoint}/assign-room",
                json={"room_name": room_name}
            )
        
        return agent_endpoint
```

This implementation guide provides detailed patterns and best practices for building production-ready LiveKit AI agents with robust error handling, performance optimization, and scalability considerations.
