from PySide6.QtWidgets import (QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem,
                               QMenu, QInputDialog, QMessageBox, QMenuBar)
from PySide6.QtCore import Qt
import json
import sys

class JsonEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JSON Editor")
        self.resize(800, 600)

        # Set up the tree widget
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Key", "Value"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)  # Enable multi-selection
        self.setCentralWidget(self.tree)

        # Initialize JSON data
        self.json_file_path = r"C:\Users\Death\Desktop\Peacock-v7.7.0\userdata\users\04a21aa3-d7f7-4a42-92b5-6630b4e634a0.json"
        self.json_data = None
        self.load_json()
        self.populate_tree()

        # Connect signals
        self.tree.itemChanged.connect(self.on_item_changed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        # Set up menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        save_action = file_menu.addAction("Save")
        save_action.triggered.connect(self.save_json)
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        edit_menu = menubar.addMenu("Edit")

        set_challenge_progression_action = edit_menu.addAction("Set All Ticked & Completed in ChallengeProgression")
        set_challenge_progression_action.triggered.connect(self.set_all_challenge_progresion)

        set_levels_action = edit_menu.addAction("Set All Levels in Locations")
        set_levels_action.triggered.connect(self.set_all_location_levels)

        copy_locations_action = edit_menu.addAction("Copy Locations to Sublocations")
        copy_locations_action.triggered.connect(self.copy_locations_to_sublocations)

        set_sublocations_xp_action = edit_menu.addAction("Set All XP and ActionXp in Sublocations")
        set_sublocations_xp_action.triggered.connect(self.set_all_sublocations_xp)

        copy_peacock_action = edit_menu.addAction("Copy Peacock Escalations to Played Contracts")
        copy_peacock_action.triggered.connect(self.copy_peacock_escalations_to_played_contracts)

        copy_completed_action = edit_menu.addAction("Copy Peacock Escalations to Completed Escalations")
        copy_completed_action.triggered.connect(self.copy_peacock_escalations_to_completed_escalations)

    def load_json(self):
        try:
            with open(self.json_file_path, "r") as f:
                self.json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load JSON file: {e}")
            sys.exit(1)

    def populate_tree(self):
        self.tree.clear()
        for key, value in self.json_data.items():
            item = QTreeWidgetItem(self.tree)
            item.setText(0, key)
            self.add_tree_item(item, value, [key])

    def add_tree_item(self, parent, data, path):
        if isinstance(data, dict):
            parent.setText(1, "<dictionary>")
            parent.setData(1, Qt.UserRole, dict)
            for key, value in data.items():
                child = QTreeWidgetItem(parent)
                child.setText(0, key)
                new_path = path + [key]
                self.add_tree_item(child, value, new_path)
        elif isinstance(data, list):
            parent.setText(1, "<list>")
            parent.setData(1, Qt.UserRole, list)
            for i, value in enumerate(data):
                child = QTreeWidgetItem(parent)
                child.setText(0, str(i))
                new_path = path + [i]
                self.add_tree_item(child, value, new_path)
        else:
            parent.setText(1, "null" if data is None else str(data))
            parent.setData(0, Qt.UserRole, path)
            parent.setData(1, Qt.UserRole, type(data))
            parent.setFlags(parent.flags() | Qt.ItemIsEditable)

    def on_item_changed(self, item, column):
        if column == 1 and item.data(0, Qt.UserRole) is not None:
            path = item.data(0, Qt.UserRole)
            new_value_str = item.text(1).strip()
            value_type = item.data(1, Qt.UserRole)
            try:
                new_value = self.convert_string_to_type(new_value_str, value_type)
                self.set_value(self.json_data, path, new_value)
            except ValueError:
                original_value = self.get_value(self.json_data, path)
                item.setText(1, "null" if original_value is None else str(original_value))
                QMessageBox.warning(self, "Invalid Input", f"Cannot convert '{new_value_str}' to {value_type.__name__}")

    def show_context_menu(self, pos):
        selected_items = self.tree.selectedItems()
        editable_selected = [item for item in selected_items if item.flags() & Qt.ItemIsEditable]
        menu = QMenu(self)
        if editable_selected:
            menu.addAction("Edit Selected", lambda: self.edit_selected_items(editable_selected))
        current_item = self.tree.itemAt(pos)
        if current_item:
            node_type = current_item.data(1, Qt.UserRole)
            if node_type == dict:
                menu.addAction("Add Key", lambda: self.add_key(current_item))
            elif node_type == list:
                menu.addAction("Add Item", lambda: self.add_item(current_item))
        if menu.actions():
            menu.exec_(self.tree.mapToGlobal(pos))

    def edit_selected_items(self, items):
        if not items:
            return
        current_value = items[0].text(1)
        new_value_str, ok = QInputDialog.getText(self, "Edit Selected", "Enter new value:", text=current_value)
        if not ok or not new_value_str:
            return
        errors = []
        success = 0
        self.tree.itemChanged.disconnect(self.on_item_changed)
        try:
            for item in items:
                path = item.data(0, Qt.UserRole)
                if not path:
                    continue
                value_type = item.data(1, Qt.UserRole)
                try:
                    new_value = self.convert_string_to_type(new_value_str.strip(), value_type)
                    self.set_value(self.json_data, path, new_value)
                    display_value = "null" if new_value is None else str(new_value)
                    item.setText(1, display_value)
                    success += 1
                except Exception as e:
                    errors.append(f"Path {path}: {str(e)}")
        finally:
            self.tree.itemChanged.connect(self.on_item_changed)
        msg = QMessageBox(self)
        if errors:
            msg.setIcon(QMessageBox.Warning)
            msg.setText(f"Updated {success} items, {len(errors)} errors.")
            msg.setDetailedText("\n".join(errors))
        else:
            msg.setIcon(QMessageBox.Information)
            msg.setText(f"Successfully updated {success} items.")
        msg.exec_()

    def convert_string_to_type(self, value_str, value_type):
        if value_type == int:
            return int(value_str)
        elif value_type == float:
            return float(value_str)
        elif value_type == bool:
            return value_str.lower() in ['true', '1', 'yes']
        elif value_type == str:
            return value_str
        elif value_type is type(None):
            return None if value_str.lower() == 'null' else value_str
        else:
            return value_str

    def add_key(self, item):
        """Add a new key to a dictionary."""
        path = item.data(0, Qt.UserRole) or []
        key, ok = QInputDialog.getText(self, "Add Key", "Enter key name:")
        if not (ok and key):
            return
        dict_data = self.get_value(self.json_data, path)
        if key in dict_data:
            QMessageBox.warning(self, "Error", "Key already exists")
            return
        type_dialog = QInputDialog(self)
        type_dialog.setComboBoxItems(["string", "integer", "boolean", "null", "object", "array"])
        type_dialog.setLabelText("Select value type:")
        if type_dialog.exec_() != QInputDialog.Accepted:
            return
        value_type = type_dialog.textValue()
        value = {"string": "", "integer": 0, "boolean": False, "null": None, "object": {}, "array": []}[value_type]
        dict_data[key] = value
        new_item = QTreeWidgetItem(item)
        new_item.setText(0, key)
        new_path = path + [key]
        self.add_tree_item(new_item, value, new_path)

    def add_item(self, item):
        """Add a new item to a list."""
        path = item.data(0, Qt.UserRole) or []
        list_data = self.get_value(self.json_data, path)
        type_dialog = QInputDialog(self)
        type_dialog.setComboBoxItems(["string", "integer", "boolean", "null", "object", "array"])
        type_dialog.setLabelText("Select value type:")
        if type_dialog.exec_() != QInputDialog.Accepted:
            return
        value_type = type_dialog.textValue()
        value = {"string": "", "integer": 0, "boolean": False, "null": None, "object": {}, "array": []}[value_type]
        list_data.append(value)
        index = len(list_data) - 1
        new_item = QTreeWidgetItem(item)
        new_item.setText(0, str(index))
        new_path = path + [index]
        self.add_tree_item(new_item, value, new_path)

    def get_value(self, data, path):
        """Retrieve a value from the dictionary using a path."""
        for key in path:
            data = data[key]
        return data

    def set_value(self, data, path, value):
        """Set a value in the dictionary using a path."""
        for key in path[:-1]:
            data = data[key]
        data[path[-1]] = value

    def save_json(self):
        """Save the modified JSON data back to the file."""
        try:
            with open(self.json_file_path, "w") as f:
                json.dump(self.json_data, f, indent=4)
            QMessageBox.information(self, "Success", "JSON file saved successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save JSON file: {e}")

    def set_all_location_levels(self):
        """Set all 'Level' keys in nested Locations"""
        try:
            locations = self.json_data["Extensions"]["progression"]["Locations"]
            if not locations:
                QMessageBox.critical(self, "Error", "Could not find Locations in JSON structure")
                return
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing key in JSON structure: {e}")
            return
        new_level, ok = QInputDialog.getInt(
            self,
            "Set Levels in Locations",
            "Enter the new level value for all locations:",
            value=1,
            minValue=1,
            maxValue=100
        )
        if ok:
            self._set_all_levels(locations, new_level)
            self.populate_tree()

    def _set_all_levels(self, data, new_level):
        """Recursively set all 'Level' keys in the data structure to new_level."""
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
        """Set all 'Ticked' and 'Completed' values in ChallengeProgression"""
        try:
            challenge_progression = self.json_data["Extensions"]["ChallengeProgression"]
            if not challenge_progression:
                QMessageBox.critical(self, "Error", "Could not find ChallengeProgression in JSON structure")
                return
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing key in JSON structure: {e}")
            return
        new_ticked_str, ok_ticked = QInputDialog.getItem(
            self,
            "Set Ticked in ChallengeProgression",
            "Enter the new ticked value for all ChallengeProgression:",
            ["True", "False"],
            0,
            False
        )
        if not ok_ticked:
            return
        new_completed_str, ok_completed = QInputDialog.getItem(
            self,
            "Set Completed in ChallengeProgression",
            "Enter the new completed value for all ChallengeProgression:",
            ["True", "False"],
            0,
            False
        )
        if not ok_completed:
            return
        new_ticked = new_ticked_str == "True"
        new_completed = new_completed_str == "True"
        self._set_all_challenge_progression(challenge_progression, new_ticked, new_completed)
        self.populate_tree()

    def _set_all_challenge_progression(self, data, new_ticked, new_completed):
        """Recursively set all 'Ticked' and 'Completed' keys in the data structure."""
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
        """
        Copy all keys from Locations (under Extensions/progression/Locations)
        to Sublocations (under Extensions/progression/PlayerProfileXP/Sublocations)
        with each key's value being a dict with keys "Xp" and "ActionXp".
        The copied keys are renamed by removing the substring 'PARENT_'.
        """
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
        QMessageBox.information(self, "Success", "Locations successfully copied to Sublocations.")

    def set_all_sublocations_xp(self):
        """
        Set the Xp and ActionXp values for all keys in Sublocations (under 
        Extensions/progression/PlayerProfileXP/Sublocations) to user-provided values.
        """
        try:
            sublocations = self.json_data["Extensions"]["progression"]["PlayerProfileXP"]["Sublocations"]
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing Sublocations in JSON structure: {e}")
            return
        new_xp, ok_xp = QInputDialog.getInt(
            self,
            "Set XP for Sublocations",
            "Enter the new XP value for all Sublocations:",
            value=0,
            minValue=0
        )
        if not ok_xp:
            return
        new_action_xp, ok_action_xp = QInputDialog.getInt(
            self,
            "Set ActionXp for Sublocations",
            "Enter the new ActionXp value for all Sublocations:",
            value=0,
            minValue=0
        )
        if not ok_action_xp:
            return
        for key in sublocations:
            if isinstance(sublocations[key], dict):
                sublocations[key]["Xp"] = new_xp
                sublocations[key]["ActionXp"] = new_action_xp
        self.populate_tree()
        QMessageBox.information(self, "Success", "Sublocations XP and ActionXp values updated successfully.")

    def copy_peacock_escalations_to_played_contracts(self):
        """
        Copy all keys from PeacockEscalations (under Extensions/PeacockEscalations)
        to PeacockPlayedContracts (under Extensions/PeacockPlayedContracts). For each key,
        the value in PeacockPlayedContracts will be a dictionary containing:
          - LastPlayedAt: 1743948367768
          - IsEscalation: True
          - Completed: True
        """
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
        QMessageBox.information(self, "Success", "Peacock Escalations copied to Peacock Played Contracts successfully.")

    def copy_peacock_escalations_to_completed_escalations(self):
        """
        Copy every key from PeacockEscalations (under Extensions/PeacockEscalations)
        to PeacockCompletedEscalations (under Extensions/PeacockCompletedEscalations).
        In the target, each new element's key will be a sequential number (starting at 0)
        and its value will be the original key from PeacockEscalations.
        """
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

        # If target is a list, clear it and append the values.
        if isinstance(target, list):
            target.clear()
            for key in source:
                target.append(key)
        # Otherwise, if it's a dictionary, clear it and add numeric keys.
        elif isinstance(target, dict):
            target.clear()
            for index, key in enumerate(source):
                target[index] = key
        else:
            QMessageBox.critical(self, "Error", "PeacockCompletedEscalations has an unexpected type.")
            return

        self.populate_tree()
        QMessageBox.information(self, "Success", "Peacock Escalations copied to Completed Escalations successfully.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = JsonEditor()
    editor.show()
    sys.exit(app.exec())
