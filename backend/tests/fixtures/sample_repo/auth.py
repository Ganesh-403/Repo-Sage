"""Authentication module — handles user login and password verification."""

import hashlib
from typing import Optional


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Validate user credentials against the database.

    Looks up the user by username, verifies the password hash,
    and returns the user profile if credentials are valid.

    Args:
        username: The user's login name.
        password: The plaintext password to verify.

    Returns:
        User dict with id, username, role if valid. None otherwise.
    """
    user = get_user_from_db(username)
    if user is None:
        return None

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user.get("password_hash"):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user.get("role", "user"),
    }


def get_user_from_db(username: str) -> Optional[dict]:
    """Retrieve user record from database by username."""
    # Placeholder — would query actual database
    return None


def create_password_hash(password: str) -> str:
    """Create a SHA-256 hash of the password.

    In production, use bcrypt or argon2. SHA-256 is used here
    for simplicity in the demo fixture.

    Args:
        password: Plaintext password to hash.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    return hashlib.sha256(password.encode()).hexdigest()


class SessionManager:
    """Manages user sessions with in-memory storage.

    Provides methods to create, validate, and destroy sessions.
    Uses a simple dict-based store — in production, use Redis.
    """

    def __init__(self):
        """Initialize with empty session store."""
        self._sessions: dict[str, dict] = {}
        self._token_counter = 0

    def create_session(self, user: dict) -> str:
        """Create a new session for an authenticated user.

        Generates a unique session token and stores the user's
        profile data for later retrieval.

        Args:
            user: Authenticated user profile dict.

        Returns:
            Session token string.
        """
        self._token_counter += 1
        token = f"session_{self._token_counter}_{user['id']}"
        self._sessions[token] = {
            "user": user,
            "created_at": "2024-01-01T00:00:00Z",
        }
        return token

    def get_session(self, token: str) -> Optional[dict]:
        """Retrieve session data by token.

        Args:
            token: Session token from create_session.

        Returns:
            Session dict with user data, or None if expired/invalid.
        """
        return self._sessions.get(token)

    def destroy_session(self, token: str) -> bool:
        """Destroy a session (logout).

        Args:
            token: Session token to invalidate.

        Returns:
            True if session was found and destroyed.
        """
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False
