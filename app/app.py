import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QSplitter, QFileDialog, QMessageBox,
    QDialogButtonBox, QLabel, QDialog
)

from Plots import draw_plots, draw_boxplots, draw_threshold_plots
from ParametersDialog import ParametersDialog

from utils.preprocessing import load_data, preprocessing

from methods.quantiles.detector import detect_anomalies as detect_quantiles
from methods.range.detector import detect_anomalies as detect_range
from methods.isolation_forest.detector import detect_anomalies as detect_isolation_forest

from LLM.ai_reporter import get_answer
from LLM.generate_report import generate_json





class MainWindow(QMainWindow):
    RESULTS_PATH = "results/data_results.csv"
    OUTPUT_JSON_PATH = "results/anomaly.json"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TurbineLog — Агент диагностики гидроагрегатов")
        self.resize(1200, 700)

        self.data = None
        self.results = None
        self.last_values = {}
        self.last_method = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Верхняя панель
        top = QHBoxLayout()

        self.btn_quant = QPushButton("Метод квантилей")
        self.btn_range = QPushButton("Метод диапазонов")
        self.btn_if = QPushButton("Метод Isolation Forest")
        self.freeSpace = QLabel("\t")
        self.btn_save = QPushButton("Выгрузить в файл")

        self.btn_quant.clicked.connect(lambda: self.load_data_for_method("Метод квантилей"))
        self.btn_range.clicked.connect(lambda: self.open_method_dialog("Метод диапазонов"))
        self.btn_if.clicked.connect(lambda: self.load_data_for_method("Метод Isolation Forest"))
        self.btn_save.clicked.connect(self.save_file)

        top.addWidget(self.btn_quant)
        top.addWidget(self.btn_range)
        top.addWidget(self.btn_if)
        top.addWidget(self.freeSpace)
        top.addWidget(self.btn_save)
        top.addStretch()

        root.addLayout(top)

        # Нижняя часть
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText(
            "Загрузите данные и выберите метод диагностики.\n"
            "Результаты отобразятся здесь."
        )
        splitter.addWidget(self.text_edit)

        self.figure = Figure(figsize=(6, 5))
        self.canvas = FigureCanvas(self.figure)
        splitter.addWidget(self.canvas)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([400, 800])

        root.addWidget(splitter, stretch=1)

    def load_data_for_method(self, method_name: str):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть CSV с данными", "data",
            "CSV-файлы (*.csv);;Все файлы (*)"
        )
        if not path:
            return
        try:
            self.data = preprocessing(load_data(path))
            self.results = None
            self.text_edit.append(f"\nЗагружен файл: {path}\n")
            draw_plots(self, self.data)

            self.run_method(method_name, self.data)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось загрузить данные:\n{e}")

    # диалог и запуск метода
    def open_method_dialog(self, method_name: str):
        dlg = ParametersDialog(method_name, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        values = dlg.values()
        self.run_method(method_name, values)

    def run_method(self, method_name: str, values: dict):
        data = self.data
        if data is None or len(data) == 0:
            data = self._data_from_values(values)

        try:
            if method_name == "Метод квантилей":
                results = detect_quantiles(data)
                draw_boxplots(self, results)
            elif method_name == "Метод диапазонов":
                ranges = [list(pair) for pair in values.values()]
                results = detect_range(data, ranges)
                draw_threshold_plots(self, results, ranges=values)
            elif method_name == "Метод Isolation Forest":
                results = detect_isolation_forest(data)
            else:
                return
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка",
                f"{method_name} завершился с ошибкой:\n{e}"
            )
            return

        self.results = results

        saved_path = None
        try:
            os.makedirs(os.path.dirname(self.RESULTS_PATH), exist_ok=True)
            results.to_csv(self.RESULTS_PATH, index="Timestamp")
            saved_path = self.RESULTS_PATH
            generate_json(self.RESULTS_PATH, self.OUTPUT_JSON_PATH)
        except Exception as e:
            QMessageBox.warning(
                self, "Предупреждение",
                f"Не удалось сохранить результаты в файл:\n{e}"
            )

        self._log_results(method_name, results, values, saved_path)

        try:
            self.text_edit.append("Идёт генерация отчёта...\n")
            self.text_edit.append(get_answer(self.OUTPUT_JSON_PATH))
        except Exception as e:
            self.text_edit.append("Ошибка генерации отчёта.\n\n")
            QMessageBox.warning(
                self, "Ошибка",
                "Не удалось отправить запрос или получить ответ от модели."
            )

    def _log_results(self, method_name, results, values, saved_path):
        self.text_edit.append("Найдено аномалий:")
        for col in results.columns:
            if col.endswith("_anomaly"):
                n = int(results[col].sum())
                self.text_edit.append(f"  • {col[:-len('_anomaly')]}: {n}")
        self.text_edit.append("\n")

    def _data_from_values(self, values: dict, n_points: int = 20) -> pd.DataFrame:
        cols = {}
        for col, (mn, mx) in values.items():
            if mx < mn:
                mn, mx = mx, mn
            if mx == mn:
                cols[col] = np.full(n_points, mn)
            else:
                cols[col] = np.linspace(mn, mx, n_points)
        df = pd.DataFrame(cols)
        df.index = pd.RangeIndex(n_points, name="Timestamp")
        return df

    # сохранение журнала
    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить журнал", "results_log.txt",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            QMessageBox.information(self, "Готово", "Журнал сохранён.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось сохранить файл:\n{e}")


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()