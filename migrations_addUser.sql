-- migrations_addUser.sql

-- 1. Create the users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    current_level TEXT DEFAULT 'N5' NOT NULL CHECK(current_level IN ('N5', 'N4', 'N3', 'N2', 'N1')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Add user_id to study_sessions
-- We'll add it as NULLABLE first, then populate it, then consider making it NOT NULL.
ALTER TABLE study_sessions ADD COLUMN user_id INTEGER REFERENCES users(id);

-- 3. Add user_id to progression_history
-- Same approach: add nullable, populate, then consider NOT NULL.
ALTER TABLE progression_history ADD COLUMN user_id INTEGER REFERENCES users(id); 