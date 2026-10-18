"""Synthetic EPA SWMM subcatchment dataset generator for surface runoff modeling.

Generates the parametric simulation dataset (`dataset.xlsx`) used in:
Dawidowicz, J.; Buczyński, R. (2025). Comparison of the Effectiveness of
Artificial Neural Networks and Elastic Net Regression in Surface Runoff
Modeling. Water, 17(3), 405. https://doi.org/10.3390/w17030405
"""

from __future__ import annotations

import argparse
import itertools
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pyswmm import Simulation
from swmmio.core import rpt
from swmmio.utils.dataframes import dataframe_from_inp
from swmmio.utils.modify_model import replace_inp_section


@dataclass(frozen=True)
class SubcatchmentGrid:
    """Parameter grid for EPA SWMM subcatchment sensitivity sweep."""

    areas: tuple[float, ...] = (1.0, 2.0, 3.0, 4.0, 5.0)
    widths: tuple[int, ...] = (1, 250, 500, 750, 1000)
    slopes: tuple[int, ...] = field(default_factory=lambda: tuple(range(0, 101, 20)))
    imperviousness: tuple[int, ...] = field(default_factory=lambda: tuple(range(0, 101, 20)))
    manning_n: tuple[float, ...] = (0.015, 0.24, 0.4, 0.8)
    depression_storage: tuple[float, ...] = (0.05, 0.1, 0.2, 0.3)
    pct_zero_imperv: tuple[int, ...] = field(default_factory=lambda: tuple(range(0, 100, 20)))


def generate_runoff_dataset(
    template_inp: Path,
    output_excel: Path,
    subcatchment_id: str = "S1",
    grid: SubcatchmentGrid | None = None,
) -> pd.DataFrame:
    """Run EPA SWMM simulations across the parameter grid and export results.

    Reads the base `[SUBCATCHMENTS]` and `[SUBAREAS]` sections once into memory,
    updates the working `.inp` copy in place for each parameter combination,
    and accumulates runoff summary metrics in a list buffer before constructing
    the final DataFrame in a single pass.
    """
    active_grid = grid or SubcatchmentGrid()
    work_inp = template_inp.with_name(f"{template_inp.stem}_work.inp")
    work_rpt = work_inp.with_suffix(".rpt")
    shutil.copyfile(template_inp, work_inp)

    base_subcatchments = dataframe_from_inp(str(work_inp), "[SUBCATCHMENTS]")
    base_subareas = dataframe_from_inp(str(work_inp), "[SUBAREAS]")

    records: list[dict[str, float]] = []
    combinations = itertools.product(
        active_grid.areas,
        active_grid.widths,
        active_grid.slopes,
        active_grid.imperviousness,
        active_grid.manning_n,
        active_grid.manning_n,
        active_grid.depression_storage,
        active_grid.depression_storage,
        active_grid.pct_zero_imperv,
    )

    for area, width, slope, perc_imperv, n_imperv, n_perv, s_imperv, s_perv, pct_zero in combinations:
        base_subcatchments.loc[
            subcatchment_id, ["Area", "Width", "PercSlope", "PercImperv"]
        ] = [area, width, slope, perc_imperv]
        base_subareas.loc[
            subcatchment_id, ["N-Imperv", "N-Perv", "S-Imperv", "S-Perv", "PctZero"]
        ] = [n_imperv, n_perv, s_imperv, s_perv, pct_zero]

        replace_inp_section(str(work_inp), "[SUBCATCHMENTS]", base_subcatchments)
        replace_inp_section(str(work_inp), "[SUBAREAS]", base_subareas)

        with Simulation(str(work_inp)) as sim:
            for _ in sim:
                pass

        report = rpt(str(work_rpt))
        summary = report.subcatchment_runoff_summary.loc[subcatchment_id]
        records.append(
            {
                "Area": float(area),
                "Width": int(width),
                "PercSlope": int(slope),
                "PercImperv": int(perc_imperv),
                "N-Imperv": float(n_imperv),
                "N-Perv": float(n_perv),
                "S-Imperv": float(s_imperv),
                "S-Perv": float(s_perv),
                "PctZero": int(pct_zero),
                "TotalInfil": float(summary["TotalInfil"]),
                "ImpervRunoff": float(summary["ImpervRunoff"]),
                "PervRunoff": float(summary["PervRunoff"]),
                "TotalRunoffMG": float(summary["TotalRunoffMG"]),
            }
        )

    df = pd.DataFrame.from_records(records)
    df.to_excel(output_excel, index=False)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic EPA SWMM surface runoff dataset."
    )
    parser.add_argument(
        "--inp",
        type=Path,
        default=Path("example_copy.inp"),
        help="Path to the template EPA SWMM .inp file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dataset.xlsx"),
        help="Output Excel path for the generated dataset.",
    )
    parser.add_argument(
        "--subcatchment",
        type=str,
        default="S1",
        help="Target subcatchment identifier in the SWMM model.",
    )
    args = parser.parse_args()
    generate_runoff_dataset(
        template_inp=args.inp,
        output_excel=args.output,
        subcatchment_id=args.subcatchment,
    )


if __name__ == "__main__":
    main()
