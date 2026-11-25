import pandas as pd
import numpy as np
import matplotlib.dates as mdates

def draw_threshold_plots(view, data: pd.DataFrame, ranges: dict = None):
    view.figure.clear()

    if data is None or len(data.columns) == 0:
        ax = view.figure.add_subplot(111)
        ax.text(0.5, 0.5, "Данные не загружены.", ha="center", va="center")
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

    color_line = "#000000"  # Чёрная линия
    color_limit = "#aa0000"  # Красные границы
    color_anom = "#e74c3c"  # Красные аномалии
    color_axis = "#111111"  # Черные оси

    for i, col in enumerate(signal_cols):
        ax = axes[i]

        ax.plot(data.index, data[col], color=color_line, linewidth=2, zorder=2)

        if ranges and col in ranges:
            min_val, max_val = ranges[col]
            ax.axhline(y=min_val, color=color_limit, linewidth=2, zorder=1)
            ax.axhline(y=max_val, color=color_limit, linewidth=2, zorder=1)

        anom_col = col + "_anomaly"
        if anom_col in data.columns:
            mask = data[anom_col].astype(bool)
            if mask.any():
                ax.scatter(data.index[mask], data.loc[mask, col],
                           color=color_anom, s=40, edgecolors="white",
                           linewidth=0.8, zorder=3, label="Аномалия")

        ax.set_title(col, fontsize=10, pad=10)
        ax.grid(False)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        ax.spines['left'].set_color(color_axis)
        ax.spines['left'].set_linewidth(2)
        ax.spines['bottom'].set_color(color_axis)
        ax.spines['bottom'].set_linewidth(2)

        ax.set_xticks([])
        ax.set_yticks([])

        ax.plot(1, 0, ls="", marker=">", ms=10, color=color_axis,
                transform=ax.get_yaxis_transform(), clip_on=False)

        ax.plot(0, 1, ls="", marker="^", ms=10, color=color_axis,
                transform=ax.get_xaxis_transform(), clip_on=False)

    for j in range(len(signal_cols), len(axes)):
        axes[j].set_axis_off()

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