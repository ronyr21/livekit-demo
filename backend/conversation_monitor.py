"""
Conversation Monitor for LiveKit Agent
=====================================

This module provides comprehensive monitoring and logging of conversations
between users and the LiveKit agent, including real-time transcription,
conversation history, agent state changes, and speech generation events.
"""

import logging
import datetime
from typing import Optional
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


class ConversationMonitor:
    """
    Monitor and log conversation between user and agent with detailed timestamps and formatting.
    """

    def __init__(self, session: AgentSession, enable_partial_transcripts: bool = True):
        """
        Initialize the conversation monitor.

        Args:
            session: The AgentSession to monitor
            enable_partial_transcripts: Whether to log partial (non-final) transcripts
        """
        self.session = session
        self.enable_partial_transcripts = enable_partial_transcripts

        # Set up dedicated logger for conversation monitoring
        self.logger = logging.getLogger("conversation_monitor")
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
            self.logger.addHandler(console_handler)

        # Conversation state tracking
        self.conversation_count = 0
        self.current_user_transcript = ""

        # Register all event handlers
        self._register_event_handlers()

        # Log initialization
        self.logger.info("=" * 80)
        self.logger.info("🎤 CONVERSATION MONITOR STARTED")
        self.logger.info("=" * 80)

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

    def _handle_conversation_item_added(self, event: ConversationItemAddedEvent):
        """Handle when a conversation item (user or agent message) is committed to chat history."""
        item: ChatMessage = event.item
        role = item.role
        content = item.text_content
        interrupted = getattr(item, "interrupted", False)

        self.conversation_count += 1

        # Format the message based on role
        if role == "user":
            self.logger.info("-" * 80)
            self.logger.info(f"👤 USER MESSAGE #{self.conversation_count}")
            if interrupted:
                self.logger.info(f"⚠️  [INTERRUPTED] {content}")
            else:
                self.logger.info(f"💬 {content}")

        elif role == "assistant":
            self.logger.info("-" * 80)
            self.logger.info(f"🤖 AGENT RESPONSE #{self.conversation_count}")
            if interrupted:
                self.logger.info(f"⚠️  [INTERRUPTED] {content}")
            else:
                self.logger.info(f"💬 {content}")

        elif role == "system":
            self.logger.info("-" * 80)
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

    def _handle_user_input_transcribed(self, event: UserInputTranscribedEvent):
        """Handle real-time user transcription events."""
        transcript = event.transcript
        is_final = event.is_final

        if is_final:
            # Final transcript - this will likely be followed by conversation_item_added
            self.logger.info(f"🎯 FINAL TRANSCRIPT: {transcript}")
            self.current_user_transcript = transcript
        elif self.enable_partial_transcripts and transcript.strip():
            # Partial transcript - real-time feedback
            self.logger.info(f"📝 PARTIAL: {transcript}")

    def _handle_speech_created(self, event: SpeechCreatedEvent):
        """Handle when agent speech is created."""
        user_initiated = event.user_initiated
        source = event.source

        if user_initiated:
            self.logger.info(f"🗣️  AGENT SPEECH CREATED - Source: {source}")
        else:
            self.logger.info(f"🔄 AUTO SPEECH CREATED - Source: {source}")

    def _handle_agent_state_changed(self, event: AgentStateChangedEvent):
        """Handle agent state changes."""
        old_state = event.old_state
        new_state = event.new_state

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

    def _handle_user_state_changed(self, event: UserStateChangedEvent):
        """Handle user state changes (speaking/listening)."""
        old_state = event.old_state
        new_state = event.new_state

        state_icons = {"speaking": "🎤", "listening": "👂"}

        old_icon = state_icons.get(old_state, "❓")
        new_icon = state_icons.get(new_state, "❓")

        self.logger.info(
            f"🔄 USER STATE: {old_icon} {old_state} → {new_icon} {new_state}"
        )

    def _handle_close(self, event: CloseEvent):
        """Handle session close."""
        self.logger.info("🔚 SESSION CLOSING...")
        if hasattr(event, "error") and event.error:
            self.logger.error(f"❌ Session closed with error: {event.error}")
        self.log_session_end()

    def log_custom_event(self, message: str, level: str = "info"):
        """
        Log a custom event with timestamp.

        Args:
            message: The message to log
            level: Log level ('info', 'warning', 'error')
        """
        if level == "warning":
            self.logger.warning(f"⚠️  {message}")
        elif level == "error":
            self.logger.error(f"❌ {message}")
        else:
            self.logger.info(f"ℹ️  {message}")

    def log_session_start(self, room_name: Optional[str] = None):
        """Log session start with optional room information."""
        if room_name:
            self.logger.info(f"🚀 SESSION STARTED - Room: {room_name}")
        else:
            self.logger.info("🚀 SESSION STARTED")

    def log_session_end(self):
        """Log session end with summary."""
        self.logger.info("=" * 80)
        self.logger.info(
            f"🏁 SESSION ENDED - Total conversation items: {self.conversation_count}"
        )
        self.logger.info("=" * 80)

    def get_conversation_stats(self) -> dict:
        """Get conversation statistics."""
        return {
            "total_conversation_items": self.conversation_count,
            "monitor_start_time": datetime.datetime.now().isoformat(),
        }
