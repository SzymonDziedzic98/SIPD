"""Sprawdzian P1: długie przebiegi (100 000 cykli), prędkość 0,1, mutacja 0,01, N=200.
Użycie: python web/p1_long_check.py (ok. 5 min na 4 rdzeniach)."""
import os, sys, statistics as st
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sipd
def job(a):
    preset, seed = a
    p = dict(sipd.BATCH_EXPERIMENTS["S1_P1_mobility"]["params"], player_speed=0.1, mutation_rate=0.01,
             payoff_preset=preset, compat_N=200, end_cycle=100000, synthetic_grid=sipd.park_grid_for(200))
    m = sipd.Model(sipd.Params(**p), seed=seed)
    m.run(100001)
    ts = m.timeseries_rows
    idx = sipd.CSV_HEADERS["character_timeseries.csv"].index("share_ALLD")
    w = lambda a, b: st.mean(r[idx] for r in ts if a < r[8] <= b)
    return preset, seed, [round(w(c, c + 10000), 2) for c in range(0, 100000, 10000)], m.compat_rows[0]
if __name__ == "__main__":
    jobs = [(pr, s) for pr in ("PD_classic", "weak_PD", "snowdrift") for s in (11, 22)]
    with Pool(4) as pool:
        for preset, seed, traj, row in pool.imap_unordered(job, jobs):
            H = sipd.COMPAT_HEADER
            print(f"{preset:10s} seed {seed}: ALLD co 10k cykli {traj} | stabilizacja {row[H.index('stabilized')]} od {row[H.index('stabilized_at')]} | D {row[H.index('d_share')]:.2f}", flush=True)
