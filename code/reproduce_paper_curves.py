#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = PROJECT_ROOT / "data" / "monthly_in_situ_co2_mlo.csv"
DEFAULT_OUTPUTS = PROJECT_ROOT / "2020_reproduction_outputs"
DEFAULT_EXTENSION_DATA = PROJECT_ROOT / "data" / "noaa_mlo_co2_monthly_2026_download.csv"
DEFAULT_EXTENSION_OUTPUTS = PROJECT_ROOT / "2026_test_extension_outputs"
NOAA_EXTENSION_URL = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv"
BASELINE_PPM = 280.0
MODEL_YEARS = [2020, 2010, 2000, 1990, 1980, 1970, 1960]

PAPER_TABLE = {
    2020: {"b": 0.0273, "c": -55.8, "ti": 2042, "smax": 649, "r2": 0.992},
    2010: {"b": 0.0288, "c": -58.5, "ti": 2029, "smax": 573, "r2": 0.988},
    2000: {"b": 0.0285, "c": -58.0, "ti": 2030, "smax": 581, "r2": 0.980},
    1990: {"b": 0.0237, "c": None, "ti": None, "smax": math.inf, "r2": 0.962},
    1980: {"b": 0.0241, "c": -50.2, "ti": 2080, "smax": 962, "r2": 0.906},
    1970: {"b": 0.0375, "c": -73.7, "ti": 1966, "smax": 363, "r2": 0.648},
    1960: {"b": -0.0365, "c": 72.3, "ti": 1983, "smax": 331, "r2": 0.014},
}


@dataclass(frozen=True)
class Observation:
    year: int
    month: int
    decimal_year: float
    co2_filled_ppm: float


@dataclass(frozen=True)
class CurveFit:
    model_year: int
    n_observations: int
    finite_saturation: bool
    smax_ppm: float
    b: float
    c: float | None
    ti: float | None
    r2: float
    rmse_ppm: float
    residual_sd_ppm: float


def main() -> None:
    args = build_parser().parse_args()
    data_path = Path(args.data)
    output_dir = Path(args.output_dir)
    extension_data_path = Path(args.extension_data)
    extension_output_dir = Path(args.extension_output_dir)

    if args.download_extension_data:
        download_file(args.extension_data_url, extension_data_path)

    observations = read_scripps_mlo(data_path)
    fits = [
        fit_curve(training_window(observations, year, include_partial_2020=args.include_partial_2020), year)
        for year in MODEL_YEARS
    ]

    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    write_parameter_table(tables_dir / "reproduced_parameters.csv", fits)
    write_rmse_matrix(tables_dir / "reproduced_rmse_matrix.csv", observations, fits, args.include_partial_2020)
    write_curve_points(tables_dir / "reproduced_curve_points.csv", fits, args.plot_start, args.plot_end)
    write_figure(figures_dir / "reproduced_co2_s_curve.png", observations, fits, args.plot_start, args.plot_end)

    if not args.no_extension:
        extension_observations = extension_window(
            read_noaa_mlo(extension_data_path),
            start_year=args.extension_start_year,
            end_year=args.extension_end_year,
        )
        extension_tables_dir = extension_output_dir / "tables"
        extension_figures_dir = extension_output_dir / "figures"
        extension_tables_dir.mkdir(parents=True, exist_ok=True)
        extension_figures_dir.mkdir(parents=True, exist_ok=True)
        write_extension_comparison(
            extension_tables_dir / "extension_observed_vs_fixed_models.csv",
            extension_observations,
            fits,
        )
        write_extension_figure(
            extension_figures_dir / "extension_co2_s_curve_2020_2026.png",
            observations,
            extension_observations,
            fits,
            args.plot_start,
            args.plot_end,
        )

    print_summary(fits)
    print(f"Wrote {tables_dir / 'reproduced_parameters.csv'}")
    print(f"Wrote {tables_dir / 'reproduced_rmse_matrix.csv'}")
    print(f"Wrote {tables_dir / 'reproduced_curve_points.csv'}")
    print(f"Wrote {figures_dir / 'reproduced_co2_s_curve.png'}")
    if not args.no_extension:
        print(f"Wrote {extension_tables_dir / 'extension_observed_vs_fixed_models.csv'}")
        print(f"Wrote {extension_figures_dir / 'extension_co2_s_curve_2020_2026.png'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reproduce the logistic CO2 curves reported in the 2020 paper."
    )
    parser.add_argument("--data", default=DEFAULT_DATA, help="Local copy of monthly_in_situ_co2_mlo.csv.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUTS, help="Output directory.")
    parser.add_argument("--extension-data", default=DEFAULT_EXTENSION_DATA, help="NOAA monthly Mauna Loa CO2 data for the 2020-2026 extension.")
    parser.add_argument("--extension-output-dir", default=DEFAULT_EXTENSION_OUTPUTS, help="Output directory for the 2020-2026 extension figure and tables.")
    parser.add_argument("--download-extension-data", action="store_true", help="Refresh the NOAA extension data before plotting.")
    parser.add_argument("--extension-data-url", default=NOAA_EXTENSION_URL, help="NOAA GML monthly Mauna Loa CO2 CSV URL.")
    parser.add_argument("--no-extension", action="store_true", help="Only reproduce the original 2020 paper outputs.")
    parser.add_argument(
        "--include-partial-2020",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="For the 2020 model, include available non-missing 2020 observations. This matches the paper table most closely.",
    )
    parser.add_argument("--plot-start", type=float, default=1958.0)
    parser.add_argument("--plot-end", type=float, default=2050.0)
    parser.add_argument("--extension-start-year", type=int, default=2020)
    parser.add_argument("--extension-end-year", type=int, default=2026)
    return parser


def download_file(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "logistic-co2-reproduction/1.0"})
    try:
        with urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
    except URLError as error:
        if not isinstance(getattr(error, "reason", None), ssl.SSLCertVerificationError):
            raise
        context = ssl._create_unverified_context()
        with urlopen(request, context=context, timeout=60) as response:
            path.write_bytes(response.read())


