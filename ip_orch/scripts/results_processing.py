import pandas as pd

cols = ["model", "index", "element", "energy", "status", "error"]

df = pd.read_csv("isolated_atom_energies.csv", header=0, names=cols)

df.columns = df.columns.str.strip()
df["status"] = df["status"].astype(str).str.strip().str.lower()
df["energy"] = pd.to_numeric(df["energy"], errors="coerce")

filtered = df[df["status"] == "ok"]

aux = df[
    (df["model"] != "grace-1l-oam")
    & (df["model"] != "grace-2l-mp-r6")
    & (df["model"] != "grace-2l-oam")
    & (df["model"] != "matris-10m-mp")
    & (df["model"] != "matris-10m-oam")
    & (df["model"] != "m3gnet")
]

final = (
    aux.pivot(index=["index", "element"], columns="model", values="energy").reset_index().sort_values("index").round(4)
)

final.to_csv("reference_energies.csv", index=False)
