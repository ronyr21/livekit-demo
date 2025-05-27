"""
Enhanced Agent with Streaming Conversation Monitoring
===================================================

This is an enhanced version of the LiveKit agent that incorporates
advanced streaming conversation monitoring capabilities.
"""

from __future__ import annotations
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    Agent,
    AgentSession,
    cli,
    llm,
    ModelSettings,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import openai, azure, silero
from dotenv import load_dotenv
from api import AssistantFnc
from prompts import WELCOME_MESSAGE, INSTRUCTIONS, LOOKUP_VIN_MESSAGE
from streaming_conversation_monitor_fixed import StreamingConversationMonitor
from livekit import rtc
import os
import logging
import asyncio
import sys
import time
from typing import AsyncIterator, AsyncIterable
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class EnhancedAgent(Agent):
    """Enhanced Agent with streaming monitoring integration."""

    def __init__(self, instructions: str, monitor: StreamingConversationMonitor, llm):
        super().__init__(instructions=instructions, llm=llm)
        self.monitor = monitor

    def stt_node(self, audio, model_settings):
        """Override STT node to monitor audio frames."""
        # Log audio input received
        self.monitor.log_custom_event(
            f"STT processing audio input - type: {type(audio)}", category="audio"
        )
        # Call the parent STT processing (returns async generator)
        return super().stt_node(audio, model_settings)

    def tts_node1(self, input, model_settings):
        """Override TTS node to monitor speech generation."""
        # Log TTS input received (input could be text or other data)
        self.monitor.log_custom_event(
            f"TTS processing input - type: {type(input)}", category="audio"
        )
        # Call the parent TTS processing (returns async generator)
        return super().tts_node1(input, model_settings)

    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        """
        Override TTS node to show transcript synchronized with actual speech playback.

        This collects text first, then displays it progressively as audio frames are generated,
        so you see the transcript AS the agent speaks, not before.
        """

        # First, collect all the text from LLM
        collected_text = ""
        text_chunks = []

        async for text_chunk in text:
            collected_text += text_chunk
            text_chunks.append(text_chunk)

        # Log start of speech generation
        logger.info("━" * 100)
        logger.info("🤖 AGENT STARTING TO SPEAK:")
        logger.info("━" * 100)

        if hasattr(self, "monitor") and self.monitor.enable_text_streaming:
            self.monitor.log_custom_event(
                "🎤 AGENT SPEECH GENERATION STARTED",
                category="streaming",
                level="info",
            )

        # Convert text to audio frames and display transcript synchronized with audio
        async def text_to_async_iterable():
            """Convert collected text back to async iterable for TTS."""
            for chunk in text_chunks:
                yield chunk  # Get audio frames from parent TTS

        audio_generator = super().tts_node(text_to_async_iterable(), model_settings)

        # Variables for synchronized transcript display
        total_chars = len(collected_text)
        chars_per_frame = max(1, total_chars // 50) if total_chars > 0 else 1
        current_char_index = 0
        frame_count = 0
        displayed_text = ""

        async for audio_frame in audio_generator:
            frame_count += 1

            # Calculate how much text to show based on audio progress
            target_char_index = min(current_char_index + chars_per_frame, total_chars)

            if target_char_index > current_char_index:
                # Show the new portion of text
                new_text_portion = collected_text[current_char_index:target_char_index]
                displayed_text += new_text_portion
                current_char_index = target_char_index

                # Display current progress every few frames
                if frame_count % 15 == 0 or current_char_index >= total_chars:
                    logger.info(f"🗣️ SPEAKING: '{displayed_text.strip()}'")

                    if hasattr(self, "monitor") and self.monitor.enable_text_streaming:
                        self.monitor.log_custom_event(
                            f"🎵 AUDIO FRAME #{frame_count}: '{displayed_text.strip()}'",
                            category="streaming",
                            level="info",
                        )

            # Yield the audio frame to continue the pipeline
            yield audio_frame

        # Log completion when all audio frames have been generated
        logger.info("━" * 100)
        logger.info(f"✅ AGENT FINISHED SPEAKING ({frame_count} audio frames)")
        logger.info(f"💬 COMPLETE TRANSCRIPT: '{collected_text.strip()}'")
        logger.info("━" * 100)

        if hasattr(self, "monitor"):
            self.monitor.log_custom_event(
                f"✅ SPEECH COMPLETE - {frame_count} frames, {len(collected_text)} chars",
                category="streaming",
                level="info",
            )


async def entrypoint(ctx: JobContext):
    try:
        logger.info("🔌 Connecting to the room...")
        await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
        logger.info("⏳ Waiting for a participant...")
        await ctx.wait_for_participant()
        logger.info("👋 Participant joined, initializing enhanced assistant...")

        # Create the initial chat context with system instructions
        logger.info("📝 Setting up initial chat context...")
        chat_ctx = llm.ChatContext()

        # Initialize assistant function
        logger.info("🔧 Initializing AssistantFnc...")
        assistant_fnc = AssistantFnc(instructions=INSTRUCTIONS)

        # Create AgentSession first to get access to the session for monitoring
        logger.info("🎯 Creating AgentSession with enhanced monitoring...")
        session = AgentSession(
            stt=azure.STT(
                language="en-US",
            ),
            tts=azure.TTS(
                voice="en-US-AriaNeural",
                language="en-US",
            ),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
        )

        # Initialize the streaming conversation monitor BEFORE starting the session
        logger.info("📡 Initializing enhanced streaming conversation monitor...")
        monitor = StreamingConversationMonitor(
            session=session,
            enable_partial_transcripts=True,
            enable_audio_monitoring=True,
            enable_text_streaming=True,
            streaming_buffer_size=100,
        )

        # Create Enhanced Agent with monitoring integration
        logger.info("🤖 Creating Enhanced Agent with monitoring...")
        enhanced_assistant = EnhancedAgent(
            instructions=INSTRUCTIONS,
            monitor=monitor,
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.8),
        )

        # Start the agent session
        logger.info("🚀 Starting the enhanced agent session...")
        await session.start(agent=enhanced_assistant, room=ctx.room)
        logger.info("✅ Enhanced agent started successfully.")

        # Log session start with room information
        monitor.log_session_start(room_name=ctx.room.name)

        # Generate a welcome message
        logger.info("💬 Generating welcome message...")
        monitor.log_custom_event(
            "Generating initial welcome message", category="function"
        )
        session.generate_reply(instructions=WELCOME_MESSAGE)

        # Enhanced event handlers with streaming monitoring
        @session.on("user_speech_committed")
        def on_user_speech_committed(ev):
            transcript = ev.user_message.content
            try:
                logger.info("📥 User speech committed, processing...")
                monitor.log_custom_event(
                    f"Processing user speech: {len(transcript)} characters",
                    category="streaming",
                )

                # Enhanced business logic decision with detailed logging
                if not assistant_fnc.has_car():
                    monitor.log_custom_event(
                        f"No car profile found - initiating VIN lookup workflow",
                        category="function",
                    )
                    monitor.log_custom_event(
                        f"User input: '{transcript[:50]}{'...' if len(transcript) > 50 else ''}'",
                        category="streaming",
                    )

                    lookup_message = LOOKUP_VIN_MESSAGE(transcript)
                    session.generate_reply(instructions=lookup_message)

                    monitor.log_custom_event(
                        "VIN lookup workflow initiated successfully",
                        category="function",
                    )
                else:
                    monitor.log_custom_event(
                        "Car profile exists - proceeding with normal conversation",
                        category="function",
                    )
                    session.generate_reply(user_input=transcript)

            except Exception as e:
                logger.error(f"❌ Error in on_user_speech_committed: {e}")
                monitor.log_custom_event(
                    f"Error processing user speech: {e}",
                    level="error",
                    category="general",
                )

        @session.on("conversation_item_added")
        def on_conversation_item_added1(ev):
            """Handle conversation items and stream agent responses to console AFTER speech."""
            try:
                item = ev.item
                if hasattr(item, "role") and item.role == "assistant":
                    content = ""
                    if hasattr(item, "content"):
                        content = item.content
                    elif hasattr(item, "text"):
                        content = item.text
                    elif hasattr(item, "message") and hasattr(item.message, "content"):
                        content = item.message.content

                    if content:
                        # Simple delay to ensure this runs AFTER TTS sync
                        async def delayed_word_display():
                            await asyncio.sleep(2)  # Wait for TTS to start

                            logger.info("=" * 80)
                            logger.info("🤖 AGENT RESPONSE (Word-by-Word):")
                            logger.info("=" * 80)

                            # Split into words and display in chunks
                            text_content = content
                            if isinstance(text_content, list):
                                text_content = " ".join(text_content)

                            words = text_content.split()
                            chunk_size = 4  # 4 words at a time

                            for i in range(0, len(words), chunk_size):
                                chunk = " ".join(words[i : i + chunk_size])
                                logger.info(f"💬 {chunk}")
                                await asyncio.sleep(
                                    0.2
                                )  # Small delay for streaming effect

                            logger.info("=" * 80)
                            logger.info("✅ Agent response completed")
                            logger.info("=" * 80)

                        asyncio.create_task(delayed_word_display())

                    # Also log the simple message for tracking
                    logger.info("Assistant message added to conversation history.")

            except Exception as e:
                logger.error(f"Error in conversation_item_added handler: {e}")
                monitor.log_custom_event(
                    f"Error handling conversation item: {e}",
                    level="error",
                    category="streaming",
                )

        @session.on("close")
        def on_session_close(event):
            """Handle session close with enhanced logging."""
            logger.info("🔚 Enhanced session is closing...")
            monitor.log_custom_event(
                "Session close event triggered", category="general"
            )

            # Log final session statistics
            stats = monitor.get_enhanced_conversation_stats()
            logger.info(f"📊 Final session stats: {stats}")

            monitor.log_session_end()
            if hasattr(event, "error") and event.error:
                monitor.log_custom_event(
                    f"Session closed with error: {event.error}",
                    level="error",
                    category="general",
                )

        # Set up periodic monitoring reports
        async def periodic_monitoring_report():
            """Provide periodic monitoring reports."""
            while True:
                try:
                    await asyncio.sleep(30)  # Report every 30 seconds
                    stats = monitor.get_enhanced_conversation_stats()
                    monitor.log_custom_event(
                        f"Periodic report - Conversations: {stats.get('total_conversation_items', 0)}, "
                        f"Buffer: {stats.get('streaming_buffer_size', 0)}",
                        category="performance",
                    )
                except Exception as e:
                    logger.error(f"Error in periodic monitoring: {e}")
                    break

        # Start periodic monitoring in background
        asyncio.create_task(
            periodic_monitoring_report()
        )  # Set up text streaming for real-time updates (if room supports it)
        try:
            # Monitor text streams from the room
            if hasattr(ctx.room, "register_text_stream_handler"):

                async def handle_text_stream(reader, participant_info):
                    monitor.log_custom_event(
                        f"Text stream received from {participant_info.identity}",
                        category="streaming",
                    )

                    async for chunk in reader:
                        monitor.log_streaming_text(
                            chunk, participant=participant_info.identity
                        )

                # Register the handler
                ctx.room.register_text_stream_handler(
                    "conversation_stream", handle_text_stream
                )

                monitor.log_custom_event(
                    "Text stream handler registered successfully", category="streaming"
                )
        except Exception as e:
            logger.warning(f"⚠️  Text streaming setup failed: {e}")
            monitor.log_custom_event(
                f"Text streaming unavailable: {e}",
                level="warning",
                category="streaming",
            )

        # Enhanced function tool monitoring
        # Note: Since FunctionToolsExecutedEvent is not available, we'll monitor through custom logging
        original_lookup_car = assistant_fnc.lookup_car
        original_create_car = assistant_fnc.create_car
        original_get_car_details = assistant_fnc.get_car_details

        async def monitored_lookup_car(ctx, vin: str):
            monitor.log_custom_event(
                f"🔍 Function call: lookup_car(vin='{vin}')", category="function"
            )
            start_time = asyncio.get_event_loop().time()
            try:
                result = await original_lookup_car(ctx, vin)
                end_time = asyncio.get_event_loop().time()
                duration = (end_time - start_time) * 1000
                monitor.log_custom_event(
                    f"✅ lookup_car completed in {duration:.1f}ms - Result: {result[:100]}{'...' if len(result) > 100 else ''}",
                    category="function",
                )
                return result
            except Exception as e:
                monitor.log_custom_event(
                    f"❌ lookup_car failed: {e}", level="error", category="function"
                )
                raise

        async def monitored_create_car(ctx, vin: str, make: str, model: str, year: int):
            monitor.log_custom_event(
                f"🔍 Function call: create_car(vin='{vin}', make='{make}', model='{model}', year={year})",
                category="function",
            )
            start_time = asyncio.get_event_loop().time()
            try:
                result = await original_create_car(ctx, vin, make, model, year)
                end_time = asyncio.get_event_loop().time()
                duration = (end_time - start_time) * 1000
                monitor.log_custom_event(
                    f"✅ create_car completed in {duration:.1f}ms - Result: {result}",
                    category="function",
                )
                return result
            except Exception as e:
                monitor.log_custom_event(
                    f"❌ create_car failed: {e}", level="error", category="function"
                )
                raise

        async def monitored_get_car_details(ctx):
            monitor.log_custom_event(
                "🔍 Function call: get_car_details()", category="function"
            )
            start_time = asyncio.get_event_loop().time()
            try:
                result = await original_get_car_details(ctx)
                end_time = asyncio.get_event_loop().time()
                duration = (end_time - start_time) * 1000
                monitor.log_custom_event(
                    f"✅ get_car_details completed in {duration:.1f}ms - Result: {result[:100]}{'...' if len(result) > 100 else ''}",
                    category="function",
                )
                return result
            except Exception as e:
                monitor.log_custom_event(
                    f"❌ get_car_details failed: {e}",
                    level="error",
                    category="function",
                )
                raise

        # Replace the original methods with monitored versions
        assistant_fnc.lookup_car = monitored_lookup_car
        assistant_fnc.create_car = monitored_create_car
        assistant_fnc.get_car_details = monitored_get_car_details

        monitor.log_custom_event(
            "Enhanced function monitoring active", category="function"
        )

        # Final setup completion
        monitor.log_custom_event(
            "Enhanced agent setup completed - All monitoring systems active",
            category="general",
        )

    except Exception as e:
        logger.error(f"❌ Error in enhanced entrypoint: {e}")
        # Try to log session end if monitor was initialized
        try:
            if "monitor" in locals():
                monitor.log_custom_event(
                    f"Session ended with critical error: {e}",
                    level="error",
                    category="general",
                )
                monitor.log_session_end()
        except:
            pass
        ctx.shutdown()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
