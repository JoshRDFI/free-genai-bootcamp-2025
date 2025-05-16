#!/usr/bin/env python3
import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "shared_db" / "db.sqlite3"

# Combined word categories with words from both files
WORD_CATEGORIES = [
    # N5 Level Categories
    {
        "name": "Basic Greetings",
        "level": "N5",
        "words": [
            ("こんにちは", "konnichiwa", "Hello"),
            ("ありがとう", "arigatou", "Thank you"),
            ("おはよう", "ohayou", "Good morning"),
            ("さようなら", "sayounara", "Goodbye"),
            ("こんばんは", "konbanwa", "Good evening"),
            ("すみません", "sumimasen", "Excuse me/I'm sorry"),
            ("いってきます", "ittekimasu", "I'm leaving"),
            ("いってらっしゃい", "itterasshai", "Have a safe trip"),
            ("ただいま", "tadaima", "I'm home"),
            ("おかえり", "okaeri", "Welcome back")
        ]
    },
    {
        "name": "Daily Life",
        "level": "N5",
        "words": [
            ("朝ごはん", "asagohan", "Breakfast"),
            ("昼ごはん", "hirugohan", "Lunch"),
            ("晩ごはん", "bangohan", "Dinner"),
            ("水", "mizu", "Water"),
            ("お茶", "ocha", "Tea"),
            ("コーヒー", "koohii", "Coffee"),
            ("家", "ie", "House"),
            ("部屋", "heya", "Room"),
            ("トイレ", "toire", "Toilet"),
            ("お風呂", "ofuro", "Bath")
        ]
    },
    {
        "name": "Basic Adjectives",
        "level": "N5",
        "words": [
            ("大きい", "ookii", "Big"),
            ("小さい", "chiisai", "Small"),
            ("暑い", "atsui", "Hot (weather)"),
            ("寒い", "samui", "Cold"),
            ("良い", "yoi", "Good"),
            ("悪い", "warui", "Bad"),
            ("新しい", "atarashii", "New"),
            ("古い", "furui", "Old"),
            ("忙しい", "isogashii", "Busy"),
            ("楽しい", "tanoshii", "Fun")
        ]
    },

    # N4 Level Categories
    {
        "name": "Common Verbs",
        "level": "N4",
        "words": [
            ("食べる", "taberu", "To eat"),
            ("飲む", "nomu", "To drink"),
            ("行く", "iku", "To go"),
            ("来る", "kuru", "To come"),
            ("見る", "miru", "To see"),
            ("聞く", "kiku", "To hear/ask"),
            ("話す", "hanasu", "To speak"),
            ("読む", "yomu", "To read"),
            ("書く", "kaku", "To write"),
            ("買う", "kau", "To buy"),
            ("売る", "uru", "To sell"),
            ("待つ", "matsu", "To wait")
        ]
    },
    {
        "name": "Weather",
        "level": "N4",
        "words": [
            ("天気", "tenki", "Weather"),
            ("雨", "ame", "Rain"),
            ("雪", "yuki", "Snow"),
            ("曇り", "kumori", "Cloudy"),
            ("晴れ", "hare", "Sunny"),
            ("風", "kaze", "Wind"),
            ("台風", "taifuu", "Typhoon"),
            ("気温", "kion", "Temperature"),
            ("湿度", "shitsudo", "Humidity")
        ]
    },

    # N3 Level Categories
    {
        "name": "Travel",
        "level": "N3",
        "words": [
            ("飛行機", "hikouki", "Airplane"),
            ("ホテル", "hoteru", "Hotel"),
            ("観光", "kankou", "Sightseeing"),
            ("旅行", "ryokou", "Travel"),
            ("予約", "yoyaku", "Reservation"),
            ("切符", "kippu", "Ticket"),
            ("パスポート", "pasupooto", "Passport"),
            ("出発", "shuppatsu", "Departure"),
            ("到着", "touchaku", "Arrival"),
            ("案内所", "annaijo", "Information center"),
            ("両替", "ryougae", "Currency exchange"),
            ("荷物", "nimotsu", "Luggage")
        ]
    },
    {
        "name": "Emotions",
        "level": "N3",
        "words": [
            ("幸せ", "shiawase", "Happiness"),
            ("悲しい", "kanashii", "Sad"),
            ("怒り", "ikari", "Anger"),
            ("不安", "fuan", "Anxiety"),
            ("心配", "shinpai", "Worry"),
            ("喜び", "yorokobi", "Joy"),
            ("恐れ", "osore", "Fear"),
            ("驚き", "odoroki", "Surprise"),
            ("期待", "kitai", "Expectation")
        ]
    },

    # N2 Level Categories
    {
        "name": "Work",
        "level": "N2",
        "words": [
            ("会議", "kaigi", "Meeting"),
            ("報告", "houkoku", "Report"),
            ("プロジェクト", "purojekuto", "Project"),
            ("締め切り", "shimekiri", "Deadline"),
            ("残業", "zangyou", "Overtime"),
            ("昇進", "shoushin", "Promotion"),
            ("給料", "kyuuryou", "Salary"),
            ("採用", "saiyou", "Recruitment"),
            ("退職", "taishoku", "Resignation"),
            ("面接", "mensetsu", "Interview"),
            ("契約", "keiyaku", "Contract"),
            ("取引", "torihiki", "Transaction")
        ]
    },
    {
        "name": "Technology",
        "level": "N2",
        "words": [
            ("情報", "jouhou", "Information"),
            ("技術", "gijutsu", "Technology"),
            ("開発", "kaihatsu", "Development"),
            ("システム", "shisutemu", "System"),
            ("データ", "deeta", "Data"),
            ("ネットワーク", "nettowaaku", "Network"),
            ("セキュリティ", "sekuriti", "Security"),
            ("更新", "koushin", "Update"),
            ("設定", "settei", "Settings")
        ]
    },

    # N1 Level Categories
    {
        "name": "Advanced Concepts",
        "level": "N1",
        "words": [
            ("哲学", "tetsugaku", "Philosophy"),
            ("経済", "keizai", "Economy"),
            ("政治", "seiji", "Politics"),
            ("環境", "kankyou", "Environment"),
            ("文明", "bunmei", "Civilization"),
            ("革新", "kakushin", "Innovation"),
            ("思想", "shisou", "Ideology"),
            ("倫理", "rinri", "Ethics"),
            ("主義", "shugi", "Principle/Doctrine"),
            ("概念", "gainen", "Concept"),
            ("理論", "riron", "Theory"),
            ("仮説", "kasetsu", "Hypothesis")
        ]
    },
    {
        "name": "Academic",
        "level": "N1",
        "words": [
            ("研究", "kenkyuu", "Research"),
            ("分析", "bunseki", "Analysis"),
            ("仮定", "katei", "Assumption"),
            ("証明", "shoumei", "Proof"),
            ("結論", "ketsuron", "Conclusion"),
            ("引用", "in'you", "Citation"),
            ("論文", "ronbun", "Thesis/Paper"),
            ("実験", "jikken", "Experiment"),
            ("調査", "chousa", "Investigation"),
            ("統計", "toukei", "Statistics")
        ]
    }
]

def initialize_basic_words():
    """Initialize the database with basic word categories and words."""
    try:
        logger.info(f"Initializing basic words in {DB_PATH}")
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            for category in WORD_CATEGORIES:
                # Insert word group
                cursor.execute(
                    "INSERT INTO word_groups (name, level) VALUES (?, ?)",
                    (category["name"], category["level"])
                )
                group_id = cursor.lastrowid
                
                # Insert words
                cursor.executemany(
                    """INSERT INTO words 
                    (kanji, romaji, english, group_id) 
                    VALUES (?, ?, ?, ?)""",
                    [(w[0], w[1], w[2], group_id) for w in category["words"]]
                )
                
                # Update word count in word_groups
                cursor.execute(
                    "UPDATE word_groups SET words_count = ? WHERE id = ?",
                    (len(category["words"]), group_id)
                )
            
            conn.commit()
            logger.info(f"Successfully inserted {len(WORD_CATEGORIES)} categories with basic words")
            return True
            
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    initialize_basic_words() 