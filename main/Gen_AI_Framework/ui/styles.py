class Styles:
    MAIN_STYLE = """
        QMainWindow {
            background-color: #f8f9fa;
        }
        QPushButton {
            background-color: #6c757d;
            color: white;
            border: 1px solid #5a6268;
            padding: 6px;
            min-width: 80px;
            border-radius: 4px;
            font-weight: 500;
        }
        /* Additional styles from your existing code */
    """

    BUTTON_STYLES = {
        "primary": """
            background-color: #007bff;
            border: 1px solid #0056b3;
        """,
        "success": """
            background-color: #28a745;
            border: 1px solid #1e7e34;
        """,
        "danger": """
            background-color: #dc3545;
            border: 1px solid #bd2130;
        """
    }