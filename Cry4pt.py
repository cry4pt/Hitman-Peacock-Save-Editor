import json, sys, re, os
from PySide6.QtWidgets import (QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem,
                               QMenu, QInputDialog, QMessageBox, QLineEdit,
                               QWidget, QVBoxLayout, QTabWidget, QTextEdit, QPushButton,
                               QStatusBar)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont, QSyntaxHighlighter, QColor
from collections import defaultdict

# JSON Syntax Highlighter
class JsonHighlighter(QSyntaxHighlighter):
    """Simple JSON syntax highlighter."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlight_rules = [
            (r'"[^"\\]*(\\.[^"\\]*)*"', QColor(Qt.darkGreen)),  # Strings
            (r'\b(true|false|null)\b', QColor(Qt.darkBlue)),     # Keywords
            (r'\b\d+\b', QColor(Qt.darkMagenta)),                # Numbers
        ]

    def highlightBlock(self, text):
        for pattern, color in self.highlight_rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                fmt = self.format(start)
                fmt.setForeground(color)
                self.setFormat(start, end - start, fmt)

# Main JSON Editor Class
class JsonEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced JSON Editor")
        self.resize(1000, 700)

        # Find and load JSON file
        self.json_file_path = self.find_peacock_user_json()
        if not self.json_file_path:
            QMessageBox.critical(self, "Error", "No JSON file found.")
            sys.exit(1)
        self.load_json()

        # Set up tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Tree View Tab
        self.tree_tab = QWidget()
        tree_layout = QVBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for 'mymoney', 'xpgain', 'profilelevel'...")
        tree_layout.addWidget(self.search_bar)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Key", "Value"])
        self.tree.setColumnWidth(0, 400)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        tree_layout.addWidget(self.tree)
        self.path_bar = QLineEdit()
        self.path_bar.setReadOnly(True)
        tree_layout.addWidget(self.path_bar)
        self.tree_tab.setLayout(tree_layout)
        self.tab_widget.addTab(self.tree_tab, "Tree View")

        # Raw JSON Editor Tab
        self.raw_tab = QWidget()
        raw_layout = QVBoxLayout()
        self.raw_editor = QTextEdit()
        self.raw_editor.setFont(QFont("Courier", 10))
        self.highlighter = JsonHighlighter(self.raw_editor.document())
        raw_layout.addWidget(self.raw_editor)
        refresh_button = QPushButton("Refresh Tree from Raw JSON")
        refresh_button.clicked.connect(self.refresh_tree_from_raw)
        raw_layout.addWidget(refresh_button)
        self.raw_tab.setLayout(raw_layout)
        self.tab_widget.addTab(self.raw_tab, "Raw JSON Editor")

        # Cheats Tab
        self.cheats_tab = QWidget()
        cheats_layout = QVBoxLayout()
        cheats_layout.setContentsMargins(10, 10, 10, 10)
        cheats_layout.setSpacing(5)

        set_levels_button = QPushButton("Set All Location Levels")
        set_levels_button.clicked.connect(self.set_all_location_levels)
        cheats_layout.addWidget(set_levels_button)

        set_challenge_button = QPushButton("Set All Challenge Progression")
        set_challenge_button.clicked.connect(self.set_all_challenge_progresion)
        cheats_layout.addWidget(set_challenge_button)

        copy_locations_button = QPushButton("Copy Locations to Sublocations")
        copy_locations_button.clicked.connect(self.copy_locations_to_sublocations)
        cheats_layout.addWidget(copy_locations_button)

        set_sublocations_xp_button = QPushButton("Set All Sublocations XP")
        set_sublocations_xp_button.clicked.connect(self.set_all_sublocations_xp)
        cheats_layout.addWidget(set_sublocations_xp_button)

        copy_escalations_played_button = QPushButton("Copy Peacock Escalations to Played Contracts")
        copy_escalations_played_button.clicked.connect(self.copy_peacock_escalations_to_played_contracts)
        cheats_layout.addWidget(copy_escalations_played_button)

        copy_escalations_completed_button = QPushButton("Copy Peacock Escalations to Completed Escalations")
        copy_escalations_completed_button.clicked.connect(self.copy_peacock_escalations_to_completed_escalations)
        cheats_layout.addWidget(copy_escalations_completed_button)

        cheats_layout.addStretch()
        self.cheats_tab.setLayout(cheats_layout)
        self.tab_widget.addTab(self.cheats_tab, "Cheats")

        # Populate UI
        self.populate_tree()
        self.update_raw_editor()

        # Connect signals
        self.tree.itemChanged.connect(self.on_item_changed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        self.tree.itemSelectionChanged.connect(self.update_path_bar)

        # Menu and status bar
        self.setup_menu_bar()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    ### File and JSON Handling
    def find_peacock_user_json(self):
        home_dir = os.path.expanduser('~')
        search_dirs = [
            os.path.join(home_dir, 'Games'),
            os.path.join(home_dir, 'Desktop'),
            os.path.join(home_dir, 'Documents'),
            os.path.join(home_dir, 'Downloads'),
            home_dir
        ]
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.json$', re.IGNORECASE)

        for base_dir in search_dirs:
            if not os.path.isdir(base_dir):
                continue
            for root, dirs, files in os.walk(base_dir):
                for dir_name in dirs:
                    if dir_name.lower() == "peacock":
                        peacock_dir = os.path.join(root, dir_name, "userdata")
                        if os.path.isdir(peacock_dir):
                            users_dir = os.path.join(peacock_dir, "users")
                            for check_dir in [users_dir, peacock_dir]:  # check both
                                if os.path.isdir(check_dir):
                                    for entry in os.listdir(check_dir):
                                        entry_path = os.path.join(check_dir, entry)
                                        if os.path.isfile(entry_path) and uuid_pattern.match(entry):
                                            print(f"Found Peacock user JSON: {entry_path}")
                                            return entry_path
        print("No matching Peacock user JSON found.")
        return None

    def load_json(self):
        try:
            with open(self.json_file_path, "r") as f:
                self.json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load JSON: {e}")
            sys.exit(1)

    def save_json(self):
        with open(self.json_file_path, "w") as f:
            json.dump(self.json_data, f, indent=4)
        self.status_bar.showMessage("Saved", 2000)

    ### Tree View Methods
    def populate_tree(self):
        self.tree.clear()
        for key, value in self.json_data.items():
            item = QTreeWidgetItem(self.tree)
            item.setText(0, key)
            item.setIcon(0, QIcon("icons/dict.png"))  # Ensure icons exist or remove
            self.add_tree_item(item, value, [key])

    def add_tree_item(self, parent, data, path):
        parent.setData(0, Qt.UserRole, path)
        if isinstance(data, dict):
            parent.setText(1, "<dictionary>")
            parent.setIcon(0, QIcon("icons/dict.png"))
            for key, value in data.items():
                child = QTreeWidgetItem(parent)
                child.setText(0, key)
                self.add_tree_item(child, value, path + [key])
        elif isinstance(data, list):
            parent.setText(1, "<list>")
            parent.setIcon(0, QIcon("icons/list.png"))
            for i, value in enumerate(data):
                child = QTreeWidgetItem(parent)
                child.setText(0, str(i))
                self.add_tree_item(child, value, path + [i])
        else:
            parent.setText(1, "null" if data is None else str(data))
            parent.setFlags(parent.flags() | Qt.ItemIsEditable)
            parent.setIcon(0, QIcon("icons/value.png"))

    def on_item_changed(self, item, column):
        if column == 1 and (item.flags() & Qt.ItemIsEditable):
            path = item.data(0, Qt.UserRole)
            new_value = item.text(1)
            try:
                self.set_value(self.json_data, path, json.loads(new_value if new_value != "null" else "null"))
                self.update_raw_editor()
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Invalid Input", "Enter a valid JSON value.")

    ### Context Menu and Multi-Select Features
    def show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.addAction("Copy Path", lambda: self.copy_path(item))
        if item.flags() & Qt.ItemIsEditable:
            menu.addAction("Copy Value", lambda: self.copy_value(item))
        if isinstance(self.get_value(self.json_data, item.data(0, Qt.UserRole)), dict):
            menu.addAction("Add Key", lambda: self.add_key(item))
        selected_items = self.tree.selectedItems()
        if selected_items:
            menu.addAction("Delete Selected", self.delete_selected)
            if all(item.flags() & Qt.ItemIsEditable for item in selected_items):
                menu.addAction("Edit Selected", self.edit_selected)
        menu.exec_(self.tree.mapToGlobal(pos))

    def copy_path(self, item):
        path = item.data(0, Qt.UserRole)
        QApplication.clipboard().setText(json.dumps(path))
        self.status_bar.showMessage("Path copied to clipboard", 2000)

    def copy_value(self, item):
        value = self.get_value(self.json_data, item.data(0, Qt.UserRole))
        QApplication.clipboard().setText(json.dumps(value))
        self.status_bar.showMessage("Value copied to clipboard", 2000)

    def add_key(self, item):
        key, ok = QInputDialog.getText(self, "Add Key", "Enter key name:")
        if ok and key:
            path = item.data(0, Qt.UserRole)
            data = self.get_value(self.json_data, path)
            data[key] = None
            child = QTreeWidgetItem(item)
            child.setText(0, key)
            child.setText(1, "null")
            child.setFlags(child.flags() | Qt.ItemIsEditable)
            child.setIcon(0, QIcon("icons/value.png"))
            self.update_raw_editor()

    def delete_selected(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
        parent_groups = defaultdict(list)
        for item in selected_items:
            path = item.data(0, Qt.UserRole)
            if len(path) > 1:
                parent_path = path[:-1]
                key_or_index = path[-1]
                parent_groups[tuple(parent_path)].append(key_or_index)
        for parent_path_tuple, keys_or_indices in parent_groups.items():
            parent_path = list(parent_path_tuple)
            parent_data = self.get_value(self.json_data, parent_path)
            if isinstance(parent_data, dict):
                for key in keys_or_indices:
                    if key in parent_data:
                        del parent_data[key]
            elif isinstance(parent_data, list):
                indices = [i for i in keys_or_indices if isinstance(i, int)]
                indices.sort(reverse=True)
                for index in indices:
                    if 0 <= index < len(parent_data):
                        del parent_data[index]
        self.populate_tree()
        self.update_raw_editor()

    def edit_selected(self):
        selected_items = [item for item in self.tree.selectedItems() if item.flags() & Qt.ItemIsEditable]
        if not selected_items:
            return
        new_value_str, ok = QInputDialog.getText(self, "Edit Selected", "Enter new value (JSON format):")
        if not ok:
            return
        try:
            new_value = json.loads(new_value_str if new_value_str != "null" else "null")
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Invalid Input", "Enter a valid JSON value.")
            return
        for item in selected_items:
            path = item.data(0, Qt.UserRole)
            self.set_value(self.json_data, path, new_value)
            item.setText(1, str(new_value))
        self.update_raw_editor()

    ### Raw Editor Methods
    def refresh_tree_from_raw(self):
        try:
            self.json_data = json.loads(self.raw_editor.toPlainText())
            self.populate_tree()
            self.status_bar.showMessage("Tree refreshed", 2000)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"Invalid JSON: {e}")

    def update_raw_editor(self):
        self.raw_editor.setPlainText(json.dumps(self.json_data, indent=4))

    def find_in_raw_editor(self):
        self.tab_widget.setCurrentWidget(self.raw_tab)
        search_term, ok = QInputDialog.getText(self, "Find", "Enter text to find:")
        if ok and search_term:
            self.raw_editor.find(search_term)

    ### Search Functionality
    def on_search_text_changed(self, text):
        self.search_timer.start(500)  # Delay search by 500ms to wait for complete word

    def perform_search(self):
        text = self.search_bar.text().lower().strip()
        self.tree.clearSelection()
        if not text or text not in ["money", "xp", "profilelevel", "level", "mymoney", "xpgain", "lastscore", "evergreenlevel"]:
            return
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            self.search_item(item, text)

    def search_item(self, item, text):
        item_text_0 = item.text(0).lower()
        item_text_1 = item.text(1).lower()
        if (text == item_text_0 or text == item_text_1):
            item.setSelected(True)
            parent = item.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()
        for i in range(item.childCount()):
            self.search_item(item.child(i), text)

    ### UI Setup
    def update_path_bar(self):
        selected = self.tree.selectedItems()
        if selected:
            path = selected[0].data(0, Qt.UserRole)
            self.path_bar.setText(" > ".join(map(str, path)))
        else:
            self.path_bar.clear()

    def setup_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Save", self.save_json, "Ctrl+S")
        file_menu.addAction("Exit", self.close, "Ctrl+Q")
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Add Key", self.add_key_action)
        edit_menu.addAction("Find in Raw Editor", self.find_in_raw_editor, "Ctrl+F")
        view_menu = menubar.addMenu("View")
        view_menu.addAction("Expand All", self.tree.expandAll)
        view_menu.addAction("Collapse All", self.tree.collapseAll)

    def add_key_action(self):
        selected = self.tree.selectedItems()
        if selected:
            self.add_key(selected[0])

    ### JSON Data Manipulation
    def get_value(self, data, path):
        current = data
        for key in path:
            current = current[key]
        return current

    def set_value(self, data, path, value):
        current = data
        for key in path[:-1]:
            current = current[key]
        current[path[-1]] = value

    ### Cheats Tab Methods
    def set_all_location_levels(self):
        try:
            locations = self.json_data["Extensions"]["progression"]["Locations"]
            if not locations:
                QMessageBox.critical(self, "Error", "Could not find Locations in JSON structure")
                return
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing key in JSON structure: {e}")
            return
        new_level, ok = QInputDialog.getInt(
            self, "Set Levels in Locations", "Enter the new level value for all locations:",
            value=1, minValue=1, maxValue=100
        )
        if ok:
            self._set_all_levels(locations, new_level)
            self.populate_tree()
            self.update_raw_editor()

    def _set_all_levels(self, data, new_level):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "Level":
                    data[key] = new_level
                else:
                    self._set_all_levels(value, new_level)
        elif isinstance(data, list):
            for item in data:
                self._set_all_levels(item, new_level)

    def set_all_challenge_progresion(self):
        try:
            challenge_progression = self.json_data["Extensions"]["ChallengeProgression"]
            if not challenge_progression:
                QMessageBox.critical(self, "Error", "Could not find ChallengeProgression in JSON structure")
                return
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing key in JSON structure: {e}")
            return
        new_ticked_str, ok_ticked = QInputDialog.getItem(
            self, "Set Ticked in ChallengeProgression", "Enter the new ticked value for all ChallengeProgression:",
            ["True", "False"], 0, False
        )
        if not ok_ticked:
            return
        new_completed_str, ok_completed = QInputDialog.getItem(
            self, "Set Completed in ChallengeProgression", "Enter the new completed value for all ChallengeProgression:",
            ["True", "False"], 0, False
        )
        if not ok_completed:
            return
        new_ticked = new_ticked_str == "True"
        new_completed = new_completed_str == "True"
        self._set_all_challenge_progression(challenge_progression, new_ticked, new_completed)
        self.populate_tree()
        self.update_raw_editor()

    def _set_all_challenge_progression(self, data, new_ticked, new_completed):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "Ticked":
                    data[key] = new_ticked
                elif key == "Completed":
                    data[key] = new_completed
                else:
                    self._set_all_challenge_progression(value, new_ticked, new_completed)
        elif isinstance(data, list):
            for item in data:
                self._set_all_challenge_progression(item, new_ticked, new_completed)

    def copy_locations_to_sublocations(self):
        try:
            locations = self.json_data["Extensions"]["progression"]["Locations"]
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing Locations in JSON structure: {e}")
            return
        try:
            sublocations = self.json_data["Extensions"]["progression"]["PlayerProfileXP"]["Sublocations"]
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing PlayerProfileXP/Sublocations in JSON structure: {e}")
            return
        for key in locations:
            new_key = key.replace("PARENT_", "")
            sublocations[new_key] = {"Xp": 0, "ActionXp": 0}
        self.populate_tree()
        self.update_raw_editor()
        QMessageBox.information(self, "Success", "Locations successfully copied to Sublocations.")

    def set_all_sublocations_xp(self):
        try:
            sublocations = self.json_data["Extensions"]["progression"]["PlayerProfileXP"]["Sublocations"]
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing Sublocations in JSON structure: {e}")
            return
        new_xp, ok_xp = QInputDialog.getInt(
            self, "Set XP for Sublocations", "Enter the new XP value for all Sublocations:",
            value=0, minValue=0
        )
        if not ok_xp:
            return
        new_action_xp, ok_action_xp = QInputDialog.getInt(
            self, "Set ActionXp for Sublocations", "Enter the new ActionXp value for all Sublocations:",
            value=0, minValue=0
        )
        if not ok_action_xp:
            return
        for key in sublocations:
            if isinstance(sublocations[key], dict):
                sublocations[key]["Xp"] = new_xp
                sublocations[key]["ActionXp"] = new_action_xp
        self.populate_tree()
        self.update_raw_editor()
        QMessageBox.information(self, "Success", "Sublocations XP and ActionXp values updated successfully.")

    def copy_peacock_escalations_to_played_contracts(self):
        try:
            peacock_escalations = self.json_data["Extensions"]["PeacockEscalations"]
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing PeacockEscalations in JSON structure: {e}")
            return
        try:
            played_contracts = self.json_data["Extensions"]["PeacockPlayedContracts"]
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing PeacockPlayedContracts in JSON structure: {e}")
            return
        for key in peacock_escalations:
            played_contracts[key] = {
                "LastPlayedAt": 1743948367768,
                "IsEscalation": True,
                "Completed": True
            }
        self.populate_tree()
        self.update_raw_editor()
        QMessageBox.information(self, "Success", "Peacock Escalations copied to Peacock Played Contracts successfully.")

    def copy_peacock_escalations_to_completed_escalations(self):
        try:
            source = self.json_data["Extensions"]["PeacockEscalations"]
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing PeacockEscalations in JSON structure: {e}")
            return
        try:
            target = self.json_data["Extensions"]["PeacockCompletedEscalations"]
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing PeacockCompletedEscalations in JSON structure: {e}")
            return
        if isinstance(target, list):
            target.clear()
            for key in source:
                target.append(key)
        elif isinstance(target, dict):
            target.clear()
            for index, key in enumerate(source):
                target[str(index)] = key
        else:
            QMessageBox.critical(self, "Error", "PeacockCompletedEscalations has an unexpected type.")
            return
        self.populate_tree()
        self.update_raw_editor()
        QMessageBox.information(self, "Success", "Peacock Escalations copied to Completed Escalations successfully.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = JsonEditor()
    editor.show()
    sys.exit(app.exec())
