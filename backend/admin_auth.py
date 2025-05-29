"""
Admin Authentication Service for LiveKit Call Center
==================================================

Simplified authentication service for admin monitoring functionality.
This module handles token generation and basic admin access control
for the demo version (no complex auth required).

Based on ADMIN_MONITORING_demo.md - STEP 1: Core Admin Monitor Service
"""

import os
import time
import logging
from typing import Optional
from datetime import datetime, timedelta

from livekit import api
from livekit.api import AccessToken
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger("admin_auth")
logger.setLevel(logging.INFO)


class AdminAuthError(Exception):
    """Custom exception for admin authentication errors"""

    pass


class SimpleAdminAuth:
    """
    Simplified admin authentication service for demo purposes.

    This class handles:
    - Admin token generation with proper permissions
    - Token validation and refresh
    - Simple access control (no complex auth for demo)
    """

    def __init__(self):
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")

        # Validate required environment variables
        if not all([self.api_key, self.api_secret]):
            raise AdminAuthError(
                "Missing required LiveKit environment variables: "
                "LIVEKIT_API_KEY, LIVEKIT_API_SECRET"
            )

        # Token cache for efficiency (simple in-memory cache for demo)
        self.token_cache = {}

        logger.info("🔐 SimpleAdminAuth initialized")
        logger.info(f"🗝️ API Key: {self.api_key[:10]}...")

    def generate_admin_access_token(
        self,
        room_name: str,
        admin_identity: Optional[str] = None,
        token_lifetime_hours: int = 24,
    ) -> str:
        """
        Generate an access token for admin monitoring with hidden permissions.

        Args:
            room_name (str): Name of the room to monitor
            admin_identity (str, optional): Custom admin identity
            token_lifetime_hours (int): Token lifetime in hours (default: 24)

        Returns:
            str: JWT access token for admin monitoring

        Raises:
            AdminAuthError: If token generation fails
        """
        try:
            # Generate unique admin identity if not provided
            if admin_identity is None:
                timestamp = int(time.time())
                admin_identity = (
                    f"admin_{timestamp}"  # Check cache first (simple cache key)
                )
            cache_key = f"{room_name}:{admin_identity}"
            if cache_key in self.token_cache:
                cached_token, expiry = self.token_cache[cache_key]
                if datetime.now() < expiry:
                    logger.info(f"🎯 Returning cached token for {admin_identity}")
                    return cached_token

            logger.info(f"🎟️ Generating new admin access token")
            logger.info(f"🏠 Room: {room_name}")
            logger.info(f"👤 Admin Identity: {admin_identity}")
            logger.info(f"⏰ Lifetime: {token_lifetime_hours} hours")

            # Set token expiration
            expiration_time = datetime.now() + timedelta(hours=token_lifetime_hours)

            # Configure admin video grant with hidden monitoring permissions
            grant = api.VideoGrants(
                # Basic room permissions
                room_join=True,  # Allow joining the room
                room=room_name,  # Specific room name
                # Publishing permissions (disabled for monitoring)
                can_publish=False,  # Admin cannot publish audio/video
                can_publish_data=False,  # Admin cannot send data messages
                # Subscription permissions (enabled for monitoring)
                can_subscribe=True,  # Admin can subscribe to tracks
                # Metadata permissions (disabled for monitoring)
                can_update_own_metadata=False,  # Admin cannot update metadata
                # Critical: Hidden participant
                hidden=True,  # Hide admin from other participants
                # Optional: Admin role identifier
                # Note: 'kind' field is typically set by LiveKit internals
                # We'll let LiveKit handle this automatically
            )

            # Create access token with fluent interface
            token = (
                AccessToken(self.api_key, self.api_secret)
                .with_identity(admin_identity)
                .with_grants(grant)
            )

            # Generate JWT
            jwt_token = token.to_jwt()

            # Cache the token
            self.token_cache[cache_key] = (jwt_token, expiration_time)

            logger.info(f"✅ Admin access token generated successfully")
            logger.info(f"🔐 Token expires at: {expiration_time}")
            logger.info(f"📝 Token preview: {jwt_token[:30]}...")

            return jwt_token

        except Exception as e:
            logger.error(f"❌ Failed to generate admin access token: {e}")
            raise AdminAuthError(f"Token generation failed: {e}")

    def generate_room_list_token(self, admin_identity: Optional[str] = None) -> str:
        """
        Generate a token for listing rooms (admin dashboard functionality).

        Args:
            admin_identity (str, optional): Admin identity

        Returns:
            str: JWT token with room listing permissions"""
        try:
            if admin_identity is None:
                admin_identity = f"admin_dashboard_{int(time.time())}"

            logger.info(f"📋 Generating room list token for: {admin_identity}")

            # Configure grant for room listing
            grant = api.VideoGrants(
                room_list=True,  # Allow listing rooms
                room_join=False,  # Don't allow joining rooms with this token
                can_publish=False,  # No publishing
                can_subscribe=False,  # No subscribing
                hidden=True,  # Keep admin hidden
            )

            # Create access token with fluent interface
            token = (
                AccessToken(self.api_key, self.api_secret)
                .with_identity(admin_identity)
                .with_grants(grant)
            )

            jwt_token = token.to_jwt()

            logger.info(f"✅ Room list token generated")
            return jwt_token

        except Exception as e:
            logger.error(f"❌ Failed to generate room list token: {e}")
            raise AdminAuthError(f"Room list token generation failed: {e}")

    def validate_admin_identity(self, admin_identity: str) -> bool:
        """
        Simple admin identity validation for demo purposes.

        Args:
            admin_identity (str): Identity to validate

        Returns:
            bool: True if valid admin identity
        """
        # Simple validation rules for demo
        if not admin_identity:
            return False

        # Allow admin identities that start with 'admin_'
        if admin_identity.startswith("admin_"):
            return True

        # Allow specific demo admin identities
        demo_admins = ["demo_admin", "test_admin", "call_center_admin"]
        if admin_identity in demo_admins:
            return True

        logger.warning(f"⚠️ Invalid admin identity: {admin_identity}")
        return False

    def clear_token_cache(self):
        """Clear the token cache (useful for testing)."""
        logger.info("🧹 Clearing admin token cache")
        self.token_cache.clear()

    def get_cache_info(self) -> dict:
        """Get information about cached tokens."""
        active_tokens = 0
        expired_tokens = 0
        current_time = datetime.now()

        for cache_key, (token, expiry) in self.token_cache.items():
            if current_time < expiry:
                active_tokens += 1
            else:
                expired_tokens += 1

        return {
            "total_cached": len(self.token_cache),
            "active_tokens": active_tokens,
            "expired_tokens": expired_tokens,
        }

    def cleanup_expired_tokens(self):
        """Remove expired tokens from cache."""
        current_time = datetime.now()
        expired_keys = [
            key
            for key, (token, expiry) in self.token_cache.items()
            if current_time >= expiry
        ]

        for key in expired_keys:
            del self.token_cache[key]

        if expired_keys:
            logger.info(f"🧹 Cleaned up {len(expired_keys)} expired tokens")


