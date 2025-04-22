import json
import sqlite3

# Function to execute SQL commands and return results
def execute_sql_commands(sql_commands):
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    for command in sql_commands.split(';'):
        if command.strip():
            cursor.execute(command.strip())

    data = {}
    for table_name in ['word_groups', 'words', 'sentences', 'writing_submissions']:
        cursor.execute(f"SELECT * FROM {table_name}")
        data[table_name] = cursor.fetchall()

    conn.close()
    return data

# Read SQL commands from the file
with open('db.sqlite3', 'r') as file:
    sql_commands = file.read()

# Execute SQL commands and get data
data = execute_sql_commands(sql_commands)

# Write data to JSON file
with open('database_backup.json', 'w') as json_file:
    json.dump(data, json_file, indent=2)

print("JSON file 'database_backup.json' has been created.")