import sqlite3


# Initialize database and create table if it doesn't exist
def init_db():
    conn = sqlite3.connect("locators.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS locators (
                        element_name TEXT PRIMARY KEY,
                        locator_type TEXT,
                        locator_value TEXT,
                        last_healed TEXT)''')
    conn.commit()
    conn.close()


# Insert sample data into the locators table
def insert_sample_data():
    conn = sqlite3.connect("locators.db")
    cursor = conn.cursor()

    # Sample data: elements with different locators
    sample_data = [
        ("loginButton", "id", "newLoginBtn", "2024-11-01 10:00:00"),
        ("searchBox", "name", "queryInput", "2024-11-01 10:05:00"),
        ("submitButton", "css", ".submit-btn", "2024-11-01 10:10:00"),
        ("userMenu", "xpath", "//div[@id='userMenu']", "2024-11-01 10:15:00"),
        ("footerLink", "link_text", "About Us", "2024-11-01 10:20:00")
    ]

    # Insert data into the table
    cursor.executemany(
        "REPLACE INTO locators (element_name, locator_type, locator_value, last_healed) VALUES (?, ?, ?, ?)",
        sample_data)

    conn.commit()
    conn.close()
    print("Sample data inserted successfully.")


# Run initialization and data insertion
init_db()
insert_sample_data()