def read_scripps_mlo(path: Path) -> list[Observation]:
    observations: list[Observation] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip().strip('"')
        if not stripped or not stripped[0].isdigit():
            continue

        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 10:
            continue

        co2_filled = float(parts[8])
        if co2_filled <= -90:
            continue

        observations.append(
            Observation(
                year=int(parts[0]),
                month=int(parts[1]),
                decimal_year=float(parts[3]),
                co2_filled_ppm=co2_filled,
            )
        )

    if not observations:
        raise ValueError(f"No usable observations found in {path}")

    return observations


def read_noaa_mlo(path: Path) -> list[Observation]:
    observations: list[Observation] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = [part.strip() for part in stripped.split(",")]
        if len(parts) < 4 or not parts[0].isdigit():
            continue

        co2_average = float(parts[3])
        if co2_average <= -90:
            continue

        observations.append(
            Observation(
                year=int(parts[0]),
                month=int(parts[1]),
                decimal_year=float(parts[2]),
                co2_filled_ppm=co2_average,
            )
        )

    if not observations:
        raise ValueError(f"No usable NOAA observations found in {path}")

    return observations


def training_window(
    observations: Iterable[Observation],
    model_year: int,
    include_partial_2020: bool,
) -> list[Observation]:
    if model_year == 2020 and include_partial_2020:
        return [obs for obs in observations if obs.year <= 2020]
    return [obs for obs in observations if obs.year < model_year]


def extension_window(
    observations: Iterable[Observation],
    start_year: int,
    end_year: int,
) -> list[Observation]:
    return [obs for obs in observations if start_year <= obs.year <= end_year]


def fit_curve(observations: list[Observation], model_year: int) -> CurveFit:
    finite_fit = fit_best_finite_smax(observations, model_year)
    exponential_fit = fit_exponential_limit(observations, model_year)

    if exponential_fit.r2 > finite_fit.r2:
        return exponential_fit
    return finite_fit


