"""
Tests for code chunkers — verify AST, regex, and generic chunking.

Tests cover:
- Python AST chunker extracts functions and classes correctly
- JS chunker detects function declarations and arrow functions
- Generic chunker produces correct window sizes
- Edge cases: syntax errors, empty files, tiny functions
"""

import os
import tempfile
import pytest
from pathlib import Path

# Add backend to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reposage.chunkers.python_chunker import PythonASTChunker, CodeChunk
from reposage.chunkers.js_chunker import JSChunker
from reposage.chunkers.generic_chunker import GenericChunker


# ─── Fixtures ───

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "sample_repo")


@pytest.fixture
def python_chunker():
    return PythonASTChunker()


@pytest.fixture
def js_chunker():
    return JSChunker()


@pytest.fixture
def generic_chunker():
    return GenericChunker(chunk_size=20, overlap=5)


@pytest.fixture
def sample_python_file(tmp_path):
    """Create a temporary Python file with known functions."""
    code = '''"""Authentication module for the application."""

import hashlib
from typing import Optional


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Validate user credentials against the database.

    Args:
        username: The user's login name.
        password: The plaintext password to verify.

    Returns:
        User dict if valid, None otherwise.
    """
    user = find_user_by_username(username)
    if user is None:
        return None

    hashed = hashlib.sha256(password.encode()).hexdigest()
    if hashed != user["password_hash"]:
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }


def find_user_by_username(username: str) -> Optional[dict]:
    """Look up a user in the database by username."""
    # Simulated database lookup
    return None


class UserService:
    """Manages user operations: create, update, delete."""

    def __init__(self, db_connection):
        """Initialize with database connection.

        Args:
            db_connection: Active database connection object.
        """
        self.db = db_connection
        self.cache = {}

    def get_user(self, user_id: int) -> Optional[dict]:
        """Retrieve a user by ID with caching.

        First checks the local cache, then queries the database.
        Results are cached for subsequent calls.
        """
        if user_id in self.cache:
            return self.cache[user_id]

        user = self.db.query("SELECT * FROM users WHERE id = ?", user_id)
        if user:
            self.cache[user_id] = user
        return user

    def create_user(self, username: str, email: str) -> dict:
        """Create a new user account.

        Validates uniqueness, hashes password, inserts into database.
        """
        if self.db.query("SELECT id FROM users WHERE username = ?", username):
            raise ValueError(f"Username {username} already exists")

        user = {"username": username, "email": email}
        user["id"] = self.db.insert("users", user)
        return user
'''
    file_path = tmp_path / "auth.py"
    file_path.write_text(code)
    return str(file_path)


@pytest.fixture
def sample_js_file(tmp_path):
    """Create a temporary JS file with known functions."""
    code = '''/**
 * Authentication middleware for Express
 */

const jwt = require("jsonwebtoken");
const { JWT_SECRET } = require("../config");

/**
 * Verify JWT token from Authorization header.
 * Extracts user info and attaches to req.user.
 */
function verifyToken(req, res, next) {
    const authHeader = req.headers["authorization"];
    if (!authHeader) {
        return res.status(401).json({ error: "No token provided" });
    }

    const token = authHeader.split(" ")[1];
    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        req.user = decoded;
        next();
    } catch (err) {
        return res.status(403).json({ error: "Invalid token" });
    }
}

const rateLimiter = (maxRequests, windowMs) => {
    const requests = new Map();

    return (req, res, next) => {
        const ip = req.ip;
        const now = Date.now();
        const windowStart = now - windowMs;

        if (!requests.has(ip)) {
            requests.set(ip, []);
        }

        const timestamps = requests.get(ip).filter(t => t > windowStart);
        if (timestamps.length >= maxRequests) {
            return res.status(429).json({ error: "Too many requests" });
        }

        timestamps.push(now);
        requests.set(ip, timestamps);
        next();
    };
};

class AuthService {
    constructor(userRepository) {
        this.userRepo = userRepository;
        this.tokenExpiry = "24h";
    }

    async login(email, password) {
        const user = await this.userRepo.findByEmail(email);
        if (!user || !await this.verifyPassword(password, user.hashedPassword)) {
            throw new Error("Invalid credentials");
        }

        const token = jwt.sign(
            { userId: user.id, role: user.role },
            JWT_SECRET,
            { expiresIn: this.tokenExpiry }
        );
        return { user, token };
    }

    async verifyPassword(plain, hashed) {
        return plain === hashed; // Simplified for example
    }
}

module.exports = { verifyToken, rateLimiter, AuthService };
'''
    file_path = tmp_path / "auth.js"
    file_path.write_text(code)
    return str(file_path)


