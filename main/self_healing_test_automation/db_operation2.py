from db_operations import DBManager

# Initialize the DB manager
db_manager = DBManager("locators.db")

# Create a new locator
# db_manager.create_locator(
#     element_name="register_button",
#     primary_locator="xpath=//*[contains(text(), 'Register')]",
#     fallback_locators=[("css_selector", "[id='register']")]
# )
#
# # Retrieve a locator
# locator = db_manager.get_locator("register_button")
# print("Retrieved Locator:", locator)
#
# # Update a locator
# db_manager.update_locator(
#     element_name="register_button",
#     primary_locator="css_selector=[id='register_button']"
# )

# Delete a locator
db_manager.delete_locator("register_button")

# Close the database connection
db_manager.close()
