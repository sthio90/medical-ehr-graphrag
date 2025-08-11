import sqlite3
import os

def create_database():
    """Create the database and feedback table if they don't already exist."""
    if not os.path.exists('data'):
        os.makedirs('data')  # Create the 'data' folder if it doesn't exist
    
    conn = sqlite3.connect('data/feedback.db')  # Connect to the database in the 'data' folder
    cursor = conn.cursor()
    
    # Create a table for storing the feedback data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        generated_query TEXT,
        feedback INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()  # Save the changes
    conn.close()   # Close the connection

def store_feedback(question, generated_query, feedback):
    """Store user feedback in the database."""
    # Ensure that question and generated_query are strings
    question = str(question) if question is not None else "Unknown question"
    generated_query = str(generated_query) if generated_query is not None else "Unknown query"
    
    conn = sqlite3.connect('data/feedback.db')  # Connect to the database in the 'data' folder
    cursor = conn.cursor()
    
    # Insert the feedback into the database
    cursor.execute('''
    INSERT INTO feedback (question, generated_query, feedback)
    VALUES (?, ?, ?)
    ''', (question, generated_query, feedback))
    
    conn.commit()  # Save the changes
    conn.close()   # Close the connection

