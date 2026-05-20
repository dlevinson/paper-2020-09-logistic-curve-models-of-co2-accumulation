# Paper Evidence And Package Boundary

Generated: 2026-05-17 08:42:21 AEST

## Bibliographic Information

- Row ID: `paper-2020-09`
- Citation: David M. Levinson. (2020). Logistic Curve Models Of CO2 Accumulation. Transport Findings (2020). https://doi.org/10.32866/001c.13709
- DOI: https://doi.org/10.32866/001c.13709

## Paper Evidence

The inspected paper source and PDF identify the monthly Mauna Loa atmospheric CO2 series from the Scripps Institution of Oceanography as the data source. The methods section says the raw Mauna Loa series, interpolated to complete missing observations, was used, with model fits estimated for 1960, 1970, 1980, 1990, 2000, 2010, and 2020. The paper describes ordinary least squares fitting of transformed logistic curves, with the best saturation level selected by optimizing fit.

## Local Reproduction Evidence

The attached local reproduction folder at `/Users/dlev2617/Documents/Reproducibility/logistic-co2-accumulation` matches the title, DOI, paper source, data source, and model-year workflow. The archive package includes the Python reproduction script, requirements file, Scripps working data CSV, paper source files, and the 2020 reproduced outputs. A fresh test run on 2026-05-17 wrote reproduction outputs to `/tmp/paper-2020-09-repro-check`; the generated 2020 parameter table, RMSE matrix, curve points, and figure were byte-identical to the local reproduction outputs copied into this package.

## Package Boundary

This package is staged as a public upload candidate because it contains public source data and author-created reproduction code, with no human-subject, proprietary, or controlled-access data. The 2026 NOAA extension input and outputs are intentionally excluded because they are post-paper validation material, not evidence used in the 2020 paper. They remain documented in `EXCLUDED_NONARCHIVAL_FILES.csv`.

## License And Attribution Notes

The live Findings article page inspected on 2026-05-17 displays `ccby-sa-4.0` for the article. Retain source attribution to the Scripps CO2 Program for the Mauna Loa data; the Scripps data are public source data, not newly licensed by this package. Repository-level license text for the author-created reproduction code should be set consistently with the paper/repository release decision at upload time.
