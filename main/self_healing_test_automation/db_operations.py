import sqlite3
import json


class DBManager:
    def __init__(self, db_path="locators.db"):
        """
        Initialize the connection to the SQLite database.

        Parameters:
        - db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.ensure_table_schema()

    def ensure_table_schema(self):
        """
        Ensure the locators table schema exists.
        """
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS locators (
                    element_name TEXT PRIMARY KEY,
                    primary_locator TEXT,
                    fallback_locators TEXT
                )
            """)

    def create_locator(self, element_name, primary_locator, fallback_locators):
        """
        Insert a new locator entry into the database.

        Parameters:
        - element_name: The name of the element.
        - primary_locator: The primary locator (e.g., "id=email").
        - fallback_locators: A list of fallback locators.
        """
        fallback_locators_json = json.dumps(fallback_locators)
        with self.conn:
            self.conn.execute("""
                INSERT INTO locators (element_name, primary_locator, fallback_locators)
                VALUES (?, ?, ?)
            """, (element_name, primary_locator, fallback_locators_json))
        print(f"Locator '{element_name}' created in the database.")

    def get_locator(self, element_name):
        """
        Retrieve a locator entry from the database.

        Parameters:
        - element_name: The name of the element to retrieve.

        Returns:
        - A dictionary with primary and fallback locators if found, else None.
        """
        cursor = self.conn.execute("""
            SELECT primary_locator, fallback_locators FROM locators WHERE element_name = ?
        """, (element_name,))
        row = cursor.fetchone()
        if row:
            primary_locator = row[0]
            fallback_locators = json.loads(row[1])
            return {"primary_locator": primary_locator, "fallback_locators": fallback_locators}
        print(f"Locator '{element_name}' not found in the database.")
        return None

    def update_locator(self, element_name, primary_locator=None, fallback_locators=None):
        """
        Update an existing locator entry in the database.

        Parameters:
        - element_name: The name of the element to update.
        - primary_locator: The new primary locator.
        - fallback_locators: The new fallback locators list.
        """
        updates = []
        params = []
        if primary_locator:
            updates.append("primary_locator = ?")
            params.append(primary_locator)
        if fallback_locators:
            updates.append("fallback_locators = ?")
            params.append(json.dumps(fallback_locators))
        params.append(element_name)

        with self.conn:
            self.conn.execute(f"""
                UPDATE locators SET {', '.join(updates)} WHERE element_name = ?
            """, params)
        print(f"Locator '{element_name}' updated in the database.")

    def delete_locator(self, element_name):
        """
        Delete a locator entry from the database.

        Parameters:
        - element_name: The name of the element to delete.
        """
        with self.conn:
            self.conn.execute("DELETE FROM locators WHERE element_name = ?", (element_name,))
        print(f"Locator '{element_name}' has been deleted from the database.")

    def close(self):
        """
        Close the database connection.
        """
        self.conn.close()
