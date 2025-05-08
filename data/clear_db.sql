-- Delete all entries from the tables
DELETE FROM word_groups;
DELETE FROM words;
DELETE FROM sentences;
DELETE FROM writing_submissions;

-- Reset the auto-increment sequence for each table
UPDATE sqlite_sequence SET seq = 0 WHERE name IN ('word_groups', 'words', 'sentences', 'writing_submissions');