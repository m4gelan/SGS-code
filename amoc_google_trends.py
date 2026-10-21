"""Google Trends (GB) for the Atlantic meridional overturning circulation (AMOC)."""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data" / "google_trends"
MONTHLY_PATH = DATA_DIR / "time_series_GB_20211020-1552_20261020-1552.csv"
WEEKLY_PATH = DATA_DIR / "time_series_GB_20251013-1534_20261013-1534.csv"
OUTPUT_PATH = ROOT / "figures" / "amoc_google_trends.png"

LINE_COLOR = "#1f4e79"

# (publication date, label, colour)
ARTICLES = [
    (pd.Timestamp("2026-04-15"), "The Guardian article", "#d35400"),
    (pd.Timestamp("2026-06-14"), "The Guardian article", "#1e8449"),
    (pd.Timestamp("2026-07-15"), "BBC article", "#6c3483"),
]


def week_start(date: pd.Timestamp) -> pd.Timestamp:
    """Return the Sunday that starts the week containing ``date``.

    Google Trends aggregates searches over whole weeks running Sunday to
    Saturday, so an article is placed at the start of its week rather than on
    its exact publication day.
    """
    return date - pd.Timedelta(days=(date.dayofweek + 1) % 7)


def load_trends(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["Time"] = pd.to_datetime(frame["Time"])
    frame = frame.rename(columns={frame.columns[1]: "popularity"})
    return frame.sort_values("Time").reset_index(drop=True)


def combine_trends(monthly: pd.DataFrame, weekly: pd.DataFrame) -> pd.DataFrame:
    """Join the 5-year monthly series to the 1-year weekly series on one 0–100 scale.

    Each Google Trends download is scaled so its own peak is 100. The weekly
    file's peak is a single week, higher than any monthly average, so the
    monthly values are divided by the typical monthly-to-weekly ratio in the
    overlap. The busiest week then remains 100.
    """
    weekly = weekly.copy()
    monthly = monthly.copy()
    weekly["month"] = weekly["Time"].dt.to_period("M")
    monthly["month"] = monthly["Time"].dt.to_period("M")

    week_counts = weekly.groupby("month").size()
    week_means = weekly.groupby("month")["popularity"].mean()
    full_months = week_counts[week_counts >= 4].index
    month_values = monthly.set_index("month")["popularity"]
    ratios = (month_values.loc[full_months] / week_means.loc[full_months]).dropna()
    ratios = ratios[week_means.loc[ratios.index] > 0]
    scale = float(ratios.median())

    history = monthly.loc[
        monthly["Time"] < weekly["Time"].min(), ["Time", "popularity"]
    ].copy()
    history["popularity"] = history["popularity"] / scale
    recent = weekly.loc[:, ["Time", "popularity"]].copy()

    combined = pd.concat([history, recent], ignore_index=True)
    peak = float(combined["popularity"].max())
    combined["popularity"] = combined["popularity"] / peak * 100
    return combined.sort_values("Time").reset_index(drop=True)


def smooth_curve(frame: pd.DataFrame) -> tuple[pd.DatetimeIndex, np.ndarray]:
    """Monotone cubic interpolation of the trend values onto a daily grid.

    PCHIP passes through every observed point without overshooting, so the
    curve stays within 0–100 and keeps the true peaks.
    """
    x = mdates.date2num(frame["Time"])
    interpolator = PchipInterpolator(x, frame["popularity"].to_numpy(dtype=float))
    dense_time = pd.date_range(frame["Time"].min(), frame["Time"].max(), freq="D")
    dense_values = interpolator(mdates.date2num(dense_time))
    return dense_time, dense_values


def plot_trends(frame: pd.DataFrame, output_path: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 150,
        }
    )

    dense_time, dense_values = smooth_curve(frame)

    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.fill_between(dense_time, dense_values, color=LINE_COLOR, alpha=0.12, linewidth=0)
    ax.plot(dense_time, dense_values, color=LINE_COLOR, linewidth=2.2, label="AMOC")
    ax.scatter(
        frame["Time"],
        frame["popularity"],
        color=LINE_COLOR,
        s=8,
        alpha=0.5,
        zorder=3,
    )
    for date, label, color in ARTICLES:
        start = week_start(date)
        ax.axvline(
            start,
            color=color,
            linestyle=":",
            linewidth=1.6,
            label=f"{label} (week of {start:%d %b %Y})",
        )

    ax.set_xlim(frame["Time"].min(), frame["Time"].max())
    ax.set_ylim(0, 105)
    ax.set_xlabel("Time")
    ax.set_ylabel("Relative popularity (0–100)")
    ax.set_title("Google Trends for AMOC (United Kingdom)")

    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_yticks(range(0, 101, 20))
    ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    ax.set_axisbelow(True)

    ax.legend(frameon=False, loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.24)
    ax.text(
        0.0,
        -0.28,
        "Source : Google trends, keyword ; Atlantic Meridional Overturning Circulation, accessed on 20/10/2026\n"
        "October 2021–September 2025 monthly; October 2025–October 2026 weekly, on the same 0–100 scale; "
        "curve smoothed by monotone cubic interpolation.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color="#444444",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    if plt.get_backend().lower() != "agg":
        plt.show()


def main() -> None:
    monthly = load_trends(MONTHLY_PATH)
    weekly = load_trends(WEEKLY_PATH)
    frame = combine_trends(monthly, weekly)
    plot_trends(frame, OUTPUT_PATH)


if __name__ == "__main__":
    main()
