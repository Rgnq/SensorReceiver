import sqlite3
# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('tutorial.db')

cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS movie(title, year, score)")
cur.execute("""
    INSERT INTO movie VALUES
        ('Monty Python and the Holy Grail', 1975, 8.2),
        ('And Now for Something Completely Different', 1971, 7.5)
""")