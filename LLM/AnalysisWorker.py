from PyQt6.QtCore import QThread, pyqtSignal

from .generate_report import generate_json
from .ai_reporter import get_answer


class AnalysisWorker(QThread):
    completed = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, csv_path: str, json_path: str, parent=None):
        super().__init__(parent)
        self._csv_path = csv_path
        self._json_path = json_path

    def run(self):
        try:
            generate_json(self._csv_path, self._json_path)
            answer = get_answer(self._json_path)
        except Exception as e:
            self.failed.emit(str(e))
            return
        self.completed.emit(answer)