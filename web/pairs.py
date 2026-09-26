"""
Zestawienia parami i razem (etapy 2-3 CLAUDE.md) z gotowych wyników portu.

    python web/pairs.py results/p1p3_network_N200_r10.csv results/p2_network_N200_r10.csv \
        results/p4_N200_r10.csv > docs/pairs_verdict_N200_r10.md

Źródła:
- PM7_P1P3_network (mutacja 0,01) i PM8_P2_network (mutacja 0): PD, sieci × prędkość × limit Dunbara;
- PM5_P4_* (well_mixed, ALLC/ALLD, gra dawcy).

Kryteria (FIX = 0,05, istotność = 95% CI różnicy względem limitu 0):
- P1: przy mutacji > 0 udział ALLD i udział D w (FIX, 1 - FIX) i stabilizacja;
- P2: bez mutacji ALLC wymiera (< 1/N), przy mutacji > 0 ALLC obecny i średnio <= 0,2 (obie części, ten sam limit);
- P3: udział ALLD przy limicie większy niż bez limitu (miara selekcji, mutacja > 0); bez mutacji
  ALLD fiksuje się także bez limitu, więc P3 jest wtedy nietestowalna (sufit);
- para/trójka: "tak" gdy wszystkie składowe "tak", "nie" gdy któraś "nie", inaczej "warunkowo";
- P4 + P1/P2 z przebiegów P4 (mutacja 0,01); P4 + P3: limit nie działa na ALLC/ALLD (brak pamięci
  w decyzji), sprawdzone przebiegiem kontrolnym - opis w docs/pairs_verdict_N200_r10.md.
"""
import itertools
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stage1 import FIX, ci_diff, classify, fmt, layout, load, share_verdict  # noqa: E402


def combine(*vs):
    if any(v == "nie" for v in vs):
        return "nie"
    return "tak" if all(v == "tak" for v in vs) else "warunkowo"


def p1(g):
    ok = [FIX < r["share_ALLD"] < 1 - FIX and FIX < r["d_share"] < 1 - FIX and r["stabilized"] for r in g]
    return share_verdict(sum(ok) / len(g))


def p2_extinct(g):
    return share_verdict(sum(r["share_ALLC"] < 1.0 / r["compat_N"] for r in g) / len(g))


def p2_persist(g):
    frac = sum(r["share_ALLC"] > 0 for r in g) / len(g)
    return "tak" if frac >= 0.8 and st.mean(r["share_ALLC"] for r in g) <= 0.2 else ("nie" if frac <= 0.2 else "warunkowo")


def p3(g, base):
    if len(g) < 2 or len(base) < 2:
        return "—", ""
    d, lo, hi = ci_diff([r["share_ALLD"] for r in g], [r["share_ALLD"] for r in base])
    return ("tak" if lo > 0 else ("nie" if hi < 0 else "brak efektu")), "ΔALLD %+.3f" % d


def spatial_pairs(rows):
    col = lambda r: (layout(r), r["payoff_preset"], r["player_speed"])
    by = {}
    for r in rows:
        by.setdefault((col(r), r["mutation_rate"] > 0, int(r["dunbar_limit"])), []).append(r)
    cols = sorted({k[0] for k in by})
    limits = sorted({k[2] for k in by if k[2] > 0})
    table = {}
    detail = ["| układ | macierz | prędkość | limit | n (mut. 0 / 0,01) | limit działa | ALLC bez mutacji | "
              "ALLC mut. 0,01 | ALLD mut. 0,01 | udział D mut. 0,01 | P1 | P2 | P3 |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in cols:
        for lim in [0] + limits:
            m0, m1 = by.get((c, False, lim), []), by.get((c, True, lim), [])
            if not m1:
                continue
            v1 = p1(m1)
            v2 = combine(p2_extinct(m0), p2_persist(m1)) if m0 else "—"
            v3, info3 = p3(m1, by.get((c, True, 0), [])) if lim > 0 else ("—", "")
            works = st.mean(r["exceeding_dunbar"] for r in m1) if lim > 0 else None
            detail.append("| %s | %s | %g | %d | %d / %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                c[0], c[1], c[2], lim, len(m0), len(m1), "—" if works is None else "%d%%" % round(100 * works),
                fmt([r["share_ALLC"] for r in m0], 3) if m0 else "—", fmt([r["share_ALLC"] for r in m1], 3),
                fmt([r["share_ALLD"] for r in m1]), fmt([r["d_share"] for r in m1]), v1, v2,
                v3 + (" (%s)" % info3 if info3 else "")))
            if lim == 0:
                if v2 != "—":
                    table.setdefault("P1+P2 (bez limitu)", {})[c] = combine(v1, v2)
                continue
            off = works < 0.2        # limit prawie nikogo nie ogranicza - P3 nietestowalna
            na = "n/d (limit nie działa)"
            if v2 != "—":
                table.setdefault("P2+P3, limit %d" % lim, {})[c] = na if off else combine(v2, v3)
                table.setdefault("P1+P2+P3, limit %d" % lim, {})[c] = na if off else combine(v1, v2, v3)
    return cols, table, detail


