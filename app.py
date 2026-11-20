import sys
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QSplitter, QFileDialog, QMessageBox
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TurbineLog — Агент диагностики гидроагрегатов")
        self.resize(1200, 700)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Верхняя панель с кнопками
        top = QHBoxLayout()
        self.btn_load = QPushButton("Загрузить файл")
        self.btn_save = QPushButton("Выгрузить в файл")
        self.btn_load.clicked.connect(self.load_file)
        self.btn_save.clicked.connect(self.save_file)
        top.addWidget(self.btn_load)
        top.addWidget(self.btn_save)
        top.addStretch()
        root.addLayout(top)

        # Нижняя часть
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая часть
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Здесь будет отображаться текст")
        splitter.addWidget(self.text_edit)

        # Правая часть (сетка 2×2 внутри одной фигуры)
        self.figure = Figure(figsize=(6, 5))
        self.canvas = FigureCanvas(self.figure)
        splitter.addWidget(self.canvas)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([400, 800])

        root.addWidget(splitter, stretch=1)

        self.draw_plots()

    # Отрисовка 4 графиков (просто пример)
    def draw_plots(self):
        self.figure.clear()
        axes = self.figure.subplots(2, 2).flatten()

        for i, ax in enumerate(axes):
            x = np.linspace(0, 10, 200)
            y = np.sin(x + i) * (i + 1)
            ax.plot(x, y)
            ax.set_title(f"График {i + 1}")
            ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

    # Загрузка файла
    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл", "",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.text_edit.setPlainText(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{e}")

    # Выгрузка файла
    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл", "",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            QMessageBox.information(self, "Готово", "Файл сохранён.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()