def fit_best_finite_smax(observations: list[Observation], model_year: int) -> CurveFit:
    maximum_observed = max(obs.co2_filled_ppm for obs in observations)
    lower = maximum_observed + 1e-6
    upper = 100_000.0

    grid = np.concatenate(
        [
            np.linspace(lower, 1200.0, 2400),
            np.geomspace(1200.0, upper, 1600),
        ]
    )
    scored = [(score_smax(observations, smax), float(smax)) for smax in grid]
    best_index = max(range(len(scored)), key=lambda index: scored[index][0])

    if best_index == 0 or best_index == len(scored) - 1:
        best_smax = scored[best_index][1]
    else:
        left = scored[best_index - 1][1]
        right = scored[best_index + 1][1]
        best_smax = golden_section_max(lambda value: score_smax(observations, value), left, right)

    return fit_for_smax(observations, model_year, best_smax)


def score_smax(observations: list[Observation], smax_ppm: float) -> float:
    try:
        return fit_for_smax(observations, 0, smax_ppm).r2
    except ValueError:
        return -math.inf


def fit_for_smax(observations: list[Observation], model_year: int, smax_ppm: float) -> CurveFit:
    years, co2 = arrays(observations)
    excess = co2 - BASELINE_PPM
    carrying_capacity = smax_ppm - BASELINE_PPM
    if np.any(excess <= 0) or np.any(excess >= carrying_capacity):
        raise ValueError("Smax must be above every observed CO2 value and baseline-adjusted CO2 must be positive")

    transformed = np.log(excess / (carrying_capacity - excess))
    b, c = ols_line(years, transformed)
    fitted_transformed = b * years + c
    r2 = r_squared(transformed, fitted_transformed)
    ti = -c / b
    predicted = predict_logistic_ppm(years, smax_ppm=smax_ppm, b=b, ti=ti)
    residuals = co2 - predicted

    return CurveFit(
        model_year=model_year,
        n_observations=len(observations),
        finite_saturation=True,
        smax_ppm=float(smax_ppm),
        b=float(b),
        c=float(c),
        ti=float(ti),
        r2=float(r2),
        rmse_ppm=float(np.sqrt(np.mean(residuals**2))),
        residual_sd_ppm=float(np.std(residuals, ddof=1)),
    )


def fit_exponential_limit(observations: list[Observation], model_year: int) -> CurveFit:
    years, co2 = arrays(observations)
    excess = co2 - BASELINE_PPM
    if np.any(excess <= 0):
        raise ValueError("Baseline-adjusted CO2 must be positive")

    logged = np.log(excess)
    b, c = ols_line(years, logged)
    predicted = BASELINE_PPM + np.exp(b * years + c)
    residuals = co2 - predicted

    return CurveFit(
        model_year=model_year,
        n_observations=len(observations),
        finite_saturation=False,
        smax_ppm=math.inf,
        b=float(b),
        c=float(c),
        ti=None,
        r2=float(r_squared(logged, b * years + c)),
        rmse_ppm=float(np.sqrt(np.mean(residuals**2))),
        residual_sd_ppm=float(np.std(residuals, ddof=1)),
    )


def arrays(observations: list[Observation]) -> tuple[np.ndarray, np.ndarray]:
    years = np.array([obs.decimal_year for obs in observations], dtype=float)
    co2 = np.array([obs.co2_filled_ppm for obs in observations], dtype=float)
    return years, co2


def ols_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    design = np.column_stack([x, np.ones_like(x)])
    slope, intercept = np.linalg.lstsq(design, y, rcond=None)[0]
    return float(slope), float(intercept)


def r_squared(observed: np.ndarray, fitted: np.ndarray) -> float:
    residual_sum = float(np.sum((observed - fitted) ** 2))
    total_sum = float(np.sum((observed - observed.mean()) ** 2))
    return 1.0 - residual_sum / total_sum


