from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QGridLayout, QVBoxLayout,
    QDialogButtonBox
)
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

        self.pressure = self._add_row(grid, 1, "Давление масла:",
                                      "0", "10",   "бар")
        self.temp     = self._add_row(grid, 2, "Температура подшипника:",
                                      "0", "100",  "°C")
        self.vib      = self._add_row(grid, 3, "Вибрация оборудования:",
                                      "0", "10",   "мм/с")
        self.rpm      = self._add_row(grid, 4, "Частота вращения ротора:",
                                      "0", "5000", "об/мин")
        self.power    = self._add_row(grid, 5, "Активная мощность:",
                                      "0", "300",  "МВт")
        self.flow     = self._add_row(grid, 6, "Расход воды:",
                                      "0", "2000", "м³/ч")

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