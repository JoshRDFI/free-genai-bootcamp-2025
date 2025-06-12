import os
import sqlite3
import json
from flask import Flask, jsonify, request
from pathlib import Path
import logging

# Setup paths
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = Path(BASE_DIR.parent, "data")  # Use shared data directory
DB_PATH = DATA_DIR / "shared_db" / "db.sqlite3"  # Use shared database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / "api.log"),  # Save log in writing-practice directory
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vocabulary_api')

app = Flask(__name__)

def get_db_connection():
    """Create a connection to the SQLite database"""
    try:
        if not DB_PATH.exists():
            logger.warning(f"Database file not found at {DB_PATH}")
            # Create data directory if it doesn't exist
            DATA_DIR.mkdir(exist_ok=True, parents=True)
            
            # Create a new database with basic schema
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Create word_groups table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS word_groups (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                level TEXT
            )
            ''')
            
            # Create words table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                kanji TEXT NOT NULL,
                romaji TEXT,
                english TEXT NOT NULL,
                group_id INTEGER,
                FOREIGN KEY (group_id) REFERENCES word_groups (id)
            )
            ''')
            
            # Create default groups and words
            create_default_data(conn)
            
            conn.commit()
            logger.info("Created new database with default schema and data")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def create_default_data(conn):
    """Create default groups and words"""
    cursor = conn.cursor()
    
    # Default groups
    default_groups = [
        (1, "Basic Greetings", "N5"),
        (2, "Food & Dining", "N5"),
        (3, "Travel Phrases", "N5"),
        (4, "Daily Activities", "N5"),
        (5, "Numbers & Time", "N5")
    ]
    
    for group_id, name, level in default_groups:
        cursor.execute(
            "INSERT OR IGNORE INTO word_groups (id, name, level) VALUES (?, ?, ?)",
            (group_id, name, level)
        )
    
    # Sample words for each group
    sample_words_by_group = {
        1: [  # Basic Greetings
            ("こんにちは", "konnichiwa", "hello"),
            ("おはよう", "ohayou", "good morning"),
            ("こんばんは", "konbanwa", "good evening"),
            ("さようなら", "sayounara", "goodbye"),
            ("ありがとう", "arigatou", "thank you")
        ],
        2: [  # Food & Dining
            ("ごはん", "gohan", "rice/meal"),
            ("水", "mizu", "water"),
            ("お茶", "ocha", "tea"),
            ("肉", "niku", "meat"),
            ("野菜", "yasai", "vegetables")
        ],
        3: [  # Travel Phrases
            ("駅", "eki", "station"),
            ("バス", "basu", "bus"),
            ("ホテル", "hoteru", "hotel"),
            ("いくら", "ikura", "how much"),
            ("どこ", "doko", "where")
        ],
        4: [  # Daily Activities
            ("食べる", "taberu", "to eat"),
            ("飲む", "nomu", "to drink"),
            ("見る", "miru", "to see"),
            ("行く", "iku", "to go"),
            ("寝る", "neru", "to sleep")
        ],
        5: [  # Numbers & Time
            ("一", "ichi", "one"),
            ("二", "ni", "two"),
            ("三", "san", "three"),
            ("今日", "kyou", "today"),
            ("明日", "ashita", "tomorrow")
        ]
    }
    
    for group_id, words in sample_words_by_group.items():
        for kanji, romaji, english in words:
            cursor.execute(
                "INSERT OR IGNORE INTO words (kanji, romaji, english, group_id) VALUES (?, ?, ?, ?)",
                (kanji, romaji, english, group_id)
            )
    
    logger.info("Created default groups and words")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/groups', methods=['GET'])