def golden_section_max(function, left: float, right: float, iterations: int = 80) -> float:
    inverse_phi = (math.sqrt(5.0) - 1.0) / 2.0
    inverse_phi_squared = (3.0 - math.sqrt(5.0)) / 2.0

    span = right - left
    left_probe = left + inverse_phi_squared * span
    right_probe = left + inverse_phi * span
    left_value = function(left_probe)
    right_value = function(right_probe)

    for _ in range(iterations):
        if left_value < right_value:
            left = left_probe
            left_probe = right_probe
            left_value = right_value
            span = right - left
            right_probe = left + inverse_phi * span
            right_value = function(right_probe)
        else:
            right = right_probe
            right_probe = left_probe
            right_value = left_value
            span = right - left
            left_probe = left + inverse_phi_squared * span
            left_value = function(left_probe)

    return (left + right) / 2.0


def predict_with_fit(years: np.ndarray, fit: CurveFit) -> np.ndarray:
    if fit.finite_saturation:
        assert fit.ti is not None
        return predict_logistic_ppm(years, fit.smax_ppm, fit.b, fit.ti)

    assert fit.c is not None
    return BASELINE_PPM + np.exp(fit.b * years + fit.c)


def predict_logistic_ppm(years: np.ndarray, smax_ppm: float, b: float, ti: float) -> np.ndarray:
    carrying_capacity = smax_ppm - BASELINE_PPM
    exponent = np.clip(-b * (years - ti), -700, 700)
    return BASELINE_PPM + carrying_capacity / (1.0 + np.exp(exponent))


def write_parameter_table(path: Path, fits: list[CurveFit]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "model_year",
            "n_observations",
            "smax_ppm",
            "b",
            "c",
            "ti",
            "r2",
            "rmse_ppm",
            "residual_sd_ppm",
            "paper_smax_ppm",
            "paper_b",
            "paper_c",
            "paper_ti",
            "paper_r2",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for fit in fits:
            paper = PAPER_TABLE[fit.model_year]
            writer.writerow(
                {
                    "model_year": fit.model_year,
                    "n_observations": fit.n_observations,
                    "smax_ppm": format_number(fit.smax_ppm),
                    "b": f"{fit.b:.8f}",
                    "c": format_number(fit.c),
                    "ti": format_number(fit.ti),
                    "r2": f"{fit.r2:.8f}",
                    "rmse_ppm": f"{fit.rmse_ppm:.8f}",
                    "residual_sd_ppm": f"{fit.residual_sd_ppm:.8f}",
                    "paper_smax_ppm": format_number(paper["smax"]),
                    "paper_b": format_number(paper["b"]),
                    "paper_c": format_number(paper["c"]),
                    "paper_ti": format_number(paper["ti"]),
                    "paper_r2": format_number(paper["r2"]),
                }
            )


def write_rmse_matrix(
    path: Path,
    observations: list[Observation],
    fits: list[CurveFit],
    include_partial_2020: bool,
) -> None:
    training_sets = {
        year: training_window(observations, year, include_partial_2020=include_partial_2020)
        for year in MODEL_YEARS
    }
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["data_year", *[str(fit.model_year) for fit in fits]])
        for data_year in MODEL_YEARS:
            data = training_sets[data_year]
            years, co2 = arrays(data)
            row = [data_year]
            for fit in fits:
                predicted = predict_with_fit(years, fit)
                row.append(f"{np.sqrt(np.mean((co2 - predicted) ** 2)):.3f}")
            writer.writerow(row)


def write_curve_points(path: Path, fits: list[CurveFit], start: float, end: float) -> None:
    years = np.linspace(start, end, int((end - start) * 12) + 1)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["decimal_year", *[f"model_{fit.model_year}_ppm" for fit in fits]])
        for year in years:
            row = [f"{year:.6f}"]
            for fit in fits:
                value = predict_with_fit(np.array([year]), fit)[0]
                row.append(f"{value:.6f}")
            writer.writerow(row)


