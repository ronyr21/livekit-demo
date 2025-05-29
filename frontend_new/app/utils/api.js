"use client";

// API utility functions for backend communication
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001';

export class ApiService {
  static async fetchRooms() {
    try {
      console.log('🔄 Fetching active rooms from backend...');
      const response = await fetch(`${API_BASE_URL}/admin/rooms`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      
      if (data.success) {
        console.log(`✅ Found ${data.rooms.length} active rooms`);
        return data.rooms;
      } else {
        throw new Error(data.error || 'Failed to fetch rooms');
      }
    } catch (error) {
      console.error('❌ Error fetching rooms:', error);
      throw error;
    }
  }

  static async getMonitoringToken(roomName, adminIdentity = `admin_${Date.now()}`) {
    try {
      console.log(`🎟️ Getting monitoring token for room: ${roomName}`);
      const response = await fetch(`${API_BASE_URL}/admin/monitor/${roomName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          admin_identity: adminIdentity
        })
      });

      const data = await response.json();

      if (data.success) {
        console.log('✅ Got monitoring token successfully');
        return data.token;
      } else {
        throw new Error(data.error || 'Failed to get monitoring token');
      }
    } catch (error) {
      console.error('❌ Error getting monitoring token:', error);
      throw error;
    }
  }

  static async checkAdminStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/status`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('❌ Error checking admin status:', error);
      throw error;
    }
  }
}

// Transform backend room data to match frontend interface
export function transformRoomData(backendRooms) {
  return backendRooms.map((room, index) => ({
    agentName: room.name || `Room ${index + 1}`,
    summaryTitle: `Live Call in Progress`,
    identifier: room.name || `room-${index}`,
    type: "Live", // All real rooms are considered live
    participants: room.num_participants || 0,
    createdAt: room.creation_time || Date.now(),
    metadata: room.metadata || {}
  }));
}

// Format duration from timestamp
export function formatDuration(startTime) {
  if (!startTime) return "00m 00s";
  
  const now = Date.now();
  const duration = Math.floor((now - startTime) / 1000);
  const minutes = Math.floor(duration / 60);
  const seconds = duration % 60;
  
  return `${minutes.toString().padStart(2, '0')}m ${seconds.toString().padStart(2, '0')}s`;
}

// Check if backend is available
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/status`);
    return response.ok;
  } catch {
    return false;
  }
}
