import { useState, useEffect, useCallback } from 'react';
import { LiveKitRoom, RoomAudioRenderer, useRoomContext } from '@livekit/components-react';
import '@livekit/components-styles';
import './AdminDashboard.css';

// Component to show monitoring status inside the LiveKit room
const MonitoringStatus = ({ room, onBack }) => {
  const roomContext = useRoomContext();
  const [participants, setParticipants] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
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

  return (
    <div className="monitoring-status">
      <div className="monitoring-header">
        <h2>🎧 Monitoring: {room.name}</h2>
        <button onClick={onBack} className="back-button">
          ← Back to Dashboard
        </button>
      </div>
      
      <div className="connection-info">
        <div className={`status-indicator ${connectionStatus}`}>
          <span className="status-dot"></span>
          {connectionStatus === 'connected' && '🟢 Connected'}
          {connectionStatus === 'connecting' && '🟡 Connecting...'}
          {connectionStatus === 'disconnected' && '🔴 Disconnected'}
        </div>
      </div>

      <div className="participants-info">
        <h3>👥 Participants in Call ({participants.length})</h3>
        {participants.length === 0 ? (
          <p>No participants currently in the call</p>
        ) : (
          <div className="participants-list">
            {participants.map((participant) => (
              <div key={participant.sid} className="participant-card">
                <span className="participant-name">
                  {participant.identity}
                  {participant.isLocal && ' (You - Hidden Admin)'}
                </span>
                <div className="participant-status">
                  {participant.isSpeaking && <span className="speaking">🎤 Speaking</span>}
                  {participant.audioTrack?.isEnabled && <span className="audio">🔊 Audio</span>}
                  {participant.videoTrack?.isEnabled && <span className="video">📹 Video</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="monitoring-instructions">
        <h3>🎧 Audio Monitoring</h3>
        <p>• You are listening as a <strong>hidden participant</strong></p>
        <p>• Other participants cannot see or hear you</p>
        <p>• Audio will play through your speakers/headphones</p>
        <p>• You can only listen, not speak</p>
      </div>
    </div>
  );
};

const AdminMonitor = ({ room, onBack }) => {
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Function to get admin token for monitoring
  const getMonitoringToken = useCallback(async () => {
    try {      console.log(`🎟️ Getting monitoring token for room: ${room.name}`);
      setLoading(true);
      setError(null);
      
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
      const response = await fetch(`${apiBaseUrl}/admin/monitor/${room.name}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          admin_identity: `admin_${Date.now()}`
        })
      });

      const data = await response.json();

      if (data.success) {
        setToken(data.token);
        console.log('✅ Got monitoring token successfully');
      } else {
        throw new Error(data.error || 'Failed to get monitoring token');
      }
    } catch (err) {
      console.error('❌ Error getting monitoring token:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [room.name]);

  // Get token when component loads
  useEffect(() => {
    getMonitoringToken();
  }, [getMonitoringToken]);

  // Handle connection errors
  const handleDisconnected = useCallback(() => {
    console.log('🔌 Disconnected from monitoring session');
    // Could auto-reconnect here if needed
  }, []);

  if (loading) {
    return (
      <div className="admin-monitor loading">
        <div className="loading-content">
          <h2>🔄 Connecting to Monitor Room</h2>
          <p>Getting authorization to monitor: <strong>{room.name}</strong></p>
          <div className="loading-spinner"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-monitor error">
        <div className="error-content">
          <h2>❌ Connection Error</h2>
          <p>Failed to connect to room: <strong>{room.name}</strong></p>
          <p className="error-message">{error}</p>
          <div className="error-actions">
            <button onClick={getMonitoringToken}>🔄 Try Again</button>
            <button onClick={onBack}>← Back to Dashboard</button>
          </div>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="admin-monitor no-token">
        <div className="no-token-content">
          <h2>🔐 Authorization Required</h2>
          <p>Unable to get monitoring token for: <strong>{room.name}</strong></p>
          <button onClick={getMonitoringToken}>🔄 Retry</button>
          <button onClick={onBack}>← Back to Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-monitor connected">
      <LiveKitRoom
        serverUrl={import.meta.env.VITE_LIVEKIT_URL}
        token={token}
        connect={true}
        video={false}  // Admin doesn't need video
        audio={true}   // Admin needs to hear audio
        onDisconnected={handleDisconnected}
      >
        {/* This component renders the audio from all participants */}
        <RoomAudioRenderer />
        
        {/* Our custom monitoring interface */}
        <MonitoringStatus room={room} onBack={onBack} />
      </LiveKitRoom>
    </div>
  );
};

export default AdminMonitor;
