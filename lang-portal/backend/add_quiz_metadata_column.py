from sqlalchemy import create_engine, text
import os

# Create database engine
db_path = os.path.join(os.path.dirname(__file__), 'langportal.db')
engine = create_engine(f'sqlite:///{db_path}')

# Add the quiz_metadata column
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE study_sessions ADD COLUMN quiz_metadata JSON DEFAULT "{}"'))
    conn.commit()

print("Successfully added quiz_metadata column to study_sessions table!") 