"""
Demo script for Enhanced Streaming Conversation Monitoring
=========================================================

This script demonstrates the advanced streaming monitoring capabilities,
including real-time transcript streaming, audio frame monitoring, and
enhanced performance metrics.
"""

import asyncio
import logging
import time
import numpy as np
from datetime import datetime


# Mock classes for enhanced testing
class MockAudioFrame:
    def __init__(self, sample_rate=48000, num_channels=1, duration_ms=100):
        """Create a mock audio frame with realistic data."""
        self.sample_rate = sample_rate
        self.num_channels = num_channels

        # Generate sample audio data (sine wave for demo)
        samples_per_channel = int(sample_rate * duration_ms / 1000)
        frequency = 440  # A4 note
        t = np.linspace(0, duration_ms / 1000, samples_per_channel, False)
        audio_signal = np.sin(2 * np.pi * frequency * t)

        # Add some random noise to make it more realistic
        noise = np.random.normal(0, 0.1, samples_per_channel)
        audio_signal += noise

        # Convert to int16 format
        audio_data = (audio_signal * 32767).astype(np.int16)
        self.data = audio_data.tobytes()
        self.samples_per_channel = samples_per_channel


class MockChatMessage:
    def __init__(self, role, content, interrupted=False):
        self.role = role
        self.content = [content]
        self.text_content = content
        self.interrupted = interrupted


class MockConversationItemAddedEvent:
    def __init__(self, role, content, interrupted=False):
        self.item = MockChatMessage(role, content, interrupted)


class MockUserInputTranscribedEvent:
    def __init__(self, transcript, is_final=True):
        self.transcript = transcript
        self.is_final = is_final


class MockSpeechCreatedEvent:
    def __init__(self, user_initiated=True, source="generate_reply"):
        self.user_initiated = user_initiated
        self.source = source

        # Mock speech handle
        self.speech_handle = MockSpeechHandle()


class MockSpeechHandle:
    def __init__(self):
        self.completed = False

    async def wait_for_playout(self):
        """Simulate speech playout delay."""
        await asyncio.sleep(1.5)  # Simulate 1.5 second speech
        self.completed = True


class MockAgentStateChangedEvent:
    def __init__(self, old_state, new_state):
        self.old_state = old_state
        self.new_state = new_state


class MockUserStateChangedEvent:
    def __init__(self, old_state, new_state):
        self.old_state = old_state
        self.new_state = new_state


class MockCloseEvent:
    def __init__(self, error=None):
        self.error = error


class MockSession:
    def __init__(self):
        self.handlers = {}

    def on(self, event_name):
        def decorator(func):
            self.handlers[event_name] = func
            return func

        return decorator

    def emit(self, event_name, event):
        if event_name in self.handlers:
            self.handlers[event_name](event)


