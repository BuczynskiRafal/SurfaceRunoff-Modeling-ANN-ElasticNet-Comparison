import swmmio
import pandas as pd
import numpy as np

from pyswmm import Simulation
from swmmio.utils.dataframes import dataframe_from_inp
from swmmio.utils.modify_model import replace_inp_section
from swmmio.core import rpt


df = pd.DataFrame(
    columns=[
        "width",
        "percent_slope",
        "percent_impervious",
        "TotalInfil",
        "ImpervRunoff",
        "PervRunoff",
        "TotalRunoffMG",
    ]
)
model = swmmio.Model("example_copy.inp")
subcatchments = model.inp.subcatchments
subareas = model.inp.subareas
# manning_n = np.sort([0.011, 0.012, 0.013, 0.014, 0.015, 0.024, 0.05, 0.06, 0.17, 0.13, 0.15, 0.24, 0.41, 0.4, 0.8])
manning_n = [0.015, 0.24, 0.4, 0.8]
# manning_n = np.sort([0.011, 0.012])
destore = [0.05, 0.1, 0.2, 0.3]
# destore = np.array([0.1, 0.3])

width = []
slope = []
percent_impervious = []
n_imperv = []
n_perv = []
destore_iperv = []
destore_perv = []
zero_imperv = []
TotalInfil = []
ImpervRunoff = []
PervRunoff = []
TotalRunoffMG = []
for area in [1, 2, 3, 4, 5]:
    for w in [1, 250, 500, 750, 1000]:
        for s in range(0, 101, 20):
            for pi in range(0, 101, 20):
                for n_i in manning_n:
                    for n_p in manning_n:
                        for di in destore:
                            for dp in destore:
                                for zi in np.arange(0, 100, 20):
                                    width.append(w)
                                    slope.append(s)
                                    percent_impervious.append(pi)
                                    n_imperv.append(n_i)
                                    n_perv.append(n_p)
                                    destore_iperv.append(di)
                                    destore_perv.append(dp)
                                    zero_imperv.append(zi)
                                    subcatchments = dataframe_from_inp(
                                        "example_copy.inp", "[SUBCATCHMENTS]"
                                    )
                                    subcatchments.loc[
                                        "S1", ["Width", "PercSlope", "PercImperv"]
                                    ] = [w, s, pi]
                                    subareas = dataframe_from_inp(
                                        "example_copy.inp", "[SUBAREAS]"
                                    )
                                    subareas.loc[
                                        "S1",
                                        [
                                            "N-Imperv",
                                            "N-Perv",
                                            "S-Imperv",
                                            "S-Perv",
                                            "PctZero",
                                        ],
                                    ] = [n_i, n_p, di, dp, zi]
                                    replace_inp_section(
                                        "example_copy.inp", "[SUBCATCHMENTS]", subcatchments
                                    )
                                    replace_inp_section(
                                        "example_copy.inp", "[SUBAREAS]", subareas
                                    )
                                    with Simulation("example_copy.inp") as sim:
                                        for _ in sim:
                                            pass
                                    report = rpt("example_copy.rpt")
                                    TotalInfil.append(
                                        report.subcatchment_runoff_summary.loc["S1"][
                                            "TotalInfil"
                                        ]
                                    )
                                    ImpervRunoff.append(
                                        report.subcatchment_runoff_summary.loc["S1"][
                                            "ImpervRunoff"
                                        ]
                                    )
                                    PervRunoff.append(
                                        report.subcatchment_runoff_summary.loc["S1"][
                                            "PervRunoff"
                                        ]
                                    )
                                    TotalRunoffMG.append(
                                        report.subcatchment_runoff_summary.loc["S1"][
                                            "TotalRunoffMG"
                                        ]
                                    )
                    print(f"n_i: {n_i}")
                    print(f"cl: {pi}")
                    print(f"slope: {s}")
                    print(f"Loop: {w}")
df["width"] = width
df["percent_slope"] = slope
df["percent_impervious"] = percent_impervious
df["n_imperv"] = n_imperv
df["n_perv"] = n_perv
df["destore_iperv"] = destore_iperv
df["destore_perv"] = destore_perv
df["zero_imperv"] = zero_imperv
df["TotalInfil"] = TotalInfil
df["ImpervRunoff"] = ImpervRunoff
df["PervRunoff"] = PervRunoff
df["TotalRunoffMG"] = TotalRunoffMG

df.to_excel("data_.xlsx", index=False)


with Simulation("example_copy.inp") as sim:
    for _ in sim:
        pass
model = swmmio.Model("example_copy.inp")
data = model.subcatchments.dataframe.copy()

for area in [1, 2, 3, 4, 5]:
    for w in [1, 250, 500, 750, 1000]:
        for s in range(0, 101, 20):
            for pi in range(0, 101, 20):
                for n_i in manning_n:
                    for n_p in manning_n:
                        for di in destore:
                            for dp in destore:
                                for zi in np.arange(0, 100, 20):
                                    subcatchments = dataframe_from_inp( "example_copy.inp", "[SUBCATCHMENTS]" ) 
                                    subcatchments.loc[ "S1", ["Width", "PercSlope", "PercImperv"] ] = [w, s, pi]
                                    subareas = dataframe_from_inp( "example_copy.inp", "[SUBAREAS]" )
                                    subareas.loc[ "S1", [ "N-Imperv", "N-Perv", "S-Imperv", "S-Perv", "PctZero", ], ] = [n_i, n_p, di, dp, zi]
                                    replace_inp_section( "example_copy.inp", "[SUBCATCHMENTS]", subcatchments )
                                    replace_inp_section( "example_copy.inp", "[SUBAREAS]", subareas )
                                    with Simulation("example_copy.inp") as sim:
                                        for _ in sim:
                                            pass
                                    df = model.subcatchments.dataframe
                                    data = pd.concat([data, df], ignore_index=True)
                                    print(data.head())
                    print(f"n_i: {n_i}")
                    print(f"cl: {pi}")
                    print(f"slope: {s}")
                    print(f"Loop: {w}")

                    
                    
