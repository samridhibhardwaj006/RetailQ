from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    out = ROOT / "data" / "online_retail.csv"
    out.parent.mkdir(exist_ok=True)
    if out.exists():
        print(f"Dataset already exists: {out}")
        return
    try:
        from ucimlrepo import fetch_ucirepo
        ds = fetch_ucirepo(id=352)
        frame = ds.data.features.copy()
        if ds.data.targets is not None:
            for col in ds.data.targets.columns:
                if col not in frame:
                    frame[col] = ds.data.targets[col]
        frame.to_csv(out, index=False)
        print(f"Downloaded {len(frame):,} rows to {out}")
    except Exception as exc:
        print("Could not fetch UCI dataset:", exc)
        print("RetailIQ will use its labelled synthetic fallback dataset.")
        print("Install ucimlrepo and retry: pip install ucimlrepo")

if __name__ == "__main__":
    main()
