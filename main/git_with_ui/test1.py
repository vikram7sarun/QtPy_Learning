import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QTextEdit, QLabel, QScrollArea, QComboBox, QFormLayout, QDialog, QLineEdit, QFileDialog, QCheckBox
)
from PyQt5.QtCore import QProcess

DB_FILE = "repositories.db"


class AddRepoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Repository URL")
        self.setGeometry(300, 300, 300, 100)

        layout = QVBoxLayout()
        self.repo_url_input = QLineEdit(self)
        layout.addWidget(QLabel("Repo URL"))
        layout.addWidget(self.repo_url_input)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def get_repo_url(self):
        return self.repo_url_input.text()


class CloneRepoDialog(QDialog):
    def __init__(self, repo_urls, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clone Repository")
        self.setGeometry(300, 300, 400, 150)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.repo_url_dropdown = QComboBox()
        self.repo_url_dropdown.addItems(repo_urls)
        form_layout.addRow("Repository URL:", self.repo_url_dropdown)

        self.directory_label = QLabel("No directory selected")
        self.select_dir_button = QPushButton("Select Directory")
        self.select_dir_button.clicked.connect(self.select_directory)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.select_dir_button)
        dir_layout.addWidget(self.directory_label)

        layout.addLayout(form_layout)
        layout.addLayout(dir_layout)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)
        self.selected_directory = ""

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory for Cloning")
        if directory:
            self.selected_directory = directory
            self.directory_label.setText(directory)

    def get_selected_repo_url(self):
        return self.repo_url_dropdown.currentText()

    def get_selected_directory(self):
        return self.selected_directory


