-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    current_level TEXT DEFAULT 'N5' NOT NULL CHECK(current_level IN ('N5', 'N4', 'N3', 'N2', 'N1')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Word Groups Table
CREATE TABLE IF NOT EXISTS word_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    level TEXT CHECK(level IN ('N5', 'N4', 'N3', 'N2', 'N1')), -- Optional: Associate groups with JLPT levels
    words_count INTEGER DEFAULT 0 -- ADDED words_count
);

-- Words Table with FTS (Full Text Search) support
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kanji TEXT NOT NULL,
    romaji TEXT NOT NULL,
    english TEXT NOT NULL,
    group_id INTEGER, -- Now nullable since we use word_to_group_join
    parts TEXT,
    correct_count INTEGER DEFAULT 0,
    wrong_count INTEGER DEFAULT 0,
    sentence_id INTEGER CONSTRAINT fk_words_sentences REFERENCES sentences(id), -- Reflects live schema
    FOREIGN KEY (group_id) REFERENCES word_groups(id)
    -- Note: The foreign key for words.group_id remains, but new logic shouldn't rely on this column for associations.
);

-- Word to Group Join Table (Many-to-Many)
CREATE TABLE IF NOT EXISTS word_to_group_join (
    word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES word_groups(id) ON DELETE CASCADE,
    PRIMARY KEY (word_id, group_id)
);

-- Study Sessions Table
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_type TEXT NOT NULL CHECK(activity_type IN ('typing_tutor', 'adventure_mud', 'flashcards')),
    group_id INTEGER NOT NULL,
    user_id INTEGER REFERENCES users(id), -- ADDED user_id
    duration INTEGER NOT NULL,  -- in minutes
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    accuracy REAL NOT NULL CHECK(accuracy >= 0 AND accuracy <= 100),
    writing_submission_id INTEGER REFERENCES writing_submissions(id), -- Reflects live schema
    FOREIGN KEY (group_id) REFERENCES word_groups(id)
);

-- Word Review Items (for session results)
CREATE TABLE IF NOT EXISTS word_review_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    correct BOOLEAN NOT NULL,
    reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (word_id) REFERENCES words(id),
    FOREIGN KEY (session_id) REFERENCES study_sessions(id)
);

-- Progression History Table
CREATE TABLE IF NOT EXISTS progression_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id), -- ADDED user_id
    previous_level TEXT NOT NULL CHECK(previous_level IN ('N5', 'N4', 'N3', 'N2', 'N1')),
    new_level TEXT NOT NULL CHECK(new_level IN ('N5', 'N4', 'N3', 'N2', 'N1')),
    progressed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Sentences Table (for writing practice)
CREATE TABLE IF NOT EXISTS sentences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    japanese TEXT NOT NULL,
    english TEXT NOT NULL,
    level TEXT CHECK(level IN ('N5', 'N4', 'N3', 'N2', 'N1')),
    category TEXT NOT NULL
);

-- Writing Practice Submissions Table
CREATE TABLE IF NOT EXISTS writing_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sentence_id INTEGER NOT NULL,
    transcription TEXT NOT NULL,
    translation TEXT NOT NULL,
    grade TEXT CHECK(grade IN ('S', 'A', 'B', 'C', 'N/A')) NOT NULL,
    feedback TEXT NOT NULL,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sentence_id) REFERENCES sentences(id)
);

-- Transcripts Table
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL, -- This was 'transcript' in live schema, but 'content' in old schema.sql. Keeping 'content' as per last file read.
    language TEXT NOT NULL DEFAULT 'ja', -- Added from old schema.sql
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Generated Questions Table
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL, -- This was transcript_id in live schema. Assuming video_id is preferred from old schema.sql
    section_num INTEGER NOT NULL, -- Added from old schema.sql
    introduction TEXT, -- Added from old schema.sql
    conversation TEXT, -- Added from old schema.sql
    question TEXT NOT NULL,
    options TEXT NOT NULL, -- JSON array of options
    correct_answer INTEGER NOT NULL DEFAULT 1, -- correct_option in live schema. Using correct_answer from old schema.sql
    image_path TEXT, -- Path to associated image
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES transcripts(id) -- Assuming video_id FK
);

-- Embeddings Table
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN ('ja', 'en')),
    embedding BLOB NOT NULL,
    vector_dimensions INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User Feedback Table
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    selected_option INTEGER NOT NULL,
    correct BOOLEAN NOT NULL,
    feedback TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- Image Generation Table
CREATE TABLE IF NOT EXISTS image_generation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'completed', 'failed')) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    error_message TEXT,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- Schema Versions Table
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Optimize common queries with indexes
CREATE INDEX IF NOT EXISTS idx_words_group ON words(group_id);
CREATE INDEX IF NOT EXISTS idx_sessions_activity ON study_sessions(activity_type);
CREATE INDEX IF NOT EXISTS idx_sessions_time ON study_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_reviews_session ON word_review_items(session_id);
CREATE INDEX IF NOT EXISTS idx_submissions_sentence ON writing_submissions(sentence_id);
CREATE INDEX IF NOT EXISTS idx_submissions_grade ON writing_submissions(grade);
CREATE INDEX IF NOT EXISTS idx_image_generation_question ON image_generation(question_id);
CREATE INDEX IF NOT EXISTS idx_study_sessions_user ON study_sessions(user_id); -- ADDED index for user_id
CREATE INDEX IF NOT EXISTS idx_progression_history_user ON progression_history(user_id); -- ADDED index for user_id
CREATE INDEX IF NOT EXISTS idx_word_to_group_join_word ON word_to_group_join(word_id);
CREATE INDEX IF NOT EXISTS idx_word_to_group_join_group ON word_to_group_join(group_id);

-- Trigger to update word correctness counts
CREATE TRIGGER IF NOT EXISTS update_word_counts
AFTER INSERT ON word_review_items
BEGIN
    UPDATE words SET
    correct_count = correct_count + CASE WHEN NEW.correct THEN 1 ELSE 0 END,
    wrong_count = wrong_count + CASE WHEN NEW.correct THEN 0 ELSE 1 END
    WHERE id = NEW.word_id;
END;

-- Triggers to maintain word_groups.words_count
CREATE TRIGGER IF NOT EXISTS increment_word_group_count
AFTER INSERT ON word_to_group_join
BEGIN
    UPDATE word_groups SET words_count = words_count + 1 WHERE id = NEW.group_id;
END;

CREATE TRIGGER IF NOT EXISTS decrement_word_group_count
AFTER DELETE ON word_to_group_join
BEGIN
    UPDATE word_groups SET words_count = words_count - 1 WHERE id = OLD.group_id;
END;
