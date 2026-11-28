import pandas as pd
import numpy as np
import matplotlib.dates as mdates

COLUMN_LABELS = {
    "Oil_Pressure_Bar": "Давление масла, бар",
    "Bearing_Temp_C":   "Температура подшипника, °C",
    "Vibration_mm_s":   "Вибрация, мм/с",
    "RPM":              "Частота вращения, об/мин",
    "Active_Power_MW":  "Активная мощность, МВт",
    "Water_Flow_m3_h":  "Расход воды, м³/ч",
}


def _label(col: str) -> str:
    return COLUMN_LABELS.get(col, col)

def draw_threshold_plots(view, data: pd.DataFrame, ranges: dict = None):
    view.figure.clear()

    if data is None or len(data.columns) == 0:
        ax = view.figure.add_subplot(111)
        ax.text(0.5, 0.5, "Данные не загружены.",
                ha="center", va="center", fontsize=11, transform=ax.transAxes)
        ax.set_axis_off()
        view.figure.tight_layout()
        view.canvas.draw()
        return

    signal_cols = [
        c for c in data.columns
        if not c.endswith("_anomaly") and c != "Timestamp"
    ]
    if not signal_cols:
        view.canvas.draw()
        return

    ncols = 2
    nrows = (len(signal_cols) + ncols - 1) // ncols
    axes = view.figure.subplots(nrows, ncols)
    axes = np.array(axes).flatten()

    range_values = list(ranges.values()) if ranges else []

    for i, col in enumerate(signal_cols):
        ax = axes[i]

        ax.plot(data.index, data[col], color="steelblue",
                linewidth=0.7, label="сигнал")

        # Сначала пробуем найти диапазон по русскому ключу,
        # затем — по позиции (на случай нестандартных имён).
        pair = None
        if ranges:
            pair = ranges.get(_label(col))
            if pair is None and i < len(range_values):
                pair = range_values[i]

        if pair is not None:
            min_val, max_val = pair
            if min_val > max_val:
                min_val, max_val = max_val, min_val

            ax.axhline(y=min_val, color="crimson", linewidth=1.1,
                       linestyle="--", label=f"мин = {min_val:g}")
            ax.axhline(y=max_val, color="crimson", linewidth=1.1,
                       linestyle="--", label=f"макс = {max_val:g}")

            mask = (data[col] < min_val) | (data[col] > max_val)
            anom_col = col + "_anomaly"
            if anom_col in data.columns:
                mask = mask | data[anom_col].astype(bool)
            mask = mask & data[col].notna()

            if mask.any():
                ax.scatter(data.index[mask], data.loc[mask, col],
                           color="red", s=18, zorder=3, label="аномалия")

        ax.set_title(_label(col), fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, loc="upper right")

        if isinstance(data.index, pd.DatetimeIndex):
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

    for j in range(len(signal_cols), len(axes)):
        axes[j].set_axis_off()

    view.figure.autofmt_xdate(rotation=30, ha='right')
    view.figure.tight_layout()
    view.canvas.draw()


def draw_boxplots(view, data: pd.DataFrame):
    view.figure.clear()

    if data is None or len(data.columns) == 0:
        ax = view.figure.add_subplot(111)
        ax.text(
            0.5, 0.5,
            "Данные не загружены.\nВыберите метод диагностики "
            "или загрузите CSV.",
            ha="center", va="center", fontsize=11, transform=ax.transAxes
        )
        ax.set_axis_off()
        view.figure.tight_layout()
        view.canvas.draw()
        return

    signal_cols = [
        c for c in data.columns
        if not c.endswith("_anomaly") and c != "Timestamp"
    ]
    if not signal_cols:
        view.figure.tight_layout()
        view.canvas.draw()
        return

    ncols = 2
    nrows = (len(signal_cols) + ncols - 1) // ncols
    axes = view.figure.subplots(nrows, ncols)
    axes = np.array(axes).flatten()

    for i, col in enumerate(signal_cols):
        ax = axes[i]
        values = data[col].dropna().to_numpy()

        ax.boxplot(
            values,
            vert=True,
            patch_artist=True,
            widths=0.45,
            showfliers=True,
            whis=2.0,
            boxprops=dict(facecolor="steelblue", alpha=0.55),
            medianprops=dict(color="darkorange", linewidth=1.6),
            whiskerprops=dict(color="gray"),
            capprops=dict(color="gray"),
            flierprops=dict(
                marker="o", markersize=3,
                markerfacecolor="gray", markeredgecolor="gray", alpha=0.5
            ),
        )

        anom_col = col + "_anomaly"
        has_anom = anom_col in data.columns and bool(data[anom_col].astype(bool).any())
        if has_anom:
            mask = data[anom_col].astype(bool)
            anom_values = data.loc[mask, col].dropna().to_numpy()
            jitter = np.random.uniform(-0.12, 0.12, size=len(anom_values))
            ax.scatter(
                np.ones(len(anom_values)) + jitter, anom_values,
                color="red", s=22, zorder=3, label="аномалия"
            )

        ax.set_title(col, fontsize=9)
        ax.set_xticks([1])
        ax.set_xticklabels([""])  # подпись сенсора уже в заголовке
        ax.grid(True, alpha=0.3, axis="y")
        if has_anom:
            ax.legend(fontsize=7, loc="upper right")

    for j in range(len(signal_cols), len(axes)):
        axes[j].set_axis_off()

    view.figure.tight_layout()
    view.canvas.draw()


def draw_plots(view, data):
    view.figure.clear()

    if data is None or len(data.columns) == 0:
        ax = view.figure.add_subplot(111)
        ax.text(
            0.5, 0.5,
            "Данные не загружены.\nНажмите «Загрузить данные» "
            "или выберите метод диагностики.",
            ha="center", va="center", fontsize=11, transform=ax.transAxes
        )
        ax.set_axis_off()
        view.figure.tight_layout()
        view.canvas.draw()
        return

    signal_cols = [
        c for c in data.columns
        if not c.endswith("_anomaly") and c != "Timestamp"
    ]
    if not signal_cols:
        view.figure.tight_layout()
        view.canvas.draw()
        return

    ncols = 2
    nrows = (len(signal_cols) + ncols - 1) // ncols
    axes = view.figure.subplots(nrows, ncols)
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

        if isinstance(data.index, pd.DatetimeIndex):
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

    for j in range(len(signal_cols), len(axes)):
        axes[j].set_axis_off()

    view.figure.autofmt_xdate(rotation=30, ha='right')

    view.figure.tight_layout()
    view.canvas.draw()