import { useState, useEffect } from 'react';
import AdminMonitor from './AdminMonitor';
import './AdminDashboard.css';

const AdminDashboard = () => {
  // State to store the list of rooms and other UI states
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(null);  // Function to fetch rooms from our backend API
  const fetchRooms = async () => {
    try {
      console.log('🔄 Fetching active rooms...');
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
      const response = await fetch(`${apiBaseUrl}/admin/rooms`);
      const data = await response.json();
      
      if (data.success) {
        setRooms(data.rooms);
        setError(null);
        console.log(`✅ Found ${data.rooms.length} active rooms`);
      } else {
        throw new Error(data.error || 'Failed to fetch rooms');
      }
    } catch (err) {
      console.error('❌ Error fetching rooms:', err);
      setError(err.message);
      setRooms([]);
    } finally {
      setLoading(false);
    }
  };

  // Load rooms when component starts and set up auto-refresh
  useEffect(() => {
    fetchRooms();
    
    // Refresh room list every 10 seconds
    const interval = setInterval(fetchRooms, 10000);
    setRefreshInterval(interval);
    
    // Cleanup interval when component is destroyed
    return () => {
      if (interval) clearInterval(interval);
    };
  }, []);
  // Function to handle when admin clicks "Monitor" button
  const handleMonitorRoom = (room) => {
    console.log(`🔍 Starting to monitor room: ${room.name}`);
    console.log('🔍 Room object:', room);
    console.log('🔍 Setting selectedRoom state...');
    setSelectedRoom(room);
    console.log('🔍 selectedRoom state set');
  };

  // Function to stop monitoring and return to room list
  const handleStopMonitoring = () => {
    console.log('⏹️ Stopping room monitoring');
    setSelectedRoom(null);
  };
  // If user is monitoring a specific room, show the monitor component
  if (selectedRoom) {
    console.log('📺 Rendering AdminMonitor for room:', selectedRoom.name);
    return (
      <AdminMonitor 
        room={selectedRoom} 
        onBack={handleStopMonitoring}
      />
    );
  }

  // Main admin dashboard view
  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1>🎛️ Call Center Admin Dashboard</h1>
        <p>Monitor active calls in real-time</p>
        <button 
          onClick={fetchRooms} 
          disabled={loading}
          className="refresh-button"
        >
          {loading ? '🔄 Loading...' : '🔄 Refresh'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <h3>❌ Error</h3>
          <p>{error}</p>
          <button onClick={fetchRooms}>Try Again</button>
        </div>
      )}

      <div className="rooms-section">
        <h2>📞 Active Calls ({rooms.length})</h2>
        
        {loading ? (
          <div className="loading">
            <p>🔄 Loading active rooms...</p>
          </div>
        ) : rooms.length === 0 ? (
          <div className="no-rooms">
            <h3>📭 No Active Calls</h3>
            <p>There are currently no ongoing calls to monitor.</p>
            <p>💡 Start a call from the main interface to test monitoring.</p>
          </div>
        ) : (
          <div className="rooms-grid">
            {rooms.map((room) => (
              <div key={room.sid} className="room-card">
                <div className="room-header">
                  <h3>📞 {room.name}</h3>
                  <span className="room-status">🟢 Live</span>
                </div>
                  <div className="room-details">
                  <p><strong>👥 Participants:</strong> {room.participant_count}</p>
                  <p><strong>🎤 Active Speakers:</strong> {room.num_publishers}</p>
                  <p><strong>🕐 Started:</strong> {new Date(room.creation_time).toLocaleTimeString()}</p>
                  {room.metadata && (
                    <p><strong>📝 Notes:</strong> {room.metadata}</p>
                  )}
                </div>
                  <div className="room-actions">
                  <button 
                    className="monitor-button"
                    onClick={() => {
                      console.log('🖱️ Monitor button clicked for room:', room.name);
                      handleMonitorRoom(room);
                    }}
                    title="Join this call as a hidden listener"
                  >
                    🎧 Monitor Call
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="admin-footer">
        <p>🔒 You are logged in as Admin • Monitoring is invisible to call participants</p>
        <p>🔄 Room list refreshes automatically every 10 seconds</p>
      </div>
    </div>
  );
};

export default AdminDashboard;
