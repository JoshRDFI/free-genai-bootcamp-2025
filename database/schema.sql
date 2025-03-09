-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Word Groups Table
CREATE TABLE IF NOT EXISTS word_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    level TEXT CHECK(level IN ('N5', 'N4', 'N3', 'N2', 'N1')) -- Optional: Associate groups with JLPT levels
);

-- Words Table with FTS (Full Text Search) support
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kanji TEXT NOT NULL,
    romaji TEXT NOT NULL,
    english TEXT NOT NULL,
    group_id INTEGER NOT NULL,
    correct_count INTEGER DEFAULT 0,
    wrong_count INTEGER DEFAULT 0,
    FOREIGN KEY (group_id) REFERENCES word_groups(id)
);

-- Study Sessions Table
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_type TEXT NOT NULL CHECK(activity_type IN ('typing_tutor', 'adventure_mud', 'flashcards')),
    group_id INTEGER NOT NULL,
    duration INTEGER NOT NULL,  -- in minutes
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    accuracy REAL NOT NULL CHECK(accuracy >= 0 AND accuracy <= 100),
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
    previous_level TEXT NOT NULL CHECK(previous_level IN ('N5', 'N4', 'N3', 'N2', 'N1')),
    new_level TEXT NOT NULL CHECK(new_level IN ('N5', 'N4', 'N3', 'N2', 'N1')),
    progressed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Optimize common queries with indexes
CREATE INDEX IF NOT EXISTS idx_words_group ON words(group_id);
CREATE INDEX IF NOT EXISTS idx_sessions_activity ON study_sessions(activity_type);
CREATE INDEX IF NOT EXISTS idx_sessions_time ON study_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_reviews_session ON word_review_items(session_id);

-- Trigger to update word correctness counts
CREATE TRIGGER IF NOT EXISTS update_word_counts
AFTER INSERT ON word_review_items
BEGIN
    UPDATE words SET
    correct_count = correct_count + CASE WHEN NEW.correct THEN 1 ELSE 0 END,
    wrong_count = wrong_count + CASE WHEN NEW.correct THEN 0 ELSE 1 END
    WHERE id = NEW.word_id;
END;

-- Sentences Table for Writing Practice
CREATE TABLE IF NOT EXISTS sentences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    japanese TEXT NOT NULL,
    english TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (word_id) REFERENCES words(id)
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

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_sentences_word ON sentences(word_id);
CREATE INDEX IF NOT EXISTS idx_submissions_sentence ON writing_submissions(sentence_id);
CREATE INDEX IF NOT EXISTS idx_submissions_grade ON writing_submissions(grade);

-- Transcripts Table
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL UNIQUE,
    transcript TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Generated Questions Table
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    options TEXT NOT NULL, -- JSON array of options
    correct_option INTEGER NOT NULL, -- Index of the correct option (1-4)
    image_path TEXT, -- Path to associated image
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
);

-- Embeddings Table
-- Note: SQLite doesn't have a native Vector type, so we store embeddings as BLOBs
-- When using this table, the application should:
-- 1. For storing: Serialize vectors to binary (e.g., using numpy.ndarray.tobytes())
-- 2. For retrieval: Deserialize from binary (e.g., using numpy.frombuffer())
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN ('ja', 'en')),
    embedding BLOB NOT NULL, -- Serialized vector data
    vector_dimensions INTEGER NOT NULL, -- Store the dimensions for proper deserialization
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

-- Create table for tracking image generation
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

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_image_generation_question ON image_generation(question_id);

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Sentences Table for Writing Practice
CREATE TABLE IF NOT EXISTS sentences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    japanese TEXT NOT NULL,
    english TEXT NOT NULL,
    level TEXT CHECK(level IN ('N5', 'N4', 'N3', 'N2', 'N1')) NOT NULL,
    category TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_sentences_category ON sentences(category);
CREATE INDEX IF NOT EXISTS idx_sentences_level ON sentences(level);