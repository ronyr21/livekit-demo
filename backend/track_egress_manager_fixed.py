"""
Individual Participant Track Recording Manager
===========================================

This module provides TrackEgress-based recording for individual participants
with WebSocket streaming and S3 upload capabilities.
"""

import asyncio
import logging
import os
import json
import time
import io
import wave
import struct
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import parse_qs, urlparse

from livekit import api, rtc
from livekit.protocol.egress import (
    TrackEgressRequest,
    TrackCompositeEgressRequest,
    DirectFileOutput,
)
import websockets
import aiohttp
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


@dataclass
class ParticipantRecordingInfo:
    """Information about an individual participant recording"""

    participant_identity: str
    track_id: str
    egress_id: Optional[str] = None
    recording_status: str = "pending"  # pending, recording, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    websocket_url: Optional[str] = None
    s3_object_name: Optional[str] = None
    chunks_received: int = 0
    total_duration: float = 0.0


@dataclass
class AudioChunk:
    """Audio chunk data for processing"""

    participant_identity: str
    chunk_number: int
    audio_data: bytes
    timestamp: datetime
    sample_rate: int = 48000  # LiveKit default
    channels: int = 1  # Mono audio
    format: str = "pcm_s16le"  # LiveKit WebSocket format


class TrackEgressManager:
    """
    Manages individual participant audio recording using LiveKit TrackEgress
    with WebSocket streaming and S3 storage capabilities.
    """

    def __init__(self, room_name: str, websocket_port: int = 8080):
        self.room_name = room_name
        self.websocket_port = websocket_port
        self.websocket_url = f"ws://localhost:{websocket_port}/audio-stream"

        # Track recordings by participant identity
        self.participant_recordings: Dict[str, ParticipantRecordingInfo] = {}

        # LiveKit API client
        self.livekit_client = None

        # MinIO client for storage
        self.minio_client = None

        # WebSocket server for real-time streaming
        self.websocket_server = None
        self.websocket_clients: set = set()

        # Audio processing
        self.audio_buffers: Dict[str, List[AudioChunk]] = {}
        self.chunk_duration_seconds = 5.0  # Save chunks every 5 seconds
        self.sample_rate = 48000  # LiveKit default sample rate
        self.channels = 1  # Mono audio
        self.bytes_per_sample = 2  # 16-bit audio (2 bytes per sample)

        logger.info(f"🎵 TrackEgressManager initialized for room: {room_name}")

    async def initialize(self):
        """Initialize LiveKit API client and MinIO storage"""
        try:
            # Initialize LiveKit API client
            self.livekit_client = api.LiveKitAPI(
                url=os.getenv("LIVEKIT_URL"),
                api_key=os.getenv("LIVEKIT_API_KEY"),
                api_secret=os.getenv("LIVEKIT_API_SECRET"),
            )

            # Initialize MinIO client
            minio_endpoint_raw = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
            if minio_endpoint_raw.startswith("https://"):
                minio_endpoint = minio_endpoint_raw.replace("https://", "")
                secure = True
            else:
                minio_endpoint = minio_endpoint_raw.replace("http://", "")
                secure = False

            self.minio_client = Minio(
                minio_endpoint,
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
                secure=secure,
            )

            # Ensure bucket exists
            bucket = os.getenv("MINIO_BUCKET", "livekit-recordings")
            if not self.minio_client.bucket_exists(bucket):
                self.minio_client.make_bucket(bucket)
                logger.info(f"✅ Created MinIO bucket: {bucket}")

            # Start WebSocket server for real-time audio streaming
            await self._start_websocket_server()

            logger.info("✅ TrackEgressManager initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize TrackEgressManager: {e}")
            raise

    async def start_participant_recording(
        self,
        participant_identity: str,
        audio_track_id: str,
        enable_websocket_streaming: bool = True,
    ) -> str:
        """
        Start individual participant audio recording using TrackEgress

        Args:
            participant_identity: The participant's identity
            audio_track_id: The audio track ID to record
            enable_websocket_streaming: Whether to enable real-time WebSocket streaming

        Returns:
            egress_id: The LiveKit egress ID for this recording
        """
        try:
            if participant_identity in self.participant_recordings:
                existing = self.participant_recordings[participant_identity]
                if existing.recording_status == "recording":
                    logger.warning(
                        f"⚠️ Recording already active for {participant_identity}"
                    )
                    return existing.egress_id

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"participant_{participant_identity}_{timestamp}.wav"

            # Create recording info
            recording_info = ParticipantRecordingInfo(
                participant_identity=participant_identity,
                track_id=audio_track_id,
                started_at=datetime.now(),
                file_path=f"participants/{self.room_name}/{filename}",
                websocket_url=(
                    self.websocket_url if enable_websocket_streaming else None
                ),
                s3_object_name=f"participants/{self.room_name}/{filename}",
            )  # Build TrackEgress request with WebSocket output for chunked recording
            # Generate WebSocket URL with track and room parameters for identification
            websocket_stream_url = f"{self.websocket_url}?track_id={audio_track_id}&room={self.room_name}&participant={participant_identity}"  # FIXED: Use correct TrackEgressRequest with file output instead of stream
            # TrackEgress with WebSocket is not directly supported, use file output to S3 instead            # Create file output for direct recording
            file_output = DirectFileOutput(
                filepath=f"{recording_info.s3_object_name}.mp4",
            )

            track_egress_request = TrackEgressRequest(
                room_name=self.room_name, track_id=audio_track_id, file=file_output
            )

            logger.info(f"🎬 Starting TrackEgress recording for {participant_identity}")
            logger.info(f"📁 File path: {recording_info.file_path}")
            logger.info(f"🎵 Track ID: {audio_track_id}")
            logger.info(f"🌐 WebSocket streaming: {enable_websocket_streaming}")

            # Start the recording
            response = await self.livekit_client.egress.start_track_egress(
                track_egress_request
            )

            # Update recording info
            recording_info.egress_id = response.egress_id
            recording_info.recording_status = "recording"

            # Store recording info
            self.participant_recordings[participant_identity] = recording_info

            logger.info(f"✅ TrackEgress recording started successfully!")
            logger.info(f"📁 Egress ID: {response.egress_id}")
            logger.info(f"📊 Initial status: {response.status}")

            # Monitor egress status
            asyncio.create_task(
                self._monitor_egress_status(response.egress_id, participant_identity)
            )

            return response.egress_id

        except Exception as e:
            logger.error(
                f"❌ Failed to start participant recording for {participant_identity}: {e}"
            )
            if participant_identity in self.participant_recordings:
                self.participant_recordings[participant_identity].recording_status = (
                    "failed"
                )
            raise

    async def stop_participant_recording(self, participant_identity: str) -> bool:
        """
        Stop individual participant recording

        Args:
            participant_identity: The participant's identity

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            if participant_identity not in self.participant_recordings:
                logger.warning(f"⚠️ No recording found for {participant_identity}")
                return False

            recording_info = self.participant_recordings[participant_identity]

            if recording_info.recording_status != "recording":
                logger.warning(f"⚠️ Recording not active for {participant_identity}")
                return False

            if not recording_info.egress_id:
                logger.error(f"❌ No egress ID for {participant_identity}")
                return False

            logger.info(f"🛑 Stopping TrackEgress recording for {participant_identity}")
            logger.info(f"📁 Egress ID: {recording_info.egress_id}")

            # Stop the egress
            stop_request = api.StopEgressRequest(egress_id=recording_info.egress_id)
            response = await self.livekit_client.egress.stop_egress(stop_request)

            # Update status
            recording_info.recording_status = "stopping"
            recording_info.completed_at = datetime.now()

            logger.info(f"✅ TrackEgress recording stopped successfully!")
            logger.info(f"📊 Stop response: {response}")

            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to stop participant recording for {participant_identity}: {e}"
            )
            return False

    async def stop_all_recordings(self) -> Dict[str, bool]:
        """
        Stop all active participant recordings

        Returns:
            Dict[str, bool]: Results for each participant
        """
        results = {}

        for participant_identity in list(self.participant_recordings.keys()):
            recording_info = self.participant_recordings[participant_identity]
            if recording_info.recording_status == "recording":
                results[participant_identity] = await self.stop_participant_recording(
                    participant_identity
                )
            else:
                results[participant_identity] = True  # Already stopped

        return results

    async def get_recording_status(
        self, participant_identity: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get recording status for a participant

        Args:
            participant_identity: The participant's identity

        Returns:
            Dict with recording information or None if not found
        """
        if participant_identity not in self.participant_recordings:
            return None

        recording_info = self.participant_recordings[participant_identity]
        return asdict(recording_info)

    async def get_all_recordings_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all participant recordings

        Returns:
            Dict mapping participant identities to their recording info
        """
        return {
            identity: asdict(info)
            for identity, info in self.participant_recordings.items()
        }

    async def _monitor_egress_status(self, egress_id: str, participant_identity: str):
        """Monitor egress status and update recording info"""
        try:
            while True:
                # Check egress status
                egress_list = await self.livekit_client.egress.list_egress(
                    api.ListEgressRequest()
                )

                egress_found = False
                for egress in egress_list.items:
                    if egress.egress_id == egress_id:
                        egress_found = True

                        if participant_identity in self.participant_recordings:
                            recording_info = self.participant_recordings[
                                participant_identity
                            ]

                            if egress.status == api.EgressStatus.EGRESS_COMPLETE:
                                logger.info(
                                    f"✅ Recording completed for {participant_identity}"
                                )
                                recording_info.recording_status = "completed"
                                recording_info.completed_at = datetime.now()

                                # Process file results if available
                                if (
                                    hasattr(egress, "file_results")
                                    and egress.file_results
                                ):
                                    for file_result in egress.file_results:
                                        if hasattr(file_result, "size"):
                                            recording_info.file_size = file_result.size

                                return  # Exit monitoring

                            elif egress.status == api.EgressStatus.EGRESS_FAILED:
                                logger.error(
                                    f"❌ Recording failed for {participant_identity}"
                                )
                                recording_info.recording_status = "failed"
                                return  # Exit monitoring

                            elif egress.status == api.EgressStatus.EGRESS_ACTIVE:
                                logger.debug(
                                    f"📊 Recording active for {participant_identity}"
                                )
                                recording_info.recording_status = "recording"

                        break

                if not egress_found:
                    logger.warning(f"⚠️ Egress {egress_id} not found in list")
                    if participant_identity in self.participant_recordings:
                        self.participant_recordings[
                            participant_identity
                        ].recording_status = "failed"
                    return

                # Wait before next check
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"❌ Error monitoring egress {egress_id}: {e}")
            if participant_identity in self.participant_recordings:
                self.participant_recordings[participant_identity].recording_status = (
                    "failed"
                )

    async def _start_websocket_server(self):
        """Start WebSocket server for receiving LiveKit TrackEgress audio data"""

        async def handle_livekit_egress(websocket, path):
            """Handle incoming audio data from LiveKit TrackEgress"""
            participant_identity = None
            try:
                logger.info(f"🔗 New WebSocket connection attempt: {path}")
                logger.info(f"🔗 Connection headers: {websocket.request_headers}")

                # Parse WebSocket path to extract track and participant info
                parsed_url = urlparse(path)
                query_params = parse_qs(parsed_url.query)

                track_id = query_params.get("track_id", [None])[0]
                room = query_params.get("room", [None])[0]
                participant_identity = query_params.get("participant", [None])[0]

                logger.info(
                    f"🔍 Parsed parameters - Track: {track_id}, Room: {room}, Participant: {participant_identity}"
                )

                if not all([track_id, room, participant_identity]):
                    logger.error(
                        f"❌ Missing required parameters in WebSocket URL: {path}"
                    )
                    logger.error(f"❌ Available query params: {query_params}")
                    await websocket.close(code=1008, reason="Missing parameters")
                    return

                logger.info(
                    f"🎵 LiveKit TrackEgress connected for {participant_identity}"
                )
                logger.info(f"📡 Track ID: {track_id}, Room: {room}")

                # Initialize audio buffer for this participant
                if participant_identity not in self.audio_buffers:
                    self.audio_buffers[participant_identity] = []

                chunk_number = 0
                messages_received = 0

                # Handle incoming audio data
                async for message in websocket:
                    try:
                        messages_received += 1
                        if messages_received % 10 == 1:  # Log every 10th message
                            logger.debug(
                                f"📨 Received message #{messages_received} from {participant_identity}"
                            )

                        if isinstance(message, bytes):
                            # Binary message = audio data (PCM format from LiveKit)
                            logger.debug(
                                f"🎵 Received {len(message)} bytes of audio data from {participant_identity}"
                            )
                            await self._process_audio_chunk(
                                participant_identity, track_id, message, chunk_number
                            )
                            chunk_number += 1

                        else:
                            # Text message = control/status messages
                            logger.info(
                                f"📜 Received control message from {participant_identity}: {message}"
                            )
                            try:
                                control_data = json.loads(message)
                                await self._handle_egress_control_message(
                                    participant_identity, control_data
                                )
                            except json.JSONDecodeError:
                                logger.warning(
                                    f"⚠️ Invalid JSON control message: {message}"
                                )

                    except Exception as chunk_error:
                        logger.error(f"❌ Error processing audio chunk: {chunk_error}")
                        continue

                logger.info(
                    f"🏁 WebSocket loop ended for {participant_identity}, total messages: {messages_received}"
                )

            except websockets.exceptions.ConnectionClosed:
                logger.info(
                    f"🔌 LiveKit TrackEgress disconnected for {participant_identity}"
                )
                # Finalize any remaining audio chunks
                if participant_identity and participant_identity in self.audio_buffers:
                    await self._finalize_participant_recording(participant_identity)

            except Exception as e:
                logger.error(f"❌ LiveKit TrackEgress error: {e}")
                logger.exception("Full traceback:")
            finally:
                # Clean up buffers
                if participant_identity and participant_identity in self.audio_buffers:
                    del self.audio_buffers[participant_identity]

        async def handle_client_websocket(websocket, path):
            """Handle client WebSocket connections (for real-time monitoring)"""
            try:
                self.websocket_clients.add(websocket)
                logger.info(
                    f"🌐 Client WebSocket connected: {websocket.remote_address}"
                )

                # Send welcome message
                await websocket.send(
                    json.dumps(
                        {
                            "type": "connected",
                            "room_name": self.room_name,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )

                # Keep connection alive and handle client messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._handle_websocket_message(websocket, data)
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ Invalid JSON from client")

            except websockets.exceptions.ConnectionClosed:
                logger.info(f"🔌 Client WebSocket disconnected")
            except Exception as e:
                logger.error(f"❌ Client WebSocket error: {e}")
            finally:
                self.websocket_clients.discard(websocket)

        async def websocket_router(websocket, path):
            """Route WebSocket connections based on path"""
            if path.startswith("/audio-stream"):
                # LiveKit TrackEgress connections (with query parameters)
                if "track_id=" in path:
                    await handle_livekit_egress(websocket, path)
                else:
                    # Client monitoring connections
                    await handle_client_websocket(websocket, path)
            else:
                logger.warning(f"⚠️ Unknown WebSocket path: {path}")
                await websocket.close(code=1008, reason="Unknown path")

        # Start WebSocket server
        try:
            self.websocket_server = await websockets.serve(
                websocket_router,
                "localhost",
                self.websocket_port,
                ping_interval=20,
                ping_timeout=10,
            )
            logger.info(
                f"🌐 WebSocket server started on ws://localhost:{self.websocket_port}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to start WebSocket server: {e}")
            raise

    async def _process_audio_chunk(
        self,
        participant_identity: str,
        track_id: str,
        audio_data: bytes,
        chunk_number: int,
    ):
        """Process incoming audio chunk from LiveKit TrackEgress"""
        try:
            # Create audio chunk object
            chunk = AudioChunk(
                participant_identity=participant_identity,
                chunk_number=chunk_number,
                audio_data=audio_data,
                timestamp=datetime.now(),
                sample_rate=self.sample_rate,
                channels=self.channels,
                format="pcm_s16le",
            )

            # Add to buffer
            if participant_identity not in self.audio_buffers:
                self.audio_buffers[participant_identity] = []

            self.audio_buffers[participant_identity].append(chunk)

            # Update recording info
            if participant_identity in self.participant_recordings:
                recording_info = self.participant_recordings[participant_identity]
                recording_info.chunks_received += 1

                # Calculate duration (assuming PCM 16-bit mono at 48kHz)
                samples = len(audio_data) // self.bytes_per_sample
                duration_seconds = samples / self.sample_rate
                recording_info.total_duration += duration_seconds

            # Check if we should save a chunk (every 5 seconds worth of audio)
            buffer_duration = self._calculate_buffer_duration(participant_identity)
            if buffer_duration >= self.chunk_duration_seconds:
                await self._save_audio_chunk_to_s3(participant_identity)

            # Broadcast to connected clients for real-time monitoring
            await self._broadcast_audio_chunk_to_clients(
                participant_identity, audio_data
            )

            # Log progress every 100 chunks
            if chunk_number > 0 and chunk_number % 100 == 0:
                logger.info(
                    f"📊 Processed {chunk_number} chunks for {participant_identity}"
                )

        except Exception as e:
            logger.error(f"❌ Error processing audio chunk: {e}")

    async def _handle_egress_control_message(
        self, participant_identity: str, control_data: dict
    ):
        """Handle control messages from LiveKit TrackEgress"""
        try:
            message_type = control_data.get("type")

            if message_type == "track_muted":
                logger.info(f"🔇 Track muted for {participant_identity}")
                # Could pause chunking here if needed

            elif message_type == "track_unmuted":
                logger.info(f"🔊 Track unmuted for {participant_identity}")

            elif message_type == "track_ended":
                logger.info(f"🛑 Track ended for {participant_identity}")
                await self._finalize_participant_recording(participant_identity)

            else:
                logger.debug(f"📡 Egress control message: {control_data}")

        except Exception as e:
            logger.error(f"❌ Error handling egress control message: {e}")

    async def _handle_websocket_message(self, websocket, data: dict):
        """Handle incoming WebSocket messages from monitoring clients"""
        try:
            message_type = data.get("type")

            if message_type == "subscribe_participant":
                # Client wants to subscribe to specific participant audio
                participant_identity = data.get("participant_identity")
                logger.info(
                    f"📡 Client subscribed to participant: {participant_identity}"
                )

                # Send current recording status
                recording_status = await self.get_recording_status(participant_identity)
                if recording_status:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "recording_status",
                                "participant_identity": participant_identity,
                                "status": recording_status,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )

            elif message_type == "get_all_recordings":
                # Client wants status of all recordings
                all_recordings = await self.get_all_recordings_status()
                await websocket.send(
                    json.dumps(
                        {
                            "type": "all_recordings_status",
                            "recordings": all_recordings,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )

        except Exception as e:
            logger.error(f"❌ Error handling WebSocket message: {e}")

    def _calculate_buffer_duration(self, participant_identity: str) -> float:
        """Calculate total duration of buffered audio for a participant"""
        if participant_identity not in self.audio_buffers:
            return 0.0

        total_samples = 0
        for chunk in self.audio_buffers[participant_identity]:
            samples = len(chunk.audio_data) // self.bytes_per_sample
            total_samples += samples

        return total_samples / self.sample_rate

    async def _save_audio_chunk_to_s3(self, participant_identity: str):
        """Convert buffered audio to WAV and save to S3"""
        try:
            if participant_identity not in self.audio_buffers:
                return

            chunks = self.audio_buffers[participant_identity]
            if not chunks:
                return

            # Combine all buffered audio data
            combined_audio = b""
            for chunk in chunks:
                combined_audio += chunk.audio_data

            # Convert to WAV format
            wav_data = self._convert_pcm_to_wav(combined_audio)

            # Generate S3 object name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            first_chunk_num = chunks[0].chunk_number
            last_chunk_num = chunks[-1].chunk_number
            object_name = f"participants/{self.room_name}/{participant_identity}/chunk_{first_chunk_num}_{last_chunk_num}_{timestamp}.wav"

            # Upload to S3/MinIO
            if self.minio_client:
                bucket_name = os.getenv("MINIO_BUCKET", "livekit-recordings")

                self.minio_client.put_object(
                    bucket_name,
                    object_name,
                    io.BytesIO(wav_data),
                    length=len(wav_data),
                    content_type="audio/wav",
                )

                logger.info(f"✅ Saved audio chunk to S3: {object_name}")
                logger.info(
                    f"📊 Chunk size: {len(wav_data)} bytes, Duration: {self._calculate_buffer_duration(participant_identity):.2f}s"
                )

            # Clear buffer after saving
            self.audio_buffers[participant_identity] = []

        except Exception as e:
            logger.error(f"❌ Error saving audio chunk to S3: {e}")

    def _convert_pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """Convert raw PCM data to WAV format"""
        try:
            # Create WAV file in memory
            wav_buffer = io.BytesIO()

            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(self.channels)  # Mono
                wav_file.setsampwidth(self.bytes_per_sample)  # 16-bit
                wav_file.setframerate(self.sample_rate)  # 48kHz
                wav_file.writeframes(pcm_data)

            wav_buffer.seek(0)
            return wav_buffer.getvalue()

        except Exception as e:
            logger.error(f"❌ Error converting PCM to WAV: {e}")
            return pcm_data  # Return original data as fallback

    async def _finalize_participant_recording(self, participant_identity: str):
        """Finalize recording by saving any remaining buffered audio"""
        try:
            if (
                participant_identity in self.audio_buffers
                and self.audio_buffers[participant_identity]
            ):
                logger.info(f"🏁 Finalizing recording for {participant_identity}")
                await self._save_audio_chunk_to_s3(participant_identity)

            # Update recording status
            if participant_identity in self.participant_recordings:
                recording_info = self.participant_recordings[participant_identity]
                recording_info.recording_status = "completed"
                recording_info.completed_at = datetime.now()
                logger.info(f"✅ Recording finalized for {participant_identity}")
                logger.info(f"📊 Total chunks: {recording_info.chunks_received}")
                logger.info(f"📊 Total duration: {recording_info.total_duration:.2f}s")

        except Exception as e:
            logger.error(f"❌ Error finalizing recording: {e}")

    async def _broadcast_audio_chunk_to_clients(
        self, participant_identity: str, audio_data: bytes
    ):
        """Broadcast audio chunk to connected monitoring clients"""
        if not self.websocket_clients:
            return

        try:
            # Encode audio data for transmission
            encoded_audio = base64.b64encode(audio_data).decode("utf-8")

            message = {
                "type": "audio_chunk",
                "participant_identity": participant_identity,
                "audio_data": encoded_audio,
                "timestamp": datetime.now().isoformat(),
                "format": "PCM_S16LE",
                "sample_rate": self.sample_rate,
                "channels": self.channels,
            }

            # Broadcast to all connected clients
            disconnected_clients = set()
            for client in self.websocket_clients:
                try:
                    await client.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send audio chunk to client: {e}")
                    disconnected_clients.add(client)

            # Remove disconnected clients
            self.websocket_clients -= disconnected_clients

        except Exception as e:
            logger.error(f"❌ Error broadcasting audio chunk: {e}")

    async def cleanup(self):
        """Cleanup resources and stop all recordings"""
        try:
            logger.info("🧹 Cleaning up TrackEgressManager...")

            # Stop all active recordings
            stop_results = await self.stop_all_recordings()
            logger.info(f"📊 Stop results: {stop_results}")

            # Close WebSocket server
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
                logger.info("🌐 WebSocket server closed")

            # Close LiveKit API client
            if self.livekit_client:
                await self.livekit_client.aclose()
                logger.info("🔌 LiveKit API client closed")

            logger.info("✅ TrackEgressManager cleanup completed")

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

    async def cleanup_all_recordings(self):
        """Alias for cleanup method to match the expected interface"""
        await self.cleanup()


# Utility functions for integration with existing system


async def create_track_egress_manager(room_name: str) -> TrackEgressManager:
    """
    Factory function to create and initialize a TrackEgressManager

    Args:
        room_name: The LiveKit room name

    Returns:
        Initialized TrackEgressManager instance
    """
    manager = TrackEgressManager(room_name)
    await manager.initialize()
    return manager


def get_participant_audio_tracks(room: rtc.Room) -> Dict[str, str]:
    """
    Get mapping of participant identities to their audio track IDs

    Args:
        room: LiveKit Room instance

    Returns:
        Dict mapping participant identity to audio track ID
    """
    audio_tracks = {}

    for participant in room.remote_participants.values():
        for publication in participant.track_publications.values():
            if publication.track and publication.track.kind == rtc.TrackKind.AUDIO:
                audio_tracks[participant.identity] = publication.track.sid
                break

    return audio_tracks


async def ensure_minio_bucket(minio_client: Minio, bucket_name: str):
    """Ensure MinIO bucket exists"""
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"✅ Created MinIO bucket: {bucket_name}")
    except Exception as e:
        logger.error(f"❌ Failed to create MinIO bucket: {e}")
        raise


async def monitor_egress_status(livekit_client, egress_id: str):
    """Monitor egress status and log updates"""
    try:
        while True:
            egress_list = await livekit_client.egress.list_egress(
                api.ListEgressRequest()
            )

            for egress in egress_list.items:
                if egress.egress_id == egress_id:
                    logger.info(f"📊 Egress {egress_id} status: {egress.status}")
                    if egress.status in [
                        api.EgressStatus.EGRESS_COMPLETE,
                        api.EgressStatus.EGRESS_FAILED,
                    ]:
                        return egress.status
                    break

            await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"❌ Error monitoring egress: {e}")
        return None
