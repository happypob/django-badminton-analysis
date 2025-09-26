
#!/usr/bin/env python3
"""analyze_sensor_csv.py

Usage:
    python analyze_sensor_csv.py path/to/your.csv [--json-col G]

If no CSV is provided, a small synthetic demo will run and outputs will be written to ./sensor_analysis_outputs/ (in the current working directory).

Outputs (when run):
    - ./sensor_analysis_outputs/acc_magnitude_all_sensors.png
    - ./sensor_analysis_outputs/gyro_magnitude_all_sensors.png
    - ./sensor_analysis_outputs/peak_pair_report.csv
    - ./sensor_analysis_outputs/peak_summary.csv

Dependencies: pandas, numpy, matplotlib. scipy optional (for better peak detection).
"""

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
# Import matplotlib as mpl to allow backend selection at runtime
import matplotlib as mpl
# Use a non-interactive backend so plotting works on systems without a display (Windows headless, servers)
mpl.use('Agg')
# Delay importing pyplot until runtime so we can switch backend in main()
plt = None

try:
    from scipy.signal import find_peaks, peak_prominences
    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False

OUTPUT_DIR = Path.cwd() / "sensor_analysis_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def parse_json_column(df, col_candidates=None):
    cols = df.columns.tolist()
    if col_candidates:
        cols = [c for c in col_candidates if c in df.columns] + [c for c in df.columns if c not in (col_candidates or [])]
    json_col = None
    for c in cols:
        sample = df[c].dropna().astype(str).head(40).tolist()
        if not sample:
            continue
        if all(s.strip().startswith("{") and ("sensor_id" in s or '"sensor_id"' in s) for s in sample):
            json_col = c
            break
    if json_col is None:
        raise ValueError("Can't find JSON column automatically. Please supply the column name.")
    records = []
    for idx, s in df[json_col].astype(str).items():
        try:
            obj = json.loads(s)
        except Exception:
            try:
                obj = json.loads(s.replace("'", '"'))
            except Exception:
                obj = {}
        rec = {
            "_row_index": idx,
            "sensor_id": obj.get("sensor_id", None),
            "raw_timestamp": obj.get("timestamp", None),
        }
        for vec in ("acc", "gyro", "angle"):
            vals = obj.get(vec, [None, None, None])
            if vals is None:
                vals = [None, None, None]
            rec.update({f"{vec}_x": vals[0], f"{vec}_y": vals[1], f"{vec}_z": vals[2]})
        records.append(rec)
    parsed = pd.DataFrame.from_records(records)
    return parsed, json_col

def parse_timestamp_hhmmssmmm(ts):
    if ts is None or (isinstance(ts, float) and np.isnan(ts)):
        return np.nan
    s = str(int(ts))
    s = s.zfill(9)
    try:
        hh = int(s[0:2])
        mm = int(s[2:4])
        ss = int(s[4:6])
        mmm = int(s[6:9])
    except Exception:
        try:
            return float(ts)
        except Exception:
            return np.nan
    return hh * 3600 + mm * 60 + ss + mmm / 1000.0

def magnitude(df, prefix):
    arr = df[[f"{prefix}_x", f"{prefix}_y", f"{prefix}_z"]].to_numpy(dtype=float)
    return np.linalg.norm(arr, axis=1)

def detect_peaks_simple(y):
    y = np.asarray(y, dtype=float)
    if y.size < 3:
        return np.array([], dtype=int)
    peaks = np.where((y[1:-1] > y[:-2]) & (y[1:-1] > y[2:]))[0] + 1
    return peaks

def detect_peaks(y, prominence=0.3, distance=None):
    if SCIPY_AVAILABLE:
        peaks, props = find_peaks(y, prominence=prominence, distance=distance)
        prominences = peak_prominences(y, peaks)[0] if len(peaks)>0 else np.array([])
        return peaks, prominences
    else:
        peaks = detect_peaks_simple(y)
        prominences = np.array([y[p] - 0.5*(y[p-1]+y[p+1]) if 0<p<len(y)-1 else 0 for p in peaks])
        return peaks, prominences

def nearest_indices(times_ref, times_query):
    times_ref = np.asarray(times_ref)
    times_query = np.asarray(times_query)
    idxs = np.searchsorted(times_ref, times_query)
    res = []
    for i, q in enumerate(times_query):
        j = idxs[i]
        choices = []
        if j-1 >= 0:
            choices.append(j-1)
        if j < len(times_ref):
            choices.append(j)
        if not choices:
            res.append(None)
        else:
            best = min(choices, key=lambda c: abs(times_ref[c]-q))
            res.append(best)
    return np.array([None if r is None else int(r) for r in res], dtype=object)

