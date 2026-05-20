# Logistic Curve Models of CO2 Accumulation

This sub-project reproduces the descriptive logistic curves for atmospheric CO2 accumulation reported in the 2020 paper. It is a small reproduction package, not a physical carbon-cycle model.

The published version is David Levinson, "Logistic Curve Models of CO2 Accumulation," Transport Findings, July 24, 2020: https://findingspress.org/article/13709-logistic-curve-models-of-co2-accumulation. DOI: https://doi.org/10.32866/001c.13709.

The workflow uses a local copy of the Scripps Mauna Loa monthly CO2 data and reproduces the seven model-year curves reported in the paper for 1960, 1970, 1980, 1990, 2000, 2010, and 2020. It also includes a 2020-2026 extension figure using current NOAA GML monthly Mauna Loa CO2 data, without refitting the paper's models.

## Project Layout

```text
logistic-co2-accumulation/
  data/monthly_in_situ_co2_mlo.csv
  data/noaa_mlo_co2_monthly_2026_download.csv
  paper/main.tex
  paper/bibliography.bib
  paper/CO2-S-Curve.jpg
  2020_reproduction_outputs/
  2026_test_extension_outputs/
  reproduce_paper_curves.py
  documentation/requirements.txt
```

## Quick Start

```bash
cd /Users/dlev2617/Documents/Reproducibility/logistic-co2-accumulation
python3 -m pip install -r documentation/requirements.txt
python3 reproduce_paper_curves.py
```

To refresh the extension data before running:

```bash
python3 reproduce_paper_curves.py --download-extension-data
```

The script reads `data/monthly_in_situ_co2_mlo.csv`, fits the paper-style curves, and writes the original reproduction outputs to:

- `2020_reproduction_outputs/tables/reproduced_parameters.csv`
- `2020_reproduction_outputs/tables/reproduced_rmse_matrix.csv`
- `2020_reproduction_outputs/tables/reproduced_curve_points.csv`
- `2020_reproduction_outputs/figures/reproduced_co2_s_curve.png`

It also reads `data/noaa_mlo_co2_monthly_2026_download.csv` and writes the fixed-model extension outputs to:

- `2026_test_extension_outputs/tables/extension_observed_vs_fixed_models.csv`
- `2026_test_extension_outputs/figures/extension_co2_s_curve_2020_2026.png`

## Model

The paper fixes a pre-industrial baseline of 280 ppm and estimates the logistic curve on baseline-adjusted accumulation:

```text
CO2(t) = baseline + (asymptote - baseline) / (1 + exp(-growth_rate * (t - midpoint_year)))
```

The parameters are descriptive:

- `baseline`: lower concentration implied by the curve.
- `asymptote`: upper concentration implied by the curve.
- `growth_rate`: steepness of the accumulation curve.
- `midpoint_year`: year when the curve reaches halfway between baseline and asymptote.

Interpret fitted asymptotes cautiously. Atmospheric CO2 is governed by emissions, sinks, land use, oceans, policy, and energy systems; a logistic curve is a compact empirical summary, not a causal forecast.

## Inputs

These are working copies so the originals under `Documents/Papers/...` are not modified. The primary data file is:

```text
data/monthly_in_situ_co2_mlo.csv
```

The paper says it uses raw Mauna Loa CO2 interpolated to complete missing observations. In the Scripps CSV this corresponds to the `CO2 filled` column. The 2020 model in the script includes the available non-missing 2020 observations because that matches the paper's reported 2020 parameters most closely.

The extension data file is downloaded from NOAA GML's Mauna Loa monthly mean CSV at `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv`. The downloaded file used here was created by NOAA on May 5, 2026 and runs through April 2026. NOAA notes in the file header that measurements were suspended after the November 2022 Mauna Loa eruption and that observations from December 2022 to July 4, 2023 are from Maunakea Observatories.
