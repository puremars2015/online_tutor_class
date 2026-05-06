import pyodbc

conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=courshop;UID=sa;PWD=YourStrong@Passw0rd'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print('Altering admins username column to NVARCHAR...')

cursor.execute("ALTER TABLE admins ALTER COLUMN username NVARCHAR(80)")
conn.commit()
print('Done!')

conn.close()