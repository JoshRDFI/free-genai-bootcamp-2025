# Japanese Vocabulary API

This is a simple API server that provides vocabulary data for the Japanese Writing Practice application.

## Setup and Running

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the server:
   ```
   python server.py
   ```

The server will start on port 5000 and will be accessible at http://localhost:5000.

## API Endpoints

### Health Check
- `GET /api/health` - Check if the API is running

### Vocabulary Groups
- `GET /api/groups` - Get all vocabulary groups
- `GET /api/groups/{group_id}` - Get a specific group with its words
- `GET /api/groups/{group_id}/raw` - Get just the words for a specific group
- `POST /api/groups` - Create a new group
- `PUT /api/groups/{group_id}` - Update a group
- `DELETE /api/groups/{group_id}` - Delete a group

### Words
- `GET /api/words` - Get all words
- `GET /api/words/{word_id}` - Get a specific word
- `POST /api/words` - Create a new word
- `PUT /api/words/{word_id}` - Update a word
- `DELETE /api/words/{word_id}` - Delete a word

## Database

The API uses a SQLite database located at `../data/db.sqlite3`. If the database doesn't exist, it will be created automatically with default vocabulary groups and words.