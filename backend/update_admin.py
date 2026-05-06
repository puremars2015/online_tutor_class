import pyodbc

conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=courshop;UID=sa;PWD=YourStrong@Passw0rd'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("UPDATE admins SET username = N'系統管理員'")
conn.commit()
print('Updated admin username to 系統管理員')

conn.close()