async def demo_enhanced_streaming_monitoring():
    """Demonstrate the enhanced streaming monitoring capabilities."""

    # Set up logging to see output
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("\n" + "=" * 120)
    print("🚀 ENHANCED STREAMING CONVERSATION MONITORING DEMO")
    print("=" * 120)
    print("This demonstrates advanced real-time monitoring with:")
    print("  🌊 Streaming text capture")
    print("  🎵 Audio frame monitoring")
    print("  📊 Performance metrics")
    print("  ⚡ Real-time analytics")
    print("-" * 120)

    # Import our enhanced monitor
    from streaming_conversation_monitor import StreamingConversationMonitor

    # Create mock session
    session = MockSession()

    # Initialize enhanced monitor with all features enabled
    monitor = StreamingConversationMonitor(
        session=session,
        enable_partial_transcripts=True,
        enable_audio_monitoring=True,
        enable_text_streaming=True,
        streaming_buffer_size=50,
    )
    monitor.log_session_start("enhanced-demo-room-456")

    print("\n🎭 Simulating enhanced conversation flow with streaming monitoring...\n")
    await asyncio.sleep(1)

    # Simulate agent initialization
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("initializing", "listening")
    )
    await asyncio.sleep(0.3)

    # Simulate user starting to speak with audio monitoring
    print("🎙️  SIMULATING USER AUDIO INPUT...")
    session.emit(
        "user_state_changed", MockUserStateChangedEvent("listening", "speaking")
    )

    # Simulate audio frames being processed
    for i in range(5):
        audio_frame = MockAudioFrame(duration_ms=200)
        monitor.monitor_audio_frame(audio_frame, source="user")
        await asyncio.sleep(0.2)

    # Simulate streaming partial transcripts (more granular)
    streaming_phrases = [
        "I",
        "I need",
        "I need help",
        "I need help with",
        "I need help with my",
        "I need help with my car",
        "I need help with my car that",
        "I need help with my car that won't",
        "I need help with my car that won't start",
    ]

    print("🌊 SIMULATING STREAMING TRANSCRIPTION...")
    for i, phrase in enumerate(streaming_phrases):
        session.emit(
            "user_input_transcribed", MockUserInputTranscribedEvent(phrase, False)
        )
        await asyncio.sleep(0.3)

    # Final transcript
    final_transcript = "I need help with my car that won't start"
    session.emit(
        "user_input_transcribed", MockUserInputTranscribedEvent(final_transcript, True)
    )
    await asyncio.sleep(0.3)

    # User stops speaking
    session.emit(
        "user_state_changed", MockUserStateChangedEvent("speaking", "listening")
    )

    # Conversation item added
    session.emit(
        "conversation_item_added",
        MockConversationItemAddedEvent("user", final_transcript),
    )
    await asyncio.sleep(0.5)

    # Simulate agent processing with streaming text
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("listening", "thinking")
    )
    monitor.log_streaming_text("Processing user request...", participant="system")
    await asyncio.sleep(0.5)

    # Simulate function tools with enhanced monitoring
    monitor.log_custom_event(
        "Function execution: lookup_car(vin='1HGBH41JXMN109186')", category="function"
    )
    monitor.log_custom_event("Database query latency: 45.2ms", category="performance")
    monitor.log_custom_event(
        "Function result: Car not found in database", category="function"
    )
    await asyncio.sleep(0.5)

    # Agent starts speaking
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("thinking", "speaking")
    )
    speech_event = MockSpeechCreatedEvent(True, "generate_reply")
    session.emit("speech_created", speech_event)

    # Simulate agent audio generation with monitoring
    print("🗣️  SIMULATING AGENT SPEECH GENERATION...")
    for i in range(8):
        audio_frame = MockAudioFrame(duration_ms=200)
        monitor.monitor_audio_frame(audio_frame, source="agent")
        await asyncio.sleep(0.2)

    # Agent response
    agent_response = "I can help you with your car troubles! I couldn't find that VIN in our system. Could you tell me the make, model, and year of your vehicle so I can create a profile?"
    session.emit(
        "conversation_item_added",
        MockConversationItemAddedEvent("assistant", agent_response),
    )

    # Agent back to listening
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("speaking", "listening")
    )
    await asyncio.sleep(0.5)

    # Simulate more streaming text
    monitor.log_streaming_text("User is thinking...", participant="system")
    await asyncio.sleep(1)

    # Second user interaction with interruption
    print("🌊 SIMULATING STREAMING WITH INTERRUPTION...")
    session.emit(
        "user_state_changed", MockUserStateChangedEvent("listening", "speaking")
    )

    # Simulate more audio frames
    for i in range(3):
        audio_frame = MockAudioFrame(duration_ms=150)
        monitor.monitor_audio_frame(audio_frame, source="user")
        await asyncio.sleep(0.15)

    # Streaming partials for second message
    streaming_phrases_2 = [
        "It's",
        "It's a",
        "It's a 2020",
        "It's a 2020 Honda",
        "It's a 2020 Honda Civic",
    ]

    for phrase in streaming_phrases_2:
        session.emit(
            "user_input_transcribed", MockUserInputTranscribedEvent(phrase, False)
        )
        await asyncio.sleep(0.25)

    # Final transcript
    session.emit(
        "user_input_transcribed",
        MockUserInputTranscribedEvent("It's a 2020 Honda Civic", True),
    )
    session.emit(
        "user_state_changed", MockUserStateChangedEvent("speaking", "listening")
    )
    session.emit(
        "conversation_item_added",
        MockConversationItemAddedEvent("user", "It's a 2020 Honda Civic"),
    )
    await asyncio.sleep(0.5)

    # Agent processing second request
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("listening", "thinking")
    )

    # Enhanced function monitoring
    monitor.log_custom_event(
        "Function execution: create_car(vin='AUTO123', make='Honda', model='Civic', year=2020)",
        category="function",
    )
    monitor.log_custom_event("Database insert latency: 23.7ms", category="performance")
    monitor.log_custom_event(
        "Function result: Car profile created successfully", category="function"
    )
    await asyncio.sleep(0.5)

    # Final agent response
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("thinking", "speaking")
    )
    speech_event_2 = MockSpeechCreatedEvent(True, "generate_reply")
    session.emit("speech_created", speech_event_2)

    final_response = "Perfect! I've created a profile for your 2020 Honda Civic. Now I can help you troubleshoot the starting issue. Let's begin with some diagnostics."
    session.emit(
        "conversation_item_added",
        MockConversationItemAddedEvent("assistant", final_response),
    )

    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("speaking", "listening")
    )
    await asyncio.sleep(0.5)

    # Demonstrate custom event categories
    monitor.log_custom_event(
        "User provided complete vehicle information", category="general"
    )
    monitor.log_custom_event("Diagnostic workflow initiated", category="function")
    monitor.log_custom_event("Average response latency: 127ms", category="performance")
    monitor.log_custom_event("Audio quality: High (SNR: 24.5dB)", category="audio")
    monitor.log_custom_event("Streaming buffer utilization: 65%", category="streaming")

    await asyncio.sleep(1)

    # Show streaming buffer contents
    buffer = monitor.get_streaming_buffer()
    monitor.log_custom_event(
        f"Streaming buffer contains {len(buffer)} items", category="streaming"
    )

    # Show enhanced statistics
    stats = monitor.get_enhanced_conversation_stats()
    print("\n📊 ENHANCED STATISTICS:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # End session
    monitor.log_session_end()

    print("\n" + "=" * 120)
    print("🎬 ENHANCED DEMO COMPLETE")
    print("=" * 120)
    print("This enhanced monitoring system provides:")
    print("  ✅ Real-time streaming transcript capture (character-by-character)")
    print("  ✅ Audio frame monitoring with level analysis")
    print("  ✅ Performance metrics and latency tracking")
    print("  ✅ Enhanced function execution monitoring")
    print("  ✅ Categorized event logging")
    print("  ✅ Speech handle state tracking")
    print("  ✅ Streaming buffer management")
    print("  ✅ Comprehensive session analytics")
    print("=" * 120)

    print("\n🚀 To use this enhanced monitoring:")
    print("   1. Replace 'agent.py' with 'enhanced_agent.py'")
    print("   2. Run: python enhanced_agent.py")
    print("   3. Connect via LiveKit playground")
    print("   4. Watch the enhanced streaming logs in real-time!")
    print("\n" + "=" * 120 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_enhanced_streaming_monitoring())