class GitAddDialog(QDialog):
    """Dialog to select files for git add."""

    def __init__(self, modified_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Files to Add")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()

        # Add checkboxes for each modified file
        self.checkboxes = []
        for file in modified_files:
            checkbox = QCheckBox(file)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        # Add All Files button
        self.add_all_button = QPushButton("Add All Files")
        self.add_all_button.clicked.connect(self.select_all_files)

        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        # Layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_all_button)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def select_all_files(self):
        # Select all checkboxes
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def get_selected_files(self):
        # Return list of selected files
        return [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]


class GitTab(QWidget):
    def __init__(self, commands):
        super().__init__()

        self.init_database()

        main_layout = QHBoxLayout()

        self.command_buttons_layout = QVBoxLayout()
        for cmd in commands:
            button = QPushButton(cmd)
            self.setup_button(button, cmd)
            self.command_buttons_layout.addWidget(button)

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.command_buttons_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        main_layout.addWidget(scroll_area, 1)

        output_layout = QVBoxLayout()

        input_layout = QFormLayout()

        self.repo_url_dropdown = QComboBox()
        self.load_repositories()
        self.add_button = QPushButton("Add")
        self.add_button.setFixedWidth(50)
        self.add_button.clicked.connect(self.open_add_repo_dialog)

        repo_url_layout = QHBoxLayout()
        repo_url_layout.addWidget(self.repo_url_dropdown)
        repo_url_layout.addWidget(self.add_button)

        input_layout.addRow("Repository URL:", repo_url_layout)

        output_layout.addLayout(input_layout)

        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        output_layout.addWidget(QLabel("Terminal Output"))
        output_layout.addWidget(self.terminal_output, 1)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command here...")
        self.command_input.returnPressed.connect(self.run_user_command)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_user_command)

        command_input_layout = QHBoxLayout()
        command_input_layout.addWidget(self.command_input)
        command_input_layout.addWidget(self.run_button)
        output_layout.addLayout(command_input_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        output_layout.addWidget(QLabel("Log Output"))
        output_layout.addWidget(self.log_output, 3)

        main_layout.addLayout(output_layout, 3)

        self.setLayout(main_layout)

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.command_finished)

    def setup_button(self, button, command):
        button.clicked.connect(lambda checked: self.run_command(command))

    def open_add_repo_dialog(self):
        dialog = AddRepoDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_repo_url = dialog.get_repo_url()
            if new_repo_url:
                self.add_repository_to_database(new_repo_url)
                self.repo_url_dropdown.addItem(new_repo_url)

    def init_database(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_url TEXT UNIQUE
            )
        ''')
        conn.commit()
        conn.close()

    def add_repository_to_database(self, repo_url):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO repositories (repo_url) VALUES (?)", (repo_url,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()

    def load_repositories(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT repo_url FROM repositories")
        rows = cursor.fetchall()
        for row in rows:
            self.repo_url_dropdown.addItem(row[0])
        conn.close()

    def run_command(self, command):
        if command == "git init":
            # Prompt for directory selection for `git init`
            directory = QFileDialog.getExistingDirectory(self, "Select Directory for git init")
            if directory:
                self.terminal_output.append(f"$ git init (in directory: {directory})")
                self.process.setWorkingDirectory(directory)
                self.process.start("git init")
            else:
                self.terminal_output.append("Directory selection canceled.")

        elif command == "git clone <repository-url>":
            # Prompt for repository URL and directory for cloning
            repo_urls = [self.repo_url_dropdown.itemText(i) for i in range(self.repo_url_dropdown.count())]
            dialog = CloneRepoDialog(repo_urls, self)
            if dialog.exec() == QDialog.Accepted:
                selected_repo_url = dialog.get_selected_repo_url()
                selected_directory = dialog.get_selected_directory()

                if selected_repo_url and selected_directory:
                    self.terminal_output.append(f"$ git clone {selected_repo_url}")
                    self.process.setWorkingDirectory(selected_directory)
                    self.process.start(f"git clone {selected_repo_url}")
                else:
                    self.terminal_output.append("Cloning canceled.")

        elif command == "git status":
            # Run git status in the current working directory without prompting for directory selection
            current_directory = self.process.workingDirectory()
            if current_directory:
                self.terminal_output.append(f"$ git status (in directory: {current_directory})")
                self.process.start("git status")
            else:
                self.terminal_output.append("Please set a directory with `git init` or `git clone` first.")

        elif command == "git add":
            # Prompt for directory selection, then display modified files for selection
            directory = QFileDialog.getExistingDirectory(self, "Select Directory for git add")
            if directory:
                self.process.setWorkingDirectory(directory)
                self.process.start("git status --short")
                self.process.finished.connect(self.show_git_add_dialog)
            else:
                self.terminal_output.append("Directory selection canceled.")

        else:
            # Handle other commands directly in the current working directory
            repo_url = self.repo_url_dropdown.currentText()
            self.terminal_output.append(f"$ {command} (Repo: {repo_url})")
            self.process.start(command)

    def show_git_add_dialog(self):
        output = self.process.readAllStandardOutput().data().decode().strip()
        modified_files = [line[3:] for line in output.splitlines() if line.startswith(" M")]

        dialog = GitAddDialog(modified_files, self)
        if dialog.exec() == QDialog.Accepted:
            selected_files = dialog.get_selected_files()
            if selected_files:
                for file in selected_files:
                    self.terminal_output.append(f"$ git add {file}")
                    self.process.start(f"git add {file}")
                    self.process.waitForFinished()
                self.terminal_output.append("Selected files added.")
            else:
                self.terminal_output.append("No files selected for addition.")

    def run_user_command(self):
        user_command = self.command_input.text().strip()
        if user_command:
            self.terminal_output.append(f"$ {user_command}")
            self.command_input.clear()
            self.process.start(user_command)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.terminal_output.append(data)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.log_output.append(data)

    def command_finished(self):
        self.log_output.append("Command finished.\n")


class GitCommandsUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Git Command Interface")
        self.setGeometry(200, 200, 800, 600)

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()

        commands = {
            "Basic Git Commands": [
                "git init", "git clone <repository-url>", "git status",
                "git add <file-or-directory>", "git commit -m 'Your message'",
                "git push origin <branch-name>", "git pull origin <branch-name>"
            ],
            "Branch Management": [
                "git branch <branch-name>", "git checkout <branch-name>",
                "git checkout -b <branch-name>", "git merge <branch-name>",
                "git branch -d <branch-name>", "git push origin --delete <branch-name>"
            ],
            "Working with Remote Repositories": [
                "git remote add origin <repository-url>", "git remote -v",
                "git remote rename <old-name> <new-name>", "git remote remove <remote-name>"
            ],
            "Resetting and Reverting": [
                "git reset --soft HEAD~1", "git reset --hard HEAD~1", "git revert <commit-hash>"
            ],
            "Viewing and Logging": [
                "git log", "git log --oneline", "git diff"
            ],
            "Stashing Changes": [
                "git stash", "git stash list", "git stash apply", "git stash drop <stash@{n}>"
            ]
        }

        for tab_name, tab_commands in commands.items():
            tab = GitTab(tab_commands)
            self.tabs.addTab(tab, tab_name)

        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)


# Run the application
app = QApplication(sys.argv)
window = GitCommandsUI()
window.show()
sys.exit(app.exec_())
