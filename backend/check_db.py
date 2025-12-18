import sqlite3

conn = sqlite3.connect('refres_co.db')
cursor = conn.cursor()

# Check analyses count
cursor.execute('SELECT COUNT(*) FROM analyses')
count = cursor.fetchone()[0]
print(f'Aantal analyses in database: {count}')

# Get first 5 analyses
cursor.execute('SELECT id, workplace_id, status, timestamp FROM analyses LIMIT 5')
print('\nEerste 5 analyses:')
for row in cursor.fetchall():
    print(row)

conn.close()
