import pyodbc

conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=courshop;UID=sa;PWD=YourStrong@Passw0rd'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("SELECT id, title FROM courses WHERE is_deleted = 0 AND title IS NOT NULL")
print('Current course titles (raw bytes):')
for row in cursor.fetchall():
    title_bytes = row[1].encode('latin1') if row[1] else b''
    try:
        proper_utf8 = title_bytes.decode('latin1').encode('utf-8')
        print(f'{row[0]}: raw bytes: {title_bytes.hex()} -> try as latin1: {title_bytes.decode("latin1")} -> hex: {proper_utf8.hex()}')
    except:
        print(f'{row[0]}: {row[1].hex() if row[1] else "None"}')

conn.close()