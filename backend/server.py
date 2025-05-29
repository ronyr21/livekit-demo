import os
import time
import uuid
import logging
from datetime import datetime
from livekit import api
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
from livekit.api import LiveKitAPI, ListRoomsRequest
from datetime import datetime
import time

# Import admin monitoring modules
from admin_monitor import SimpleAdminMonitor
from admin_auth import SimpleAdminAuth

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize admin services
admin_monitor = SimpleAdminMonitor()
admin_auth = SimpleAdminAuth()


async def generate_room_name():
    name = "room-" + str(uuid.uuid4())[:8]
    rooms = await get_rooms()
    while name in rooms:
        name = "room-" + str(uuid.uuid4())[:8]
    return name


async def get_rooms():
    api = LiveKitAPI()
    rooms = await api.room.list_rooms(ListRoomsRequest())
    await api.aclose()
    return [room.name for room in rooms.rooms]


@app.route("/getToken")
async def get_token():
    name = request.args.get("name", "my name")
    room = request.args.get("room", None)

    if not room:
        room = await generate_room_name()

    token = (
        api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))
        .with_identity(name)
        .with_name(name)
        .with_grants(api.VideoGrants(room_join=True, room=room))
    )

    return token.to_jwt()


# ============================================================================
# ADMIN MONITORING ENDPOINTS
# ============================================================================


@app.route("/admin/status")
async def admin_status():
    """Health check endpoint for admin services"""
    try:
        # Test admin services
        cache_info = admin_auth.get_cache_info()

        return jsonify(
            {
                "status": "healthy",
                "admin_auth": "available",
                "admin_monitor": "available",
                "cache_info": cache_info,
                "timestamp": str(datetime.utcnow()),
            }
        )
    except Exception as e:
        logger.error(f"Admin status check failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/admin/rooms")
async def list_admin_rooms():
    """List all active rooms for admin dashboard"""
    try:
        logger.info(
            "📋 Admin requesting room list"
        )  # Get active rooms using admin monitor (already returns formatted dict list)
        room_list = await admin_monitor.get_active_rooms()

        logger.info(f"✅ Found {len(room_list)} active rooms")

        return jsonify(
            {"success": True, "rooms": room_list, "total_rooms": len(room_list)}
        )

    except Exception as e:
        logger.error(f"❌ Failed to list rooms: {e}")
        return jsonify({"success": False, "error": str(e), "rooms": []}), 500


@app.route("/admin/monitor/<room_name>", methods=["POST"])
async def get_monitor_token(room_name):
    """Generate admin monitoring token for specific room"""
    try:
        logger.info(f"🎟️ Admin requesting monitor token for room: {room_name}")

        # Get admin identity from request (optional)
        data = request.get_json() or {}
        admin_identity = data.get("admin_identity")

        # Generate admin monitoring token
        token = admin_auth.generate_admin_access_token(room_name, admin_identity)

        logger.info(f"✅ Monitor token generated for room: {room_name}")

        return jsonify(
            {
                "success": True,
                "token": token,
                "room_name": room_name,
                "admin_identity": admin_identity or f"admin_{int(time.time())}",
                "instructions": {
                    "usage": "Use this token to join the room as a hidden participant",
                    "livekit_url": os.getenv("LIVEKIT_URL", ""),
                    "note": "Admin will be invisible to other participants",
                },
            }
        )

    except Exception as e:
        logger.error(f"❌ Failed to generate monitor token: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/admin/token/<room_name>")
async def get_admin_token(room_name):
    """Quick admin token endpoint (GET method)"""
    try:
        logger.info(f"🎟️ Quick admin token request for room: {room_name}")

        # Generate token using admin monitor
        token = admin_monitor.generate_admin_token(room_name)

        return jsonify({"success": True, "token": token, "room_name": room_name})

    except Exception as e:
        logger.error(f"❌ Failed to generate admin token: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/admin/rooms/list-token")
async def get_room_list_token():
    """Generate token for room listing (if needed by frontend)"""
    try:
        logger.info("🎟️ Generating room list token")

        token = admin_auth.generate_room_list_token()

        return jsonify(
            {
                "success": True,
                "token": token,
                "usage": "Use for LiveKit API calls to list rooms",
            }
        )

    except Exception as e:
        logger.error(f"❌ Failed to generate room list token: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# END ADMIN MONITORING ENDPOINTS
# ============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
