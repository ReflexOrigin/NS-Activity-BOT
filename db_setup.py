# db_setup.py
import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('voice_chat.db')
c = conn.cursor()

# Create table with an id column
c.execute('''CREATE TABLE IF NOT EXISTS voice_chat_time (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                time_in_voice INTEGER,
                month_year TEXT
             )''')

# Create archive table for past activity
c.execute('''CREATE TABLE IF NOT EXISTS voice_chat_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                time_in_voice INTEGER,
                month_year TEXT
             )''')

# Save (commit) the changes
conn.commit()

# Close connection
conn.close()
