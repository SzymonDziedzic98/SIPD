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
- P1 oceniane tylko przy mutation_rate > 0 (bez mutacji fiksacja jest stanem pochłaniającym).
- P3 (miara główna, CLAUDE.md): kooperacja spada przy limicie = udział D przy L=5 większy niż bez
  limitu (95% CI różnicy > 0); "nie", gdy CI < 0 (kooperacja rośnie) albo różnica nieistotna.
  Próg = największy L z istotnym spadkiem.
- P3 (miara dodatkowa): zysk oszustów = wypłata ALLD na grę przy L minus bez limitu; "tak" gdy istotny
  przy L=5 i nie rośnie z L. Próg = największy L z istotnym zyskiem. Raportowane: czy limit działa.
- Klasyfikacja (tabela zbiorcza): kolumny = układ (well_mixed / wariant sieci) × macierz;
  "stała kandydacka" = ten sam werdykt we wszystkich kolumnach, "parametr kontekstowy" = werdykt
  zależy od układu lub macierzy, "nie odtworzono" = "nie" we wszystkich kolumnach walidacji
  (baseline i well_mixed).
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
PLAN_MIN = ["PM2_P12_space", "PM2_P12_wellmixed", "PM2_P3_space", "PM2_P3_wellmixed", "PM3_P1_network",
            "PM3_P3_network", "PM4_heatmap"]
PLAN_MIN_SPEED2 = ["PM2_P3_space_speed2", "PM3_P3_network_speed2", "PM4_heatmap_speed2"]
PLAN_P4 = ["PM5_P4_strategy", "PM5_P4_family"]
FIX = 0.05


def build_jobs(names, n_values, repeat, end_cycle):
    jobs = []
    for name in names:
        spec = sipd.BATCH_EXPERIMENTS[name]
        rep_n = repeat if repeat else spec["repeat"]
        among = dict(spec["among"])
        among["compat_N"] = [n for n in among["compat_N"] if n in n_values]
        seeder = random.Random(spec["seed"])
        seeds = [seeder.randrange(2 ** 31) for _ in range(rep_n)]   # keep_seed: te same dla kombinacji
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
    return m.compat_rows, m.timeseries_rows, m.encounter_rows


def _norm(v):
    try:
        return repr(float(v))
    except (TypeError, ValueError):
        return str(v)


def job_signature(params, seed, keys):
    return (params["variant_name"], _norm(seed)) + tuple(_norm(params[k]) for k in keys)


def done_signatures(path, keys):
    """Przebiegi już zapisane w compat CSV (do --resume po przerwaniu)."""
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {(r["variant_name"], _norm(r["seed"])) + tuple(_norm(r[k]) for k in keys)
                for r in csv.DictReader(f)}


def run(args):
    jobs = build_jobs(args.experiments, set(args.N), args.repeat, args.end_cycle)
    resume = args.resume and os.path.exists(args.out)
    if resume:
        # klucze = parametry przeglądane w eksperymentach (wszystkie są kolumnami compat CSV)
        keys = sorted({k for n in args.experiments for k in sipd.BATCH_EXPERIMENTS[n]["among"]})
        done = done_signatures(args.out, keys)
        before = len(jobs)
        jobs = [j for j in jobs if job_signature(j[0], j[1], keys) not in done]
        print("wznowienie: %d z %d przebiegów już zapisanych" % (before - len(jobs), before), flush=True)
    jobs.sort(key=lambda j: -(j[0]["compat_N"] * (4 if j[0]["well_mixed"] else 1)))   # najdroższe najpierw
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    t0 = time.time()
    ts_out = args.ts_out or args.out.replace(".csv", "_timeseries.csv")
    enc_out = args.out.replace(".csv", "_encounter_cells.csv")
    mode = "a" if resume else "w"
    enc_new = not (resume and os.path.exists(enc_out))
    with open(args.out, mode, newline="", encoding="utf-8") as f, \
            open(ts_out, mode, newline="", encoding="utf-8") as ft, \
            open(enc_out, "w" if enc_new else "a", newline="", encoding="utf-8") as fe, Pool(args.workers) as pool:
        w, wt, we = csv.writer(f), csv.writer(ft), csv.writer(fe)
        if not resume:
            w.writerow(sipd.COMPAT_HEADER)
            wt.writerow(sipd.CSV_HEADERS["character_timeseries.csv"])
        if enc_new:
            we.writerow(sipd.CSV_HEADERS["encounter_cells.csv"])
        for i, (rows, ts, enc) in enumerate(pool.imap_unordered(run_job, jobs), 1):
            w.writerows(rows)
            wt.writerows(ts)
            we.writerows(enc)
            f.flush()
            ft.flush()
            fe.flush()
            print("[%d/%d] %.0f s" % (i, len(jobs), time.time() - t0), flush=True)
    if os.path.getsize(enc_out) < 200:
        os.remove(enc_out)
    print("zapisano", args.out, "i", ts_out)


