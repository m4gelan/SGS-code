"""Google Trends (GB) for the Atlantic meridional overturning circulation (AMOC)."""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data" / "google_trends"
MONTHLY_PATH = DATA_DIR / "time_series_GB_20211013-1505_20261013-1505.csv"
WEEKLY_PATH = DATA_DIR / "time_series_GB_20251013-1534_20261013-1534.csv"
OUTPUT_PATH = ROOT / "figures" / "amoc_google_trends.png"

JULY7_DATE = pd.Timestamp("2026-07-07")
JULY7_LABEL = "Yale article"
APRIL15_DATE = pd.Timestamp("2026-04-15")
APRIL15_LABEL = "The Guardian article"
PLOT_START = pd.Timestamp("2025-01-01")


def load_trends(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["Time"] = pd.to_datetime(frame["Time"])
    frame = frame.rename(
        columns={"Atlantic meridional overturning circulation": "popularity"}
    )
    return frame


def combine_trends(monthly: pd.DataFrame, weekly: pd.DataFrame) -> pd.DataFrame:
    """Join the monthly series to the weekly series on one 0–100 scale.

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


def plot_trends(frame: pd.DataFrame, output_path: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 150,
        }
    )

    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.plot(
        frame["Time"],
        frame["popularity"],
        color="#1f4e79",
        linewidth=1.8,
        marker="o",
        markersize=3.5,
        label="AMOC",
    )
    ax.axvline(
        JULY7_DATE,
        color="#6c3483",
        linestyle=":",
        linewidth=1.6,
    )
    ax.axvline(
        APRIL15_DATE,
        color="#d35400",
        linestyle=":",
        linewidth=1.6,
    )

    ax.set_xlim(frame["Time"].min(), frame["Time"].max())
    ax.set_ylim(0, 100)
    ax.set_xlabel("Time")
    ax.set_ylabel("Relative popularity (0–100)")
    ax.set_title("Google Trends for AMOC (United Kingdom)")

    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 4, 7, 10)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_yticks(range(0, 101, 20))

    ax.annotate(
        JULY7_LABEL,
        xy=(JULY7_DATE, 82),
        xytext=(-8, 0),
        textcoords="offset points",
        ha="right",
        va="center",
        fontsize=8.5,
        color="#6c3483",
    )
    ax.annotate(
        APRIL15_LABEL,
        xy=(APRIL15_DATE, 68),
        xytext=(-8, 0),
        textcoords="offset points",
        ha="right",
        va="center",
        fontsize=8.5,
        color="#d35400",
    )

    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.24)
    ax.text(
        0.0,
        -0.28,
        "Source : Google trends, keyword ; Atlantic Meridional Atlantic circulation, accessed on 13/10/2026\n"
        "January–September 2025 monthly; October 2025–October 2026 weekly, on the same 0–100 scale.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color="#444444",
    )
    fig.savefig(output_path, bbox_inches="tight")
    if plt.get_backend().lower() != "agg":
        plt.show()


def main() -> None:
    monthly = load_trends(MONTHLY_PATH)
    weekly = load_trends(WEEKLY_PATH)
    frame = combine_trends(monthly, weekly)
    frame = frame.loc[frame["Time"] >= PLOT_START].reset_index(drop=True)
    plot_trends(frame, OUTPUT_PATH)


if __name__ == "__main__":
    main()
