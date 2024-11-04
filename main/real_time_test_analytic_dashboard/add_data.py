import sqlite3
import random
from datetime import datetime, timedelta

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('analytics_dashboard.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_execution_status (
        test_case TEXT,
        status TEXT,
        execution_time REAL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS defect_trends (
        date TEXT,
        defect_count INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS coverage_levels (
        coverage_type TEXT,
        percentage INTEGER
    )
''')

# Insert sample data into test_execution_status
test_cases = ["Test Case 1", "Test Case 2", "Test Case 3", "Test Case 4", "Test Case 5"]
statuses = ["Passed", "Failed", "In Progress"]
for _ in range(10):  # Insert 10 records
    test_case = random.choice(test_cases)
    status = random.choice(statuses)
    execution_time = round(random.uniform(1, 5), 2)  # Random execution time between 1 and 5 seconds
    cursor.execute('''
        INSERT INTO test_execution_status (test_case, status, execution_time)
        VALUES (?, ?, ?)
    ''', (test_case, status, execution_time))

# Insert sample data into defect_trends for the past 7 days
today = datetime.now()
for i in range(7):
    date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
    defect_count = random.randint(0, 10)  # Random defect count between 0 and 10
    cursor.execute('''
        INSERT INTO defect_trends (date, defect_count)
        VALUES (?, ?)
    ''', (date, defect_count))

# Insert sample data into coverage_levels
coverage_data = [
    ("Code Coverage", random.randint(70, 95)),  # Random percentage between 70 and 95
    ("Test Case Coverage", random.randint(60, 85))  # Random percentage between 60 and 85
]
for coverage_type, percentage in coverage_data:
    cursor.execute('''
        INSERT INTO coverage_levels (coverage_type, percentage)
        VALUES (?, ?)
    ''', (coverage_type, percentage))

# Commit the transaction and close the connection
conn.commit()
conn.close()

print("Sample data inserted into database.")
