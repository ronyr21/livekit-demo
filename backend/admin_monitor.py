"""
Admin Monitoring Service for LiveKit Call Center
===============================================

This module provides the core functionality for admin call monitoring,
allowing administrators to join ongoing calls as hidden participants
and listen to conversations in real-time.

Based on ADMIN_MONITORING_demo.md - STEP 1: Core Admin Monitor Service
"""

import os
import time
import logging
import asyncio
from typing import Optional, Dict, List, Callable
from datetime import datetime

from livekit import rtc, api
from livekit.api import AccessToken
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger("admin_monitor")
logger.setLevel(logging.INFO)


class AdminMonitorError(Exception):
    """Custom exception for admin monitoring errors"""

    pass


class SimpleAdminMonitor:
    """
    Core admin monitoring service that enables hidden participant functionality.

    This class handles:
    - Generating hidden participant tokens
    - Connecting to rooms as invisible admin
    - Subscribing to audio tracks
    - Managing room events and state
    """

    def __init__(self):
        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")

        # Validate required environment variables
        if not all([self.livekit_url, self.api_key, self.api_secret]):
            raise AdminMonitorError(
                "Missing required LiveKit environment variables: "
                "LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET"
            )

        # Active monitoring sessions
        self.active_sessions: Dict[str, Dict] = {}

        logger.info("🔧 SimpleAdminMonitor initialized")
        logger.info(f"🔌 LiveKit URL: {self.livekit_url}")
        logger.info(f"🗝️ API Key: {self.api_key[:10]}...")

    def generate_admin_token(
        self, room_name: str, admin_identity: Optional[str] = None
    ) -> str:
        """
        Generate a hidden participant access token for admin monitoring.

        Args:
            room_name (str): Name of the room to monitor
            admin_identity (str, optional): Custom identity for admin.
                                          Defaults to auto-generated.

        Returns:
            str: JWT access token for hidden participant

        Raises:
            AdminMonitorError: If token generation fails
        """
        try:
            # Generate unique admin identity if not provided
            if admin_identity is None:
                timestamp = int(time.time())
                admin_identity = f"admin_monitor_{timestamp}"

            logger.info(f"🎟️ Generating admin token for room: {room_name}")
            logger.info(f"👤 Admin identity: {admin_identity}")

            # Configure video grant with hidden admin permissions
            grant = api.VideoGrants(
                room_join=True,  # Allow joining the room
                room=room_name,  # Specific room name
                can_publish=False,  # Admin cannot publish (speak)
                can_subscribe=True,  # Admin can subscribe (listen)
                can_publish_data=False,  # Admin cannot send data
                can_update_own_metadata=False,  # Admin cannot update metadata
                hidden=True,  # CRITICAL: Hide admin from other participants
            )

            # Create access token with fluent interface
            token = (
                AccessToken(self.api_key, self.api_secret)
                .with_identity(admin_identity)
                .with_grants(grant)
            )

            jwt_token = token.to_jwt()

            logger.info(f"✅ Admin token generated successfully")
            logger.info(f"🔐 Token preview: {jwt_token[:20]}...")

            return jwt_token

        except Exception as e:
            logger.error(f"❌ Failed to generate admin token: {e}")
            raise AdminMonitorError(f"Token generation failed: {e}")

    async def join_room_as_hidden_monitor(
        self,
        room_name: str,
        admin_identity: Optional[str] = None,
        event_handlers: Optional[Dict[str, Callable]] = None,
    ) -> rtc.Room:
        """
        Join a LiveKit room as a hidden participant for monitoring.

        Args:
            room_name (str): Name of the room to monitor
            admin_identity (str, optional): Custom admin identity
            event_handlers (dict, optional): Custom event handlers

        Returns:
            rtc.Room: Connected room instance

        Raises:
            AdminMonitorError: If connection fails
        """
        try:
            logger.info(f"🚪 Attempting to join room as hidden monitor: {room_name}")

            # Generate admin token
            token = self.generate_admin_token(room_name, admin_identity)

            # Create room instance
            room = rtc.Room()

            # Set up default event handlers
            self._setup_default_event_handlers(room, room_name)

            # Add custom event handlers if provided
            if event_handlers:
                for event_name, handler in event_handlers.items():
                    room.on(event_name, handler)
                    logger.info(f"📡 Custom event handler registered: {event_name}")

            # Configure room options for monitoring
            options = rtc.RoomOptions(
                auto_subscribe=True,  # Automatically subscribe to all tracks
                dynacast=False,  # Disable dynacast for monitoring
            )

            logger.info(f"🔌 Connecting to room with hidden permissions...")

            # Connect to the room
            await room.connect(self.livekit_url, token, options)

            logger.info(f"✅ Successfully joined room as hidden monitor!")
            logger.info(f"🏠 Room name: {room.name}")
            logger.info(f"🆔 Room SID: {room.sid}")
            logger.info(f"👥 Participants: {len(room.remote_participants)}")

            # Store session information
            session_info = {
                "room": room,
                "room_name": room_name,
                "admin_identity": admin_identity or f"admin_monitor_{int(time.time())}",
                "connected_at": datetime.now(),
                "token": token,
            }

            self.active_sessions[room_name] = session_info

            # Subscribe to existing audio tracks
            await self._subscribe_to_audio_tracks(room)

            return room

        except Exception as e:
            logger.error(f"❌ Failed to join room as hidden monitor: {e}")
            raise AdminMonitorError(f"Room join failed: {e}")

    def _setup_default_event_handlers(self, room: rtc.Room, room_name: str):
        """Set up default event handlers for room monitoring."""

        @room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            logger.info(f"👋 Participant joined: {participant.identity}")
            logger.info(f"📊 Total participants: {len(room.remote_participants) + 1}")

        @room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            logger.info(f"👋 Participant left: {participant.identity}")
            logger.info(f"📊 Total participants: {len(room.remote_participants) + 1}")

        @room.on("track_published")
        def on_track_published(
            publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
        ):
            logger.info(
                f"📢 Track published by {participant.identity}: {publication.kind}"
            )

            # Auto-subscribe to audio tracks for monitoring
            if publication.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(
                    f"🎵 Auto-subscribing to audio track from {participant.identity}"
                )
                # The track will be automatically subscribed due to auto_subscribe=True

        @room.on("track_unpublished")
        def on_track_unpublished(
            publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
        ):
            logger.info(
                f"📢 Track unpublished by {participant.identity}: {publication.kind}"
            )

        @room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            logger.info(
                f"🎧 Subscribed to {track.kind} track from {participant.identity}"
            )

            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(
                    f"🔊 Admin now monitoring audio from: {participant.identity}"
                )

        @room.on("track_unsubscribed")
        def on_track_unsubscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            logger.info(
                f"🎧 Unsubscribed from {track.kind} track from {participant.identity}"
            )

        @room.on("track_muted")
        def on_track_muted(
            publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
        ):
            logger.info(f"🔇 Track muted by {participant.identity}: {publication.kind}")

        @room.on("track_unmuted")
        def on_track_unmuted(
            publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
        ):
            logger.info(
                f"🔊 Track unmuted by {participant.identity}: {publication.kind}"
            )

        @room.on("disconnected")
        def on_disconnected():
            logger.info(f"🔌 Admin monitor disconnected from room: {room_name}")
            # Clean up session info
            if room_name in self.active_sessions:
                del self.active_sessions[room_name]

        logger.info("📡 Default event handlers registered for room monitoring")

    async def _subscribe_to_audio_tracks(self, room: rtc.Room):
        """Subscribe to all existing audio tracks in the room."""
        audio_track_count = 0

        for participant in room.remote_participants.values():
            for publication in participant.track_publications.values():
                if publication.kind == rtc.TrackKind.KIND_AUDIO and publication.track:
                    audio_track_count += 1
                    logger.info(
                        f"🎵 Found existing audio track from: {participant.identity}"
                    )

        logger.info(
            f"🎧 Total audio tracks available for monitoring: {audio_track_count}"
        )

    async def get_active_rooms(self) -> List[Dict]:
        """
        Get list of active LiveKit rooms for admin monitoring.

        Returns:
            List[Dict]: List of active rooms with participant count

        Raises:
            AdminMonitorError: If room listing fails
        """
        try:
            logger.info("📋 Fetching active rooms...")

            # Create LiveKit API client
            lkapi = api.LiveKitAPI(
                url=self.livekit_url, api_key=self.api_key, api_secret=self.api_secret
            )

            # List all rooms
            rooms_response = await lkapi.room.list_rooms(api.ListRoomsRequest())
            await lkapi.aclose()

            # Format room information
            active_rooms = []
            for room in rooms_response.rooms:
                room_info = {
                    "name": room.name,
                    "sid": room.sid,
                    "participant_count": room.num_participants,
                    "creation_time": room.creation_time,
                    "is_monitored": room.name in self.active_sessions,
                }
                active_rooms.append(room_info)

            logger.info(f"📊 Found {len(active_rooms)} active rooms")
            for room in active_rooms:
                logger.info(
                    f"🏠 {room['name']} - {room['participant_count']} participants"
                )

            return active_rooms

        except Exception as e:
            logger.error(f"❌ Failed to get active rooms: {e}")
            raise AdminMonitorError(f"Room listing failed: {e}")

    async def disconnect_from_room(self, room_name: str):
        """
        Disconnect admin monitor from a specific room.

        Args:
            room_name (str): Name of the room to disconnect from
        """
        try:
            if room_name not in self.active_sessions:
                logger.warning(f"⚠️ No active session found for room: {room_name}")
                return

            session = self.active_sessions[room_name]
            room = session["room"]

            logger.info(f"🔌 Disconnecting admin monitor from room: {room_name}")

            # Disconnect from room
            await room.disconnect()

            # Clean up session
            del self.active_sessions[room_name]

            logger.info(f"✅ Successfully disconnected from room: {room_name}")

        except Exception as e:
            logger.error(f"❌ Failed to disconnect from room {room_name}: {e}")

    def get_session_info(self, room_name: str) -> Optional[Dict]:
        """Get information about an active monitoring session."""
        return self.active_sessions.get(room_name)

    def get_all_sessions(self) -> Dict[str, Dict]:
        """Get information about all active monitoring sessions."""
        return self.active_sessions.copy()

    async def cleanup_all_sessions(self):
        """Cleanup all active monitoring sessions."""
        logger.info("🧹 Cleaning up all admin monitoring sessions...")

        for room_name in list(self.active_sessions.keys()):
            await self.disconnect_from_room(room_name)

        logger.info("✅ All admin monitoring sessions cleaned up")


# Test function for development
async def test_admin_monitor():
    """Test function to verify admin monitoring functionality."""
    logger.info("🧪 Testing Admin Monitor functionality...")

    try:
        # Initialize admin monitor
        monitor = SimpleAdminMonitor()

        # Test token generation
        test_room = "test_room"
        token = monitor.generate_admin_token(test_room)
        logger.info(f"✅ Token generation test passed")

        # Test room listing
        rooms = await monitor.get_active_rooms()
        logger.info(f"✅ Room listing test passed - {len(rooms)} rooms found")

        logger.info("🎉 All admin monitor tests passed!")

    except Exception as e:
        logger.error(f"❌ Admin monitor test failed: {e}")
        raise


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_admin_monitor())
