# api_server.py
import sqlite3
from flask import Flask, jsonify
import threading
import logging

app = Flask(__name__)

def create_app(db_path):
    # Configure routes
    @app.route('/api/health')
    def health_check():
        return jsonify({"status": "ok"})

    @app.route('/api/groups/<int:group_id>/raw')
    def get_group_words(group_id):
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, kanji, romaji, english
                    FROM words
                    WHERE group_id = ?
                """, (group_id,))
                return jsonify([dict(row) for row in cursor.fetchall()])
        except Exception as e:
            logging.error(f"API error: {e}")
            return jsonify({"error": str(e)}), 500

    return app

def run_server(db_path, port=5000):
    flask_app = create_app(db_path)
    flask_app.run(port=port, use_reloader=False)

if __name__ == '__main__':
    from pathlib import Path
    BASE_DIR = Path(__file__).parent.absolute()
    DB_PATH = BASE_DIR.parent / "data" / "db.sqlite3"
    run_server(DB_PATH)