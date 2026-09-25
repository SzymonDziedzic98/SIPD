"""
Etap 1 (walidacja pojedyncza P1, P2, P3) na porcie Pythona + werdykty.

Uruchamia eksperymenty S1_P12_space, S1_P12_wellmixed, S1_P3_space, S1_P3_wellmixed (te same co
w PD.gaml), równolegle na wielu rdzeniach. Park syntetyczny skaluje się z N (stała gęstość);
w GAMA park jest stały (drogi.geojson), więc gęstość rośnie z N.

    python web/stage1.py --N 200 --repeat 5 --out results/compat_results.csv
    python web/stage1.py --verdict results/compat_results.csv > docs/stage1_verdict.md

Kryteria werdyktów (FIX = 0.05, zob. docs/gamadays.md):
- P1: w przebiegu z ewolucją udział ALLD i udział D (ostatnie okno 1000 cykli) leżą w (FIX, 1-FIX),
  a przebieg się ustabilizował: nachylenie prostej dopasowanej do udziału ALLD w 2. połowie przebiegu
  ma |nachylenie| < 0,02 na 10 000 cykli. "tak" gdy spełnia >= 80% powtórzeń, "nie" gdy <= 20%, inaczej "warunkowo".
- P2: mutation_rate = 0 -> ALLC wymiera (udział < 1/N) w >= 80% powtórzeń; mutation_rate > 0 ->
  ALLC obecny (> 0) w >= 80% powtórzeń i średnio <= 0.2. "tak" gdy obie części, "warunkowo" gdy jedna.
- P3: zysk oszustów = wypłata ALLD na grę przy limicie L minus przy braku limitu; istotny, gdy
  95% przedział ufności różnicy jest > 0. "tak" gdy istotny przy L=5 i średni zysk nie rośnie
  z L (5 >= 15 >= 50), "warunkowo" gdy istotny tylko częściowo, "nie" gdy nieistotny przy L=5.
  Próg = największy L z istotnym zyskiem. Raportowane też: czy limit działa (distinct > L).
- Etap 2 (S2_pairs, ewolucja + limit): P1 i P2 jak wyżej, osobno dla każdego limitu. P3 w ewolucji =
  udział ALLD przy limicie L większy niż bez limitu (95% CI różnicy > 0). Zgodność pary = obie
  predykcje z pary utrzymują się przy tym samym limicie.
"""
import argparse
import csv
import itertools
import math
import os
import random
import statistics as st
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sipd  # noqa: E402

STAGE1 = ["S1_P12_space", "S1_P12_wellmixed", "S1_P1_mobility", "S1_P3_space", "S1_P3_wellmixed"]
STAGE2 = ["S2_pairs"]
FIX = 0.05


def build_jobs(names, n_values, repeat, end_cycle):
    jobs = []
    for name in names:
        spec = sipd.BATCH_EXPERIMENTS[name]
        among = dict(spec["among"])
        among["compat_N"] = [n for n in among["compat_N"] if n in n_values]
        seeder = random.Random(spec["seed"])
        seeds = [seeder.randrange(2 ** 31) for _ in range(repeat)]   # keep_seed: te same dla kombinacji
        for vals in itertools.product(*among.values()):
            combo = dict(zip(among.keys(), vals))
            params = dict(spec["params"], **combo)
            if end_cycle:
                params["end_cycle"] = end_cycle
            params["synthetic_grid"] = sipd.park_grid_for(params["compat_N"])
            for s in seeds:
                jobs.append((params, s))
    return jobs


def run_job(job):
    params, seed = job
    m = sipd.Model(sipd.Params(**params), seed=seed)
    m.run(params["end_cycle"] + 1)   # until: cycle > end_cycle
    return m.compat_rows, m.timeseries_rows


def run(args):
    jobs = build_jobs(args.experiments, set(args.N), args.repeat, args.end_cycle)
    jobs.sort(key=lambda j: -(j[0]["compat_N"] * (4 if j[0]["well_mixed"] else 1)))   # najdroższe najpierw
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    t0 = time.time()
    ts_out = args.ts_out or args.out.replace(".csv", "_timeseries.csv")
    with open(args.out, "w", newline="", encoding="utf-8") as f, \
            open(ts_out, "w", newline="", encoding="utf-8") as ft, Pool(args.workers) as pool:
        w, wt = csv.writer(f), csv.writer(ft)
        w.writerow(sipd.COMPAT_HEADER)
        wt.writerow(sipd.CSV_HEADERS["character_timeseries.csv"])
        for i, (rows, ts) in enumerate(pool.imap_unordered(run_job, jobs), 1):
            w.writerows(rows)
            wt.writerows(ts)
            f.flush()
            ft.flush()
            print("[%d/%d] %.0f s" % (i, len(jobs), time.time() - t0), flush=True)
    print("zapisano", args.out, "i", ts_out)


# ---------------------------------------------------------------------------
# werdykty
# ---------------------------------------------------------------------------

def load(path):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k, v in r.items():
            if v in ("True", "False", "true", "false"):
                r[k] = v.lower() == "true"
            else:
                try:
                    r[k] = float(v)
                except ValueError:
                    pass
    return rows


