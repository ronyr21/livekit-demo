#!/usr/bin/env python3
"""
Simple test script for admin monitoring functionality
"""

import os
from admin_monitor import SimpleAdminMonitor
from admin_auth import SimpleAdminAuth


def test_admin_functionality():
    print("🧪 Testing Admin Monitoring Functionality")
    print("=" * 50)

    try:
        # Check environment variables
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")

        if not api_key or not api_secret:
            print("❌ Missing LiveKit credentials in environment")
            print("Please ensure LIVEKIT_API_KEY and LIVEKIT_API_SECRET are set")
            return False

        print(f"✅ LiveKit API Key found: {api_key[:8]}...")

        # Test admin auth
        print("\n🔐 Testing Admin Authentication...")
        auth = SimpleAdminAuth()

        # Test token generation
        test_room = "test-room-123"
        admin_token = auth.generate_admin_access_token(test_room)
        print(f"✅ Admin access token generated: {admin_token[:50]}...")

        # Test admin monitor
        print("\n📡 Testing Admin Monitor...")
        monitor = SimpleAdminMonitor()

        # Test admin token generation via monitor
        monitor_token = monitor.generate_admin_token(test_room)
        print(f"✅ Monitor token generated: {monitor_token[:50]}...")

        print("\n🎉 All tests passed! Admin monitoring is ready.")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_admin_functionality()
