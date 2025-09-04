from __future__ import annotations
import json, pathlib
import pandas as pd
import plotly.express as px

HIST_DIR = pathlib.Path("benchmarks/history")
DOCS = pathlib.Path("docs")
DOCS.mkdir(exist_ok=True)

def flatten_rows() -> pd.DataFrame:
    rows = []
    for f in HIST_DIR.glob("*.json"):
        dataset = f.stem
        arr = json.loads(f.read_text())
        for rec in arr:
            row = {
                "dataset": dataset,
                "timestamp": rec.get("timestamp"),
                "fastoma_commit": rec.get("fastoma_commit"),
                "step": rec.get("step", "n/a"),
            }
            for k, v in rec.get("metrics", {}).items():
                row[k] = v
            rows.append(row)
    df = pd.DataFrame(rows)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

df = flatten_rows()
print(df.describe())
print(f"Loaded {len(df)} records")
df.sort_values(["dataset", "step", "timestamp"], inplace=True)

# Metrics you want to expose
metrics = [
    "elapsed_sec", "user_sec", "sys_sec",
    "max_rss_kb", "fraction_placed", "n_passed"
]
metrics = [m for m in metrics if m in df.columns]

# Build one graph with dropdowns
# (two dropdowns: dataset multi-select and metric select)
datasets = sorted(df["dataset"].unique().tolist())

figs_html = []
for step in sorted(df["step"].unique()):
    dstep = df[df["step"] == step]
    fig = px.line(
        dstep,
        x="timestamp",
        y=metrics[0],
        color="dataset",
        hover_data=["fastoma_commit"],
        title=f"{step} metrics over time"
    )
    # metric selector
    fig.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {
                        "label": m,
                        "method": "update",
                        "args": [
                            {"y": [dstep[m]]},
                            {"yaxis": {"title": m}, "title": f"{step}: {m} over time"}
                        ],
                    } for m in metrics
                ],
                "direction": "down",
                "x": 0.0, "y": 1.15, "xanchor": "left"
            }
        ]
    )
    figs_html.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))

html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>FastOMA Benchmarks</title></head>
<body style="max-width:1100px;margin:40px auto;font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
  <h1>FastOMA Benchmarks</h1>
  <p>Interactive, asv-inspired dashboard tracking performance & quality over time.</p>
  <p><b>Datasets:</b> {len(datasets)} | <b>Records:</b> {len(df)}</p>
  {''.join(figs_html)}
  <hr/>
  <p>Last build includes commits through: {df['fastoma_commit'].dropna().iloc[-1] if len(df) else 'n/a'}</p>
</body></html>
"""
(DOCS / "index.html").write_text(html)
print("Dashboard written to docs/index.html")