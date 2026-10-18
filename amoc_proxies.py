"""Multi-proxy evidence for an AMOC slowdown over the past millennia.

Data: Caesar et al. (2021), Nature Geoscience, compiled in
https://github.com/ncahill89/AMOC-Analysis (data/Data_compilation.xlsx).
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "caesar2021" / "Data_compilation.xlsx"
OUTPUT_PATH = ROOT / "figures" / "amoc_proxies.png"

X_MIN, X_MAX = 400, 2025
INDUSTRIAL_START = 1850


def read_block(sheet: str, header_row: int, first_col: int, n_cols: int) -> pd.DataFrame:
    """Read a block of numeric columns from one sheet of the compilation."""
    raw = pd.read_excel(DATA_PATH, sheet_name=sheet, header=None)
    block = raw.iloc[header_row + 1 :, first_col : first_col + n_cols]
    block = block.apply(pd.to_numeric, errors="coerce").dropna(how="all")
    return block.reset_index(drop=True)


def load_sst() -> tuple[pd.DataFrame, pd.DataFrame]:
    rahmstorf = read_block("Rahmstorf et al. (2015)", 1, 0, 5)
    rahmstorf.columns = ["year", "value", "two_sigma", "low", "high"]
    rahmstorf["low"] = rahmstorf["value"] - rahmstorf["two_sigma"]
    rahmstorf["high"] = rahmstorf["value"] + rahmstorf["two_sigma"]

    caesar = read_block("Caesar et al. (2018)", 1, 0, 4)
    caesar.columns = ["year", "value", "low", "high"]
    overlap = caesar["year"].between(rahmstorf["year"].min(), rahmstorf["year"].max())
    shared_years = caesar.loc[overlap, "year"]
    offset = (
        rahmstorf.set_index("year").loc[shared_years, "value"].mean()
        - caesar.loc[overlap, "value"].mean()
    )
    caesar[["value", "low", "high"]] += offset
    return rahmstorf.dropna(subset=["value"]), caesar.dropna(subset=["value"])


def load_corals() -> tuple[pd.DataFrame, pd.DataFrame]:
    annual = read_block("Sheerwood et al. (2011)", 1, 0, 4)
    annual.columns = ["year", "value", "low", "high"]
    dated = read_block("Sheerwood et al. (2011)", 1, 5, 7)
    dated.columns = ["year_min", "year_max", "year", "value", "two_sigma", "low", "high"]
    return annual.dropna(subset=["value"]), dated.dropna(subset=["value"])


def load_sortable_silt() -> dict[str, pd.DataFrame]:
    cores = {}
    for label, first_col in (("KNR-178-56JPC", 0), ("KNR-178-48JPC", 7)):
        core = read_block("Thornalley et al. (2018) s-silt", 2, first_col, 4)
        core.columns = ["year", "value", "smooth", "two_sigma"]
        core = core.dropna(subset=["value"]).sort_values("year")
        core["low"] = core["value"] - core["two_sigma"]
        core["high"] = core["value"] + core["two_sigma"]
        cores[label] = core
    return cores


def load_msa() -> pd.DataFrame:
    msa = read_block("Osmann et al. (2019)", 1, 0, 4)
    msa.columns = ["year", "value", "low", "high"]
    msa = msa.dropna(subset=["value"]).sort_values("year").reset_index(drop=True)
    msa["smooth"] = msa["value"].rolling(11, center=True, min_periods=6).mean()
    return msa


def shade_industrial(ax: plt.Axes) -> None:
    ax.axvspan(INDUSTRIAL_START, X_MAX, color="#f2d7d5", alpha=0.45, zorder=0, lw=0)


def plot_proxies(output_path: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 150,
        }
    )

    rahmstorf, caesar = load_sst()
    corals_annual, corals_dated = load_corals()
    silt = load_sortable_silt()
    msa = load_msa()

    fig, axes = plt.subplots(4, 1, figsize=(11, 11), sharex=True)
    ax_sst, ax_coral, ax_silt, ax_msa = axes

    ax_sst.fill_between(
        rahmstorf["year"], rahmstorf["low"], rahmstorf["high"], color="#c0392b", alpha=0.18, lw=0
    )
    ax_sst.plot(
        rahmstorf["year"], rahmstorf["value"], color="#c0392b", lw=1.6,
        label="Rahmstorf et al. (2015), proxy SST index",
    )
    ax_sst.plot(
        caesar["year"], caesar["value"], color="#7b241c", lw=1.0,
        label="Caesar et al. (2018), instrumental SST fingerprint",
    )
    ax_sst.set_ylabel("AMOC index\n(SST anomaly, K)")
    ax_sst.set_title("a) Sea surface temperature reconstruction (subpolar North Atlantic)",
                     loc="left", fontsize=10.5)

    ax_coral.fill_between(
        corals_annual["year"], corals_annual["low"], corals_annual["high"],
        color="#1e8449", alpha=0.2, lw=0,
    )
    ax_coral.plot(
        corals_annual["year"], corals_annual["value"], color="#1e8449", lw=1.4,
        label="Annual record (1926-2002)",
    )
    ax_coral.errorbar(
        corals_dated["year"], corals_dated["value"],
        xerr=[corals_dated["year"] - corals_dated["year_min"],
              corals_dated["year_max"] - corals_dated["year"]],
        yerr=corals_dated["two_sigma"],
        fmt="o", color="#145a32", ms=4, elinewidth=0.8, capsize=2,
        label="Radiocarbon-dated colonies (lifespan shown)",
    )
    ax_coral.set_ylabel("Coral δ¹⁵N (‰)")
    ax_coral.set_title("b) Deep-sea gorgonian corals, Gulf of Maine (Sherwood et al., 2011)",
                       loc="left", fontsize=10.5)

    for (label, core), color in zip(silt.items(), ("#b9770e", "#6e2c00")):
        ax_silt.fill_between(core["year"], core["low"], core["high"], color=color, alpha=0.18, lw=0)
        ax_silt.plot(core["year"], core["value"], color=color, lw=1.4, marker="o", ms=2.5,
                     label=f"Core {label}")
    ax_silt.set_ylabel("Mean sortable silt\ngrain size (µm)")
    ax_silt.set_title("c) Grain size of marine sediments, Cape Hatteras (Thornalley et al., 2018)",
                      loc="left", fontsize=10.5)

    ax_msa.fill_between(msa["year"], msa["low"], msa["high"], color="#2e86c1", alpha=0.18, lw=0)
    ax_msa.plot(msa["year"], msa["value"], color="#2e86c1", lw=0.7, alpha=0.6, label="Annual")
    ax_msa.plot(msa["year"], msa["smooth"], color="#1b4f72", lw=1.8, label="11-year mean")
    ax_msa.set_ylabel("Methanesulfonic acid\n(standardised units)")
    ax_msa.set_title("d) Acid concentration in Greenland ice cores (Osman et al., 2019)",
                     loc="left", fontsize=10.5)

    for ax in axes:
        shade_industrial(ax)
        ax.legend(frameon=False, loc="lower left", fontsize=8)
        ax.text(1.005, 0.95, "stronger\nAMOC ↑", transform=ax.transAxes,
                fontsize=7.5, color="#555555", va="top")
        ax.text(1.005, 0.05, "weaker\nAMOC ↓", transform=ax.transAxes,
                fontsize=7.5, color="#555555", va="bottom")

    ax_sst.text(INDUSTRIAL_START + 10, 0.97, "Industrial era", transform=ax_sst.get_xaxis_transform(),
                fontsize=8.5, color="#922b21", va="top")
    ax_msa.set_xlim(X_MIN, X_MAX)
    ax_msa.set_xlabel("Year (CE)")

    fig.suptitle(
        "Multiple proxies point to an AMOC weakening unprecedented in the past millennium",
        fontsize=13, x=0.02, ha="left",
    )
    fig.tight_layout(rect=(0, 0.04, 0.95, 0.98))
    fig.text(
        0.02, 0.01,
        "Data: compilation from Caesar et al. (2021), Nature Geoscience, github.com/ncahill89/AMOC-Analysis. "
        "Shaded bands: 95% uncertainty.\n"
        "Caesar et al. (2018) series offset to the Rahmstorf et al. (2015) mean over their overlap. "
        "For every panel, lower values indicate a weaker AMOC.",
        fontsize=8, color="#444444", ha="left", va="bottom",
    )
    fig.savefig(output_path, bbox_inches="tight")
    if plt.get_backend().lower() != "agg":
        plt.show()


def main() -> None:
    plot_proxies(OUTPUT_PATH)


if __name__ == "__main__":
    main()
