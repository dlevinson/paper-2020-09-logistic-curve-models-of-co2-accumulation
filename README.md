# Logistic Curve Models Of CO2 Accumulation

## Bibliographic Information

- Row ID: `paper-2020-09`
- Year: 2020
- Authors: David M. Levinson
- Venue: Transport Findings (2020)
- DOI: https://doi.org/10.32866/001c.13709
- Citation: David M. Levinson. (2020). Logistic Curve Models Of CO2 Accumulation. Transport Findings (2020). https://doi.org/10.32866/001c.13709

## Archive Status

- Pipeline: `READY-TO-UPLOAD/PUBLIC`
- Package type: public data/code reproduction package
- Rights status: likely clear with provenance
- Human subjects status: none
- Generated: 2026-05-17 08:42:21 AEST

## Contents

- `paper/` contains the local paper PDF reference copy and inspected paper source files.
- `data/monthly_in_situ_co2_mlo.csv` is the Scripps Mauna Loa monthly CO2 working data used by the reproduction.
- `code/reproduce_paper_curves.py` reproduces the model-year logistic curves and tables.
- `outputs/2020_reproduction/` contains small regenerated output tables and the reproduced figure for verification.
- `documentation/` records the package boundary, source manifest, data profile, and intentionally excluded post-paper extension files.

## Reproduction

From this package root:

```bash
python3 -m pip install -r documentation/requirements.txt
python3 code/reproduce_paper_curves.py --data data/monthly_in_situ_co2_mlo.csv --output-dir outputs/2020_reproduction --no-extension
```

The script produces:

- `code/legacy/outputs/2020_reproduction/tables/reproduced_parameters.csv`
- `code/legacy/outputs/2020_reproduction/tables/reproduced_rmse_matrix.csv`
- `code/legacy/outputs/2020_reproduction/tables/reproduced_curve_points.csv`
- `code/legacy/outputs/2020_reproduction/figures/reproduced_co2_s_curve.png`

## Source Data

The paper uses the Mauna Loa monthly in situ CO2 series from the Scripps Institution of Oceanography, with filled/interpolated observations. Keep the Scripps attribution with any public release of this package.

## Exclusions

The 2026 NOAA extension data and generated extension outputs are not included in this 2020 paper archive package because they are post-paper validation material. See `documentation/EXCLUDED_NONARCHIVAL_FILES.csv`.



<!-- published-paper-reference:start -->
## Published Paper Reference

- Local published/final PDF reference: `paper/00_published_reference_logistic_curve_models_of_co2_accumulation.pdf`
- Official published source: https://findingspress.org/article/13709
- Official PDF/source link: https://findingspress.org/article/13709.pdf
- Paper-reference note: Findings published PDF.
<!-- published-paper-reference:end -->

<!-- package-hardening-status:start -->
## Package Hardening Status

Generated: 2026-05-20 15:23:47 AEST

- Pipeline: `READY-TO-UPLOAD/PUBLIC`
- Sidecars added/updated: `PACKAGE_STATUS.md`, `PACKAGE_MANIFEST.csv`, `LICENSE_STATUS.md`.
- Paper reference copies are for local audit convenience and are not public-upload assets without rights review.
- Final GitHub upload should use the manifest include statuses and the license-status note.
<!-- package-hardening-status:end -->