def p4_pairs(rows):
    out = ["| dobór | c/b | dopasowanie | strona progu | n | ALLC | ALLD | udział D | P4 (kierunek) | P1 | P2 (ALLC nisko, obecny) |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    table = {}
    keyf = lambda r: (r["kin_matching_mode"], r["c_over_b"], r["fitness_mode"])
    for key, grp in itertools.groupby(sorted(rows, key=keyf), key=keyf):
        g = [r for r in grp if isinstance(r["r_hat_all"], float)]
        cb = key[1]
        for side, sel in (("r̂ < c/b", lambda r: r["r_hat_all"] < cb - 0.05), ("r̂ > c/b", lambda r: r["r_hat_all"] > cb + 0.05)):
            gs = [r for r in g if sel(r)]
            if not gs:
                continue
            ok4 = [(r["r_hat_all"] > cb) == (r["share_ALLC"] > 0.5) for r in gs]
            v4 = share_verdict(sum(ok4) / len(gs))
            v1, v2 = p1(gs), p2_persist(gs)
            out.append("| %s | %g | %s | %s | %d | %s | %s | %s | %s | %s | %s |" % (
                key[0], cb, key[2], side, len(gs), fmt([r["share_ALLC"] for r in gs], 3),
                fmt([r["share_ALLD"] for r in gs], 3), fmt([r["d_share"] for r in gs], 3), v4, v1, v2))
            c = ("well_mixed", "c/b = %g" % cb)
            name = "%s / %s, %s" % (key[0], key[2], side)
            table.setdefault("P4+P1 (%s)" % name, {})[c] = combine(v4, v1)
            table.setdefault("P4+P2 (%s)" % name, {})[c] = combine(v4, v2)
    return table, out


def render_table(title, cols, table, note=""):
    out = ["### " + title, ""] + ([note, ""] if note else [])
    out += ["| zestawienie | " + " | ".join(" / ".join(str(x) for x in c) for c in cols) + " | klasyfikacja |",
            "|" + "---|" * (len(cols) + 2)]
    for name in table:
        d = table[name]
        out.append("| %s | %s | %s |" % (name, " | ".join("**%s**" % d.get(c, "—") for c in cols),
                                         classify({c: v for c, v in d.items() if not v.startswith("n/d")})))
    return out + [""]


def main(paths):
    rows = [r for p in paths for r in load(p)]
    sp = [r for r in rows if r["prediction"] == "S2"]
    p4 = [r for r in rows if r["prediction"] == "P4"]
    out = ["# Zestawienia parami i razem (port Pythona)", "",
           "Źródła: %s; %d przebiegów." % (", ".join("`%s`" % os.path.basename(p) for p in paths), len(rows)), ""]
    if sp:
        cols, table, detail = spatial_pairs(sp)
        order = lambda n: (["P1+P2", "P2+P3", "P1+P2+P3"].index(n.split(" ")[0].rstrip(",")),
                           int(n.rsplit(" ", 1)[1]) if n[-1].isdigit() else 0)
        table = {k: table[k] for k in sorted(table, key=order)}
        out += ["## P1, P2, P3 w przestrzeni (PD, ewolucja)", ""] + detail + [""]
        out += render_table("Tabela zbiorcza – pary i trójka z P1, P2, P3", cols, table,
                            "Kolumny: układ × macierz × prędkość. P1+P3 osobno: `p1p3_network_verdict_N200_r10.md`.")
    if p4:
        table, detail = p4_pairs(p4)
        cols = sorted({c for d in table.values() for c in d})
        out += ["## P4 z P1 i P2 (well_mixed, ALLC/ALLD, gra dawcy, mutacja 0,01)", "",
                "Przebiegi podzielone wg strony progu (pominięte |r̂ − c/b| ≤ 0,05).", ""] + detail + [""]
        out += render_table("Tabela zbiorcza – pary z P4", cols, table)
    return "\n".join(out)


if __name__ == "__main__":
    print(main(sys.argv[1:]))
