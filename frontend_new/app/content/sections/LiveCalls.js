import { Bell, User, Search } from "lucide-react";
import Image from "next/image";
import styles from "../content.module.css";
import { useState, useEffect } from "react";
import AudioMonitor from "@/app/components/AudioMonitor";
import { ApiService, transformRoomData, formatDuration, checkBackendHealth } from "@/app/utils/api";
import { mockCallList } from "@/app/models/MockedData";


export default function LiveCalls() {
  const [selectedCall, setSelectedCall] = useState(null);
  const [liveRooms, setLiveRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [backendAvailable, setBackendAvailable] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // Check backend health and fetch rooms
  const fetchRooms = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Check if backend is available
      const isHealthy = await checkBackendHealth();
      setBackendAvailable(isHealthy);
      
      if (isHealthy) {
        // Fetch real rooms from backend
        const rooms = await ApiService.fetchRooms();
        const transformedRooms = transformRoomData(rooms);
        setLiveRooms(transformedRooms);
      } else {
        // Use mock data if backend is not available
        console.log('⚠️ Backend not available, using mock data');
        setLiveRooms(mockCallList);
      }
    } catch (err) {
      console.error('❌ Error fetching rooms:', err);
      setError(err.message);
      // Fallback to mock data on error
      setLiveRooms(mockCallList);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh rooms every 10 seconds
  useEffect(() => {
    fetchRooms();
    
    const interval = setInterval(fetchRooms, 10000);
    return () => clearInterval(interval);
  }, []);

  // Filter rooms based on search term
  const filteredLiveRooms = liveRooms.filter(room => 
    room.agentName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    room.summaryTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
    room.identifier.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleMonitorCall = (room) => {
    console.log(`🔍 Starting to monitor room: ${room.agentName}`);
    setSelectedCall(room);
  };

  const handleStopMonitoring = () => {
    console.log('⏹️ Stopping monitoring session');
    setSelectedCall(null);
  };

  // Helper to wrap names only if needed
  function formatName(name) {
    // Use a span with CSS to allow wrapping only if needed
    return name;
  }

  return (
    <div className={styles.maincontent}>
      {/* Header row with subtitle and controls */}
      <div className={`${styles.headerRow} mb-4`}>
        {/* Subtitle */}
        <h2 className={styles.subtitle}>Live Calls</h2>
        {/* Right controls */}
        <div className={styles.controls}>
          {/* Search bar */}          <div className="flex items-center bg-[#F4F7FE] rounded-full px-3 py-1" style={{ marginRight: '8px' }}>
            <Search size={16} color="#2B3674" />
            <input
              type="text"
              placeholder="Search rooms..."
              className={styles.searchBar}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Notification icon */}
          <div className={styles.notificationIcon}>
            <Bell size={20} color="#A3AED0" />
          </div>
          {/* User icon */}
          <div className={styles.userIcon}>
            <User size={18} color="#3d3d63" />
          </div>
        </div>
      </div>      <div className={styles.agentMainContainer}>
        <div className={styles.agentContainer}>
          {/* Main content card */}
          <div className={styles.contentCard}>
            {/* Backend Status Indicator */}
            {!backendAvailable && (
              <div className={styles.statusBanner}>
                ⚠️ Backend not available - showing demo data
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className={styles.loadingSection}>
                <div className={styles.loadingSpinner}></div>
                <p>Loading active calls...</p>
              </div>
            )}

            {/* Error State */}
            {error && !loading && (
              <div className={styles.errorSection}>
                <p>❌ Error: {error}</p>
                <button onClick={fetchRooms} className={styles.retryButton}>
                  🔄 Retry
                </button>
              </div>
            )}

            {/* Live Calls */}
            {!loading && (
              <>
                <div className={styles.liveAgentsTitle}>
                  {backendAvailable ? 'Live Calls' : 'Demo Calls'} ({filteredLiveRooms.length})
                  {backendAvailable && (
                    <span className={styles.liveIndicator}>🟢 Live</span>
                  )}
                </div>
                <div className={styles.grid}>
                  {filteredLiveRooms.length === 0 ? (
                    <div className={styles.noCalls}>
                      {searchTerm ? 'No calls found matching your search' : 'No active calls at the moment'}
                    </div>
                  ) : (
                    filteredLiveRooms.map((data, idx) => (
                      <div
                        className={styles.gridItem}
                        key={`${data.identifier}-${idx}`}
                        onClick={() => handleMonitorCall(data)}
                        style={{ cursor: "pointer" }}
                      >
                        <div className={styles.gridItemIcon}>
                          <span className={styles.gridItemName}>{formatName(data.agentName)}</span>
                        </div>
                        <div className={styles.gridItemText}>
                          <span className={styles.gridItemTitle}>{data.summaryTitle}</span>
                          <span className={styles.gridItemSubtext}>
                            {data.identifier} • {backendAvailable ? formatDuration(data.createdAt) : '01m46s'}
                          </span>
                        </div>
                        <div className={styles.gridItemSvg}>
                          <Image
                            src="/Headphones_Icon.svg"
                            alt="Monitor Call"
                            width={22}
                            height={22}
                          />
                        </div>
                      </div>
                    ))
                  )}
                </div>
                
                {/* Virtual Agents - Only show in demo mode */}
                {!backendAvailable && (
                  <>
                    <div className={styles.liveAgentsTitle} style={{ marginTop: 32 }}>
                      Virtual Agents ({mockCallList.filter(call => call.type === "Virtual").length})
                    </div>
                    <div className={styles.grid}>
                      {mockCallList
                      .filter(call => call.type === "Virtual") 
                      .map((data, idx) => (
                        <div
                          className={styles.gridItem}
                          key={`virtual-${idx}`}
                          onClick={() => handleMonitorCall(data)}
                          style={{ cursor: "pointer" }}
                        >
                          <div
                            className={styles.gridItemIcon}
                            style={{ background: "#9b38f6" }}
                          >
                            <span className={styles.gridItemName}>{formatName(data.agentName)}</span>
                          </div>
                          <div className={styles.gridItemText}>
                            <span className={styles.gridItemTitle}>{data.summaryTitle}</span>
                            <span className={styles.gridItemSubtext}>
                              {data.identifier} • 01m46s
                            </span>
                          </div>
                          <div className={styles.gridItemSvg}>
                            <Image
                              src="/Headphones_Icon.svg"
                              alt="Monitor Call"
                              width={22}
                              height={22}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </>
            )}

            {/* Leave space for footer */}
            <div style={{ height: 40 }} />
          </div>

          {/* Audio Monitoring Panel */}
          {selectedCall && (
            <div className={styles.callPanel}>
              <AudioMonitor 
                room={selectedCall} 
                onStop={handleStopMonitoring}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
