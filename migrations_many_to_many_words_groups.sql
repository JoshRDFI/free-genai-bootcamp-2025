-- migrations_many_to_many_words_groups.sql

-- 1. Create the join table for words and groups
CREATE TABLE IF NOT EXISTS word_to_group_join (
    word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES word_groups(id) ON DELETE CASCADE,
    PRIMARY KEY (word_id, group_id)
);

-- 2. Populate the join table from the existing words.group_id
-- This assumes words.group_id currently holds the ID of the single group a word belongs to.
-- IMPORTANT: Run this only once. If run again, it might create duplicates if word_id, group_id isn't unique yet
-- The PRIMARY KEY on word_to_group_join will prevent exact duplicates if run again.
INSERT OR IGNORE INTO word_to_group_join (word_id, group_id)
SELECT id, group_id FROM words WHERE group_id IS NOT NULL;

-- 3. Add triggers to maintain word_groups.words_count

-- Trigger to increment words_count on new association
CREATE TRIGGER IF NOT EXISTS increment_word_group_count
AFTER INSERT ON word_to_group_join
BEGIN
    UPDATE word_groups SET words_count = words_count + 1 WHERE id = NEW.group_id;
END;

-- Trigger to decrement words_count when an association is removed
CREATE TRIGGER IF NOT EXISTS decrement_word_group_count
AFTER DELETE ON word_to_group_join
BEGIN
    UPDATE word_groups SET words_count = words_count - 1 WHERE id = OLD.group_id;
END;

-- Optional: Recalculate all word_groups.words_count once after populating and adding triggers
-- This ensures counts are correct if they were off or if the triggers didn't exist during initial population.
-- UPDATE word_groups SET words_count = (
--    SELECT COUNT(*) FROM word_to_group_join WHERE word_to_group_join.group_id = word_groups.id
-- );
-- The above recalculation should ideally be run after the INSERT OR IGNORE and before triggers are active,
-- or triggers should be robust to it. For simplicity, we rely on triggers for new changes.
-- A one-time manual recalculation after this script might be safest if unsure about initial state. 