# Convenience functions for easy integration
def create_admin_monitor_token(
    room_name: str, admin_identity: Optional[str] = None
) -> str:
    """
    Convenience function to quickly create an admin monitoring token.

    Args:
        room_name (str): Room to monitor
        admin_identity (str, optional): Admin identity

    Returns:
        str: JWT token for monitoring
    """
    auth = SimpleAdminAuth()
    return auth.generate_admin_access_token(room_name, admin_identity)


def create_room_list_token(admin_identity: Optional[str] = None) -> str:
    """
    Convenience function to quickly create a room listing token.

    Args:
        admin_identity (str, optional): Admin identity

    Returns:
        str: JWT token for room listing
    """
    auth = SimpleAdminAuth()
    return auth.generate_room_list_token(admin_identity)


# Test function for development
def test_admin_auth():
    """Test function to verify admin authentication functionality."""
    logger.info("🧪 Testing Admin Authentication functionality...")

    try:
        # Initialize admin auth
        auth = SimpleAdminAuth()

        # Test admin token generation
        test_room = "test_room"
        test_admin = "test_admin"

        # Test monitoring token
        monitor_token = auth.generate_admin_access_token(test_room, test_admin)
        logger.info(f"✅ Monitor token generation test passed")

        # Test room list token
        list_token = auth.generate_room_list_token(test_admin)
        logger.info(f"✅ Room list token generation test passed")

        # Test identity validation
        valid_identity = auth.validate_admin_identity("admin_test")
        invalid_identity = auth.validate_admin_identity("user_test")

        assert valid_identity == True, "Valid admin identity should pass"
        assert invalid_identity == False, "Invalid identity should fail"
        logger.info(f"✅ Identity validation test passed")

        # Test cache functionality
        cache_info = auth.get_cache_info()
        logger.info(f"✅ Cache info test passed: {cache_info}")

        logger.info("🎉 All admin authentication tests passed!")

    except Exception as e:
        logger.error(f"❌ Admin authentication test failed: {e}")
        raise


if __name__ == "__main__":
    # Run test if executed directly
    test_admin_auth()