@pytest.fixture
def sample_empty_file(tmp_path):
    file_path = tmp_path / "empty.py"
    file_path.write_text("")
    return str(file_path)


@pytest.fixture
def sample_syntax_error_file(tmp_path):
    code = '''def broken_func(
        this is not valid python
        {{{
    '''
    file_path = tmp_path / "broken.py"
    file_path.write_text(code)
    return str(file_path)


# ═══════ Python AST Chunker Tests ═══════

class TestPythonASTChunker:
    """Tests for the Python AST-based code chunker."""

    def test_extracts_functions(self, python_chunker, sample_python_file):
        """Verify that functions are extracted as individual chunks."""
        chunks = python_chunker.chunk_file(sample_python_file)
        names = [c.name for c in chunks]

        assert "authenticate_user" in names, "Should extract authenticate_user function"
        assert any(c.chunk_type == "function" for c in chunks), "Should mark as function type"

    def test_extracts_classes(self, python_chunker, sample_python_file):
        """Verify that classes are extracted as chunks."""
        chunks = python_chunker.chunk_file(sample_python_file)
        class_chunks = [c for c in chunks if c.chunk_type == "class"]

        assert len(class_chunks) >= 1, "Should extract at least one class"
        assert any(c.name == "UserService" for c in class_chunks)

    def test_captures_docstrings(self, python_chunker, sample_python_file):
        """Verify that docstrings are captured in chunk metadata."""
        chunks = python_chunker.chunk_file(sample_python_file)
        auth_chunk = next(c for c in chunks if c.name == "authenticate_user")

        assert auth_chunk.docstring is not None
        assert "Validate user credentials" in auth_chunk.docstring

    def test_captures_line_ranges(self, python_chunker, sample_python_file):
        """Verify that line start/end are captured correctly."""
        chunks = python_chunker.chunk_file(sample_python_file)
        auth_chunk = next(c for c in chunks if c.name == "authenticate_user")

        assert auth_chunk.line_start > 0
        assert auth_chunk.line_end > auth_chunk.line_start
        assert auth_chunk.line_end - auth_chunk.line_start >= 5

    def test_searchable_content_includes_name(self, python_chunker, sample_python_file):
        """Verify that chunk content includes function name for searchability."""
        chunks = python_chunker.chunk_file(sample_python_file)
        auth_chunk = next(c for c in chunks if c.name == "authenticate_user")

        assert "# function: authenticate_user" in auth_chunk.content
        assert "# Summary:" in auth_chunk.content

    def test_skips_tiny_functions(self, python_chunker, sample_python_file):
        """Verify that functions shorter than min_lines are skipped."""
        chunks = python_chunker.chunk_file(sample_python_file)
        names = [c.name for c in chunks]

        # find_user_by_username is only 3 lines — should be skipped
        assert "find_user_by_username" not in names

    def test_captures_module_docstring(self, python_chunker, sample_python_file):
        """Verify that the module-level docstring is captured."""
        chunks = python_chunker.chunk_file(sample_python_file)
        module_chunks = [c for c in chunks if c.chunk_type == "module"]

        assert len(module_chunks) >= 1
        assert "Authentication module" in module_chunks[0].content

    def test_syntax_error_fallback(self, python_chunker, sample_syntax_error_file):
        """Verify graceful fallback for files with syntax errors."""
        chunks = python_chunker.chunk_file(sample_syntax_error_file)

        assert len(chunks) == 1, "Should produce exactly one fallback chunk"
        assert chunks[0].chunk_type == "module"

    def test_empty_file(self, python_chunker, sample_empty_file):
        """Verify handling of empty files."""
        chunks = python_chunker.chunk_file(sample_empty_file)
        # Empty file has no functions, classes, or module docstring
        assert len(chunks) == 0

    def test_file_path_preserved(self, python_chunker, sample_python_file):
        """Verify that file path is preserved in chunk metadata."""
        chunks = python_chunker.chunk_file(sample_python_file)
        for chunk in chunks:
            assert chunk.file_path == sample_python_file

    def test_language_set_to_python(self, python_chunker, sample_python_file):
        """Verify language metadata is set correctly."""
        chunks = python_chunker.chunk_file(sample_python_file)
        for chunk in chunks:
            assert chunk.language == "python"


# ═══════ JS Chunker Tests ═══════

