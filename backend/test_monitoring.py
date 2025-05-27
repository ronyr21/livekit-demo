"""
Test script to demonstrate conversation monitoring capabilities.
Run this to see what the monitoring output looks like.
"""

import asyncio
import logging
from datetime import datetime


# Mock classes to simulate LiveKit events for testing
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


async def demo_conversation_monitoring():
    """Demonstrate the conversation monitoring in action."""

    # Set up logging to see output
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("\n" + "=" * 80)
    print("🎬 CONVERSATION MONITORING DEMO")
    print("=" * 80)
    print(
        "This demonstrates what you'll see in your terminal during actual conversations."
    )
    print("-" * 80)

    # Import our monitor
    from conversation_monitor import ConversationMonitor

    # Create mock session
    session = MockSession()

    # Initialize monitor
    monitor = ConversationMonitor(session)
    monitor.log_session_start("demo-room-123")

    print("\n🎭 Simulating a typical conversation flow...\n")
    await asyncio.sleep(1)

    # Simulate agent state changes
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("initializing", "listening")
    )
    await asyncio.sleep(0.5)

    # Simulate user starting to speak
    session.emit(
        "user_state_changed", MockUserStateChangedEvent("listening", "speaking")
    )
    await asyncio.sleep(0.5)

    # Simulate partial transcripts
    session.emit(
        "user_input_transcribed", MockUserInputTranscribedEvent("Hello", False)
    )
    await asyncio.sleep(0.3)
    session.emit(
        "user_input_transcribed", MockUserInputTranscribedEvent("Hello, I need", False)
    )
    await asyncio.sleep(0.3)
    session.emit(
        "user_input_transcribed",
        MockUserInputTranscribedEvent("Hello, I need help with my car", True),
    )
    await asyncio.sleep(0.5)

    # Simulate user stopping speaking
    session.emit(
        "user_state_changed", MockUserStateChangedEvent("speaking", "listening")
    )
    await asyncio.sleep(0.3)
    # Simulate conversation item added (final user message)
    session.emit(
        "conversation_item_added",
        MockConversationItemAddedEvent("user", "Hello, I need help with my car"),
    )
    await asyncio.sleep(0.5)

    # Simulate agent thinking
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("listening", "thinking")
    )
    await asyncio.sleep(0.5)

    # Note: Function tools executed event is not available in current LiveKit version
    # So we'll simulate with a custom log instead
    monitor.log_custom_event(
        "Function tool executed: lookup_car with VIN 1HGBH41JXMN109186"
    )
    monitor.log_custom_event("Function result: Car not found")
    await asyncio.sleep(0.5)

    # Simulate agent speaking
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("thinking", "speaking")
    )
    session.emit("speech_created", MockSpeechCreatedEvent(True, "generate_reply"))
    await asyncio.sleep(0.5)

    # Simulate agent response
    session.emit(
        "conversation_item_added",
        MockConversationItemAddedEvent(
            "assistant",
            "I'd be happy to help you with your car! I couldn't find that VIN in our system. Could you please provide your car's make, model, and year so I can create a new profile for you?",
        ),
    )
    await asyncio.sleep(0.5)

    # Simulate agent back to listening
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("speaking", "listening")
    )
    await asyncio.sleep(1)

    # Simulate another user input
    session.emit(
        "user_state_changed", MockUserStateChangedEvent("listening", "speaking")
    )
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

    # Simulate function tool execution for creating car
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("listening", "thinking")
    )
    monitor.log_custom_event(
        "Function tool executed: create_car with VIN 1HGBH41JXMN109186, make Honda, model Civic, year 2020"
    )
    monitor.log_custom_event("Function result: Car created!")
    await asyncio.sleep(0.5)

    # Final agent response
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("thinking", "speaking")
    )
    session.emit("speech_created", MockSpeechCreatedEvent(True, "generate_reply"))
    session.emit(
        "conversation_item_added",
        MockConversationItemAddedEvent(
            "assistant",
            "Perfect! I've created a profile for your 2020 Honda Civic. How can I assist you with your vehicle today?",
        ),
    )
    session.emit(
        "agent_state_changed", MockAgentStateChangedEvent("speaking", "listening")
    )

    await asyncio.sleep(1)

    # Simulate custom events
    monitor.log_custom_event("User provided vehicle information successfully")
    monitor.log_custom_event("Ready to proceed with service inquiry")

    await asyncio.sleep(1)

    # End session
    monitor.log_session_end()
    print("\n" + "=" * 80)
    print("🎬 DEMO COMPLETE")
    print("=" * 80)
    print(
        "This is what you'll see in your terminal when running the actual LiveKit agent!"
    )
    print("The monitoring captures:")
    print("  ✅ Real-time transcription (partial and final)")
    print("  ✅ Complete conversation history")
    print("  ✅ Agent state changes (listening, thinking, speaking)")
    print("  ✅ User state changes (speaking, listening)")
    print("  ✅ Function tool executions (via custom logs)")
    print("  ✅ Custom business logic events")
    print("  ✅ Error handling and session lifecycle")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_conversation_monitoring())
