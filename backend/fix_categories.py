import pyodbc

conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=courshop;UID=sa;PWD=YourStrong@Passw0rd'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("DELETE FROM course_categories")
cursor.execute("DBCC CHECKIDENT ('course_categories', RESEED, 0)")

categories = [
    (1, '\u7db2\u9801'),       # 網頁
    (2, 'docker'),
    (3, 'openclaw'),
    (4, 'opencode'),
    (5, 'claude cowork'),
    (6, 'llm\u8a13\u7df4\u8207\u67fb\u8a2d')  # llm訓練與架設
]

print('Inserting with Unicode escapes...')
for id, name in categories:
    cursor.execute("INSERT INTO course_categories (name, sort_order) VALUES (?, ?)", (name, id))
    conn.commit()
    print(f'{id} inserted')

cursor.execute('SELECT id, name FROM course_categories ORDER BY id')
print('\nVerification:')
for row in cursor.fetchall():
    name_bytes = row[1].encode('utf-8') if row[1] else b''
    print(f'{row[0]}: {name_bytes.hex()}')

conn.close()
print('\nDone!')