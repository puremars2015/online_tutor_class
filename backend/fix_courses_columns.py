import pyodbc

conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=courshop;UID=sa;PWD=YourStrong@Passw0rd'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print('Checking courses table structure...')
cursor.execute("""
    SELECT
        c.name as column_name,
        t.name as data_type,
        c.max_length,
        c.collation_name
    FROM sys.columns c
    JOIN sys.types t ON c.user_type_id = t.user_type_id
    WHERE c.object_id = OBJECT_ID('courses')
""")

print('Current structure:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} ({row[2]})')

print('\nAltering columns to nvarchar...')
cursor.execute("ALTER TABLE courses ALTER COLUMN title NVARCHAR(200)")
cursor.execute("ALTER TABLE courses ALTER COLUMN description NVARCHAR(MAX)")
cursor.execute("ALTER TABLE courses ALTER COLUMN content NVARCHAR(MAX)")
cursor.execute("ALTER TABLE courses ALTER COLUMN image_url NVARCHAR(500)")
conn.commit()

print('\nNew structure:')
cursor.execute("""
    SELECT
        c.name as column_name,
        t.name as data_type,
        c.max_length
    FROM sys.columns c
    JOIN sys.types t ON c.user_type_id = t.user_type_id
    WHERE c.object_id = OBJECT_ID('courses')
""")
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} ({row[2]})')

conn.close()
print('\nDone!')