def write_extension_comparison(path: Path, observations: list[Observation], fits: list[CurveFit]) -> None:
    years, co2 = arrays(observations)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "year",
                "month",
                "decimal_year",
                "observed_noaa_mlo_ppm",
                *[f"fixed_model_{fit.model_year}_ppm" for fit in fits],
            ]
        )
        predictions = [predict_with_fit(years, fit) for fit in fits]
        for index, obs in enumerate(observations):
            writer.writerow(
                [
                    obs.year,
                    obs.month,
                    f"{obs.decimal_year:.6f}",
                    f"{co2[index]:.6f}",
                    *[f"{prediction[index]:.6f}" for prediction in predictions],
                ]
            )


def write_figure(path: Path, observations: list[Observation], fits: list[CurveFit], start: float, end: float) -> None:
    colors = {
        2020: "#c44e52",
        2010: "#8db255",
        2000: "#8064a2",
        1990: "#4f81bd",
        1980: "#f28e2b",
        1970: "#1f4e79",
        1960: "#7f2f2a",
    }
    years, co2 = arrays(observations)
    plot_years = np.linspace(start, end, 1000)

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.plot(years, co2, color="black", linewidth=2.2, label="Measured CO2")

    for fit in fits:
        predicted = predict_with_fit(plot_years, fit)
        ax.plot(
            plot_years,
            predicted,
            color=colors.get(fit.model_year, "0.4"),
            linewidth=2.1,
            label=f"Predicted CO2 - {fit.model_year} Model",
        )

    ax.set_title("Measured and Modeled CO2 (ppm) over time")
    ax.set_xlim(1950, 2050)
    ax.set_ylim(280, 630)
    ax.set_xlabel("Year")
    ax.set_ylabel("CO2 (ppm)")
    ax.grid(True, color="#d9d9d9", linewidth=0.9)
    ax.legend(loc="center left", frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def write_extension_figure(
    path: Path,
    original_observations: list[Observation],
    extension_observations: list[Observation],
    fits: list[CurveFit],
    start: float,
    end: float,
) -> None:
    colors = {
        2020: "#c44e52",
        2010: "#8db255",
        2000: "#8064a2",
        1990: "#4f81bd",
        1980: "#f28e2b",
        1970: "#1f4e79",
        1960: "#7f2f2a",
    }
    original_years, original_co2 = arrays(original_observations)
    extension_years, extension_co2 = arrays(extension_observations)
    plot_years = np.linspace(start, end, 1000)

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.plot(original_years, original_co2, color="black", linewidth=2.2, label="Measured CO2 (2020 paper data)")
    ax.plot(
        extension_years,
        extension_co2,
        color="#d81b60",
        linewidth=2.4,
        marker="o",
        markersize=3.5,
        label="Observed CO2 extension (NOAA MLO, 2020-2026)",
    )

    for fit in fits:
        predicted = predict_with_fit(plot_years, fit)
        ax.plot(
            plot_years,
            predicted,
            color=colors.get(fit.model_year, "0.4"),
            linewidth=2.1,
            label=f"Predicted CO2 - {fit.model_year} Model",
        )

    last = extension_observations[-1]
    ax.set_title(f"Measured and Modeled CO2 (ppm) with 2020-2026 Extension through {last.year}-{last.month:02d}")
    ax.set_xlim(1950, 2050)
    ax.set_ylim(280, 630)
    ax.set_xlabel("Year")
    ax.set_ylabel("CO2 (ppm)")
    ax.grid(True, color="#d9d9d9", linewidth=0.9)
    ax.legend(loc="center left", frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def format_number(value: float | int | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isinf(value):
        return "inf"
    if isinstance(value, float):
        return f"{value:.8f}"
    return str(value)


def print_summary(fits: list[CurveFit]) -> None:
    print("model_year,n,smax_ppm,b,c,ti,r2,paper_smax")
    for fit in fits:
        print(
            ",".join(
                [
                    str(fit.model_year),
                    str(fit.n_observations),
                    format_number(fit.smax_ppm),
                    f"{fit.b:.4f}",
                    format_number(fit.c),
                    format_number(fit.ti),
                    f"{fit.r2:.3f}",
                    format_number(PAPER_TABLE[fit.model_year]["smax"]),
                ]
            )
        )


if __name__ == "__main__":
    main()
