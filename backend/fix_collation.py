import pyodbc

conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=courshop;UID=sa;PWD=YourStrong@Passw0rd'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Change name column from varchar to nvarchar
print('Altering name column to nvarchar...')
cursor.execute("ALTER TABLE course_categories ALTER COLUMN name NVARCHAR(100)")
conn.commit()
print('Done!')

# Check new structure
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

print('\nNew table structure:')
for row in cursor.fetchall():
    print(f'Column: {row[0]}, Type: {row[1]}, Length: {row[2]}, Collation: {row[3]}')

conn.close()