def ms(xs):
    return (st.mean(xs), st.stdev(xs) if len(xs) > 1 else 0.0)


def fmt(xs, d=2):
    m, s = ms(xs)
    return "%.*f ± %.*f" % (d, m, d, s)


def share_verdict(frac):
    return "tak" if frac >= 0.8 else ("nie" if frac <= 0.2 else "warunkowo")


def verdict(path):
    rows = load(path)
    space = lambda r: "well_mixed" if r["well_mixed"] else "przestrzeń"
    out = ["# Etap 1 – werdykty (port Pythona)", "",
           "Źródło: `%s`, %d przebiegów. Wartości: średnia ± odchylenie standardowe między powtórzeniami." % (
               os.path.basename(path), len(rows)), ""]

    p12 = [r for r in rows if r["prediction"] == "P1P2"]
    if p12:
        out += ["## P1 – oszuści stabilni w (0, 1), P2 – altruiści", "",
                "| układ | macierz | N | prędkość | mutacja | n | gier/partnera | ALLD | udział D | ALLC | trend ALLD /10k | stabilizacja | P1 | P2 (część) |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        p2_parts = {}
        keyf = lambda r: (space(r), r["payoff_preset"], int(r["compat_N"]), r.get("player_speed", 2.0),
                          r["mutation_rate"])
        for key, grp in itertools.groupby(sorted(p12, key=keyf), key=keyf):
            g = list(grp)
            n = len(g)
            ok1 = [FIX < r["share_ALLD"] < 1 - FIX and FIX < r["d_share"] < 1 - FIX and r["stabilized"] for r in g]
            v1 = share_verdict(sum(ok1) / n)
            if key[4] == 0:
                ok2 = [r["share_ALLC"] < 1.0 / r["compat_N"] for r in g]
                v2 = share_verdict(sum(ok2) / n)
                part = "wymiera: " + v2
            else:
                ok2 = [r["share_ALLC"] > 0 for r in g]
                v2 = "tak" if (sum(ok2) / n >= 0.8 and st.mean(r["share_ALLC"] for r in g) <= 0.2) else \
                    ("nie" if sum(ok2) / n <= 0.2 else "warunkowo")
                part = "utrzymuje się: " + v2
            p2_parts.setdefault(key[:4], []).append(v2)
            out.append("| %s | %s | %d | %g | %g | %d | %s | %s | %s | %s | %s | %d%% | %s | %s |" % (
                key[0], key[1], key[2], key[3], key[4], n, fmt([r["games_per_partner"] for r in g], 1),
                fmt([r["share_ALLD"] for r in g]),
                fmt([r["d_share"] for r in g]), fmt([r["share_ALLC"] for r in g], 3),
                fmt([r["alld_trend_10k"] for r in g], 3),
                round(100 * sum(r["stabilized"] for r in g) / n), v1, part))
        out += ["", "**P2 łącznie** (obie części muszą się utrzymać):", ""]
        for key, parts in sorted(p2_parts.items()):
            v = "tak" if all(p == "tak" for p in parts) else ("nie" if all(p == "nie" for p in parts) else "warunkowo")
            out.append("- %s, %s, N=%d, prędkość %g: **%s**" % (key[0], key[1], key[2], key[3], v))
        out.append("")

    p3 = [r for r in rows if r["prediction"] == "P3"]
    if p3:
        out += ["## P3 – limit Dunbara: zysk oszustów", "",
                "| układ | macierz | N | limit | n | różnych partnerów | limit działa | ALLD / grę | zysk vs brak limitu (95% CI) | TFT / grę | udział D |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        summary = []
        keyf = lambda r: (space(r), r["payoff_preset"], int(r["compat_N"]))
        for key, grp in itertools.groupby(sorted(p3, key=keyf), key=keyf):
            g = list(grp)
            base = [r["payoff_ALLD"] for r in g if r["dunbar_limit"] == 0]
            gains, signif = {}, {}
            for lim in sorted({int(r["dunbar_limit"]) for r in g}):
                gl = [r for r in g if int(r["dunbar_limit"]) == lim]
                pa = [r["payoff_ALLD"] for r in gl]
                gain_txt = "—"
                if lim > 0 and len(base) > 1 and len(pa) > 1:
                    d = st.mean(pa) - st.mean(base)
                    se = math.sqrt(st.variance(pa) / len(pa) + st.variance(base) / len(base))
                    gains[lim], signif[lim] = d, d - 1.96 * se > 0
                    gain_txt = "%+.3f [%+.3f, %+.3f]" % (d, d - 1.96 * se, d + 1.96 * se)
                works = "—" if lim == 0 else "%d%%" % round(100 * st.mean(r["exceeding_dunbar"] for r in gl))
                out.append("| %s | %s | %d | %d | %d | %s | %s | %s | %s | %s | %s |" % (
                    key[0], key[1], key[2], lim, len(gl), fmt([r["distinct_partners"] for r in gl], 1), works,
                    fmt(pa, 3), gain_txt, fmt([r["payoff_TFT"] for r in gl], 3), fmt([r["d_share"] for r in gl], 3)))
            if 5 in signif:
                mono = all(gains[a] >= gains[b] for a, b in zip(sorted(gains), sorted(gains)[1:]))
                thr = max([l for l, s in signif.items() if s], default=None)
                v = "tak" if signif[5] and mono else ("nie" if not signif[5] else "warunkowo")
                summary.append("- %s, %s, N=%d: **%s** (próg: %s)" % (
                    key[0], key[1], key[2], v, "limit ≤ %d" % thr if thr else "brak"))
        out += ["", "**P3 łącznie:**", ""] + summary + [""]
    s2 = [r for r in rows if r["prediction"] == "S2"]
    if s2:
        out += verdict_stage2(s2)
    return "\n".join(out)


def ci_diff(a, b):
    d = st.mean(a) - st.mean(b)
    se = math.sqrt(st.variance(a) / len(a) + st.variance(b) / len(b)) if len(a) > 1 and len(b) > 1 else float("nan")
    return d, d - 1.96 * se, d + 1.96 * se


def verdict_stage2(rows):
    out = ["## Etap 2 – zestawienia parami (ewolucja + limit Dunbara)", "",
           "| macierz | mutacja | limit | n | limit działa | ALLD | Δ ALLD vs brak limitu (95% CI) | udział D | ALLC | trend ALLD /10k | stabilizacja | P1 | P2 (część) | P3 |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    pairs = []
    keyf = lambda r: (r["payoff_preset"], r["mutation_rate"])
    for key, grp in itertools.groupby(sorted(rows, key=keyf), key=keyf):
        g = list(grp)
        base = [r["share_ALLD"] for r in g if int(r["dunbar_limit"]) == 0]
        for lim in sorted({int(r["dunbar_limit"]) for r in g}):
            gl = [r for r in g if int(r["dunbar_limit"]) == lim]
            n = len(gl)
            ok1 = [FIX < r["share_ALLD"] < 1 - FIX and FIX < r["d_share"] < 1 - FIX and r["stabilized"] for r in gl]
            v1 = share_verdict(sum(ok1) / n) if key[1] > 0 else "—"
            if key[1] == 0:
                v2 = share_verdict(sum(r["share_ALLC"] < 1.0 / r["compat_N"] for r in gl) / n)
                p2 = "wymiera: " + v2
            else:
                frac = sum(r["share_ALLC"] > 0 for r in gl) / n
                v2 = "tak" if frac >= 0.8 and st.mean(r["share_ALLC"] for r in gl) <= 0.2 else \
                    ("nie" if frac <= 0.2 else "warunkowo")
                p2 = "utrzymuje się: " + v2
            if lim == 0:
                dtxt, v3 = "—", "—"
            else:
                d, lo, hi = ci_diff([r["share_ALLD"] for r in gl], base)
                dtxt = "%+.3f [%+.3f, %+.3f]" % (d, lo, hi)
                v3 = "tak" if lo > 0 else ("nie" if hi < 0 else "brak efektu")
            works = "—" if lim == 0 else "%d%%" % round(100 * st.mean(r["exceeding_dunbar"] for r in gl))
            out.append("| %s | %g | %d | %d | %s | %s | %s | %s | %s | %s | %d%% | %s | %s | %s |" % (
                key[0], key[1], lim, n, works, fmt([r["share_ALLD"] for r in gl]), dtxt,
                fmt([r["d_share"] for r in gl]), fmt([r["share_ALLC"] for r in gl], 3),
                fmt([r["alld_trend_10k"] for r in gl], 3),
                round(100 * sum(r["stabilized"] for r in gl) / n), v1, p2, v3))
            if lim > 0:
                pairs.append((key, lim, v1, v2, v3))
    out += ["", "**Zgodność par** (obie predykcje utrzymane przy danym limicie):", ""]
    for (preset, mut), lim, v1, v2, v3 in pairs:
        if mut > 0:
            out.append("- %s, mutacja %g, limit %d: P1+P3 **%s** (P1 %s, P3 %s); P2 część: %s" % (
                preset, mut, lim, "tak" if v1 == "tak" and v3 == "tak" else
                ("nie" if "nie" in (v1, v3) else "warunkowo"), v1, v3, v2))
        else:
            out.append("- %s, bez mutacji, limit %d: P2 część (wymiera) %s; P3 %s" % (preset, lim, v2, v3))
    out.append("")
    return out


def main():
    ap = argparse.ArgumentParser(description="Etap 1: przebiegi i werdykty")
    ap.add_argument("--experiments", nargs="*", default=STAGE1, choices=STAGE1 + STAGE2)
    ap.add_argument("--N", nargs="*", type=int, default=[200, 500])
    ap.add_argument("--repeat", type=int, default=15)
    ap.add_argument("--end-cycle", type=int)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--out", default="compat_results.csv")
    ap.add_argument("--ts-out", help="plik szeregów czasowych (domyślnie <out>_timeseries.csv)")
    ap.add_argument("--verdict", metavar="CSV", help="tylko policz werdykty z istniejącego pliku")
    a = ap.parse_args()
    if a.verdict:
        print(verdict(a.verdict))
    else:
        run(a)


if __name__ == "__main__":
    main()
