-- migrations_add_parts_and_counts.sql

ALTER TABLE words ADD COLUMN parts TEXT; -- SQLite uses TEXT for JSON
ALTER TABLE word_groups ADD COLUMN words_count INTEGER DEFAULT 0; 