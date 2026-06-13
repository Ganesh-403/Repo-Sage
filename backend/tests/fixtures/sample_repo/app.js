/**
 * Express application entry point
 * Sets up routes, middleware, and database connections
 */

const express = require("express");
const cors = require("cors");
const { connectDB } = require("./config/database");

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

/**
 * Health check endpoint
 * Returns server status and uptime
 */
function healthCheck(req, res) {
    return res.json({
        status: "healthy",
        uptime: process.uptime(),
        timestamp: new Date().toISOString(),
    });
}

/**
 * Get all users with pagination
 * Supports query params: page, limit, search
 */
async function getUsers(req, res) {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 20;
        const search = req.query.search || "";

        const offset = (page - 1) * limit;
        const users = await db.query(
            "SELECT id, username, email, created_at FROM users WHERE username LIKE ? LIMIT ? OFFSET ?",
            [`%${search}%`, limit, offset]
        );

        const total = await db.query("SELECT COUNT(*) as count FROM users");

        return res.json({
            users,
            pagination: {
                page,
                limit,
                total: total[0].count,
                pages: Math.ceil(total[0].count / limit),
            },
        });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
}

/**
 * Create a new user account
 * Validates input, checks uniqueness, hashes password
 */
async function createUser(req, res) {
    try {
        const { username, email, password } = req.body;

        if (!username || !email || !password) {
            return res.status(400).json({ error: "Missing required fields" });
        }

        const existing = await db.query("SELECT id FROM users WHERE email = ?", [email]);
        if (existing.length > 0) {
            return res.status(409).json({ error: "Email already registered" });
        }

        const hashedPassword = await hashPassword(password);
        const result = await db.query(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            [username, email, hashedPassword]
        );

        return res.status(201).json({
            id: result.insertId,
            username,
            email,
        });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
}

const handleError = (error, req, res, next) => {
    console.error("Unhandled error:", error);
    return res.status(500).json({
        error: "Internal server error",
        message: process.env.NODE_ENV === "development" ? error.message : undefined,
    });
};

// Routes
app.get("/health", healthCheck);
app.get("/api/users", getUsers);
app.post("/api/users", createUser);
app.use(handleError);

// Start server
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    connectDB();
});

module.exports = app;
