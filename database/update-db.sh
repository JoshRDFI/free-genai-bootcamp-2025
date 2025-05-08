#!/bin/bash
# File: update-db.sh
# Usage: ./update-db.sh /path/to/your/database.db

DB_FILE="${1:-data/db.sqlite3}"

# Backup
BACKUP_FILE="${DB_FILE}.bak-$(date +%Y%m%d%H%M%S)"
echo "Creating backup: ${BACKUP_FILE}"
cp "$DB_FILE" "$BACKUP_FILE"

sqlite3 "$DB_FILE" <<EOF
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- Create schema_versions first
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Add columns conditionally (SQLite workaround)
SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM pragma_table_info('words') WHERE name = 'sentence_id'
) THEN 'ALTER TABLE words ADD COLUMN sentence_id INTEGER REFERENCES sentences(id);' 
END;

SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM pragma_table_info('study_sessions') WHERE name = 'writing_submission_id'
) THEN 'ALTER TABLE study_sessions ADD COLUMN writing_submission_id INTEGER REFERENCES writing_submissions(id);' 
END;

-- Create tables (preserve original order)
$(grep -E 'CREATE TABLE IF NOT EXISTS' schema.sql | grep -v 'schema_versions')

-- Create indexes (excluding problematic ones)
$(grep -E 'CREATE INDEX IF NOT EXISTS' schema.sql | grep -v 'idx_sentences_word')

-- Update version only if new
INSERT OR IGNORE INTO schema_versions (version) VALUES (1);

COMMIT;

PRAGMA foreign_keys = ON;
VACUUM;
EOF

echo "Database update complete. Exit code: $?"