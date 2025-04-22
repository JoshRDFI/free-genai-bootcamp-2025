#!/bin/bash
# File: migrate-data.sh
# Usage: ./migrate-data.sh

OLD_DB="db.sqlite3.old"
NEW_DB="db.sqlite3"

# 1. Create new database if missing
if [ ! -f "$NEW_DB" ]; then
    echo "Creating fresh database..."
    sqlite3 "$NEW_DB" < database/schema.sql
fi

# 2. Migrate data using SQLite's ATTACH DATABASE
sqlite3 "$NEW_DB" <<EOF
PRAGMA foreign_keys = OFF;

ATTACH DATABASE '${OLD_DB}' AS old_db;

-- Preserve existing data first
BEGIN TRANSACTION;

-- Get list of tables common to both databases
CREATE TEMPORARY TABLE common_tables AS
SELECT name FROM (
    SELECT name FROM sqlite_master
    UNION ALL
    SELECT name FROM old_db.sqlite_master
) GROUP BY name HAVING COUNT(*) = 2;

-- Migrate data for each table
WITH tables AS (
    SELECT name 
    FROM common_tables 
    WHERE name NOT LIKE 'sqlite_%' 
    AND name NOT IN ('schema_versions')
)
INSERT INTO main.schema_versions(version) VALUES (1);

-- Migration sequence respecting foreign keys
INSERT INTO word_groups SELECT * FROM old_db.word_groups;
INSERT INTO words SELECT * FROM old_db.words;
INSERT INTO study_sessions SELECT * FROM old_db.study_sessions;
INSERT INTO word_review_items SELECT * FROM old_db.word_review_items;
INSERT INTO progression_history SELECT * FROM old_db.progression_history;
INSERT INTO sentences SELECT * FROM old_db.sentences;
INSERT INTO writing_submissions SELECT * FROM old_db.writing_submissions;
INSERT INTO transcripts SELECT * FROM old_db.transcripts;
INSERT INTO questions SELECT * FROM old_db.questions;
INSERT INTO embeddings SELECT * FROM old_db.embeddings;
INSERT INTO user_feedback SELECT * FROM old_db.user_feedback;
INSERT INTO image_generation SELECT * FROM old_db.image_generation;

-- Handle schema_versions separately
INSERT INTO main.schema_versions(version)
SELECT version FROM old_db.schema_versions;

COMMIT;
DETACH DATABASE old_db;

PRAGMA foreign_keys = ON;
VACUUM;
EOF

echo "Migration complete. Verify with:"
echo "sqlite3 ${NEW_DB} 'SELECT COUNT(*) FROM word_groups;'"