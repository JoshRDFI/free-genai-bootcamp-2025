-- populate_default_user.sql

-- 1. Insert the default user, ignore if a user with ID 1 or name 'Default User' already exists.
INSERT OR IGNORE INTO users (id, name, current_level) VALUES (1, 'Default User', 'N5');

-- 2. Update existing study_sessions to link to the default user (ID 1)
-- This assumes all existing sessions should belong to this single default user.
UPDATE study_sessions SET user_id = 1 WHERE user_id IS NULL;

-- 3. Update existing progression_history to link to the default user (ID 1)
-- This assumes all existing progression history should belong to this default user.
UPDATE progression_history SET user_id = 1 WHERE user_id IS NULL; 