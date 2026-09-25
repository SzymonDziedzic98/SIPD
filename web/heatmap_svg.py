"""
Heatmapy stabilności spotkań (SVG, tylko biblioteka standardowa).

Z pliku encounter_cells.csv (PM4_heatmap) rysuje po jednym panelu na wariant sieci: udział spotkań
powtórnych z partnerem pamiętanym (cały przebieg) w każdej komórce siatki, wspólna skala 0-1.
Ścieżki parku są odtwarzane z portu (ten sam seed i wariant) - dotyczy sieci syntetycznej.

    python web/heatmap_svg.py results/plan_min_encounter_cells.csv docs/heatmap_spotkan.svg [vmin]

vmin (domyślnie 0): dolny koniec skali - np. 0.7, gdy wszystkie wartości są wysokie; opisany w legendzie.
"""
import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sipd  # noqa: E402

# rampa sekwencyjna (jeden odcień, jasny -> ciemny), wartości z palety referencyjnej
RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
        "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
SURFACE, INK, MUTED, GRID, PATH = "#fcfcfb", "#1f2328", "#5b6068", "#e6e5e1", "#8a8a85"
VARIANTS = ["baseline", "fragmented", "connected"]


def color(v, vmin=0.0):
    v = min(1.0, max(0.0, (v - vmin) / (1.0 - vmin)))
    i = v * (len(RAMP) - 1)
    lo = int(i)
    hi = min(lo + 1, len(RAMP) - 1)
    t = i - lo
    a = [int(RAMP[lo][k:k + 2], 16) for k in (1, 3, 5)]
    b = [int(RAMP[hi][k:k + 2], 16) for k in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def rebuild_network(variant, seed, experiment="PM4_heatmap", n_agents=200):
    """Sieć użyta w przebiegu (park syntetyczny, ten sam seed -> ten sam wariant)."""
    p = dict(sipd.BATCH_EXPERIMENTS[experiment]["params"], network_variant=variant,
             synthetic_grid=sipd.park_grid_for(n_agents), compat_N=0)
    return sipd.Model(sipd.Params(**p), seed=seed).network


def render(csv_path, out_path, metric="share_repeat_remembered", vmin=0.0):
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    by_var = defaultdict(list)
    for r in rows:
        by_var[r["network_variant"]].append(r)
    variants = [v for v in VARIANTS if v in by_var] + sorted(set(by_var) - set(VARIANTS))
    exp = rows[0]["variant_name"]
    ep = sipd.BATCH_EXPERIMENTS.get(exp, sipd.BATCH_EXPERIMENTS["PM4_heatmap"])["params"]
    speed = ("%g" % ep.get("player_speed", 2.0)).replace(".", ",")
    cols = rows_n = 50
    cell, pad, gap, head = 6, 24, 28, 58
    panel = cols * cell
    width = pad * 2 + len(variants) * panel + (len(variants) - 1) * gap
    height = head + panel + 92
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'font-family="IBM Plex Sans, Segoe UI, Helvetica, Arial, sans-serif">' % (width, height, width, height),
           '<rect width="100%%" height="100%%" fill="%s"/>' % SURFACE,
           '<text x="%d" y="24" font-size="15" font-weight="600" fill="%s">Stabilność spotkań: udział spotkań '
           'z partnerem pamiętanym</text>' % (pad, INK),
           '<text x="%d" y="42" font-size="11.5" fill="%s">Komórka 50 × 50 siatki; cały przebieg (%s, '
           'N = 200, PD, mutacja 0,01, prędkość %s). Szare kreski: ścieżki parku. Puste pola: brak gier.</text>'
           % (pad, MUTED, exp, speed)]
    for k, var in enumerate(variants):
        x0 = pad + k * (panel + gap)
        y0 = head + 18
        rs = by_var[var]
        games = sum(int(r["total_games"]) for r in rs)
        wmean = sum(float(r[metric]) * int(r["total_games"]) for r in rs) / games if games else 0.0
        out.append('<text x="%d" y="%d" font-size="13" font-weight="600" fill="%s">%s</text>'
                   % (x0, head + 8, INK, var))
        out.append('<text x="%d" y="%d" font-size="11" fill="%s" text-anchor="end">średnio %s · %d komórek z grami</text>'
                   % (x0 + panel, head + 8, MUTED, ("%.2f" % wmean).replace(".", ","), len(rs)))
        out.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="%s"/>'
                   % (x0, y0, panel, panel, GRID))
        for r in rs:
            c, rr = int(r["col"]), int(r["row"])
            v = float(r[metric])
            out.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"><title>komórka (%d, %d): %s, '
                       'gier %s</title></rect>' % (x0 + c * cell, y0 + rr * cell, cell, cell, color(v, vmin), c, rr,
                                                    ("%.2f" % v).replace(".", ","),
                                                    r["total_games"]))
        try:
            net = rebuild_network(var, int(float(rs[0]["seed"])), exp if exp in sipd.BATCH_EXPERIMENTS else "PM4_heatmap")
            sx, sy = panel / net.width, panel / net.height
            d = " ".join("M" + " L".join("%.1f %.1f" % (x0 + x * sx, y0 + y * sy) for x, y in pl)
                         for pl in net.polylines)
            out.append('<path d="%s" fill="none" stroke="%s" stroke-width="0.6" stroke-opacity="0.55"/>' % (d, PATH))
        except Exception:  # noqa: BLE001 - sieć spoza portu (np. GAMA z drogi.geojson): bez ścieżek
            pass
    # legenda: pasek 0-1
    lx, ly, lw = pad, head + 18 + panel + 34, 240
    out.append('<defs><linearGradient id="g">%s</linearGradient></defs>' % "".join(
        '<stop offset="%.3f" stop-color="%s"/>' % (i / (len(RAMP) - 1), c) for i, c in enumerate(RAMP)))
    out.append('<rect x="%d" y="%d" width="%d" height="10" rx="2" fill="url(#g)"/>' % (lx, ly, lw))
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        out.append('<text x="%.1f" y="%d" font-size="10.5" fill="%s" text-anchor="middle">%s</text>'
                   % (lx + t * lw, ly + 24, MUTED, ("%.2f" % (vmin + t * (1 - vmin))).replace(".", ",")))
    out.append('<text x="%d" y="%d" font-size="11" fill="%s">udział spotkań powtórnych (pamiętany partner)%s</text>'
               % (lx + lw + 16, ly + 9, INK, "" if vmin == 0 else "; skala od %s, niższe wartości = najjaśniejszy kolor"
                  % ("%.2f" % vmin).replace(".", ",")))
    out.append("</svg>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return variants


if __name__ == "__main__":
    print("warianty:", render(sys.argv[1], sys.argv[2], vmin=float(sys.argv[3]) if len(sys.argv) > 3 else 0.0))
