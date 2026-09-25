"""
Diagnostyka dynamiki modelu (port Pythona) w skali GAMA Days: 200 agentów, park ~1,9 x 1,9 km
(syntetyczna siatka 32x32), 50 000 cykli. Wyniki opisane w docs/gamadays.md.

    python web/diagnostics.py [plik_wyników.json]      # ok. 15-20 min na 4 rdzeniach
"""
import os, sys, statistics as st, collections, json, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sipd

BIG = dict(synthetic_grid=32)            # park ~10x większy powierzchniowo (32x32 zamiast 10x10 węzłów)
BIGWIN = 10 ** 9                          # partner_window: pamiętaj wszystkich - do liczenia różnych partnerów

def job(args):
    tag, cycles, seed, p = args
    t = time.time()
    m = sipd.Model(sipd.Params(**dict(BIG, **p)), seed=seed)
    m.run(cycles)
    ch = {pl.name: pl.character for pl in m.players}
    half = cycles // 2
    agg = collections.defaultdict(lambda: [0, 0]); aggl = collections.defaultdict(lambda: [0, 0])
    pairs = collections.Counter()
    for nb, cyc, a, b, ma, mb, *_ in m.game_log:
        pairs[(a, b) if a < b else (b, a)] += 1
        for me, opp, mv in ((a, b, ma), (b, a, mb)):
            agg[(ch[me], ch[opp])][0] += mv == "D"; agg[(ch[me], ch[opp])][1] += 1
            if cyc >= half:
                aggl[(ch[me], ch[opp])][0] += mv == "D"; aggl[(ch[me], ch[opp])][1] += 1
    late = [x for r in m.game_log if r[1] >= half for x in (r[4], r[5])]
    dis = [c.disorder for c in m.cells]
    return dict(tag=tag, seed=seed, secs=time.time() - t,
                games_per_agent=st.mean(pl.nb_games for pl in m.players),
                distinct_total=st.mean(len(pl.last_met_cycle) for pl in m.players) if p.get("partner_window") == BIGWIN else None,
                known=st.mean(len(pl.known_others) for pl in m.players),
                games_per_pair=st.mean(pairs.values()) if pairs else 0, games_per_pair_median=st.median(pairs.values()) if pairs else 0,
                d_late=late.count("D") / max(1, len(late)),
                d_by={f"{k[0]}>{k[1]}": v[0] / max(1, v[1]) for k, v in agg.items()},
                d_by_late={f"{k[0]}>{k[1]}": v[0] / max(1, v[1]) for k, v in aggl.items()},
                score={c: m.mean_for(c) / 1000 for c in set(ch.values())},
                forgets=m.nb_forgets_total, disorder_max=max(dis), cells_over1=sum(x > 1 for x in dis))

J = []
C = 50000
for vr in (10, 30):
    for s in (1, 2):
        J.append((f"1_vision{vr}", C, s, dict(nb_TFT=200, vision_radius=vr, partner_window=BIGWIN)))
for start in (False, True):
    for s in (1, 2):
        J.append((f"2_tft_start{start}", C, s, dict(nb_TFT=200, vision_radius=30, unlimited_games=True, classic_start_cooperate=start)))
for s in (1, 2):
    J.append(("3_qlearn", 10 * 20000, s, dict(nb_QLEARN=100, nb_ALLD=50, nb_ALLC=50, vision_radius=30, unlimited_games=True)))
for bw in (0.0, 0.4):
    for s in (1, 2):
        J.append((f"4_bw{bw}", C, s, dict(nb_AQLEARN=200, vision_radius=30, social_sensitivity_aqlearn=1.5,
                                            social_learning_boost_aqlearn=2.0, broken_windows_sensitivity=bw, character_strength_qlearn=0.6)))
J.append(("4_allc_bw0.4", C, 1, dict(nb_ALLC=200, vision_radius=30, broken_windows_sensitivity=0.4)))
for s in (1, 2):
    J.append(("5_limited", C, s, dict(nb_ALLC=50, nb_ALLD=50, nb_TFT=50, nb_GRIM=50, vision_radius=30)))
for lim in (0, 5, 15, 50, 150):
    for s in (1, 2):
        J.append((f"6a_tft_dunbar{lim}", 30000, s, dict(nb_TFT=200, vision_radius=30, unlimited_games=True, dunbar_limit=lim, partner_window=BIGWIN)))
        J.append((f"6b_tftalld_dunbar{lim}", 30000, s, dict(nb_TFT=160, nb_ALLD=40, vision_radius=30, unlimited_games=True,
                                                             classic_start_cooperate=True, dunbar_limit=lim, partner_window=BIGWIN)))
J.sort(key=lambda j: -j[1])   # najdłuższe najpierw
if __name__ == "__main__":
    OUT = sys.argv[1] if len(sys.argv) > 1 else "diagnostics.json"
    out = []
    with Pool(4) as pool:
        for r in pool.imap_unordered(job, J):
            out.append(r)
            print(f"[{len(out)}/{len(J)}] {r['tag']} seed {r['seed']}: {r['secs']:.0f} s", flush=True)
            json.dump(out, open(OUT, "w"))
    print("KONIEC")
