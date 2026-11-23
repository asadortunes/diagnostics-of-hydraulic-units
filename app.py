import os
import sys
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QSplitter, QFileDialog, QMessageBox,
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QGridLayout
)

from utils.preprocessing import load_data, preprocessing
from methods.quantiles.detector import detect_anomalies as detect_quantiles
from methods.range.detector import detect_anomalies as detect_range
from methods.isolation_forest.detector import detect_anomalies as detect_isolation_forest
from LLM.ai_reporter import get_answer


class ParametersDialog(QDialog):

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(620)

        layout = QVBoxLayout(self)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Параметр"), 0, 0)
        h_min = QLabel("<b>min</b>")
        h_min.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_max = QLabel("<b>max</b>")
        h_max.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(h_min, 0, 1)
        grid.addWidget(h_max, 0, 2)
        grid.addWidget(QLabel("Ед. изм."), 0, 3)

        self.pressure = self._add_row(grid, 1, "Давление масла:",          "0", "10",   "бар")
        self.temp     = self._add_row(grid, 2, "Температура подшипника:",  "0", "100",  "°C")
        self.vib      = self._add_row(grid, 3, "Вибрация оборудования:",   "0", "10",   "мм/с")
        self.rpm      = self._add_row(grid, 4, "Частота вращения ротора:", "0", "5000", "об/мин")
        self.power    = self._add_row(grid, 5, "Активная мощность:",       "0", "300",  "МВт")
        self.flow     = self._add_row(grid, 6, "Расход воды:",             "0", "2000", "м³/ч")

        layout.addLayout(grid)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _make_line(default: str) -> QLineEdit:
        line = QLineEdit(default)
        regex = QRegularExpression(r"^-?\d{0,6}([.,]\d{0,4})?$")
        line.setValidator(QRegularExpressionValidator(regex, line))
        line.setMaximumWidth(120)
        line.setAlignment(Qt.AlignmentFlag.AlignRight)
        return line

    @staticmethod
    def _add_row(grid: QGridLayout, row: int, name: str,
                 min_default: str, max_default: str, unit: str):
        grid.addWidget(QLabel(name), row, 0)
        e_min = ParametersDialog._make_line(min_default)
        e_max = ParametersDialog._make_line(max_default)
        grid.addWidget(e_min, row, 1)
        grid.addWidget(e_max, row, 2)
        grid.addWidget(QLabel(unit), row, 3)
        return e_min, e_max

    @staticmethod
    def _read(line: QLineEdit) -> float:
        text = line.text().strip().replace(",", ".")
        if text in ("", "-", ".", "-."):
            return 0.0
        try:
            return float(text)
        except ValueError:
            return 0.0

    def values(self) -> dict:
        return {
            "Давление масла, бар":        (self._read(self.pressure[0]), self._read(self.pressure[1])),
            "Температура подшипника, °C": (self._read(self.temp[0]),     self._read(self.temp[1])),
            "Вибрация, мм/с":             (self._read(self.vib[0]),      self._read(self.vib[1])),
            "Частота вращения, об/мин":   (self._read(self.rpm[0]),      self._read(self.rpm[1])),
            "Активная мощность, МВт":     (self._read(self.power[0]),    self._read(self.power[1])),
            "Расход воды, м³/ч":          (self._read(self.flow[0]),     self._read(self.flow[1])),
        }


