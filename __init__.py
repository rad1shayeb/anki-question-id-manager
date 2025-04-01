import re
import json
import os
import logging
from typing import List

from aqt import mw
from aqt.utils import showInfo, tooltip
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QAction, QMenu, QListWidget, Qt, QLabel, QLineEdit
)

# Logging setup
LOG_FILE = os.path.join(os.path.dirname(__file__), 'qid_addon.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration now includes selected_tags as a list.
DEFAULT_CONFIG = {
    "selected_tags": []
}

class QIDConfigManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.config = self._load_config()

    def _load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    # Ensure our keys are present
                    for key, val in DEFAULT_CONFIG.items():
                        if key not in data:
                            data[key] = val
                    return data
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Config load failed: {str(e)}")
            return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Config save failed: {str(e)}")

config_manager = QIDConfigManager()

### CONFIGURATION DIALOG ###
class QIDConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UWorld QID Configuration")
        self.resize(600, 500)
        self.setup_ui()
        self.build_tag_tree()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Instruction Label
        instr = QLabel("Select base tags (the prefix before the ID) to retrieve QIDs.\n"
                       "Use checkboxes below. You can also add a manual tag if needed.")
        main_layout.addWidget(instr)

        # Tree widget for hierarchical tags with checkboxes
        self.tag_tree = QTreeWidget()
        self.tag_tree.setHeaderHidden(True)
        main_layout.addWidget(self.tag_tree)

        # Buttons for tree operations
        tree_btn_layout = QHBoxLayout()
        self.expand_btn = QPushButton("Expand All")
        self.expand_btn.clicked.connect(self.tag_tree.expandAll)
        tree_btn_layout.addWidget(self.expand_btn)
        self.collapse_btn = QPushButton("Collapse All")
        self.collapse_btn.clicked.connect(self.tag_tree.collapseAll)
        tree_btn_layout.addWidget(self.collapse_btn)
        self.check_all_btn = QPushButton("Check All")
        self.check_all_btn.clicked.connect(lambda: self.set_all_checkstate(Qt.Checked))
        tree_btn_layout.addWidget(self.check_all_btn)
        self.uncheck_all_btn = QPushButton("Uncheck All")
        self.uncheck_all_btn.clicked.connect(lambda: self.set_all_checkstate(Qt.Unchecked))
        tree_btn_layout.addWidget(self.uncheck_all_btn)
        main_layout.addLayout(tree_btn_layout)

        # Manual tag add
        manual_layout = QHBoxLayout()
        self.manual_edit = QLineEdit()
        self.manual_edit.setPlaceholderText("Enter manual tag (e.g., #CustomTag)")
        manual_layout.addWidget(self.manual_edit)
        self.add_manual_btn = QPushButton("Add Manual Tag")
        self.add_manual_btn.clicked.connect(self.add_manual_tag)
        manual_layout.addWidget(self.add_manual_btn)
        main_layout.addLayout(manual_layout)

        # Status label
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

        # Action buttons: OK, Clear Selection, Cancel
        action_btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        action_btn_layout.addWidget(self.ok_btn)
        self.clear_btn = QPushButton("Clear Selection")
        self.clear_btn.clicked.connect(self.clear_selection)
        action_btn_layout.addWidget(self.clear_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        action_btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(action_btn_layout)

        self.setLayout(main_layout)

    def build_tag_tree(self):
        self.tag_tree.clear()
        tag_structure = {}

        # Build hierarchical structure from all tags in the collection.
        # Note: tags are assumed to be stored in mw.col.tags.all()
        for tag in mw.col.tags.all():
            parts = tag.split("::")
            current_level = tag_structure
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

        # Recursive function to add items to tree
        def add_items(parent, structure, prefix=""):
            for name, children in structure.items():
                full_tag = (prefix + "::" + name) if prefix else name
                item = QTreeWidgetItem(parent)
                item.setText(0, name)
                item.setData(0, Qt.UserRole, full_tag)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                # Check item if full tag is in saved configuration.
                if full_tag in config_manager.config.get("selected_tags", []):
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)
                if children:
                    add_items(item, children, full_tag)
        root = self.tag_tree.invisibleRootItem()
        add_items(root, tag_structure)
        self.tag_tree.expandAll()

    def set_all_checkstate(self, state):
        def recursive_set(item):
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, state)
                recursive_set(child)
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item.setCheckState(0, state)
            recursive_set(item)

    def add_manual_tag(self):
        text = self.manual_edit.text().strip()
        if not text:
            self.status_label.setText("Please enter a tag.")
            return
        # Check if already exists in the tree (by comparing full tag stored in UserRole)
        found = False
        def recursive_search(item):
            nonlocal found
            if item.data(0, Qt.UserRole) == text:
                found = True
            for i in range(item.childCount()):
                recursive_search(item.child(i))
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            recursive_search(root.child(i))
        if not found:
            # Add as top-level item if not found.
            item = QTreeWidgetItem(self.tag_tree)
            item.setText(0, text)
            item.setData(0, Qt.UserRole, text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
            self.status_label.setText(f"Manual tag '{text}' added and checked.")
        else:
            self.status_label.setText("Tag already exists in the tree.")
        self.manual_edit.clear()

    def clear_selection(self):
        self.set_all_checkstate(Qt.Unchecked)
        self.status_label.setText("Selection cleared.")

    def get_checked_tags(self) -> List[str]:
        checked_tags = []
        def recursive_collect(item):
            # If the item is checked, add its full tag
            if item.checkState(0) == Qt.Checked:
                tag = item.data(0, Qt.UserRole)
                if tag:
                    checked_tags.append(tag)
            for i in range(item.childCount()):
                recursive_collect(item.child(i))
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            recursive_collect(root.child(i))
        return checked_tags

    def accept(self):
        # Save checked tags to configuration
        selected = self.get_checked_tags()
        if not selected:
            self.status_label.setText("No tags selected. Please select at least one tag.")
            return
        config_manager.config["selected_tags"] = selected
        config_manager.save_config()
        tooltip("Configuration saved!")
        super().accept()

### DISPLAY DIALOG ###
class QIDDisplayDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UWorld QID Manager")
        self.resize(400, 300)
        self.setup_ui()
        self.load_ids()

    def setup_ui(self):
        layout = QVBoxLayout()
        # Title based on current configuration
        selected = config_manager.config.get("selected_tags", [])
        if selected:
            title = f"IDs for {', '.join(selected)}"
        else:
            title = "IDs"
        layout.addWidget(QLabel(title))

        # ID list with right-click copy support
        self.id_list = QListWidget()
        self.id_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.id_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.id_list)

        self.setLayout(layout)

    def show_context_menu(self, pos):
        menu = QMenu()
        copy_action = menu.addAction("Copy ID")
        action = menu.exec(self.id_list.mapToGlobal(pos))
        if action == copy_action and self.id_list.currentItem():
            mw.app.clipboard().setText(self.id_list.currentItem().text())

    def load_ids(self):
        self.id_list.clear()
        selected_tags = config_manager.config.get("selected_tags", [])
        if not selected_tags:
            showInfo("No base tags configured. Please set up your tags via Tools > UWorld QID Config.")
            return

        ids = set()
        # Retrieve tags from the current card if available
        if mw.reviewer and mw.reviewer.card:
            note = mw.reviewer.card.note()
            tags = note.tags
        else:
            tags = []
            showInfo("No active card found. Only QIDs from the current card are displayed.")
        
        # For each selected base tag, match tags with that prefix ending in ::<number>
        for base_tag in selected_tags:
            pattern = re.compile(f"^{re.escape(base_tag)}::(\\d+)$", re.IGNORECASE)
            for tag in tags:
                match = pattern.match(tag)
                if match:
                    ids.add(match.group(1))
        if ids:
            self.id_list.addItems(sorted(ids, key=int))
        else:
            self.id_list.addItem("No matching QIDs found.")

### MENU INTEGRATION ###
def show_qid_config():
    dlg = QIDConfigDialog(mw)
    dlg.exec()
    # After config dialog closes, refresh the tree in case new tags were added.
    # (No further action required here.)

def show_qids():
    if not config_manager.config.get("selected_tags"):
        showInfo("No base tags configured. Please set up your tags via Tools > UWorld QID Config.")
        return
    dlg = QIDDisplayDialog(mw)
    dlg.exec()

def initialize_addon():
    # Menu action for displaying QIDs
    action_manager = QAction("UWorld QID Manager", mw)
    action_manager.triggered.connect(show_qids)
    mw.form.menuTools.addAction(action_manager)

    # Menu action for configuring base tags
    action_config = QAction("UWorld QID Config", mw)
    action_config.triggered.connect(show_qid_config)
    mw.form.menuTools.addAction(action_config)

initialize_addon()
