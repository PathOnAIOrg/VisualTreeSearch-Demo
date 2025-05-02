import pymysql

# Connection parameters
host = '127.0.0.1'
port = 33061
user = 'root'
password = '1234567890'
database = 'magentodb'

print(f"Attempting to connect to MySQL at {host}:{port}...")

try:
    # Create connection
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    
    print("Connection successful!")
    
    # Create cursor and execute query
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        print("\nTables in database:")
        for table in cursor.fetchall():
            print(f"- {table[0]}")
    
    # Close connection
    connection.close()
    print("\nConnection closed.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()