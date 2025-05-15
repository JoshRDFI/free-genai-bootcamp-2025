import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging
import streamlit as st

from src.generator import VocabularyGenerator
from src.validator import JLPTValidator
from src.converter import JapaneseConverter
from src.sentence_gen import SentenceGenerator
from src.database import DatabaseManager

print("DEBUG: main.py - Script started") # DEBUG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vocabulary_generator.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_USER_ID = 1
DEFAULT_USER_NAME = 'Default User'
DEFAULT_USER_LEVEL = 'N5'

# Determine Project Root once, assuming main.py is in a subdirectory like 'vocabulary_generator'
# PROJECT_ROOT will be /home/sage/free-genai-bootcamp-2025
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class VocabularyManager:
    def __init__(self, config_path: str = "config/config.json"):
        # config_path is relative to this file's directory (vocabulary_generator)
        abs_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
        self.config = self._load_config(abs_config_path)
        
        self.generator = VocabularyGenerator(abs_config_path) # Assuming VGenerator also wants abs path or handles it
        self.validator = JLPTValidator(abs_config_path) # Assuming JLPTValidator also wants abs path
        self.converter = JapaneseConverter()
        self.sentence_gen = SentenceGenerator(self.config['api']['ollama_endpoint'])
        
        # Resolve database path from config, relative to PROJECT_ROOT
        db_path_from_config = self.config['database']['path']
        actual_db_path = os.path.join(PROJECT_ROOT, db_path_from_config) if not os.path.isabs(db_path_from_config) else db_path_from_config
        self.db = DatabaseManager(actual_db_path)
        logger.info(f"VocabularyManager DB Path: {self.db.db_path}")

        # Resolve and update storage paths in config, relative to PROJECT_ROOT
        for key in ['json_output_dir', 'import_dir', 'backup_dir', 'data_verbs_file']:
            if key in self.config['storage']:
                path_from_config = self.config['storage'][key]
                abs_path = os.path.join(PROJECT_ROOT, path_from_config) if not os.path.isabs(path_from_config) else path_from_config
                self.config['storage'][key] = abs_path # Store the absolute path back in config
                logger.info(f"Resolved config path for '{key}': {abs_path}")

    def _load_config(self, abs_config_path: str) -> Dict:
        """Load and validate configuration"""
        try:
            with open(abs_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate required configuration sections
            required_sections = ['api', 'database', 'storage', 'jlpt_progression']
            missing_sections = [section for section in required_sections if section not in config]
            if missing_sections:
                raise ValueError(f"Missing required configuration sections from {abs_config_path}: {missing_sections}")
            
            logger.info(f"Config loaded successfully from {abs_config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found at {abs_config_path}")
            st.error(f"Critical Error: Config file not found at {abs_config_path}")
            raise   
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {abs_config_path}: {str(e)}")
            st.error(f"Critical Error: Invalid JSON in config file {abs_config_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading config {abs_config_path}: {str(e)}")
            st.error(f"Critical Error: Error loading config {abs_config_path}")
            raise

    async def initialize(self):
        """Initialize the database and create necessary directories"""
        print("DEBUG: VocabularyManager - initialize() started") # DEBUG
        try:
            # Correct DB path is now set in __init__ before DatabaseManager is instantiated.
            # DatabaseManager's own __init__ handles os.makedirs for its db_path.
            
            # Ensure storage directories exist (using absolute paths from config)
            Path(self.config['storage']['json_output_dir']).mkdir(parents=True, exist_ok=True)
            Path(self.config['storage']['import_dir']).mkdir(parents=True, exist_ok=True)
            
            # Backup is handled by DatabaseManager if needed. Connection pool init is also there.
            # Ensure connection pool is initialized before first use by any method that needs it.
            await self.db.init_db() # Initializes pool

            backup_target_dir = self.config['storage'].get('backup_dir')
            if os.path.exists(self.db.db_path):
                if backup_target_dir:
                    await self.db.backup_database(backup_dir=backup_target_dir)
                else:
                    await self.db.backup_database() # Uses default in DatabaseManager
            
            logger.info(f"VocabularyManager initialization completed. DB at: {self.db.db_path}")
            print("DEBUG: VocabularyManager - initialize() completed") # DEBUG
        except Exception as e:
            logger.error(f"VocabularyManager initialization failed: {str(e)}")
            st.error(f"App Initialization Error: {e}") # Show error in Streamlit UI
            raise

    async def create_vocabulary_entry(self, word: str, level: str = "N5", target_group_name: str = "Generated Words") -> Dict:
        """Create a new vocabulary entry with validation, save to JSON, and add to database."""
        try:
            if not isinstance(word, str) or not word.strip():
                raise ValueError("Word must be a non-empty string")
            
            if level not in ['N5', 'N4', 'N3', 'N2', 'N1']:
                raise ValueError(f"Invalid JLPT level: {level}")
            
            # 1. Generate vocabulary entry using LLM (as before)
            entry = await self.generator.generate_vocabulary_entry(word, level)
            # entry is expected to have keys like 'kanji', 'romaji', 'english', and potentially 'parts'
            # If 'parts' is not a string from generator, it needs conversion or handling.
            # For now, assume generator.generate_vocabulary_entry might return parts as dict/list
            # and we ensure it's a JSON string before DB insertion.

            # 2. Validate the generated entry (as before)
            if not self.validator.validate_entry(entry, level):
                raise ValueError(f"Generated entry for '{word}' does not meet {level} requirements")

            # 3. Generate example sentences (as before)
            examples = await self.sentence_gen.generate_examples(entry.get('kanji', word), level) # Use kanji from entry if available
            entry['examples'] = examples

            # 4. Save to JSON file (as before)
            output_dir = Path(self.config['storage']['json_output_dir'])
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{entry.get('kanji', word).replace('/', '_')}_{level}_{timestamp}.json" # Sanitize filename
            output_path = output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved vocabulary entry to {output_path}")

            # 5. Add to database
            # Ensure 'parts' is a JSON string. If entry['parts'] is a dict/list, convert it.
            parts_for_db = entry.get('parts')
            if isinstance(parts_for_db, (dict, list)):
                parts_for_db = json.dumps(parts_for_db, ensure_ascii=False)
            elif not isinstance(parts_for_db, str):
                parts_for_db = '{}' # Default to empty JSON object string if not suitable type
            
            group_id = await self.db.add_word_group(target_group_name)
            if group_id is None:
                logger.error(f"Failed to get or create group ID for '{target_group_name}'")
                # Decide if we should raise an error or just log and not add to DB
                raise ValueError(f"Could not ensure group '{target_group_name}' for DB insertion.")

            word_db_data = {
                'kanji': entry.get('kanji'),
                'romaji': entry.get('romaji'),
                'english': entry.get('english'),
                'parts': parts_for_db,
                'group_id': group_id # For the legacy words.group_id column
            }

            # Validate core fields before attempting to add to DB
            if not all(word_db_data.get(f) for f in ['kanji', 'romaji', 'english']):
                missing_fields = [f for f in ['kanji', 'romaji', 'english'] if not word_db_data.get(f)]
                logger.error(f"LLM-generated entry for '{word}' is missing core fields for DB: {missing_fields}")
                raise ValueError(f"LLM-generated entry for '{word}' is missing core fields for DB: {missing_fields}")

            try:
                word_id = await self.db.add_word(word_db_data)
                await self.db.add_word_to_group(word_id, group_id)
                logger.info(f"Added LLM-generated word '{entry.get('kanji')}' (ID: {word_id}) to DB group '{target_group_name}' (ID: {group_id}).")
                entry['db_id'] = word_id # Add db_id to the returned entry
                entry['db_group_id'] = group_id
            except Exception as db_error:
                logger.error(f"Failed to add LLM-generated word '{entry.get('kanji')}' to database: {db_error}")
                # Optionally re-raise or handle, e.g., by not including db_id in entry
                # For now, let the error propagate if critical, or be logged if already saved to JSON

            return entry
        except Exception as e:
            logger.error(f"Error in create_vocabulary_entry for '{word}': {str(e)}")
            st.error(f"Error creating vocabulary entry for '{word}': {e}")
            raise

    async def import_from_json(self, file_path: str, group_name: str) -> List[Dict]:
        """Import vocabulary from JSON file"""
        user_id = st.session_state.get('user_id') 
        if user_id is None: 
            st.error("User ID not found for import.")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            entries_from_file = json.load(f)
        
        group_id = await self.db.add_word_group(group_name)
        if group_id is None: # Should not happen if add_word_group raises on error
            st.error(f"Failed to find or create group: {group_name}")
            return []

        imported_entries = []
        for entry_data_from_file in entries_from_file:
            # Ensure 'parts' field exists, default to empty JSON object string if not.
            # add_word expects kanji, romaji, english, parts, and group_id (for legacy column).
            # The validator.validate_entry might also need adjustment if it expects 'parts'.
            # For now, we prepare the data for add_word.
            
            word_db_data = {
                'kanji': entry_data_from_file.get('kanji'),
                'romaji': entry_data_from_file.get('romaji'),
                'english': entry_data_from_file.get('english'),
                'parts': entry_data_from_file.get('parts', '{}'), # Default to empty JSON object string
                 # TODO: Review if 'level' or other fields from JSON entry should be used
                 # The current add_word doesn't use 'level' directly, it's more a word attribute.
                 # JLPT level for a word isn't directly stored in words table in current schema.
                 # group_id is for the legacy words.group_id column.
                'group_id': group_id # Use the target group_id for the legacy column.
            }
            
            # Assuming validator.validate_entry is generic enough or we adjust it later.
            # For now, let's assume it doesn't strictly need 'parts' or uses what's provided.
            # The main schema validation for 'parts' is in db_manager._validate_word_data
            
            # Example: If validation is tied to a specific level (e.g. "N5" as before)
            # if self.validator.validate_entry(entry_data_from_file, "N5"): 
            try:
                # _validate_word_data in db_manager will check required fields including 'parts'
                word_id = await self.db.add_word(word_db_data)
                
                # Crucially, add to the join table as well
                await self.db.add_word_to_group(word_id, group_id)
                
                # Add the word_id to the entry data we might return or use
                entry_data_from_file['id'] = word_id 
                entry_data_from_file['group_id'] = group_id # For reference, though it's now M2M
                imported_entries.append(entry_data_from_file)
                logger.info(f"Imported word '{word_db_data['kanji']}' (ID: {word_id}) into group '{group_name}' (ID: {group_id})")
            except ValueError as ve:
                logger.error(f"Validation error importing word '{word_db_data.get('kanji', 'Unknown')}': {ve}")
                st.warning(f"Skipping word '{word_db_data.get('kanji', 'Unknown')}' due to validation error: {ve}")
            except Exception as e:
                logger.error(f"Error importing word '{word_db_data.get('kanji', 'Unknown')}': {e}")
                st.warning(f"Skipping word '{word_db_data.get('kanji', 'Unknown')}' due to import error: {e}")
                
        return imported_entries

    async def create_study_session(self, activity_type: str, group_id: int) -> Dict:
        """Create a new study session"""
        user_id = st.session_state.get('user_id')
        if user_id is None:
            st.error("User ID not found in session state. Cannot create study session.")
            return None
        session_data = {
            'activity_type': activity_type,
            'group_id': group_id,
            'user_id': user_id,
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': 0,
            'accuracy': 0.0
        }
        session_id = await self.db.add_study_session(session_data)
        return {'session_id': session_id, **session_data}

    async def end_study_session(self, session_id: int) -> Dict:
        """End a study session and calculate final metrics"""
        end_time = datetime.now()
        session = await self.db.get_study_session(session_id)

        if session:
            start_time = datetime.fromisoformat(session['start_time'])
            duration = int((end_time - start_time).total_seconds() / 60)  # Duration in minutes

            # Calculate session accuracy
            reviews = await self.db.get_session_reviews(session_id)
            correct_count = sum(1 for review in reviews if review['correct'])
            accuracy = correct_count / len(reviews) if reviews else 0.0

            # Update session
            await self.db.update_study_session(session_id, {
                'end_time': end_time.isoformat(),
                'duration': duration,
                'accuracy': accuracy * 100  # Store as percentage
            })

            return await self.db.get_study_session(session_id)
        return None

    async def add_word_review(self, word_id: int, session_id: int, correct: bool):
        """Add a word review result"""
        user_id = st.session_state.get('user_id')
        if user_id is None: st.error("User ID not found."); return

        review_data = {
            'word_id': word_id,
            'session_id': session_id,
            'correct': correct
        }
        await self.db.add_word_review(review_data)

    async def get_user_stats(self) -> Optional[Dict]:
        """Get comprehensive user statistics"""
        user_id = st.session_state.get('user_id')
        if user_id is None:
            st.error("User ID not found. Cannot get stats.")
            return None
        user = await self.db.get_user(user_id)
        if not user: return None
        sessions = await self.db.get_user_sessions(user_id)
        reviews = await self.db.get_user_reviews(user_id)
        total_reviews = len(reviews)
        correct_reviews = sum(1 for review in reviews if review['correct'])
        return {
            'current_level': user['current_level'],
            'total_sessions': len(sessions),
            'total_reviews': total_reviews,
            'accuracy': (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0,
            'study_time': sum(s['duration'] for s in sessions if s.get('duration'))
        }

    async def check_progression(self, current_level: str) -> bool:
        """Check if ready to progress to next JLPT level"""
        if current_level not in self.config['jlpt_progression']:
            return False

        criteria = self.config['jlpt_progression'][current_level]
        required_accuracy = criteria['required_accuracy']
        minimum_reviews = criteria['minimum_reviews']

        groups = await self.db.get_all_word_groups()
        total_reviews = 0
        total_correct = 0

        for group in groups:
            words = await self.db.get_words_by_group(group['id'])
            for word in words:
                total_correct += word['correct_count']
                total_reviews += word['correct_count'] + word['wrong_count']

        if total_reviews < minimum_reviews:
            return False

        accuracy = total_correct / total_reviews if total_reviews > 0 else 0
        return accuracy >= required_accuracy

    async def advance_level(self) -> Optional[str]:
        """Advance user to next JLPT level if eligible"""
        user_id = st.session_state.get('user_id')
        if user_id is None: st.error("User ID not found."); return None
        user = await self.db.get_user(user_id)
        if not user: return None
        current_level = user['current_level']
        if await self.check_progression(current_level):
            next_level = self.config['jlpt_progression'][current_level]['next_level']
            await self.db.add_progression_history({
                'user_id': user_id,
                'previous_level': current_level,
                'new_level': next_level
            })
            await self.db.update_user_level(user_id, next_level)
            return next_level
        return None

    async def get_progression_history(self) -> List[Dict]:
        """Get JLPT level progression history"""
        user_id = st.session_state.get('user_id')
        if user_id is None: st.error("User ID not found."); return []
        return await self.db.get_progression_history(user_id)

async def main():
    """Example usage of the VocabularyManager"""
    print("DEBUG: async main() - Function started") # DEBUG
    manager = VocabularyManager()
    print("DEBUG: async main() - Initializing VocabularyManager...") # DEBUG
    await manager.initialize()
    print("DEBUG: async main() - VocabularyManager initialized.") # DEBUG

    # Import vocabulary
    imported = await manager.import_from_json(
        os.path.join(os.path.dirname(__file__), 'data', 'data_verbs.json'),
        'Core Verbs'
    )
    print(f"Imported {len(imported)} verbs")

    # Create study session
    session = await manager.create_study_session('typing_tutor', 1)

    # Simulate some word reviews
    for word_id in range(1, 6):
        await manager.add_word_review(word_id, session['session_id'], True)

    # End session
    await manager.end_study_session(session['session_id'])

    # Check progression history
    history = await manager.get_progression_history()
    for entry in history:
        print(f"Progressed from {entry['previous_level']} to {entry['new_level']} on {entry['progressed_at']}")

# if __name__ == "__main__":
#     asyncio.run(main())

@st.cache_resource
def get_manager_instance():
    print("DEBUG: get_manager_instance() - Creating and initializing VocabularyManager.")
    manager_instance = VocabularyManager()
    try:
        asyncio.run(manager_instance.initialize())
        user_id = asyncio.run(manager_instance.db.ensure_default_user_exists(
            DEFAULT_USER_ID, DEFAULT_USER_NAME, DEFAULT_USER_LEVEL
        ))
        st.session_state.user_id = user_id
        print(f"DEBUG: get_manager_instance() - Manager initialized. User ID: {user_id}")
    except Exception as e:
        print(f"ERROR: get_manager_instance() - Failed to initialize manager or ensure user: {e}")
        st.error(f"Application failed to initialize: {e}")
        return None
    return manager_instance

manager = get_manager_instance()

st.title("Vocabulary Generator App")

if manager and 'user_id' in st.session_state:
    st.success(f"Vocabulary Manager initialized. User ID: {st.session_state.user_id}")

    st.subheader("User Stats")
    if st.button("Refresh Stats"):
        stats = asyncio.run(manager.get_user_stats())
        if stats:
            st.metric(label="Current JLPT Level", value=stats['current_level'])
            st.metric(label="Total Study Sessions", value=stats['total_sessions'])
            st.metric(label="Total Reviews", value=stats['total_reviews'])
            st.metric(label="Overall Accuracy", value=f"{stats['accuracy']:.2f}%")
            st.metric(label="Total Study Time (minutes)", value=stats['study_time'])
        else:
            st.write("Could not load user stats.")
    
    st.subheader("Progression History")
    if st.button("Show Progression History"):
        history = asyncio.run(manager.get_progression_history())
        if history:
            st.dataframe(history)
        else:
            st.write("No progression history found or error loading.")

    st.subheader("Vocabulary Import")
    # Get the configured absolute path for data_verbs.json
    data_verbs_path = manager.config['storage'].get('data_verbs_file') 
    if st.button("Import Core Verbs"):
        if data_verbs_path and os.path.exists(data_verbs_path):
            with st.spinner("Importing Core Verbs..."):
                try:
                    imported_verbs = asyncio.run(manager.import_from_json(data_verbs_path, 'Core Verbs'))
                    st.success(f"Imported {len(imported_verbs)} verbs from Core Verbs.")
                except Exception as e:
                    st.error(f"Error importing Core Verbs: {e}")
                    logger.error(f"Error importing Core Verbs: {e}")
        else:
            st.error(f"Core Verbs file not found at: {data_verbs_path}")

    # --- Study Session Management ---
    if 'active_session_id' not in st.session_state:
        st.session_state.active_session_id = None
        st.session_state.current_session_details = {}
        st.session_state.session_words = []
        st.session_state.current_word_index = 0

    if st.session_state.active_session_id is None:
        st.subheader("Start New Study Session")
        
        # Fetch word groups
        word_groups_raw = asyncio.run(manager.db.get_all_word_groups()) 
        group_options = {}
        if word_groups_raw:
            for group in word_groups_raw:
                group_options[f"{group['name']} ({group.get('words_count', 0)} words)"] = group['id']
        
        activity_types = ['typing_tutor', 'flashcards', 'adventure_mud'] # Example types
        
        with st.form("start_session_form"):
            selected_activity = st.selectbox("Select Activity Type:", options=activity_types)
            selected_group_name = st.selectbox("Select Word Group:", options=list(group_options.keys()))
            submitted = st.form_submit_button("Start Session")

            if submitted and selected_group_name:
                selected_group_id = group_options[selected_group_name]
                with st.spinner("Starting session..."):
                    try:
                        session_info = asyncio.run(manager.create_study_session(selected_activity, selected_group_id))
                        if session_info and 'session_id' in session_info:
                            st.session_state.active_session_id = session_info['session_id']
                            st.session_state.current_session_details = session_info
                            # Fetch words for the session
                            # Assuming get_words_by_group returns a list of word dicts
                            st.session_state.session_words = asyncio.run(manager.db.get_words_by_group(selected_group_id))
                            st.session_state.current_word_index = 0
                            logger.info(f"Started session {st.session_state.active_session_id} with {len(st.session_state.session_words)} words.")
                            st.experimental_rerun() # Rerun to update UI for active session
                        else:
                            st.error("Failed to create session. Please check logs.")
                    except Exception as e:
                        st.error(f"Error starting session: {e}")
                        logger.error(f"Error starting session: {e}", exc_info=True)
    else:
        # --- UI for Active Study Session ---
        st.subheader(f"Active Study Session: {st.session_state.current_session_details.get('activity_type')}")
        st.write(f"Session ID: {st.session_state.active_session_id}")
        st.write(f"Studying Group ID: {st.session_state.current_session_details.get('group_id')}")
        st.write(f"Words in session: {len(st.session_state.session_words)}")

        if not st.session_state.session_words:
            st.warning("No words found for this session group. Ending session.")
            # Potentially auto-end session or allow user to pick another group
            if st.button("End Session (No Words)"):
                if st.session_state.active_session_id:
                     with st.spinner("Ending session..."):
                        asyncio.run(manager.end_study_session(st.session_state.active_session_id))
                st.session_state.active_session_id = None
                st.session_state.current_session_details = {}
                st.session_state.session_words = []
                st.experimental_rerun()
        elif st.session_state.current_word_index < len(st.session_state.session_words):
            current_word = st.session_state.session_words[st.session_state.current_word_index]
            st.write(f"Current word: {current_word['kanji']} ({current_word['romaji']}) - {current_word['english']}")
            # Display parts if available
            if 'parts' in current_word and current_word['parts']:
                try:
                    parts_data = json.loads(current_word['parts'])
                    st.json(parts_data, expanded=False) # Display JSON, collapsed by default
                except json.JSONDecodeError:
                    st.text(f"Parts of speech (raw): {current_word['parts']}") # Fallback for invalid JSON
            
            # TODO: Add interactive elements based on activity_type (typing_tutor, flashcards)
            
            # Example: Next word button (simple navigation for now)
            if st.button("Next Word"):
                st.session_state.current_word_index += 1
                st.experimental_rerun()
        else:
            st.success("All words in this session completed!")
            # TODO: Progression check can happen here

        # Always show End Session button if a session is active
        if st.button("End Current Session"):
            with st.spinner("Ending session..."):
                asyncio.run(manager.end_study_session(st.session_state.active_session_id))
                # Optionally, show session summary before clearing
                st.success(f"Session {st.session_state.active_session_id} ended.")
            st.session_state.active_session_id = None
            st.session_state.current_session_details = {}
            st.session_state.session_words = []
            st.session_state.current_word_index = 0
            st.experimental_rerun()

else:
    st.error("Vocabulary Manager failed to initialize. Application cannot start. Please check server logs for critical errors.")