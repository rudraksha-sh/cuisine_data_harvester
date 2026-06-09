"""Statistical and visual analysis for the Zone 1 dish dataset."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DISH_CSV = PROJECT_ROOT / "base_dish.csv"
VARIANTS_CSV = PROJECT_ROOT / "dish_variants.csv"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path.name}")
    return pd.read_csv(path)


def _combine_dataset() -> pd.DataFrame:
    base_df = _load_csv(BASE_DISH_CSV).assign(record_type="base")
    variant_df = _load_csv(VARIANTS_CSV).assign(record_type="variant")
    return pd.concat([base_df, variant_df], ignore_index=True)


def _derive_diet(series: pd.Series) -> pd.Series:
    values = series.fillna("").str.lower()
    return values.map(
        lambda value: "Non-Vegetarian"
        if "non-veg" in value or "non vegetarian" in value or "nonvegetarian" in value or "non-vegetarian" in value
        else "Vegetarian"
    )


def _save_fig(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()


def plot_veg_vs_nonveg(df: pd.DataFrame) -> Path:
    counts = df["diet_category"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 6))
    colors = ["#2E7D32", "#C62828"]
    ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=140, colors=colors[: len(counts)], wedgeprops={"edgecolor": "white", "linewidth": 2})
    ax.set_title("Vegetarian vs Non-Vegetarian Dishes", fontweight="bold")
    out_path = ANALYSIS_DIR / "01_veg_vs_nonveg_pie.png"
    _save_fig(out_path)
    return out_path


def plot_state_distribution(df: pd.DataFrame) -> Path:
    counts = df.groupby("state").size().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(12, 7))
    palette = sns.color_palette("Blues", n_colors=len(counts))
    ax.barh(counts.index, counts.values, color=palette)
    for y, count in enumerate(counts.values):
        ax.text(count + 1, y, str(count), va="center", fontsize=9)
    ax.set_xlabel("Total dishes (base + variant)")
    ax.set_title("Zone 1 State Distribution", fontweight="bold")
    ax.set_xlim(0, counts.max() * 1.12)
    out_path = ANALYSIS_DIR / "02_state_distribution.png"
    _save_fig(out_path)
    return out_path


def plot_base_vs_variant(df: pd.DataFrame) -> Path:
    counts = df.groupby(["state", "record_type"]).size().unstack(fill_value=0)
    counts = counts.reindex(columns=["base", "variant"], fill_value=0)
    fig, ax = plt.subplots(figsize=(12, 7))
    bottom = pd.Series([0] * len(counts), index=counts.index)
    colors = {"base": "#6A5ACD", "variant": "#F4A261"}
    for column in ["base", "variant"]:
        ax.bar(counts.index, counts[column], bottom=bottom, label=column.title(), color=colors[column], edgecolor="white")
        bottom += counts[column]
    ax.set_ylabel("Dish count")
    ax.set_title("Base vs Variant Contribution by State", fontweight="bold")
    ax.legend()
    plt.xticks(rotation=20, ha="right")
    out_path = ANALYSIS_DIR / "03_base_vs_variant_state.png"
    _save_fig(out_path)
    return out_path


def print_summary(df: pd.DataFrame) -> None:
    print("\nZone 1 Statistical Summary")
    print("=" * 48)
    print(f"Total dishes: {len(df)}")
    print(f"Base dishes: {int((df['record_type'] == 'base').sum())}")
    print(f"Variant dishes: {int((df['record_type'] == 'variant').sum())}")
    print(f"States covered: {df['state'].nunique()}")
    print(f"Vegetarian dishes: {int((df['diet_category'] == 'Vegetarian').sum())}")
    print(f"Non-vegetarian dishes: {int((df['diet_category'] == 'Non-Vegetarian').sum())}")
    print("\nState-wise dish distribution:")
    for state, count in df.groupby("state").size().sort_index().items():
        print(f"  {state:<22} {count}")


def main() -> None:
    ANALYSIS_DIR.mkdir(exist_ok=True)
    df = _combine_dataset()
    df["diet_category"] = _derive_diet(df["dish_type"])

    print_summary(df)

    veg_path = plot_veg_vs_nonveg(df)
    state_path = plot_state_distribution(df)
    split_path = plot_base_vs_variant(df)

    print("\nCharts saved:")
    print(f"  {veg_path.name}")
    print(f"  {state_path.name}")
    print(f"  {split_path.name}")


if __name__ == "__main__":
    main()