class TestJSChunker:
    """Tests for the JavaScript regex-based chunker."""

    def test_extracts_named_functions(self, js_chunker, sample_js_file):
        """Verify that named function declarations are found."""
        chunks = js_chunker.chunk_file(sample_js_file)
        names = [c.name for c in chunks]

        assert "verifyToken" in names, "Should extract verifyToken function"

    def test_extracts_arrow_functions(self, js_chunker, sample_js_file):
        """Verify that arrow function assignments are found."""
        chunks = js_chunker.chunk_file(sample_js_file)
        names = [c.name for c in chunks]

        assert "rateLimiter" in names, "Should extract rateLimiter arrow function"

    def test_extracts_classes(self, js_chunker, sample_js_file):
        """Verify that class declarations are found."""
        chunks = js_chunker.chunk_file(sample_js_file)
        class_chunks = [c for c in chunks if c.chunk_type == "class"]

        assert len(class_chunks) >= 1
        assert any(c.name == "AuthService" for c in class_chunks)

    def test_captures_jsdoc(self, js_chunker, sample_js_file):
        """Verify that JSDoc comments are captured."""
        chunks = js_chunker.chunk_file(sample_js_file)
        verify_chunk = next((c for c in chunks if c.name == "verifyToken"), None)

        assert verify_chunk is not None
        assert verify_chunk.docstring is not None
        assert "JWT token" in verify_chunk.docstring or "Verify" in verify_chunk.docstring

    def test_line_ranges(self, js_chunker, sample_js_file):
        """Verify line ranges are reasonable."""
        chunks = js_chunker.chunk_file(sample_js_file)
        for chunk in chunks:
            assert chunk.line_start > 0
            assert chunk.line_end >= chunk.line_start


# ═══════ Generic Chunker Tests ═══════

class TestGenericChunker:
    """Tests for the line-based generic chunker."""

    def test_small_file_single_chunk(self, generic_chunker, tmp_path):
        """Files smaller than chunk_size should produce one chunk."""
        code = "\n".join([f"line {i}" for i in range(10)])
        file_path = tmp_path / "small.go"
        file_path.write_text(code)

        chunks = generic_chunker.chunk_file(str(file_path))
        assert len(chunks) == 1

    def test_large_file_multiple_chunks(self, generic_chunker, tmp_path):
        """Files larger than chunk_size should produce multiple chunks."""
        code = "\n".join([f"line {i}" for i in range(50)])
        file_path = tmp_path / "large.go"
        file_path.write_text(code)

        chunks = generic_chunker.chunk_file(str(file_path))
        assert len(chunks) > 1

    def test_overlap_present(self, generic_chunker, tmp_path):
        """Adjacent chunks should have overlapping content."""
        code = "\n".join([f"line_{i}" for i in range(50)])
        file_path = tmp_path / "overlap.go"
        file_path.write_text(code)

        chunks = generic_chunker.chunk_file(str(file_path))
        if len(chunks) >= 2:
            # The end of chunk 0 should overlap with the start of chunk 1
            assert chunks[0].line_end > chunks[1].line_start

    def test_empty_file(self, generic_chunker, tmp_path):
        """Empty files should return no chunks."""
        file_path = tmp_path / "empty.rs"
        file_path.write_text("")

        chunks = generic_chunker.chunk_file(str(file_path))
        assert len(chunks) == 0

    def test_language_detection(self, generic_chunker, tmp_path):
        """Verify language is detected from file extension."""
        file_path = tmp_path / "main.go"
        file_path.write_text("package main\n\nfunc main() {\n}\n")

        chunks = generic_chunker.chunk_file(str(file_path))
        assert chunks[0].language == "go"

    def test_file_context_in_content(self, generic_chunker, tmp_path):
        """Verify that file context is included in chunk content."""
        code = "\n".join([f"line {i}" for i in range(10)])
        file_path = tmp_path / "context.java"
        file_path.write_text(code)

        chunks = generic_chunker.chunk_file(str(file_path))
        assert "File: context.java" in chunks[0].content


# ═══════ Integration: Fixture Files ═══════

class TestFixtureFiles:
    """Test chunking on the sample repo fixture files."""

    def test_python_fixture(self, python_chunker):
        """Test on the fixture auth.py file if it exists."""
        fixture_path = os.path.join(FIXTURES_DIR, "auth.py")
        if not os.path.exists(fixture_path):
            pytest.skip("Fixture file not found")

        chunks = python_chunker.chunk_file(fixture_path)
        assert len(chunks) > 0, "Should extract at least one chunk"

    def test_js_fixture(self, js_chunker):
        """Test on the fixture app.js file if it exists."""
        fixture_path = os.path.join(FIXTURES_DIR, "app.js")
        if not os.path.exists(fixture_path):
            pytest.skip("Fixture file not found")

        chunks = js_chunker.chunk_file(fixture_path)
        assert len(chunks) > 0, "Should extract at least one chunk"