class MainWindow(QMainWindow):
    RESULTS_PATH = "results/data_results.csv"

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

        self.btn_quant.clicked.connect(lambda: self.open_method_dialog("Метод квантилей"))
        self.btn_range.clicked.connect(lambda: self.open_method_dialog("Метод диапазонов"))
        self.btn_if.clicked.connect(self.run_method("Метод Isolation Forest"))
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

        self.draw_plots(None)

    # def load_data_for_isolation_forest(self):
    #     path, _ = QFileDialog.getOpenFileName(
    #         self, "Открыть CSV с данными", "data",
    #         "CSV-файлы (*.csv);;Все файлы (*)"
    #     )
    #     if not path:
    #         return
    #     try:
    #         self.data = preprocessing(load_data(path))
    #         self.results = None
    #         self.text_edit.append(
    #             f"\nЗагружен файл: {path}\n"
    #             f"  • строк: {len(self.data)}\n"
    #             f"  • столбцов: {len(self.data.columns)}"
    #         )
    #         self.draw_plots(self.data)
    #     except Exception as e:
    #         QMessageBox.critical(self, "Ошибка",
    #                              f"Не удалось загрузить данные:\n{e}")
    #
    # # диалог и запуск метода
    # def open_method_dialog(self, method_name: str):
    #     dlg = ParametersDialog(method_name, self)
    #     if dlg.exec() != QDialog.DialogCode.Accepted:
    #         return
    #     values = dlg.values()
    #     self.last_values = values
    #     self.last_method = method_name
    #     self.run_method(method_name, values)
    #
    # def run_method(self, method_name: str, values: dict):
    #     try:
    #         if method_name == "Метод квантилей":
    #             results = detect_quantiles(self.data)
    #         elif method_name == "Метод диапазонов":
    #             ranges = [list(pair) for pair in values.values()]
    #             results = detect_range(self.data, ranges)
    #         elif method_name == "Метод Isolation Forest":
    #             results = detect_isolation_forest(self.data)
    #         else:
    #             return
    #     except Exception as e:
    #         QMessageBox.critical(
    #             self, "Ошибка",
    #             f"{method_name} завершился с ошибкой:\n{e}"
    #         )
    #         return
    #
    #     self.results = results
    #
    #     saved_path = None
    #     try:
    #         os.makedirs(os.path.dirname(self.RESULTS_PATH), exist_ok=True)
    #         results.to_csv(self.RESULTS_PATH, index=False)
    #         saved_path = self.RESULTS_PATH
    #     except Exception as e:
    #         QMessageBox.warning(
    #             self, "Предупреждение",
    #             f"Не удалось сохранить результаты в файл:\n{e}"
    #         )
    #
    #     self._log_results(method_name, results, values, saved_path)
    #     self.draw_plots(results)

    def _log_results(self, method_name, results, values, saved_path):
        self.text_edit.append(f"\n=== {method_name} ===")
        self.text_edit.append("Введённые диапазоны:")
        for name, (vmin, vmax) in values.items():
            self.text_edit.append(f"  • {name}: min={vmin:g}, max={vmax:g}")
        self.text_edit.append("")
        self.text_edit.append("Найдено аномалий:")
        for col in results.columns:
            if col.endswith("_anomaly"):
                n = int(results[col].sum())
                self.text_edit.append(f"  • {col[:-len('_anomaly')]}: {n}")
        if saved_path:
            self.text_edit.append(f"\nРезультаты сохранены: {saved_path}")

    # графики
    def draw_plots(self, data):
        self.figure.clear()

        if data is None or len(data.columns) == 0:
            ax = self.figure.add_subplot(111)
            ax.text(
                0.5, 0.5,
                "Данные не загружены.\nНажмите «Загрузить данные» "
                "или выберите метод диагностики.",
                ha="center", va="center", fontsize=11, transform=ax.transAxes
            )
            ax.set_axis_off()
            self.figure.tight_layout()
            self.canvas.draw()
            return

        signal_cols = [
            c for c in data.columns
            if not c.endswith("_anomaly") and c != "Timestamp"
        ]
        if not signal_cols:
            self.figure.tight_layout()
            self.canvas.draw()
            return

        ncols = 2
        nrows = (len(signal_cols) + ncols - 1) // ncols
        axes = self.figure.subplots(nrows, ncols)
        axes = np.array(axes).flatten()

        for i, col in enumerate(signal_cols):
            ax = axes[i]
            ax.plot(data.index, data[col], color="steelblue",
                    linewidth=0.7, label="сигнал")
            anom_col = col + "_anomaly"
            if anom_col in data.columns:
                mask = data[anom_col].astype(bool)
                if mask.any():
                    ax.scatter(data.index[mask], data.loc[mask, col],
                               color="red", s=14, zorder=3, label="аномалия")
            ax.set_title(col, fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=7, loc="upper right")

        for j in range(len(signal_cols), len(axes)):
            axes[j].set_axis_off()

        self.figure.tight_layout()
        self.canvas.draw()

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