# ---------------------------------------------------------------------------
# werdykty
# ---------------------------------------------------------------------------

def load(path):
    with open(path, encoding="utf-8") as f:
        raw = list(csv.DictReader(f))
    # ten sam przebieg (konfiguracja + seed) z dwóch eksperymentów, np. PM2 baseline i PM3 baseline,
    # liczy się raz - inaczej n się dubluje, a przedziały ufności są sztucznie wąskie
    seen, rows = set(), []
    for r in raw:
        key = tuple((k, v) for k, v in sorted(r.items()) if k != "variant_name")
        if key not in seen:
            seen.add(key)
            rows.append(r)
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


def layout(r):
    if r["well_mixed"]:
        return "well_mixed"
    return r.get("network_variant", "baseline") or "baseline"


def share_verdict(frac):
    return "tak" if frac >= 0.8 else ("nie" if frac <= 0.2 else "warunkowo")


def verdict(path):
    rows = load(path)
    space = layout
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
                fmt([r.get("alld_trend_10k", 0.0) for r in g], 3),
                round(100 * sum(r["stabilized"] for r in g) / n), v1, part))
        out += ["", "**P2 łącznie** (obie części muszą się utrzymać):", ""]
        for key, parts in sorted(p2_parts.items()):
            v = "tak" if all(p == "tak" for p in parts) else ("nie" if all(p == "nie" for p in parts) else "warunkowo")
            out.append("- %s, %s, N=%d, prędkość %g: **%s**" % (key[0], key[1], key[2], key[3], v))
        out.append("")

    p3 = [r for r in rows if r["prediction"] == "P3"]
    if p3:
        out += ["## P3 – limit Dunbara: spadek kooperacji (miara główna) i zysk oszustów (dodatkowa)", "",
                "| układ | macierz | N | limit | n | różnych partnerów | limit działa | udział D | Δ udziału D vs brak limitu (95% CI) | ALLD / grę | zysk oszustów (95% CI) | TFT / grę |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        summary = []
        keyf = lambda r: (space(r), r["payoff_preset"], int(r["compat_N"]))
        for key, grp in itertools.groupby(sorted(p3, key=keyf), key=keyf):
            g = list(grp)
            base = [r["payoff_ALLD"] for r in g if r["dunbar_limit"] == 0]
            base_d = [r["d_share"] for r in g if r["dunbar_limit"] == 0]
            gains, signif, dsig = {}, {}, {}
            for lim in sorted({int(r["dunbar_limit"]) for r in g}):
                gl = [r for r in g if int(r["dunbar_limit"]) == lim]
                pa = [r["payoff_ALLD"] for r in gl]
                gain_txt = dtxt = "—"
                if lim > 0 and len(base_d) > 1 and len(gl) > 1:
                    dd, lo, hi = ci_diff([r["d_share"] for r in gl], base_d)
                    dsig[lim] = (lo > 0, hi < 0)
                    dtxt = "%+.3f [%+.3f, %+.3f]" % (dd, lo, hi)
                if lim > 0 and len(base) > 1 and len(pa) > 1:
                    d = st.mean(pa) - st.mean(base)
                    se = math.sqrt(st.variance(pa) / len(pa) + st.variance(base) / len(base))
                    gains[lim], signif[lim] = d, d - 1.96 * se > 0
                    gain_txt = "%+.3f [%+.3f, %+.3f]" % (d, d - 1.96 * se, d + 1.96 * se)
                works = "—" if lim == 0 else "%d%%" % round(100 * st.mean(r["exceeding_dunbar"] for r in gl))
                out.append("| %s | %s | %d | %d | %d | %s | %s | %s | %s | %s | %s | %s |" % (
                    key[0], key[1], key[2], lim, len(gl), fmt([r["distinct_partners"] for r in gl], 1), works,
                    fmt([r["d_share"] for r in gl], 3), dtxt, fmt(pa, 3), gain_txt, fmt([r["payoff_TFT"] for r in gl], 3)))
            if 5 in signif:
                vc, thr_c = p3_coop_verdict(dsig)
                ve, thr_e = p3_exploit_verdict(gains, signif)
                summary.append("- %s, %s, N=%d: spadek kooperacji **%s** (próg: %s); zysk oszustów **%s** (próg: %s)" % (
                    key[0], key[1], key[2], vc, thr_c, ve, thr_e))
        out += ["", "**P3 łącznie:**", ""] + summary + [""]
    p4 = [r for r in rows if r["prediction"] == "P4"]
    if p4:
        out += verdict_p4(p4)
    s2 = [r for r in rows if r["prediction"] == "S2"]
    if s2:
        out += verdict_stage2(s2)
    out += summary_table(rows)
    return "\n".join(out)


P4_MARGIN = 0.05   # przebiegi z |r̂ - c/b| <= P4_MARGIN nie wchodzą do testu kierunku (zbyt blisko progu)


def p4_threshold(points):
    """points: [(średnie r̂, średni udział ALLC)] posortowane po r̂. Próg r* = interpolacja liniowa
    pierwszego przejścia udziału ALLC przez 0,5 (z dołu do góry); None, gdy brak przejścia."""
    for (r0, a0), (r1, a1) in zip(points, points[1:]):
        if a0 < 0.5 <= a1:
            return r0 + (r1 - r0) * (0.5 - a0) / (a1 - a0) if a1 != a0 else r0
    return None


def verdict_p4(rows):
    """P4: kooperacja (ALLC) przejmuje populację, gdy r̂ > c/b, i zanika, gdy r̂ < c/b (r̂ zmierzone)."""
    out = ["## P4 – reguła Hamiltona (well_mixed, ALLC/ALLD, gra dawcy)", "",
           "Dobór `strategy` = kalibracja (partner z tą samą strategią z prawdopodobieństwem α, r̂ = α z konstrukcji); "
           "`family` = właściwy test z rodzinami (r̂ zmierzone). ALLC = udział na końcu (średnia z ostatniego okna); "
           "„ALLC wygrywa” = udział > 0,5. Test znaku = odsetek interwałów ewolucji, w których zmiana udziału ALLC "
           "ma znak r̂_k·b − c.", "",
           "| dobór | c/b | dopasowanie | α | n | r̂ | r̂ − α | ALLC | ALLC wygrywa | stabilizacja | test znaku |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    keyf = lambda r: (r["kin_matching_mode"], r["c_over_b"], r["fitness_mode"])
    summary, cols = [], {}
    for key, grp in itertools.groupby(sorted(rows, key=lambda r: keyf(r) + (r["kin_matching_prob"],)), key=keyf):
        g = list(grp)
        mode, cb, fm = key
        points, dev = [], []
        for a in sorted({r["kin_matching_prob"] for r in g}):
            ga = [r for r in g if r["kin_matching_prob"] == a]
            rh = [r["r_hat_all"] for r in ga if isinstance(r["r_hat_all"], float)]
            sg = [r["p4_sign_agreement"] for r in ga if isinstance(r["p4_sign_agreement"], float)]
            allc = [r["share_ALLC"] for r in ga]
            if rh:
                points.append((st.mean(rh), st.mean(allc)))
                dev.append(abs(st.mean(rh) - a))
            out.append("| %s | %g | %s | %g | %d | %s | %s | %s | %d%% | %d%% | %s |" % (
                mode, cb, fm, a, len(ga), fmt(rh, 3) if rh else "n/a",
                "%+.3f" % (st.mean(rh) - a) if rh else "n/a", fmt(allc, 3),
                round(100 * sum(x > 0.5 for x in allc) / len(ga)),
                round(100 * sum(r["stabilized"] for r in ga) / len(ga)), fmt(sg) if sg else "n/a"))
        points.sort()
        thr = p4_threshold(points)
        test = [r for r in g if isinstance(r["r_hat_all"], float) and abs(r["r_hat_all"] - cb) > P4_MARGIN]
        above = [r for r in test if r["r_hat_all"] > cb]
        ok = [(r["r_hat_all"] > cb) == (r["share_ALLC"] > 0.5) for r in test]
        v = share_verdict(sum(ok) / len(ok)) if ok else "—"
        if v == "tak" and not above:
            v = "warunkowo"      # sprawdzona tylko strona r̂ < c/b
        calib = ("; r̂ ≈ α: %s (maks. |r̂ − α| = %.3f)" % ("tak" if max(dev) <= 0.05 else "NIE", max(dev))) if dev else ""
        summary.append("- %s, c/b = %g, %s: kierunek zgodny z regułą w %d/%d przebiegów (poza ±%g od progu; "
                       "z r̂ > c/b: %d) → **%s**; próg r* = %s%s" % (
                           mode, cb, fm, sum(ok), len(ok), P4_MARGIN, len(above), v,
                           "%.3f (odchylenie od c/b %+.3f)" % (thr, thr - cb) if thr is not None
                           else "brak przejścia (maks. średnie r̂ = %.3f)" % max(p[0] for p in points) if points
                           else "n/a", calib))
        cols.setdefault(("P4 %s / %s" % (mode, fm)), {})[("well_mixed", "c/b = %g" % cb)] = v
    out += ["", "**P4 łącznie:**", ""] + summary + [""]
    cset = sorted({c for d in cols.values() for c in d})
    out += ["### Tabela zbiorcza P4", "", "| wariant | " + " | ".join(" / ".join(c) for c in cset) + " | klasyfikacja |",
            "|" + "---|" * (len(cset) + 2)]
    for name, d in sorted(cols.items()):
        out.append("| %s | %s | %s |" % (name, " | ".join("**%s**" % d.get(c, "—") for c in cset), classify(d)))
    out.append("")
    return out


def p3_coop_verdict(dsig):
    """dsig[L] = (kooperacja istotnie spada, kooperacja istotnie rośnie)."""
    if 5 not in dsig:
        return "—", "—"
    drops = [l for l, (dn, _) in dsig.items() if dn]
    v = "tak" if dsig[5][0] else "nie"
    return v, ("limit ≤ %d" % max(drops)) if drops else ("brak; kooperacja rośnie" if dsig[5][1] else "brak")


def p3_exploit_verdict(gains, signif):
    if 5 not in signif:
        return "—", "—"
    mono = all(gains[a] >= gains[b] for a, b in zip(sorted(gains), sorted(gains)[1:]))
    thr = max([l for l, s in signif.items() if s], default=None)
    v = "tak" if signif[5] and mono else ("nie" if not signif[5] else "warunkowo")
    return v, "limit ≤ %d" % thr if thr else "brak"


def column_verdicts(rows):
    """Werdykty per kolumna (układ, macierz[, prędkość]) dla P1, P2, P3 (obie miary)."""
    speeds = {r.get("player_speed", 2.0) for r in rows}
    colkey = (lambda r: (layout(r), r["payoff_preset"], r.get("player_speed", 2.0))) if len(speeds) > 1 else \
        (lambda r: (layout(r), r["payoff_preset"]))
    res = {}
    p12 = [r for r in rows if r["prediction"] == "P1P2"]
    for key, grp in itertools.groupby(sorted(p12, key=colkey), key=colkey):
        g = list(grp)
        mut = [r for r in g if r["mutation_rate"] > 0]
        nomut = [r for r in g if r["mutation_rate"] == 0]
        if mut:
            ok1 = [FIX < r["share_ALLD"] < 1 - FIX and FIX < r["d_share"] < 1 - FIX and r["stabilized"] for r in mut]
            res[("P1", key)] = (share_verdict(sum(ok1) / len(mut)), "ALLD " + fmt([r["share_ALLD"] for r in mut]))
        parts = []
        if nomut:
            parts.append(share_verdict(sum(r["share_ALLC"] < 1.0 / r["compat_N"] for r in nomut) / len(nomut)))
        if mut:
            frac = sum(r["share_ALLC"] > 0 for r in mut) / len(mut)
            parts.append("tak" if frac >= 0.8 and st.mean(r["share_ALLC"] for r in mut) <= 0.2 else
                         ("nie" if frac <= 0.2 else "warunkowo"))
        if parts:
            v = "tak" if all(p == "tak" for p in parts) else ("nie" if all(p == "nie" for p in parts) else "warunkowo")
            res[("P2", key)] = (v, "ALLC " + fmt([r["share_ALLC"] for r in mut], 3) if mut else "")
    p3 = [r for r in rows if r["prediction"] == "P3"]
    for key, grp in itertools.groupby(sorted(p3, key=colkey), key=colkey):
        g = list(grp)
        base = [r for r in g if int(r["dunbar_limit"]) == 0]
        at5 = [r for r in g if int(r["dunbar_limit"]) == 5]
        if len(base) < 2 or len(at5) < 2:
            continue
        dsig, gains, signif = {}, {}, {}
        for lim in sorted({int(r["dunbar_limit"]) for r in g} - {0}):
            gl = [r for r in g if int(r["dunbar_limit"]) == lim]
            _, lo, hi = ci_diff([r["d_share"] for r in gl], [r["d_share"] for r in base])
            dsig[lim] = (lo > 0, hi < 0)
            d, lo2, _ = ci_diff([r["payoff_ALLD"] for r in gl], [r["payoff_ALLD"] for r in base])
            gains[lim], signif[lim] = d, lo2 > 0
        vc, tc = p3_coop_verdict(dsig)
        ve, te = p3_exploit_verdict(gains, signif)
        dd = ci_diff([r["d_share"] for r in at5], [r["d_share"] for r in base])[0]
        res[("P3 kooperacja", key)] = (vc, "ΔD@5 %+.3f, próg: %s" % (dd, tc))
        res[("P3 zysk oszustów", key)] = (ve, "Δwypłaty ALLD@5 %+.3f, próg: %s" % (gains[5], te))
    return res


def classify(verdicts):
    """verdicts: {kolumna: werdykt}. Zwraca klasyfikację regularności."""
    vals = [v for v in verdicts.values() if v not in ("—", "")]
    if not vals:
        return "—"
    validation = [v for k, v in verdicts.items() if k[0] in ("baseline", "well_mixed")]
    if validation and all(v == "nie" for v in validation):
        return "nie odtworzono"
    if len(set(vals)) == 1:
        return "stała kandydacka (%s)" % vals[0]
    # wymiar d wpływa na werdykt, gdy przy ustalonych pozostałych wymiarach zmiana d zmienia werdykt
    names = ["układu przestrzeni", "macierzy wypłat", "mobilności (prędkość)"]
    deps = []
    for d in range(len(next(iter(verdicts)))):
        groups = {}
        for k, v in verdicts.items():
            if k[0] == "well_mixed" and d == 2:
                continue                                # prędkość nie ma znaczenia w well_mixed
            groups.setdefault(k[:d] + k[d + 1:], set()).add(v)
        if any(len(v) > 1 for v in groups.values()):
            deps.append(names[d])
    return "parametr kontekstowy (zależy od: %s)" % ", ".join(deps or ["kombinacji wymiarów"])


def summary_table(rows):
    res = column_verdicts(rows)
    if not res:
        return []
    cols = sorted({k for (_, k) in res})
    regs = [r for r in ("P1", "P2", "P3 kooperacja", "P3 zysk oszustów") if any(k[0] == r for k in res)]
    head = ["regularność"] + [" / ".join(str(x) for x in c) for c in cols] + ["klasyfikacja"]
    out = ["## Tabela zbiorcza – klasyfikacja", "",
           "Kolumny: układ × macierz (× prędkość, jeśli w danych jest kilka). Komórka: werdykt i miara "
           "(średnia ± odchylenie między powtórzeniami).", "",
           "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for reg in regs:
        cells, verdicts = [], {}
        for c in cols:
            if (reg, c) in res:
                v, info = res[(reg, c)]
                verdicts[c] = v
                cells.append("**%s** (%s)" % (v, info) if info else "**%s**" % v)
            else:
                cells.append("—")
        out.append("| %s | %s | %s |" % (reg, " | ".join(cells), classify(verdicts)))
    out.append("")
    return out


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
                fmt([r.get("alld_trend_10k", 0.0) for r in gl], 3),
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
    ap.add_argument("--experiments", nargs="*", default=PLAN_MIN, choices=STAGE1 + STAGE2 + PLAN_MIN + PLAN_MIN_SPEED2 + PLAN_P4)
    ap.add_argument("--N", nargs="*", type=int, default=[200, 500])
    ap.add_argument("--repeat", type=int, help="domyślnie: liczba powtórzeń z definicji eksperymentu")
    ap.add_argument("--end-cycle", type=int)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--out", default="compat_results.csv")
    ap.add_argument("--ts-out", help="plik szeregów czasowych (domyślnie <out>_timeseries.csv)")
    ap.add_argument("--resume", action="store_true", help="dopisz tylko przebiegi, których nie ma jeszcze w --out")
    ap.add_argument("--verdict", metavar="CSV", help="tylko policz werdykty z istniejącego pliku")
    a = ap.parse_args()
    if a.verdict:
        print(verdict(a.verdict))
    else:
        run(a)


if __name__ == "__main__":
    main()
