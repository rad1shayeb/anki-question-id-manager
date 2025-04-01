import re
import json
import os
import logging
from functools import lru_cache
from aqt import gui_hooks, mw
from aqt.qt import QAction, QDialog, QVBoxLayout, QCheckBox, QLineEdit, QLabel, QPushButton, QTextEdit
from aqt.utils import showInfo
from typing import List

# Logging setup
LOG_FILE = os.path.join(os.path.dirname(__file__), 'qid_addon.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "enabled": True,
    "debug_mode": True,
    "tag_patterns": [
        r"::\d+$",
        r"#QID\d+",
        r"\[\w+:\d+\]"
    ]
}

class QIDConfigManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.config = self._load_config()

    def _load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            return DEFAULT_CONFIG
        except Exception as e:
            logger.error(f"Config load failed: {str(e)}")
            return DEFAULT_CONFIG

    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Config save failed: {str(e)}")

config_manager = QIDConfigManager()

@lru_cache(maxsize=128)
def get_compiled_pattern(pattern: str):
    try:
        return re.compile(pattern)
    except re.error as e:
        logger.error(f"Invalid regex pattern: {pattern} - {str(e)}")
        return None

def extract_question_ids(tags: List[str]) -> List[str]:
    ids = []
    for pattern in config_manager.config["tag_patterns"]:
        compiled_pattern = get_compiled_pattern(pattern)
        if not compiled_pattern:
            continue
        
        for tag in tags:
            match = compiled_pattern.search(tag)
            if match:
                id_part = re.search(r'\d+', tag[match.start():])
                if id_part:
                    ids.append(id_part.group())
    return list(set(ids))

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Question ID Manager")
        self.current_note = None
        self.setup_ui()
        self.load_current_note_ids()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Current IDs display
        self.id_display = QTextEdit()
        self.id_display.setReadOnly(True)
        layout.addWidget(QLabel("<b>Current Note's Question IDs:</b>"))
        layout.addWidget(self.id_display)

        # Pattern management
        layout.addWidget(QLabel("<b>Tag Patterns (regex):</b>"))
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setText("|".join(config_manager.config["tag_patterns"]))
        layout.addWidget(self.pattern_edit)

        # Config controls
        self.enable_checkbox = QCheckBox("Enable Add-on")
        self.enable_checkbox.setChecked(config_manager.config.get("enabled", True))
        layout.addWidget(self.enable_checkbox)

        self.debug_checkbox = QCheckBox("Debug Mode")
        self.debug_checkbox.setChecked(config_manager.config.get("debug_mode", False))
        layout.addWidget(self.debug_checkbox)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def load_current_note_ids(self):
        try:
            if mw.reviewer and mw.reviewer.card:
                self.current_note = mw.reviewer.card.note()
                ids = extract_question_ids(self.current_note.tags)
                if ids:
                    self.id_display.setText("\n".join(ids))
                else:
                    self.id_display.setText("No IDs found in current note's tags")
            else:
                self.id_display.setText("No active card selected")
        except Exception as e:
            logger.error(f"Error loading note IDs: {str(e)}")
            self.id_display.setText("Error loading IDs")

    def save_settings(self):
        config_manager.config["enabled"] = self.enable_checkbox.isChecked()
        config_manager.config["debug_mode"] = self.debug_checkbox.isChecked()
        config_manager.config["tag_patterns"] = self.pattern_edit.text().split("|")
        config_manager.save_config()
        self.accept()

def show_settings():
    dialog = SettingsDialog(mw)
    dialog.exec()

def initialize_addon():
    action = QAction("Question ID Manager", mw)
    action.triggered.connect(show_settings)
    mw.form.menuTools.addAction(action)

initialize_addon()