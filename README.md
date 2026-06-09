# Zone 1 Dish Dataset Project

This project builds a structured dataset of regional dishes from Zone 1 of India and generates analysis charts from the collected data. The workflow is centered around two CSV outputs and a simple command-line entry point.

## What this project does

- Generates a base dish dataset for selected Zone 1 states and union territories
- Creates variant dish records for each base dish
- Saves the results as CSV files
- Produces visual analysis charts for the dataset

## Covered regions

The generated dataset focuses on the following Zone 1 states and regions:

- Rajasthan
- Punjab
- Haryana
- Himachal Pradesh
- Uttarakhand
- Uttar Pradesh
- Delhi
- Jammu and Kashmir
- Ladakh
- Chandigarh

## Project structure

- main.py: Entry point for building data and running analysis
- scraper.py: Creates and populates the dish dataset files
- analyzer.py: Loads the CSV files and generates summary charts
- base_dish.csv: Generated base dish dataset
- dish_variants.csv: Generated variant dish dataset
- analysis/: Folder containing generated charts

## Requirements

This project requires Python 3.10+ and the following packages:

- pandas
- matplotlib
- seaborn
- requests
- beautifulsoup4
- urllib3

Install them with:

```bash
pip install -r requirements.txt
```

## Usage

Run the full workflow:

```bash
python main.py
```

Run only the data build step:

```bash
python main.py --build
```

Run only the analysis step:

```bash
python main.py --analyze
```

## Output files

When you run the project, it generates:

- base_dish.csv
- dish_variants.csv
- analysis/01_veg_vs_nonveg_pie.png
- analysis/02_state_distribution.png
- analysis/03_base_vs_variant_state.png

## Notes

The project is designed as a lightweight dataset generation and analysis pipeline for regional food data, with a focus on curated Zone 1 dishes and their variants.
