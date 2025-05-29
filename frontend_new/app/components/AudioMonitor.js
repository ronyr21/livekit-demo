"use client";

import { useState, useEffect, useCallback } from 'react';
import { LiveKitRoom, RoomAudioRenderer, useRoomContext } from '@livekit/components-react';
import '@livekit/components-styles';
import Image from "next/image";
import styles from './AudioMonitor.module.css';

// Component to show monitoring status inside the LiveKit room
const MonitoringStatus = ({ room, onStop, onError }) => {
  const roomContext = useRoomContext();
  const [participants, setParticipants] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    if (roomContext && roomContext.participants) {
      // Update participants list
      const updateParticipants = () => {
        if (roomContext.participants) {
          const allParticipants = Array.from(roomContext.participants.values());
          setParticipants(allParticipants);
        }
      };

      // Update connection status
      const updateConnectionStatus = () => {
        if (roomContext.connectionState) {
          setConnectionStatus(roomContext.connectionState);
          setIsListening(roomContext.connectionState === 'connected');
        }
      };

      // Set up event listeners
      roomContext.on('participantConnected', updateParticipants);
      roomContext.on('participantDisconnected', updateParticipants);
      roomContext.on('connectionStateChanged', updateConnectionStatus);

      // Initial update
      updateParticipants();
      updateConnectionStatus();

      return () => {
        roomContext.off('participantConnected', updateParticipants);
        roomContext.off('participantDisconnected', updateParticipants);
        roomContext.off('connectionStateChanged', updateConnectionStatus);
      };
    }
  }, [roomContext]);

  const handleStopListening = () => {
    if (roomContext) {
      roomContext.disconnect();
    }
    onStop();
  };

  return (
    <div className={styles.monitoringContainer}>
      {/* Header */}
      <div className={styles.monitoringHeader}>
        <div className={styles.headerInfo}>
          <h3 className={styles.roomTitle}>{room.summaryTitle || 'Monitoring Call'}</h3>
          <div className={styles.roomDetails}>
            <span>{room.identifier}</span>
            <span>•</span>
            <span>Live Audio</span>
          </div>
        </div>
        <div className={styles.connectionStatus}>
          <div className={`${styles.statusDot} ${styles[connectionStatus]}`}></div>
          <span className={styles.statusText}>
            {connectionStatus === 'connected' && 'Connected'}
            {connectionStatus === 'connecting' && 'Connecting...'}
            {connectionStatus === 'disconnected' && 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Audio Visualization */}
      <div className={styles.audioSection}>
        <div className={styles.audioVisualization}>
          {isListening ? (
            <div className={styles.waveContainer}>
              <Image
                src="/call_wave.svg"
                alt="Audio Wave"
                width={300}
                height={40}
                className={styles.audioWave}
              />
              <div className={styles.listeningText}>🎧 Listening to live audio...</div>
            </div>
          ) : (
            <div className={styles.noAudio}>
              <div className={styles.noAudioText}>Connecting to audio stream...</div>
            </div>
          )}
        </div>
      </div>

      {/* Participants Info */}
      <div className={styles.participantsSection}>
        <h4 className={styles.participantsTitle}>
          👥 Participants ({participants.length})
        </h4>
        {participants.length === 0 ? (
          <p className={styles.noParticipants}>No participants in the call</p>
        ) : (
          <div className={styles.participantsList}>
            {participants.map((participant) => (
              <div key={participant.sid} className={styles.participantItem}>
                <span className={styles.participantName}>
                  {participant.identity}
                  {participant.isLocal && ' (Admin - Hidden)'}
                </span>
                <div className={styles.participantStatus}>
                  {participant.isSpeaking && (
                    <span className={styles.speaking}>🎤</span>
                  )}
                  {participant.audioTrack?.isEnabled && (
                    <span className={styles.audio}>🔊</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Control Button */}
      <div className={styles.controlSection}>
        <button 
          onClick={handleStopListening}
          className={styles.stopButton}
        >
          <Image
            src="/call_stop.svg"
            alt="Stop"
            width={20}
            height={20}
          />
          <span>Stop Listening</span>
        </button>
      </div>
    </div>
  );
};

const AudioMonitor = ({ room, onStop }) => {
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Function to get admin token for monitoring
  const getMonitoringToken = useCallback(async () => {
    try {
      console.log(`🎟️ Getting monitoring token for room: ${room.agentName}`);
      setLoading(true);
      setError(null);
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001';
      // Use identifier as room name (this should match the actual room name)
      const roomName = room.identifier || room.agentName;
      console.log(`🔍 Room object:`, room);
      console.log(`📡 Using room name: ${roomName}`);
      
      const monitorUrl = `${apiBaseUrl}/admin/monitor/${encodeURIComponent(roomName)}`;
      console.log(`📡 Making request to: ${monitorUrl}`);
      
      const response = await fetch(monitorUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          admin_identity: `admin_${Date.now()}`
        })      });

      console.log(`📊 Response status: ${response.status}`);
      const data = await response.json();
      console.log(`📦 Response data:`, data);      if (data.success) {
        setToken(data.token);
        console.log('✅ Got monitoring token successfully');
        console.log('🎟️ Token length:', data.token?.length);
        console.log('🏠 LiveKit URL from backend:', data.instructions?.livekit_url);
        console.log('🔗 Frontend LiveKit URL:', process.env.NEXT_PUBLIC_LIVEKIT_URL);
        console.log('🆔 Admin identity:', data.admin_identity);
        console.log('🏠 Room name in response:', data.room_name);
      } else {
        throw new Error(data.error || 'Failed to get monitoring token');
      }
    } catch (err) {
      console.error('❌ Error getting monitoring token:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [room]);

  // Get token when component loads
  useEffect(() => {
    getMonitoringToken();
  }, [getMonitoringToken]);

  // Handle connection errors
  const handleDisconnected = useCallback(() => {
    console.log('🔌 Disconnected from monitoring session');
    onStop();
  }, [onStop]);
  const handleError = useCallback((error) => {
    console.error('❌ LiveKit error:', error);
    console.error('❌ Error details:', {
      message: error.message,
      code: error.code,
      stack: error.stack,
      name: error.name
    });
    setError(error.message || 'Unknown connection error');
  }, []);

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.loadingContent}>
          <div className={styles.loadingSpinner}></div>
          <h3>Connecting to Monitor</h3>
          <p>Joining call: <strong>{room.agentName}</strong></p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <div className={styles.errorContent}>
          <h3>❌ Connection Error</h3>
          <p>Failed to connect to: <strong>{room.agentName}</strong></p>
          <p className={styles.errorMessage}>{error}</p>
          <div className={styles.errorActions}>
            <button onClick={getMonitoringToken} className={styles.retryButton}>
              🔄 Try Again
            </button>
            <button onClick={onStop} className={styles.backButton}>
              ← Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className={styles.noTokenContainer}>
        <div className={styles.noTokenContent}>
          <h3>🔐 Authorization Required</h3>
          <p>Unable to get monitoring token for: <strong>{room.agentName}</strong></p>
          <button onClick={getMonitoringToken} className={styles.retryButton}>
            🔄 Retry
          </button>
          <button onClick={onStop} className={styles.backButton}>
            ← Back
          </button>
        </div>
      </div>
    );
  }  return (
    <div className={styles.audioMonitorContainer}>      
    <LiveKitRoom
        serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
        token={token}
        connect={true} 
        video={false}  // Admin doesn't publish video, only receives
        audio={false}  // Admin doesn't publish audio, only receives
        onDisconnected={handleDisconnected}
        onError={handleError}
        onConnected={() => {
          console.log('✅ Successfully connected to LiveKit room');
          console.log('🏠 Server URL:', process.env.NEXT_PUBLIC_LIVEKIT_URL);
          console.log('🎟️ Token preview:', token?.substring(0, 50) + '...');
        }}
        options={{
          // Monitor-only mode: don't capture any media
          audio: false,
          video: false,
          // Enable debugging
          logLevel: 'debug',
        }}
      >
        {/* This component renders the audio from all participants */}
        <RoomAudioRenderer />
        
        {/* Our custom monitoring interface */}
        <MonitoringStatus 
          room={room} 
          onStop={onStop}
          onError={handleError}
        />
      </LiveKitRoom>
    </div>
  );
};

export default AudioMonitor;
