from __future__ import annotations
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    Agent,
    AgentSession,
    cli,
    llm,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from livekit.plugins import openai, azure, silero
from dotenv import load_dotenv
from api import AssistantFnc
from prompts import WELCOME_MESSAGE, INSTRUCTIONS, LOOKUP_VIN_MESSAGE
from conversation_monitor import ConversationMonitor
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


async def entrypoint(ctx: JobContext):
    try:
        logger.info("Connecting to the room...")
        await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
        logger.info("Waiting for a participant...")
        await ctx.wait_for_participant()
        logger.info("Participant joined, initializing assistant...")

        # Create the initial chat context with system instructions
        logger.info("Setting up initial chat context...")
        chat_ctx = llm.ChatContext()

        # Initialize assistant function
        logger.info("Initializing AssistantFnc...")
        assistant_fnc = AssistantFnc(instructions=INSTRUCTIONS)

        # Create an Agent with Azure STT, TTS, and OpenAI LLM
        logger.info("Creating Agent with Azure STT/TTS...")
        assistant = Agent(
            instructions=INSTRUCTIONS,
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.8),
        )

        # Create AgentSession - don't override the TTS here!
        logger.info("Creating AgentSession...")

        session = AgentSession(
            stt=azure.STT(
                language="en-US",  # or languages=["en-US"] for multiple
            ),
            tts=azure.TTS(
                voice="en-US-AriaNeural",
                language="en-US",
            ),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
        )

        # Start the agent session
        logger.info("Starting the agent session...")
        await session.start(agent=assistant, room=ctx.room)
        logger.info("Agent started successfully.")

        # Initialize conversation monitor
        logger.info("Initializing conversation monitor...")
        monitor = ConversationMonitor(session, enable_partial_transcripts=True)
        monitor.log_session_start(room_name=ctx.room.name)

        # Generate a welcome message
        logger.info("Generating welcome message...")
        session.generate_reply(instructions=INSTRUCTIONS)

        @session.on("user_speech_committed")
        def on_user_speech_committed(ev):
            transcript = ev.user_message.content
            try:
                logger.info("User speech committed, processing...")

                # Log the business logic decision
                if not assistant_fnc.has_car():
                    monitor.log_custom_event(
                        f"No car found, initiating VIN lookup for: {transcript}"
                    )
                    lookup_message = LOOKUP_VIN_MESSAGE(transcript)
                    # Send a system instruction to guide the response
                    session.generate_reply(instructions=lookup_message)
                else:
                    monitor.log_custom_event(
                        "Car found, proceeding with normal conversation flow"
                    )
                    # Normal flow - just generate a reply to the user's input
                    session.generate_reply(user_input=transcript)

            except Exception as e:
                logger.error(f"Error in on_user_speech_committed: {e}")
                monitor.log_custom_event(
                    f"Error processing user speech: {e}", level="error"
                )

        @session.on("close")
        def on_session_close(event):
            """Handle session close and log session end."""
            logger.info("Session is closing...")
            monitor.log_session_end()
            if hasattr(event, "error") and event.error:
                monitor.log_custom_event(
                    f"Session closed with error: {event.error}", level="error"
                )

    except Exception as e:
        logger.error(f"Error in entrypoint: {e}")
        # Try to log session end if monitor was initialized
        try:
            if "monitor" in locals():
                monitor.log_custom_event(
                    f"Session ended with error: {e}", level="error"
                )
                monitor.log_session_end()
        except:
            pass
        ctx.shutdown()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