def get_groups():
    """Get all vocabulary groups"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, level FROM word_groups ORDER BY id")
        groups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(groups)
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups/<int:group_id>', methods=['GET'])
def get_group(group_id):
    """Get a specific vocabulary group with its words"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get group info
        cursor.execute("SELECT id, name, level FROM word_groups WHERE id = ?", (group_id,))
        group = cursor.fetchone()
        
        if not group:
            conn.close()
            return jsonify({"error": "Group not found"}), 404
        
        group_dict = dict(group)
        
        # Get words for this group
        cursor.execute(
            "SELECT id, kanji, romaji, english FROM words WHERE group_id = ?",
            (group_id,)
        )
        words = [dict(row) for row in cursor.fetchall()]
        
        group_dict["words"] = words
        conn.close()
        
        return jsonify(group_dict)
    except Exception as e:
        logger.error(f"Error getting group {group_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups/<int:group_id>/raw', methods=['GET'])
def get_group_words_raw(group_id):
    """Get just the words for a specific group (raw format)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id FROM word_groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Group not found"}), 404
        
        # Get words for this group
        cursor.execute(
            "SELECT id, kanji, romaji, english FROM words WHERE group_id = ?",
            (group_id,)
        )
        words = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(words)
    except Exception as e:
        logger.error(f"Error getting words for group {group_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/words', methods=['GET'])
def get_all_words():
    """Get all words across all groups"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT w.id, w.kanji, w.romaji, w.english, w.group_id, g.name as group_name "
            "FROM words w JOIN word_groups g ON w.group_id = g.id"
        )
        words = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(words)
    except Exception as e:
        logger.error(f"Error getting all words: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/words/<int:word_id>', methods=['GET'])
def get_word(word_id):
    """Get a specific word by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT w.id, w.kanji, w.romaji, w.english, w.group_id, g.name as group_name "
            "FROM words w JOIN word_groups g ON w.group_id = g.id "
            "WHERE w.id = ?",
            (word_id,)
        )
        word = cursor.fetchone()
        conn.close()
        
        if not word:
            return jsonify({"error": "Word not found"}), 404
        
        return jsonify(dict(word))
    except Exception as e:
        logger.error(f"Error getting word {word_id}: {e}")
        return jsonify({"error": str(e)}), 500

# Add CRUD operations for words and groups
@app.route('/api/groups', methods=['POST'])
def create_group():
    """Create a new vocabulary group"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({"error": "Name is required"}), 400
        
        name = data['name']
        level = data.get('level', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO word_groups (name, level) VALUES (?, ?)",
            (name, level)
        )
        group_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({"id": group_id, "name": name, "level": level}), 201
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups/<int:group_id>', methods=['PUT'])
def update_group(group_id):
    """Update a vocabulary group"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id FROM word_groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Group not found"}), 404
        
        # Update fields that are provided
        updates = []
        params = []
        
        if 'name' in data:
            updates.append("name = ?")
            params.append(data['name'])
        
        if 'level' in data:
            updates.append("level = ?")
            params.append(data['level'])
        
        if not updates:
            conn.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.append(group_id)
        cursor.execute(
            f"UPDATE word_groups SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Group updated successfully"})
    except Exception as e:
        logger.error(f"Error updating group {group_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    """Delete a vocabulary group"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id FROM word_groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Group not found"}), 404
        
        # Delete words in this group first
        cursor.execute("DELETE FROM words WHERE group_id = ?", (group_id,))
        
        # Delete the group
        cursor.execute("DELETE FROM word_groups WHERE id = ?", (group_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Group deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting group {group_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/words', methods=['POST'])
def create_word():
    """Create a new word"""
    try:
        data = request.get_json()
        
        if not data or 'kanji' not in data or 'english' not in data or 'group_id' not in data:
            return jsonify({"error": "Kanji, English, and group_id are required"}), 400
        
        kanji = data['kanji']
        romaji = data.get('romaji', '')
        english = data['english']
        group_id = data['group_id']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id FROM word_groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Group not found"}), 404
        
        cursor.execute(
            "INSERT INTO words (kanji, romaji, english, group_id) VALUES (?, ?, ?, ?)",
            (kanji, romaji, english, group_id)
        )
        word_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            "id": word_id,
            "kanji": kanji,
            "romaji": romaji,
            "english": english,
            "group_id": group_id
        }), 201
    except Exception as e:
        logger.error(f"Error creating word: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/words/<int:word_id>', methods=['PUT'])
def update_word(word_id):
    """Update a word"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if word exists
        cursor.execute("SELECT id FROM words WHERE id = ?", (word_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Word not found"}), 404
        
        # Update fields that are provided
        updates = []
        params = []
        
        if 'kanji' in data:
            updates.append("kanji = ?")
            params.append(data['kanji'])
        
        if 'romaji' in data:
            updates.append("romaji = ?")
            params.append(data['romaji'])
        
        if 'english' in data:
            updates.append("english = ?")
            params.append(data['english'])
        
        if 'group_id' in data:
            # Check if the new group exists
            cursor.execute("SELECT id FROM word_groups WHERE id = ?", (data['group_id'],))
            if not cursor.fetchone():
                conn.close()
                return jsonify({"error": "Group not found"}), 404
            
            updates.append("group_id = ?")
            params.append(data['group_id'])
        
        if not updates:
            conn.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.append(word_id)
        cursor.execute(
            f"UPDATE words SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Word updated successfully"})
    except Exception as e:
        logger.error(f"Error updating word {word_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/words/<int:word_id>', methods=['DELETE'])
def delete_word(word_id):
    """Delete a word"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if word exists
        cursor.execute("SELECT id FROM words WHERE id = ?", (word_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Word not found"}), 404
        
        cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Word deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting word {word_id}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    
    # Log startup information
    logger.info(f"Starting Vocabulary API server on port 5001")
    logger.info(f"Database path: {DB_PATH}")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)