def analyze_dataframe(raw_df, json_col_hint=None):
    parsed, json_col = parse_json_column(raw_df, col_candidates=[json_col_hint] if json_col_hint else None)
    parsed["time_s"] = parsed["raw_timestamp"].apply(parse_timestamp_hhmmssmmm)
    parsed = parsed.sort_values("time_s").reset_index(drop=True)
    parsed["acc_mag"] = magnitude(parsed, "acc")
    parsed["gyro_mag"] = magnitude(parsed, "gyro")
    sensors = parsed["sensor_id"].unique().tolist()
    sensor_groups = {sid: parsed[parsed["sensor_id"]==sid].reset_index(drop=True) for sid in sensors}
    # Compute union time window that covers all sensors (uses available data)
    starts = []
    ends = []
    for sid, df_s in sensor_groups.items():
        if df_s.shape[0] >= 1:
            starts.append(df_s["time_s"].min())
            ends.append(df_s["time_s"].max())
    if not starts:
        raise ValueError("No sensor time data available to analyze")
    master_start = float(min(starts))
    master_end = float(max(ends))
    # Trim each sensor group's data to the union window (keep those parts that fall into the union)
    for sid, df_s in sensor_groups.items():
        mask = (df_s["time_s"] >= master_start) & (df_s["time_s"] <= master_end)
        sensor_groups[sid] = df_s.loc[mask].reset_index(drop=True)
    # Plot acc magnitude
    plt.figure(figsize=(10,4))
    for sid, df_s in sensor_groups.items():
        plt.plot(df_s["time_s"] - master_start, df_s["acc_mag"], label=f"ID{sid}")
    plt.xlabel("time (s) from master start")
    plt.ylabel("acc magnitude")
    plt.title("Acceleration magnitude - all sensors (aligned to master window)")
    plt.legend()
    acc_plot_path = OUTPUT_DIR / "acc_magnitude_all_sensors.png"
    plt.savefig(acc_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    # Plot gyro magnitude
    plt.figure(figsize=(10,4))
    for sid, df_s in sensor_groups.items():
        plt.plot(df_s["time_s"] - master_start, df_s["gyro_mag"], label=f"ID{sid}")
    plt.xlabel("time (s) from master start")
    plt.ylabel("gyro magnitude")
    plt.title("Gyro magnitude - all sensors (aligned to master window)")
    plt.legend()
    gyro_plot_path = OUTPUT_DIR / "gyro_magnitude_all_sensors.png"
    plt.savefig(gyro_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    # Peak detection & pairing
    report_rows = []
    for sid, df_s in sensor_groups.items():
        times = df_s["time_s"].to_numpy()
        acc_y = df_s["acc_mag"].to_numpy()
        gyro_y = df_s["gyro_mag"].to_numpy()
        acc_peaks, acc_prom = detect_peaks(acc_y, prominence=max(0.05, np.std(acc_y)*0.5))
        gyro_peaks, gyro_prom = detect_peaks(gyro_y, prominence=max(0.05, np.std(gyro_y)*0.5))
        if len(gyro_peaks) > 0 and len(acc_peaks) > 0:
            nearest_idx = nearest_indices(times[gyro_peaks], times[acc_peaks])
        else:
            nearest_idx = np.array([None]*len(acc_peaks), dtype=object)
        for i_ap, ap in enumerate(acc_peaks):
            t_acc = float(times[ap])
            a_val = float(acc_y[ap])
            nearest = nearest_idx[i_ap]
            if nearest is None:
                t_gyro = np.nan
                g_val = np.nan
                dt = np.nan
            else:
                gp = gyro_peaks[int(nearest)]
                t_gyro = float(times[gp])
                g_val = float(gyro_y[gp])
                dt = t_acc - t_gyro
            report_rows.append({
                "sensor_id": sid,
                "acc_peak_idx": int(ap),
                "acc_peak_time": t_acc,
                "acc_peak_value": a_val,
                "gyro_peak_time": t_gyro,
                "gyro_peak_value": g_val,
                "time_diff_acc_minus_gyro_s": dt
            })
    report_df = pd.DataFrame.from_records(report_rows)
    report_csv_path = OUTPUT_DIR / "peak_pair_report.csv"
    report_df.to_csv(report_csv_path, index=False)
    summary_rows = []
    for sid, df_s in sensor_groups.items():
        sub = report_df[report_df["sensor_id"]==sid]
        if sub.empty:
            summary_rows.append({"sensor_id": sid, "n_pairs": 0, "mean_dt_s": np.nan, "median_dt_s": np.nan})
        else:
            summary_rows.append({"sensor_id": sid, "n_pairs": sub.shape[0], "mean_dt_s": float(sub["time_diff_acc_minus_gyro_s"].dropna().mean()), "median_dt_s": float(sub["time_diff_acc_minus_gyro_s"].dropna().median())})
    summary_df = pd.DataFrame.from_records(summary_rows)
    summary_csv_path = OUTPUT_DIR / "peak_summary.csv"
    summary_df.to_csv(summary_csv_path, index=False)
    return {
        # we now use a union window across sensors rather than a single master sensor
        "master_sensor": "union",
        "master_start": master_start,
        "master_end": master_end,
        "acc_plot": str(acc_plot_path),
        "gyro_plot": str(gyro_plot_path),
        "report_csv": str(report_csv_path),
        "summary_csv": str(summary_csv_path),
        "summary_df": summary_df,
        "report_df_head": report_df.head(20)
    }

def demo_run():
    # small synthetic demo - replace in real use
    import numpy as np, pandas as pd, json
    np.random.seed(2)
    def make_sensor_series(sensor_id, start_s, duration_s, fs=100, shift_phase=0.0):
        n = int(duration_s * fs)
        t = np.linspace(start_s, start_s + duration_s, n, endpoint=False)
        acc = 1.5 * (np.sin(2*np.pi*2*(t-start_s) + shift_phase) + 0.3*np.random.randn(n))
        gyro = 40 * (np.sign(np.sin(2*np.pi*1*(t-start_s) + shift_phase)) + 0.2*np.random.randn(n))
        acc_x = acc + 0.1*np.random.randn(n)
        acc_y = 0.6*acc + 0.1*np.random.randn(n)
        acc_z = 0.2*acc + 0.05*np.random.randn(n)
        gyro_x = gyro + 2*np.random.randn(n)
        gyro_y = 0.5*gyro + 1*np.random.randn(n)
        gyro_z = 0.2*gyro + 0.5*np.random.randn(n)
        rows = []
        for i in range(n):
            hh = int(t[i] // 3600) % 24
            mm = int((t[i] % 3600) // 60)
            ss = int(t[i] % 60)
            mmm = int(round((t[i] - np.floor(t[i]))*1000))
            ts_int = int(f"{hh:02d}{mm:02d}{ss:02d}{mmm:03d}")
            obj = {
                "acc": [float(acc_x[i]), float(acc_y[i]), float(acc_z[i])],
                "gyro": [float(gyro_x[i]), float(gyro_y[i]), float(gyro_z[i])],
                "angle": [0.0, 0.0, 0.0],
                "sensor_id": int(sensor_id),
                "timestamp": ts_int
            }
            rows.append(json.dumps(obj))
        return pd.Series(rows)
    s1 = make_sensor_series(1, start_s=16*3600 + 20*60 + 0.0, duration_s=3.0, fs=100, shift_phase=0.0)
    s2 = make_sensor_series(2, start_s=16*3600 + 20*60 + 0.05, duration_s=2.8, fs=100, shift_phase=0.2)
    s3 = make_sensor_series(3, start_s=16*3600 + 20*60 + 0.10, duration_s=2.6, fs=100, shift_phase=0.4)
    s4 = make_sensor_series(4, start_s=16*3600 + 20*60 + 0.02, duration_s=2.9, fs=100, shift_phase=0.1)
    combined = pd.concat([s1, s2, s3, s4], ignore_index=True)
    demo_df = pd.DataFrame({"idx": range(len(combined)), "G": combined})
    return analyze_dataframe(demo_df, json_col_hint="G")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', nargs='?', help='path to CSV file with JSON column (if omitted, run demo)')
    parser.add_argument('--json-col', default='G', help='hint for JSON column name (default: G)')
    parser.add_argument('--interactive', action='store_true', help='open interactive plotting windows (requires a GUI backend)')
    args = parser.parse_args()
    # Configure matplotlib backend according to interactive flag before importing pyplot
    if args.interactive:
        try:
            mpl.use('TkAgg')
        except Exception:
            print('Warning: could not use TkAgg backend, falling back to Agg (non-interactive)')
            mpl.use('Agg')
    else:
        mpl.use('Agg')
    # import pyplot into the module-global name so analyze_dataframe can use it
    global plt
    import matplotlib.pyplot as _plt
    plt = _plt
    if args.csv:
        raw_df = pd.read_csv(args.csv, dtype=str)
        res = analyze_dataframe(raw_df, json_col_hint=args.json_col)
    else:
        print(f'No CSV supplied — running a small demo and saving outputs to {OUTPUT_DIR}')
        res = demo_run()
    print('Done. Results:')
    print('Master sensor:', res['master_sensor'])
    print('Master window start:', res['master_start'], 'end:', res['master_end'])
    print('acc plot:', res['acc_plot'])
    print('gyro plot:', res['gyro_plot'])
    print('report csv:', res['report_csv'])
    print('summary csv:', res['summary_csv'])

if __name__ == '__main__':
    main()
