"""
Enhanced Streaming Conversation Monitor for LiveKit Agent
========================================================

This module provides advanced streaming-type conversation monitoring with
real-time audio frame analysis, text streaming, and enhanced pipeline monitoring.
"""

import logging
import datetime
import asyncio
import time
from typing import Optional, Dict, Any, List
from livekit.agents import (
    AgentSession,
    ConversationItemAddedEvent,
    UserInputTranscribedEvent,
    SpeechCreatedEvent,
    AgentStateChangedEvent,
    UserStateChangedEvent,
    CloseEvent,
)
from livekit.agents.llm import ChatMessage
from livekit import rtc
import threading
from collections import deque


class StreamingConversationMonitor:
    """
    Advanced conversation monitor with streaming capabilities and audio frame analysis.
    """

    def __init__(
        self,
        session: AgentSession,
        enable_partial_transcripts: bool = True,
        enable_audio_monitoring: bool = True,
        enable_text_streaming: bool = True,
        streaming_buffer_size: int = 50,
    ):
        """
        Initialize the enhanced streaming conversation monitor.

        Args:
            session: The AgentSession to monitor
            enable_partial_transcripts: Whether to log partial (non-final) transcripts
            enable_audio_monitoring: Whether to monitor audio frames and levels
            enable_text_streaming: Whether to enable real-time text streaming
            streaming_buffer_size: Size of the streaming text buffer
        """
        self.session = session
        self.enable_partial_transcripts = enable_partial_transcripts
        self.enable_audio_monitoring = enable_audio_monitoring
        self.enable_text_streaming = enable_text_streaming
        self.streaming_buffer_size = streaming_buffer_size

        # Set up dedicated logger for conversation monitoring
        self.logger = logging.getLogger("streaming_conversation_monitor")
        self.logger.setLevel(logging.INFO)

        # Create a console handler if one doesn't exist
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Create a detailed formatter for conversation logs
            formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(message)s", datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)  # Enhanced state tracking
        self.conversation_count = 0
        self.current_user_transcript = ""
        self.transcript_buffer = deque(maxlen=streaming_buffer_size)
        self.audio_level_history = deque(maxlen=100)
        self.speech_handles: Dict[str, Any] = {}

        # Streaming state
        self.current_streaming_session = None
        self.last_partial_transcript = ""
        self.partial_transcript_count = (
            0  # Agent streaming state for simulated streaming
        )
        self.agent_response_chunks = []
        self.agent_chunk_count = 0
        self.agent_streaming_active = False

        # Audio monitoring state
        self.user_audio_level = 0.0
        self.agent_audio_level = 0.0
        self.audio_monitoring_active = False  # Performance metrics
        self.transcript_latency = []
        self.speech_latency = []

        # Shutdown state tracking
        self.is_shutting_down = False
        self.room_closed = False

        # Register all event handlers
        self._register_event_handlers()
        self._setup_audio_monitoring()

        # Log initialization
        self.logger.info("=" * 100)
        self.logger.info("🚀 ENHANCED STREAMING CONVERSATION MONITOR STARTED")
        self.logger.info(
            f"📊 Features enabled: Partial={enable_partial_transcripts}, Audio={enable_audio_monitoring}, Streaming={enable_text_streaming}"
        )
        self.logger.info("=" * 100)

    def _register_event_handlers(self):
        """Register all event handlers for comprehensive monitoring."""

        @self.session.on("conversation_item_added")
        def on_conversation_item_added(event: ConversationItemAddedEvent):
            self._handle_conversation_item_added(event)

        @self.session.on("user_input_transcribed")
        def on_user_input_transcribed(event: UserInputTranscribedEvent):
            self._handle_user_input_transcribed(event)

        @self.session.on("speech_created")
        def on_speech_created(event: SpeechCreatedEvent):
            self._handle_speech_created(event)

        @self.session.on("agent_state_changed")
        def on_agent_state_changed(event: AgentStateChangedEvent):
            self._handle_agent_state_changed(event)

        @self.session.on("user_state_changed")
        def on_user_state_changed(event: UserStateChangedEvent):
            self._handle_user_state_changed(event)

        @self.session.on("close")
        def on_close(event: CloseEvent):
            self._handle_close(event)

    def _setup_audio_monitoring(self):
        """Set up audio frame monitoring if enabled."""
        if self.enable_audio_monitoring:
            self.audio_monitoring_active = True
            self.logger.info(
                "🎵 AUDIO MONITORING ENABLED - Will track audio levels and frames"
            )

    def _handle_conversation_item_added(self, event: ConversationItemAddedEvent):
        """Handle when a conversation item (user or agent message) is committed to chat history."""
        item: ChatMessage = event.item
        role = item.role
        content = item.text_content
        interrupted = getattr(item, "interrupted", False)
        timestamp = datetime.datetime.now()

        self.conversation_count += 1

        # Add to streaming buffer
        if self.enable_text_streaming:
            self.transcript_buffer.append(
                {
                    "timestamp": timestamp,
                    "role": role,
                    "content": content,
                    "interrupted": interrupted,
                    "type": "final",
                }
            )

        # Format the message based on role with enhanced details
        if role == "user":
            self.logger.info("━" * 100)
            self.logger.info(f"👤 USER MESSAGE #{self.conversation_count} [FINAL]")
            if interrupted:
                self.logger.info(f"⚠️  [INTERRUPTED] {content}")
            else:
                self.logger.info(f"💬 {content}")  # Log streaming metrics
            if self.partial_transcript_count > 0:
                self.logger.info(
                    f"📈 Streaming metrics: {self.partial_transcript_count} partial transcripts processed"
                )
                self.partial_transcript_count = 0
        elif role == "assistant":
            self.logger.info("🔍 ENTERING ASSISTANT BRANCH - Starting debug")
            self.logger.info(
                f"🔍 DEBUG VALUES: enable_text_streaming={self.enable_text_streaming}, content_exists={bool(content)}, interrupted={interrupted}"
            )
            self.logger.info(
                f"🔍 CONTENT PREVIEW: '{content[:50] if content else 'None'}...'"
            )

            # Simulate streaming for agent responses similar to user partial transcripts
            if self.enable_text_streaming and content and not interrupted:
                self.logger.info(
                    "🚀 CONDITION MET - Starting agent streaming simulation..."
                )

                # Try running the streaming simulation directly instead of as a task
                try:
                    self.logger.info("🔄 CALLING _simulate_agent_streaming directly...")
                    # Run synchronously first to see if it works
                    import asyncio

                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If event loop is running, create task
                        task = asyncio.create_task(
                            self._simulate_agent_streaming(content, timestamp)
                        )
                        self.logger.info("✅ Task created successfully")
                    else:
                        # If no loop, run directly
                        asyncio.run(self._simulate_agent_streaming(content, timestamp))
                        self.logger.info("✅ Streaming simulation completed directly")
                except Exception as e:
                    self.logger.error(f"❌ ERROR in streaming: {e}")
                    import traceback

                    self.logger.error(f"❌ TRACEBACK: {traceback.format_exc()}")

                    # Fall back to standard logging
                    self.logger.info("━" * 100)
                    self.logger.info(
                        f"🤖 AGENT RESPONSE #{self.conversation_count} [FINAL - FALLBACK]"
                    )
                    self.logger.info(f"💬 {content}")
                return  # Exit early to avoid duplicate logging
            else:
                # Standard logging for interrupted responses or when streaming is disabled
                self.logger.info(f"🔍 CONDITION NOT MET - Using standard logging")
                self.logger.info(
                    f"🔍 Reasons: streaming_enabled={self.enable_text_streaming}, has_content={bool(content)}, not_interrupted={not interrupted}"
                )
                self.logger.info("━" * 100)
                self.logger.info(
                    f"🤖 AGENT RESPONSE #{self.conversation_count} [FINAL]"
                )
                if interrupted:
                    self.logger.info(f"⚠️  [INTERRUPTED] {content}")
                else:
                    self.logger.info(f"💬 {content}")

        elif role == "system":
            self.logger.info("━" * 100)
            self.logger.info(f"⚙️  SYSTEM MESSAGE #{self.conversation_count}")
            self.logger.info(f"💬 {content}")

        # Log additional content types if present
        for content_item in item.content:
            if hasattr(content_item, "__class__"):
                content_type = content_item.__class__.__name__
                if content_type == "ImageContent":
                    self.logger.info(f"🖼️  [IMAGE CONTENT DETECTED]")
                elif content_type == "AudioContent":
                    self.logger.info(f"🔊 [AUDIO CONTENT DETECTED]")

        # Log audio levels if available
        if self.enable_audio_monitoring and self.audio_level_history:
            avg_level = sum(self.audio_level_history) / len(self.audio_level_history)
            self.logger.info(f"🎚️  Recent audio level average: {avg_level:.2f}")

    def _handle_user_input_transcribed(self, event: UserInputTranscribedEvent):
        """Handle real-time user transcription events with enhanced streaming logging."""
        transcript = event.transcript
        is_final = event.is_final
        timestamp = datetime.datetime.now()

        # Calculate transcript latency if we have previous data
        if hasattr(self, "_last_transcript_time"):
            latency = (timestamp - self._last_transcript_time).total_seconds() * 1000
            self.transcript_latency.append(latency)
        self._last_transcript_time = timestamp

        if is_final:
            # Final transcript - this will likely be followed by conversation_item_added
            self.logger.info(f"🎯 FINAL TRANSCRIPT: {transcript}")
            self.current_user_transcript = transcript

            # Log streaming session summary
            if self.partial_transcript_count > 0:
                avg_latency = (
                    (
                        sum(self.transcript_latency[-10:])
                        / min(10, len(self.transcript_latency))
                    )
                    if self.transcript_latency
                    else 0
                )
                self.logger.info(
                    f"📊 Streaming session complete: {self.partial_transcript_count} partials, avg latency: {avg_latency:.1f}ms"
                )

        elif self.enable_partial_transcripts and transcript.strip():
            # Enhanced partial transcript logging with streaming indicators
            self.partial_transcript_count += 1

            # Calculate streaming speed
            char_difference = len(transcript) - len(self.last_partial_transcript)
            self.last_partial_transcript = transcript

            # Real-time streaming indicator
            streaming_indicator = "🌊" if char_difference > 0 else "⏸️"

            # Add to streaming buffer
            if self.enable_text_streaming:
                self.transcript_buffer.append(
                    {
                        "timestamp": timestamp,
                        "role": "user",
                        "content": transcript,
                        "interrupted": False,
                        "type": "partial",
                        "partial_count": self.partial_transcript_count,
                    }
                )

            # Enhanced logging with streaming metrics
            self.logger.info(
                f"{streaming_indicator} STREAMING #{self.partial_transcript_count:03d}: {transcript}"
            )  # Log character-by-character streaming if very granular
            if char_difference > 0 and char_difference < 5:
                new_chars = transcript[
                    len(self.last_partial_transcript) - char_difference :
                ]
                self.logger.info(f"📝 NEW CHARS: '{new_chars}'")

    async def _simulate_agent_streaming(
        self, content: str, timestamp: datetime.datetime
    ):
        """Simulate agent response streaming similar to user partial transcripts."""
        if not content or not self.enable_text_streaming:
            return

        # Reset streaming state for new agent response
        self.agent_response_chunks = []
        self.agent_chunk_count = 0
        self.agent_streaming_active = True

        try:
            # Log start of agent streaming
            self.logger.info("━" * 100)
            self.logger.info(
                f"🤖 AGENT RESPONSE #{self.conversation_count} [STREAMING]"
            )

            if isinstance(content, list):
                content = " ".join(content)

            # Split content into words for realistic streaming simulation
            words = content.split()

            # Simulate progressive streaming similar to user transcripts
            current_text = ""
            for i, word in enumerate(words):
                if not self.agent_streaming_active:
                    break

                # Add the next word
                if current_text:
                    current_text += " " + word
                else:
                    current_text = word

                self.agent_chunk_count += 1

                # Add to streaming buffer
                self.transcript_buffer.append(
                    {
                        "timestamp": datetime.datetime.now(),
                        "role": "assistant",
                        "content": current_text,
                        "interrupted": False,
                        "type": "agent_streaming",
                        "chunk_count": self.agent_chunk_count,
                    }
                )

                # Log the streaming chunk similar to user transcription format
                streaming_indicator = "🌊"
                self.logger.info(
                    f"{streaming_indicator} AGENT STREAMING #{self.agent_chunk_count:03d}: {current_text}"
                )

                # Small delay to simulate realistic streaming timing
                await asyncio.sleep(
                    0.1 + (len(word) * 0.02)
                )  # Longer words take slightly longer

            # Log completion
            self.logger.info(
                f"🏁 AGENT STREAMING COMPLETE - {self.agent_chunk_count} chunks"
            )
            self.logger.info("━" * 100)
            self.logger.info(f"💬 {content}")

        except Exception as e:
            self.logger.error(f"❌ Error in agent streaming simulation: {e}")
        finally:
            self.agent_streaming_active = False

    def _handle_speech_created(self, event: SpeechCreatedEvent):
        """Handle when agent speech is created with enhanced tracking."""
        user_initiated = event.user_initiated
        source = event.source
        timestamp = datetime.datetime.now()

        # Track speech handle if available
        speech_handle = getattr(event, "speech_handle", None)
        if speech_handle:
            handle_id = id(speech_handle)
            self.speech_handles[handle_id] = {
                "handle": speech_handle,
                "created_at": timestamp,
                "source": source,
                "user_initiated": user_initiated,
            }

            # Monitor speech handle state
            asyncio.create_task(self._monitor_speech_handle(handle_id, speech_handle))

        if user_initiated:
            self.logger.info(f"🗣️  AGENT SPEECH CREATED - Source: {source}")
        else:
            self.logger.info(f"🔄 AUTO SPEECH CREATED - Source: {source}")

        # Log current audio monitoring state
        if self.enable_audio_monitoring:
            self.logger.info(
                f"🎚️  Current audio state - User: {self.user_audio_level:.2f}, Agent: {self.agent_audio_level:.2f}"
            )

    async def _monitor_speech_handle(self, handle_id: str, speech_handle):
        """Monitor speech handle state changes."""
        try:
            start_time = time.time()
            self.logger.info(f"🎬 Speech handle {handle_id} monitoring started")

            # Wait for speech to complete (if handle supports it)
            if hasattr(speech_handle, "wait_for_playout"):
                await speech_handle.wait_for_playout()

            end_time = time.time()
            duration = (end_time - start_time) * 1000
            self.speech_latency.append(duration)

            self.logger.info(
                f"🎬 Speech handle {handle_id} completed - Duration: {duration:.1f}ms"
            )

            # Cleanup
            if handle_id in self.speech_handles:
                del self.speech_handles[handle_id]

        except Exception as e:
            self.logger.warning(f"⚠️  Speech handle monitoring error: {e}")

    def _handle_agent_state_changed(self, event: AgentStateChangedEvent):
        """Handle agent state changes with enhanced logging."""
        old_state = event.old_state
        new_state = event.new_state
        timestamp = datetime.datetime.now()

        state_icons = {
            "initializing": "🔧",
            "listening": "👂",
            "thinking": "🤔",
            "speaking": "🗣️",
        }

        old_icon = state_icons.get(old_state, "❓")
        new_icon = state_icons.get(new_state, "❓")

        self.logger.info(
            f"🔄 AGENT STATE: {old_icon} {old_state} → {new_icon} {new_state}"
        )

        # Log state duration if we have previous state
        if hasattr(self, "_last_agent_state_time"):
            duration = (timestamp - self._last_agent_state_time).total_seconds() * 1000
            self.logger.info(f"⏱️  Previous state duration: {duration:.1f}ms")
        self._last_agent_state_time = timestamp

        # Enhanced state-specific logging
        if new_state == "thinking":
            self.logger.info("🧠 Agent processing user input...")
        elif new_state == "speaking":
            self.logger.info("🎤 Agent speech generation started")
            if self.speech_handles:
                self.logger.info(
                    f"📞 Active speech handles: {len(self.speech_handles)}"
                )

    def _handle_user_state_changed(self, event: UserStateChangedEvent):
        """Handle user state changes with enhanced audio monitoring."""
        old_state = event.old_state
        new_state = event.new_state
        timestamp = datetime.datetime.now()

        state_icons = {"speaking": "🎤", "listening": "👂"}

        old_icon = state_icons.get(old_state, "❓")
        new_icon = state_icons.get(new_state, "❓")

        self.logger.info(
            f"🔄 USER STATE: {old_icon} {old_state} → {new_icon} {new_state}"
        )

        # Enhanced state tracking
        if new_state == "speaking":
            self.logger.info("🎙️  User started speaking - Audio input detected")
            self._reset_streaming_session()
        elif new_state == "listening":
            self.logger.info("🔇 User stopped speaking - Audio input ended")
            if self.partial_transcript_count > 0:
                self.logger.info(
                    f"📋 Streaming session ended: {self.partial_transcript_count} partial transcripts processed"
                )

    def _reset_streaming_session(self):
        """Reset streaming session state."""
        self.partial_transcript_count = 0
        self.last_partial_transcript = ""
        self.current_streaming_session = datetime.datetime.now()

    def _handle_close(self, event: CloseEvent):
        """Handle session close with enhanced metrics."""
        self.is_shutting_down = True
        self.room_closed = True
        self.audio_monitoring_active = False

        self.logger.info("🔚 SESSION CLOSING...")

        # Log session metrics
        self._log_session_metrics()

        if hasattr(event, "error") and event.error:
            self.logger.error(f"❌ Session closed with error: {event.error}")
        self.log_session_end()

    def _log_session_metrics(self):
        """Log comprehensive session metrics."""
        self.logger.info("📊 SESSION METRICS:")

        # Transcript metrics
        if self.transcript_latency:
            avg_transcript_latency = sum(self.transcript_latency) / len(
                self.transcript_latency
            )
            self.logger.info(
                f"   📝 Avg transcript latency: {avg_transcript_latency:.1f}ms"
            )
            self.logger.info(
                f"   📝 Total transcripts processed: {len(self.transcript_latency)}"
            )

        # Speech metrics
        if self.speech_latency:
            avg_speech_latency = sum(self.speech_latency) / len(self.speech_latency)
            self.logger.info(f"   🗣️  Avg speech duration: {avg_speech_latency:.1f}ms")
            self.logger.info(
                f"   🗣️  Total speeches generated: {len(self.speech_latency)}"
            )

        # Buffer metrics
        if self.enable_text_streaming:
            self.logger.info(
                f"   🌊 Streaming buffer size: {len(self.transcript_buffer)}"
            )
            partial_count = sum(
                1 for item in self.transcript_buffer if item.get("type") == "partial"
            )
            final_count = sum(
                1 for item in self.transcript_buffer if item.get("type") == "final"
            )
            self.logger.info(
                f"   🌊 Partial/Final ratio: {partial_count}/{final_count}"
            )

    def monitor_audio_frame(self, audio_frame, source: str = "unknown"):
        """Monitor individual audio frames for real-time analysis."""
        if not self.enable_audio_monitoring or not self.audio_monitoring_active:
            return

        # Calculate audio level from frame
        try:
            # Check if this is a proper AudioFrame with data attribute
            if not hasattr(audio_frame, "data"):
                self.logger.debug(
                    f"⚠️  Audio object type {type(audio_frame)} does not have 'data' attribute"
                )
                return

            import numpy as np

            audio_data = np.frombuffer(audio_frame.data, dtype=np.int16)
            audio_level = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))

            # Normalize to 0-1 range
            normalized_level = min(audio_level / 32768.0, 1.0)

            # Store audio level
            self.audio_level_history.append(normalized_level)

            # Update current levels based on source
            if source == "user":
                self.user_audio_level = normalized_level
            elif source == "agent":
                self.agent_audio_level = normalized_level

            # Log significant audio events
            if normalized_level > 0.5:  # High audio level
                self.logger.info(
                    f"🔊 HIGH AUDIO LEVEL: {source} - {normalized_level:.2f}"
                )
            elif normalized_level > 0.1:  # Moderate audio level
                self.logger.info(f"🔉 AUDIO: {source} - {normalized_level:.2f}")

        except Exception as e:
            self.logger.warning(f"⚠️  Audio frame analysis error: {e}")

    def log_streaming_text(self, text: str, participant: str = "unknown"):
        """Log streaming text in real-time."""
        if not self.enable_text_streaming or self.is_shutting_down or self.room_closed:
            return

        try:
            timestamp = datetime.datetime.now()
            self.logger.info(f"📡 STREAMING TEXT [{participant}]: {text}")

            # Add to buffer
            self.transcript_buffer.append(
                {
                    "timestamp": timestamp,
                    "role": participant,
                    "content": text,
                    "type": "streaming",
                    "source": "external",
                }
            )
        except Exception as e:
            # Silently ignore streaming errors during shutdown
            pass

    def get_streaming_buffer(self) -> List[Dict[str, Any]]:
        """Get the current streaming buffer contents."""
        return list(self.transcript_buffer)

    def shutdown(self):
        """Signal that the monitor should stop streaming operations."""
        self.is_shutting_down = True
        self.room_closed = True
        self.audio_monitoring_active = False

    def log_custom_event(
        self, message: str, level: str = "info", category: str = "general"
    ):
        """
        Log a custom event with enhanced categorization.

        Args:
            message: The message to log
            level: Log level ('info', 'warning', 'error')
            category: Event category for filtering
        """
        # Skip logging if the session is shutting down to avoid connection errors
        if self.is_shutting_down or self.room_closed:
            return

        timestamp = datetime.datetime.now()
        category_icon = {
            "general": "ℹ️",
            "function": "🔧",
            "database": "🗄️",
            "audio": "🎵",
            "streaming": "🌊",
            "performance": "⚡",
        }.get(category, "ℹ️")

        try:
            if level == "warning":
                self.logger.warning(f"⚠️  [{category.upper()}] {message}")
            elif level == "error":
                self.logger.error(f"❌ [{category.upper()}] {message}")
            else:
                self.logger.info(f"{category_icon} [{category.upper()}] {message}")
        except Exception as e:
            # Silently ignore logging errors during shutdown to prevent error spam
            pass

    def log_session_start(self, room_name: Optional[str] = None):
        """Log session start with enhanced room information."""
        if room_name:
            self.logger.info(f"🚀 STREAMING SESSION STARTED - Room: {room_name}")
        else:
            self.logger.info("🚀 STREAMING SESSION STARTED")

        # Log monitoring capabilities
        capabilities = []
        if self.enable_partial_transcripts:
            capabilities.append("Partial Transcripts")
        if self.enable_audio_monitoring:
            capabilities.append("Audio Monitoring")
        if self.enable_text_streaming:
            capabilities.append("Text Streaming")

        self.logger.info(f"🎛️  Monitoring capabilities: {', '.join(capabilities)}")

    def log_session_end(self):
        """Log session end with comprehensive summary."""
        self.logger.info("=" * 100)
        self.logger.info(f"🏁 STREAMING SESSION ENDED")
        self.logger.info(f"   💬 Total conversation items: {self.conversation_count}")

        if self.enable_text_streaming:
            buffer_stats = self.get_streaming_buffer()
            self.logger.info(
                f"   🌊 Total streaming items captured: {len(buffer_stats)}"
            )

        self.logger.info("=" * 100)

    def get_enhanced_conversation_stats(self) -> dict:
        """Get comprehensive conversation statistics."""
        stats = {
            "total_conversation_items": self.conversation_count,
            "monitor_start_time": datetime.datetime.now().isoformat(),
            "streaming_enabled": self.enable_text_streaming,
            "audio_monitoring_enabled": self.enable_audio_monitoring,
            "partial_transcripts_enabled": self.enable_partial_transcripts,
        }

        if self.transcript_latency:
            stats.update(
                {
                    "avg_transcript_latency_ms": sum(self.transcript_latency)
                    / len(self.transcript_latency),
                    "total_transcripts": len(self.transcript_latency),
                }
            )

        if self.speech_latency:
            stats.update(
                {
                    "avg_speech_duration_ms": sum(self.speech_latency)
                    / len(self.speech_latency),
                    "total_speeches": len(self.speech_latency),
                }
            )

        if self.enable_text_streaming:
            stats.update(
                {
                    "streaming_buffer_size": len(self.transcript_buffer),
                    "streaming_buffer_max_size": self.streaming_buffer_size,
                }
            )

        return stats
