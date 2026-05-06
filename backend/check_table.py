import pyodbc

conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=courshop;UID=sa;PWD=YourStrong@Passw0rd'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Check table and column info
cursor.execute("""
    SELECT
        c.name as column_name,
        t.name as data_type,
        c.max_length,
        c.collation_name
    FROM sys.columns c
    JOIN sys.types t ON c.user_type_id = t.user_type_id
    WHERE c.object_id = OBJECT_ID('course_categories')
""")

print('Table structure:')
for row in cursor.fetchall():
    print(f'Column: {row[0]}, Type: {row[1]}, Length: {row[2]}, Collation: {row[3]}')

conn.close()