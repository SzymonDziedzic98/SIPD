"""
SIPD – przestrzenny iterowany dylemat więźnia.

Port modelu models/PD.gaml (GAMA) do czystego Pythona (tylko biblioteka standardowa),
uruchamialny lokalnie (CPython) i w przeglądarce (Pyodide, zob. web/index.html).

Odwzorowane: sieć ścieżek z GeoJSON (lub syntetyczna, gdy brak pliku), siatka komórek
z disorder, 9 charakterów, Q-learning per przeciwnik (stany RISKY/SAFE), pamięć społeczna
i środowiskowa, efekt rozbitej szyby, kotwica charakteru, limit gier (height), moduł 1
(limit Dunbara), typ gry, klasyczny start od C, metryki i eksporty CSV, eksperymenty
batch (A–F, E1–E3, R0) oraz testy z PD.gaml.

Kolejność kroku jak w GAMA: świat (reflexy globalne) -> environment_cell -> game -> player
(agenci w kolejności tworzenia, reflexy w kolejności deklaracji).

Różnice względem GAMA (nie da się ich usunąć):
- inny generator liczb losowych, więc wyniki zgadzają się statystycznie, a nie bit w bit;
- projekcja GeoJSON (lon/lat) to lokalne odwzorowanie równoodległościowe, nie UTM z GAMA;
- goto po sieci idzie krawędzią do sąsiedniego wierzchołka (w GAMA najkrótszą ścieżką -
  dla sąsiada to ta sama krawędź, chyba że istnieje krótsza objazdowa);
- wander w sztucznym świecie: przy wyjściu poza kwadrat losowany jest nowy kierunek.

Uruchomienie:
    python sipd.py --test                       # testy
    python sipd.py --gui-demo --cycles 500      # przebieg z parametrami podanymi w --set
    python sipd.py --experiment A_baseline --repeat 2 --end-cycle 2000 --geojson drogi.geojson
"""

import csv
import io
import itertools
import json
import math
import random
import sys
import time
import zlib

CHARACTERS = ["TFT", "QLEARN", "AQLEARN", "ALLC", "ALLD", "FTFT", "TF2T", "GRIM", "WSLS"]
CLASSIC = ["TFT", "ALLC", "ALLD", "FTFT", "TF2T", "GRIM", "WSLS"]
LEARNERS = ("QLEARN", "AQLEARN")
# kolejność tworzenia agentów w global.init (mapa counts w PD.gaml)
CREATION_ORDER = ["QLEARN", "AQLEARN", "TFT", "ALLC", "ALLD", "FTFT", "TF2T", "GRIM", "WSLS"]

# zmienne globalne z PD.gaml (wartości domyślne = eksperyment GUI "PD")
DEFAULTS = {
    "real_env": True,
    "unlimited_games": False,
    "show_social_links": True,
    "social_link_threshold": 0.3,
    "nb_QLEARN": 0, "nb_AQLEARN": 0, "nb_TFT": 0, "nb_ALLC": 0, "nb_ALLD": 0,
    "nb_FTFT": 0, "nb_TF2T": 0, "nb_GRIM": 0, "nb_WSLS": 0,
    "env_influence_qlearn": 0.0,
    "social_sensitivity_aqlearn": 0.0,
    "social_learning_boost_aqlearn": 0.0,
    "movement_sensitivity": 2.0,
    "broken_windows_sensitivity": 0.0,
    "disorder_bump_dd": 0.15,
    "disorder_bump_d": 0.08,
    "disorder_decay": 0.98,
    "disorder_clamp": False,
    "generalization_threshold": 3,
    "base_character_qlearn": "TFT",
    "character_strength_qlearn": 0.0,
    "anchor_decay_rate": 0.15,
    "end_cycle": 50000,
    "variant_name": "unset",
    "log_games": True,
    "regression_export": False,
    "regression_cycle": 2000,
    "perf_log": False,
    "perf_interval": 100,
    "dunbar_limit": 0,
    "partner_window": 500,
    "evolution_on": False,
    "evolution_interval": 100,
    "fermi_k": 0.5,
    "mutation_rate": 0.0,
    "evolvable_characters": ["TFT", "ALLC", "ALLD", "FTFT", "TF2T", "GRIM", "WSLS"],
    "well_mixed": False,
    "timeseries_export": False,
    "sample_interval": 100,
    "compat_core": False,
    "compat_N": 200,
    "compat_mix": "equal",
    "payoff_preset": "custom",
    "prediction": "",
    "compat_export": False,
    "warmup": 5000,
    "stab_window": 1000,
    "stab_eps": 0.02,
    "player_speed": 2.0,
    "stab_k": 5,
    "stab_trend_eps": 0.02,
    "movement_mode": "default",
    # warstwa projektowa
    "network_file": "",
    # U8: układ współrzędnych GeoJSON: "auto" (heurystyka zakresu), "geographic" (lon/lat), "projected" (metry)
    "geojson_crs": "auto",
    # U2: True = pomija zamknięte pętle i osadza agentów tylko na największej składowej
    # (domyślnie False = jak w PD.gaml: closest_to po wszystkich wierzchołkach)
    "network_cleanup": False,
    "network_variant": "baseline",
    "edge_removal_fraction": 0.2,
    "shortcut_count": 20,
    "shortcut_max_length": 100.0,
    "net_path_sources": 100,
    # stabilność spotkań
    "encounter_window": 1000,
    "encounter_export": False,
    # --- Moduł 3: pokrewieństwo (Hamilton); wymaga evolution_on ---
    "payoff_mode": "classic",          # "classic" | "donation" (R=b-c, S=-c, T=b, P=0)
    "b": 1.0,
    "c": 0.3,
    "kin_on": False,
    "family_size": 10,
    "family_r": 0.5,                   # nominalne r w rodzinie (do fitness_mode "inclusive")
    "kin_spatial_clustering": 0.0,     # 0 = losowe położenia, 1 = rodzina startuje w jednym węźle
    "kin_strategy_correlation": 0.0,   # P(członek dostaje strategię rodziny przy starcie)
    "kin_imitation_bias": 0.0,         # P(model do imitacji wybierany spośród krewnych)
    "kin_matching_prob": 0.0,          # α: P(partner spośród krewnych), tylko well_mixed
    "kin_matching_mode": "family",     # "family" = krewni; "strategy" = agenci z tą samą strategią (kontrola P4, r̂ = α)
    "fitness_mode": "own",             # "own" | "inclusive"
    "inclusive_variant": "strip",      # decyzja 19: "strip" (π + r·(dane - otrzymane)); "add" tylko do porównań
    "kin_reward_learners": False,      # QLEARN/AQLEARN: nagroda + r·wypłata krewnego (nie włączać bez zgody)
    "kin_window": 1000,                # okno r̂ (cykle)
    # ile cykli para nie może zagrać ponownie (życie agenta game w PD.gaml = 10); 0 = bez blokady
    "pair_cooldown": 10,
    "kin_export": False,               # family_timeseries.csv
    "vision_radius": 10,
    "world_size": 10,
    "payoff_R": 5.0, "payoff_P": 1.0, "payoff_T": 9.0, "payoff_S": 0.0,
    "game_type": "PD",
    "classic_start_cooperate": False,
    # tylko port Pythona: rozmiar syntetycznej sieci (gdy brak GeoJSON) - n x n węzłów co spacing m
    "synthetic_grid": 10,
    "synthetic_spacing": 60.0,
    "grid_cols": 50,
    "grid_rows": 50,
    "cell_learning_rate": 0.1,
    "selected_index": 0,
}

# parametry GUI w podziale na kategorie jak w experiment PD (etykiety z PD.gaml)
GUI_PARAMETERS = [
    ("Podgląd pamięci", [
        ("selected_index", "Wybrany agent (indeks)"),
        ("show_social_links", "Pokaż linie relacji społecznych"),
        ("social_link_threshold", "Próg rysowania linii"),
    ]),
    ("Ilości agentów", [
        ("nb_QLEARN", "Ilość agentów QLEARN"), ("nb_AQLEARN", "Ilość agentów AQLEARN"),
        ("nb_TFT", "Ilość agentów TFT"), ("nb_FTFT", "Ilość agentów FTFT"),
        ("nb_TF2T", "Ilość agentów TF2T"), ("nb_GRIM", "Ilość agentów GRIM"),
        ("nb_ALLC", "Ilość agentów ALLC"), ("nb_ALLD", "Ilość agentów ALLD"),
        ("nb_WSLS", "Ilość agentów WSLS"),
    ]),
    ("Środowisko", [
        ("real_env", "Prawdziwe środowisko"),
        ("unlimited_games", "Gry bez ograniczeń (bez blokady height)"),
        ("world_size", "Rozmiar świata (działa przy sztucznym środowisku)"),
        ("grid_cols", "Kolumny siatki"), ("grid_rows", "Wiersze siatki"),
        ("vision_radius", "Zasięg widzenia"),
        ("movement_sensitivity", "Czułość ruchu (środowisko)"),
        ("env_influence_qlearn", "Wpływ środowiska na decyzję QLEARN"),
        ("social_sensitivity_aqlearn", "Czułość społeczna AQLEARN"),
        ("social_learning_boost_aqlearn", "Wzmocnienie uczenia społecznego AQLEARN"),
        ("broken_windows_sensitivity", "Czułość na rozbitą szybę"),
        ("disorder_clamp", "Disorder ograniczony do [0, 1]"),
    ]),
    ("Gra", [
        ("game_type", "Typ gry"),
        ("payoff_T", "T (pokusa)"), ("payoff_R", "R (nagroda)"),
        ("payoff_P", "P (kara)"), ("payoff_S", "S (frajer)"),
        ("classic_start_cooperate", "TFT/TF2T/WSLS zaczynają od C"),
    ]),
    ("Moduł 1 – Dunbar", [
        ("dunbar_limit", "Limit Dunbara (0 = brak)"),
        ("partner_window", "Okno metryki partnerów (cykle)"),
    ]),
    ("Moduł 2 – ewolucja", [
        ("evolution_on", "Ewolucja strategii"),
        ("evolution_interval", "Co ile cykli"),
        ("fermi_k", "Szum selekcji K (Fermi)"),
        ("mutation_rate", "Prawdopodobieństwo mutacji"),
        ("evolvable_characters", "Charaktery podlegające ewolucji"),
        ("well_mixed", "Populacja dobrze wymieszana (bez przestrzeni)"),
    ]),
    ("Etap 1 – zgodność", [
        ("compat_core", "Rdzeń zgodności (compat_core)"),
        ("compat_N", "Liczebność rdzenia N"),
        ("compat_mix", "Skład rdzenia"),
        ("payoff_preset", "Macierz wypłat"),
        ("compat_export", "Eksport compat_results.csv"),
        ("player_speed", "Prędkość graczy (m/cykl)"),
    ]),
    ("Warstwa projektowa", [
        ("network_variant", "Wariant sieci"),
        ("edge_removal_fraction", "Udział usuwanych krawędzi (fragmented)"),
        ("shortcut_count", "Liczba skrótów (connected)"),
        ("shortcut_max_length", "Maks. długość skrótu (m)"),
    ]),
    ("Stabilność spotkań", [
        ("encounter_window", "Okno metryki spotkań (cykle)"),
    ]),
    ("Moduł 3 – pokrewieństwo", [
        ("kin_on", "Rodziny (wymaga ewolucji)"),
        ("payoff_mode", "Tryb wypłat"),
        ("b", "b (korzyść)"), ("c", "c (koszt)"),
        ("family_size", "Wielkość rodziny"), ("family_r", "r w rodzinie"),
        ("kin_spatial_clustering", "Skupienie przestrzenne rodzin"),
        ("kin_strategy_correlation", "Korelacja strategii w rodzinie"),
        ("kin_imitation_bias", "Imitacja krewnych"),
        ("kin_matching_prob", "α: dobór krewnych (well_mixed)"),
        ("kin_matching_mode", "Dobór α: rodzina / strategia"),
        ("fitness_mode", "Dopasowanie"), ("inclusive_variant", "Wariant inclusive"),
    ]),
    ("Diagnostyka", [
        ("timeseries_export", "Eksport szeregów czasowych"),
        ("sample_interval", "Co ile cykli próbka"),
        ("perf_log", "Pomiar czasu cyklu"),
        ("perf_interval", "Okno pomiaru (cykle)"),
        ("regression_export", "Eksport odcisku regresyjnego"),
        ("regression_cycle", "Cykl odcisku"),
    ]),
]
GAME_TYPES = ["PD", "weak_PD", "snowdrift"]
PAYOFF_PRESETS = {
    "PD_classic": ("PD", dict(payoff_T=9.0, payoff_R=5.0, payoff_P=1.0, payoff_S=0.0)),
    "weak_PD": ("weak_PD", dict(payoff_T=1.6, payoff_R=1.0, payoff_P=0.0, payoff_S=0.0)),
    "snowdrift": ("snowdrift", dict(payoff_T=4.0, payoff_R=3.0, payoff_S=2.0, payoff_P=0.0)),
}


class ModelError(Exception):
    """Odpowiednik `error` w GAML."""


class Params:
    def __init__(self, **overrides):
        self.__dict__.update({k: (list(v) if isinstance(v, list) else v) for k, v in DEFAULTS.items()})
        for k, v in overrides.items():
            if k not in DEFAULTS:
                raise KeyError("Nieznany parametr: " + k)
            setattr(self, k, v)

    def as_dict(self):
        return dict(self.__dict__)


# ---------------------------------------------------------------------------
# sieć ścieżek (path_network = as_edge_graph(path_segment))
# ---------------------------------------------------------------------------

def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _polyline_length(pts):
    return sum(_dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


class PathNetwork:
    """Graf nieskierowany: wierzchołki = końce odcinków, krawędzie = polilinie.

    drop_loops=False (jak as_edge_graph w GAMA): zamknięta polilinia (pierścień Polygon, zamknięty
    LineString) zostawia wierzchołek bez krawędzi (w GAMA: pętla na jednym wierzchołku). Agent osadzony
    tam stoi cały przebieg - w obu implementacjach. drop_loops=True pomija takie polilinie."""

    def __init__(self, polylines, width, height, source, drop_loops=False):
        self.width = width
        self.height = height
        self.source = source
        self.polylines = polylines            # do rysowania (path_segment / park_boundary)
        self.drop_loops = drop_loops
        self.edges_removed = 0                # U5: faktycznie usunięte krawędzie (wariant fragmented)
        self.vertices = []
        self.adj = {}                         # v -> {u: polilinia v..u (najkrótsza)}
        index = {}

        def vid(pt):
            key = (round(pt[0], 6), round(pt[1], 6))
            if key not in index:
                index[key] = len(self.vertices)
                self.vertices.append((pt[0], pt[1]))
                self.adj[index[key]] = {}
            return index[key]

        for pl in polylines:
            if len(pl) < 2:
                continue
            if drop_loops and (round(pl[0][0], 6), round(pl[0][1], 6)) == (round(pl[-1][0], 6), round(pl[-1][1], 6)):
                continue
            a, b = vid(pl[0]), vid(pl[-1])
            if a == b:
                continue
            length = _polyline_length(pl)
            old = self.adj[a].get(b)
            if old is None or _polyline_length(old) > length:
                self.adj[a][b] = list(pl)
                self.adj[b][a] = list(reversed(pl))

    # --- warstwa projektowa ---------------------------------------------
    @staticmethod
    def _edges(adj):
        return sorted((a, b) for a in adj for b in adj[a] if a < b)

    @staticmethod
    def _components(adj):
        seen, comps = set(), 0
        for v in adj:
            if v in seen or not adj[v]:
                continue
            comps += 1
            stack = [v]
            seen.add(v)
            while stack:
                x = stack.pop()
                for y in adj[x]:
                    if y not in seen:
                        seen.add(y)
                        stack.append(y)
        return comps

    def components(self):
        return self._components(self.adj)

    def variant(self, kind, rng, fraction=0.2, count=20, max_length=100.0):
        """Nowa sieć: "fragmented" albo "connected" (skróty).

        U5: "fragmented" usuwa tylko krawędzie leżące w cyklach (usunięcie nie zwiększa liczby składowych
        ani nie odcina węzła), zgodnie z CLAUDE.md - redukuje redundancję (mniej obejść, dłuższe ścieżki),
        a nie rozcina sieci. W sieci bliskiej drzewu docelowe edge_removal_fraction może nie zostać
        osiągnięte; faktyczna liczba usuniętych krawędzi to atrybut edges_removed (kolumna
        net_edges_removed)."""
        if kind == "baseline":
            return self
        adj = {v: dict(nb) for v, nb in self.adj.items()}
        comps0 = self._components(adj)
        removed = 0
        if kind == "fragmented":
            edges = self._edges(adj)
            rng.shuffle(edges)
            target, removed = int(len(edges) * fraction + 0.5), 0
            for a, b in edges:
                if removed >= target:
                    break
                if len(adj[a]) <= 1 or len(adj[b]) <= 1:      # usunięcie odcięłoby węzeł
                    continue
                pa, pb = adj[a].pop(b), adj[b].pop(a)
                if self._components(adj) > comps0:
                    adj[a][b], adj[b][a] = pa, pb
                    continue
                removed += 1
        elif kind == "connected":
            vs = self.vertices
            cand = [(i, j) for i in range(len(vs)) for j in range(i + 1, len(vs))
                    if j not in adj[i] and _dist(vs[i], vs[j]) < max_length]
            rng.shuffle(cand)
            for i, j in cand[:count]:
                adj[i][j] = [vs[i], vs[j]]
                adj[j][i] = [vs[j], vs[i]]
        else:
            raise ModelError("Nieznany network_variant: %s" % kind)
        polylines = [adj[a][b] for a, b in self._edges(adj)]
        net = PathNetwork(polylines, self.width, self.height, self.source + "/" + kind,
                          drop_loops=getattr(self, "drop_loops", False))
        net.edges_removed = removed if kind == "fragmented" else 0
        return net

    def stats(self, path_sources=100):
        """Węzły, krawędzie, średni stopień, średnia najkrótsza ścieżka (kroki, z pierwszych węzłów),
        gęstość, betweenness (Brandes, znormalizowana przez (n-1)(n-2)/2) - max i średnia."""
        if getattr(self, "_stats", None) is not None and self._stats[0] == path_sources:
            return self._stats[1]
        adj = self.adj
        vs = [v for v in adj if adj[v]]
        n = len(vs)
        e = len(self._edges(adj))
        total = pairs = 0
        for src in vs[:path_sources]:
            dist = {src: 0}
            frontier = [src]
            while frontier:
                nxt = []
                for x in frontier:
                    for y in adj[x]:
                        if y not in dist:
                            dist[y] = dist[x] + 1
                            nxt.append(y)
                frontier = nxt
            total += sum(dist.values())
            pairs += len(dist) - 1
        bc = dict.fromkeys(vs, 0.0)
        for s0 in vs:
            stack, pred, sigma, dist = [], {v: [] for v in vs}, dict.fromkeys(vs, 0), {s0: 0}
            sigma[s0] = 1
            queue = [s0]
            qi = 0
            while qi < len(queue):
                v = queue[qi]
                qi += 1
                stack.append(v)
                for w in adj[v]:
                    if w not in dist:
                        dist[w] = dist[v] + 1
                        queue.append(w)
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        pred[w].append(v)
            delta = dict.fromkeys(vs, 0.0)
            while stack:
                w = stack.pop()
                for v in pred[w]:
                    delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
                if w != s0:
                    bc[w] += delta[w]
        norm = (n - 1) * (n - 2) / 2.0 if n > 2 else 1.0
        vals = [x / 2.0 / norm for x in bc.values()]            # nieskierowany: każda para liczona 2x
        st = dict(net_nodes=n, net_edges=e, net_mean_degree=2 * e / n if n else 0.0,
                  net_avg_path=total / pairs if pairs else 0.0,
                  net_density=2 * e / (n * (n - 1)) if n > 1 else 0.0,
                  net_betw_max=max(vals) if vals else 0.0,
                  net_betw_mean=sum(vals) / len(vals) if vals else 0.0)
        self._stats = (path_sources, st)
        return st

    def largest_component(self):
        """Wierzchołki największej składowej (bez wierzchołków bez krawędzi), w kolejności indeksów."""
        if getattr(self, "_largest", None) is None:
            seen, best = set(), []
            for v in sorted(self.adj):
                if v in seen or not self.adj[v]:
                    continue
                comp, stack = [v], [v]
                seen.add(v)
                while stack:
                    x = stack.pop()
                    for y in self.adj[x]:
                        if y not in seen:
                            seen.add(y)
                            comp.append(y)
                            stack.append(y)
                if len(comp) > len(best):
                    best = comp
            self._largest = sorted(best)
        return self._largest

    def closest_vertex(self, pt, largest_only=False):
        cand = self.largest_component() if largest_only else range(len(self.vertices))
        if not self.vertices or not cand:
            return None
        return min(cand, key=lambda i: _dist(self.vertices[i], pt))

    def neighbors(self, v):
        return list(self.adj.get(v, {}).keys())

    @classmethod
    def from_geojson(cls, data, drop_loops=False, crs="auto"):
        if isinstance(data, str):
            data = json.loads(data)
        lines = []

        def add_geom(g):
            if not g:
                return
            t = g.get("type")
            c = g.get("coordinates")
            if t == "LineString":
                lines.append(c)
            elif t == "MultiLineString":
                lines.extend(c)
            elif t == "Polygon":
                lines.extend(c)
            elif t == "MultiPolygon":
                for poly in c:
                    lines.extend(poly)
            elif t == "GeometryCollection":
                for sub in g.get("geometries", []):
                    add_geom(sub)

        if data.get("type") == "FeatureCollection":
            for f in data.get("features", []):
                add_geom(f.get("geometry"))
        elif data.get("type") == "Feature":
            add_geom(data.get("geometry"))
        else:
            add_geom(data)
        lines = [[(float(p[0]), float(p[1])) for p in ln] for ln in lines if len(ln) >= 2]
        if not lines:
            raise ModelError("GeoJSON nie zawiera linii.")

        xs = [p[0] for ln in lines for p in ln]
        ys = [p[1] for ln in lines for p in ln]
        if crs not in ("auto", "geographic", "projected"):
            raise ModelError("geojson_crs musi być auto, geographic albo projected: %s" % crs)
        # "auto" myli lokalne układy metryczne o małych wartościach z lon/lat - wtedy podaj "projected"
        geographic = crs == "geographic" or (crs == "auto" and all(-180 <= x <= 180 for x in xs)
                                             and all(-90 <= y <= 90 for y in ys))
        if geographic:
            # lokalne odwzorowanie równoodległościowe -> metry (GAMA: automatycznie UTM)
            lat0 = math.radians((min(ys) + max(ys)) / 2)
            r = 6371008.8
            lines = [[(math.radians(x) * r * math.cos(lat0), math.radians(y) * r) for x, y in ln]
                     for ln in lines]
            xs = [p[0] for ln in lines for p in ln]
            ys = [p[1] for ln in lines for p in ln]
        minx, maxy = min(xs), max(ys)
        # jak w GAMA: początek układu w rogu obwiedni, oś y w dół (północ u góry)
        lines = [[(x - minx, maxy - y) for x, y in ln] for ln in lines]
        return cls(lines, max(xs) - minx, maxy - min(ys), "geojson", drop_loops=drop_loops)

    @classmethod
    def synthetic(cls, seed=12345, n=10, spacing=60.0):
        """Zastępcza 'parkowa' sieć (zaszumiona siatka + kilka przekątnych), gdy brak drogi.geojson."""
        rng = random.Random(seed)
        pts = {}
        for i in range(n):
            for j in range(n):
                pts[(i, j)] = (spacing * (i + 0.5) + rng.uniform(-15, 15),
                               spacing * (j + 0.5) + rng.uniform(-15, 15))
        lines = []
        for i in range(n):
            for j in range(n):
                if i + 1 < n and rng.random() > 0.12:
                    lines.append([pts[(i, j)], pts[(i + 1, j)]])
                if j + 1 < n and rng.random() > 0.12:
                    lines.append([pts[(i, j)], pts[(i, j + 1)]])
                if i + 1 < n and j + 1 < n and rng.random() < 0.15:
                    lines.append([pts[(i, j)], pts[(i + 1, j + 1)]])
        size = spacing * n
        return cls(lines, size, size, "synthetic")


# ---------------------------------------------------------------------------
# agenci
# ---------------------------------------------------------------------------

class KinStats:
    """Sumy do r̂ (regresja ruchu partnera na własny ruch, C=1, D=0) i udziałów interakcji z krewnymi.
    Każda gra daje dwie pary uporządkowane (x=mój ruch, y=ruch partnera)."""

    def __init__(self):
        self.all = [0, 0.0, 0.0, 0.0, 0.0]      # n, Σx, Σy, Σxy, Σx² (całe okno, bez podziału)
        self.kin = [0, 0.0, 0.0, 0.0, 0.0]
        # r̂ w obrębie bloków o stałym składzie (blok = interwał ewolucji): sumy bieżącego bloku
        # i skumulowane Sxy, Sxx zamkniętych bloków; usuwa pozorną korelację ze zmian składu w czasie
        self.blk_all = [0, 0.0, 0.0, 0.0, 0.0]
        self.blk_kin = [0, 0.0, 0.0, 0.0, 0.0]
        self.fe_all = [0.0, 0.0]
        self.fe_kin = [0.0, 0.0]
        self.games = self.kin_games = 0
        self.coop_kin = self.moves_kin = self.coop_str = self.moves_str = 0

    @staticmethod
    def _add(s, x, y):
        s[0] += 1
        s[1] += x
        s[2] += y
        s[3] += x * y
        s[4] += x * x

    def record(self, m1, m2, kin):
        x1, x2 = (m1 == "C") * 1.0, (m2 == "C") * 1.0
        self.games += 1
        for x, y in ((x1, x2), (x2, x1)):
            self._add(self.all, x, y)
            self._add(self.blk_all, x, y)
            if kin:
                self._add(self.kin, x, y)
                self._add(self.blk_kin, x, y)
        if kin:
            self.kin_games += 1
            self.coop_kin += int(x1 + x2)
            self.moves_kin += 2
        else:
            self.coop_str += int(x1 + x2)
            self.moves_str += 2

    @staticmethod
    def r_hat(s):
        """Nachylenie regresji y na x; None, gdy x nie ma zmienności."""
        n, sx, sy, sxy, sxx = s
        den = n * sxx - sx * sx
        return None if n < 2 or den == 0 else (n * sxy - sx * sy) / den

    @staticmethod
    def _within(b):
        """(Sxy, Sxx) bloku: odchylenia od średnich bloku."""
        n, sx, sy, sxy, sxx = b
        return (0.0, 0.0) if n == 0 else (sxy - sx * sy / n, sxx - sx * sx / n)

    def close_block(self):
        """Zamyka blok (przed zmianą składu populacji, np. przed krokiem ewolucji)."""
        for b, fe in ((self.blk_all, self.fe_all), (self.blk_kin, self.fe_kin)):
            sxy, sxx = self._within(b)
            fe[0] += sxy
            fe[1] += sxx
            b[:] = [0, 0.0, 0.0, 0.0, 0.0]

    @classmethod
    def r_hat_within(cls, b, fe):
        """r̂ = Σ Sxy / Σ Sxx po blokach (z otwartym blokiem); None, gdy brak zmienności x."""
        sxy, sxx = cls._within(b)
        sxy, sxx = fe[0] + sxy, fe[1] + sxx
        return None if sxx <= 1e-12 else sxy / sxx

    def summary(self):
        return dict(r_hat_all=self.r_hat_within(self.blk_all, self.fe_all),
                    r_hat_kin=self.r_hat_within(self.blk_kin, self.fe_kin),
                    r_hat_all_pooled=self.r_hat(self.all),
                    kin_share=self.kin_games / self.games if self.games else None,
                    coop_kin=self.coop_kin / self.moves_kin if self.moves_kin else None,
                    coop_str=self.coop_str / self.moves_str if self.moves_str else None)


class Cell:
    __slots__ = ("index", "col", "row", "disorder", "x0", "y0", "w", "h", "enc_games", "enc_rep_rem",
                 "enc_rep_ever", "last_share_rem", "last_share_ever", "total_games", "total_rep_rem",
                 "total_rep_ever")

    def __init__(self, index, col, row, x0, y0, w, h):
        self.index, self.col, self.row = index, col, row
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.disorder = 0.0
        self.enc_games = self.enc_rep_rem = self.enc_rep_ever = 0
        self.total_games = self.total_rep_rem = self.total_rep_ever = 0
        self.last_share_rem = self.last_share_ever = -1.0

    def record_encounter(self, rem, ever):
        self.enc_games += 1
        self.total_games += 1
        if rem:
            self.enc_rep_rem += 1
            self.total_rep_rem += 1
        if ever:
            self.enc_rep_ever += 1
            self.total_rep_ever += 1

    def close_window(self):
        self.last_share_rem = -1.0 if self.enc_games == 0 else self.enc_rep_rem / self.enc_games
        self.last_share_ever = -1.0 if self.enc_games == 0 else self.enc_rep_ever / self.enc_games
        self.enc_games = self.enc_rep_rem = self.enc_rep_ever = 0

    def apply_decay(self, model):
        self.disorder = self.disorder * model.p.disorder_decay

    def __repr__(self):
        return "environment_cell(%d)" % self.index


class Game:
    """species game – cała rozgrywka dzieje się w init (konstruktorze)."""

    def __init__(self, model, p1, p2, pair_key, location=None):
        self.model = model
        self.pair_key = pair_key
        self.p1, self.p2 = p1, p2
        self.lifespan = model.p.pair_cooldown
        self.location = location
        m, P = model, model.p

        m.nb_game += 1
        # stan wiedzy PRZED grą (metryka stabilności spotkań)
        self.knew1_rem, self.knew1_ever = p2 in p1.known_others, p2 in p1.met_count
        self.knew2_rem, self.knew2_ever = p1 in p2.known_others, p1 in p2.met_count
        p1.ensure_partner(p2)
        p2.ensure_partner(p1)
        self.p1_move = p1.strategy(p2)
        self.p2_move = p2.strategy(p1)
        p1_move, p2_move = self.p1_move, self.p2_move

        fb_p1 = m.feedback_value(p1_move, p2_move)
        fb_p2 = m.feedback_value(p2_move, p1_move)
        cell_p1 = m.cell_at(p1.location)
        cell_p2 = m.cell_at(p2.location)
        self.cell1, self.cell2 = cell_p1, cell_p2

        p1.update_personal_feedback(cell_p1, fb_p1)
        p1.update_social_feedback(p2, fb_p1)
        if p2_move == "D":
            p1.register_betrayal(cell_p1)
        p2.update_personal_feedback(cell_p2, fb_p2)
        p2.update_social_feedback(p1, fb_p2)
        if p1_move == "D":
            p2.register_betrayal(cell_p2)

        p1_payoff = p2_payoff = 0.0
        if p1_move == "D" and p2_move == "D":
            p1_payoff = p2_payoff = P.payoff_P
        elif p1_move == "C" and p2_move == "C":
            p1_payoff = p2_payoff = P.payoff_R
        elif p1_move == "D" and p2_move == "C":
            p2_payoff, p1_payoff = P.payoff_S, P.payoff_T
        elif p1_move == "C" and p2_move == "D":
            p2_payoff, p1_payoff = P.payoff_T, P.payoff_S

        m.nb_moves_D += (p1_move == "D") + (p2_move == "D")
        m.nb_moves_C += (p1_move == "C") + (p2_move == "C")
        if {p1_move, p2_move} == {"C", "D"}:
            m.nb_exploitations += 1

        bump = m.disorder_bump_for(p1_move, p2_move)
        if bump > 0:
            for cell in ([cell_p1] + ([cell_p2] if cell_p2 is not cell_p1 else [])):
                if cell is not None:
                    cell.disorder = min(1.0, cell.disorder + bump) if P.disorder_clamp else cell.disorder + bump

        if P.unlimited_games:
            p2.score += p2_payoff
            p1.score += p1_payoff
        else:
            p2.height += int(p2_payoff)
            p1.height += int(p1_payoff)

        p2.lists_per_other[p1].append(p1_move)
        p2.my_moves_per_other[p1].append(p2_move)
        p1.lists_per_other[p2].append(p2_move)
        p1.my_moves_per_other[p2].append(p1_move)

        p1.nb_games += 1
        p2.nb_games += 1

        # Moduł 2: π = średnia wypłata na grę w bieżącym oknie ewolucji
        p1.window_payoff += p1_payoff
        p1.window_games += 1
        p2.window_payoff += p2_payoff
        p2.window_games += 1

        # Moduł 3: skutek mojego ruchu dla krewnego = jego wypłata minus jego wypłata, gdybym zagrał D
        kin = P.kin_on and p1.family_id >= 0 and p1.family_id == p2.family_id
        if P.kin_on and p1_move in ("C", "D") and p2_move in ("C", "D"):
            m.kin_stats.record(p1_move, p2_move, kin)
            m.kin_window_stats.record(p1_move, p2_move, kin)
            if kin:
                d12 = m.payoff_of(p2_move, p1_move) - m.payoff_of(p2_move, "D")
                d21 = m.payoff_of(p1_move, p2_move) - m.payoff_of(p1_move, "D")
                p1.window_kin_given += d12
                p2.window_kin_received += d12
                p2.window_kin_given += d21
                p1.window_kin_received += d21

        r1, r2 = p1_payoff, p2_payoff
        if kin and P.kin_reward_learners:        # preferencja, nie selekcja - nie w teście Hamiltona
            r1, r2 = p1_payoff + P.family_r * p2_payoff, p2_payoff + P.family_r * p1_payoff
        if p1.character in LEARNERS:
            p1.update_q(p2, r1)
        if p2.character in LEARNERS:
            p2.update_q(p1, r2)

        p1.touch_partner(p2)
        p2.touch_partner(p1)
        m.on_game_played(self)

        if P.log_games:
            row = [m.nb_game, m.cycle, p1.name, p2.name, p1_move, p2_move, p1.score, p2.score]
            m.game_log.append(row)
            if m.echo_games:
                print(",".join(str(x) for x in row))

    def step(self):
        self.lifespan -= 1
        if self.lifespan <= 0:               # <= : przy pair_cooldown = 0 gra znika w następnym kroku
            self.model.active_pairs.pop(self.pair_key, None)
            return False
        return True


class Player:
    def __init__(self, model, name, character, **attrs):
        self.model = model
        self.name = name
        rng = model.rng
        # atrybuty jak w species player (inicjalizatory przed facetami create)
        self.height = 0
        self.score = 0.0
        self.known_others = []
        self.last_met_cycle = {}
        self.nb_forgotten = 0
        self.window_payoff = 0.0
        self.window_games = 0
        self.family_id = -1                # Moduł 3: stały przez cały przebieg
        self.window_kin_given = 0.0        # Σ skutków moich ruchów dla krewnych w oknie
        self.window_kin_received = 0.0     # Σ skutków ruchów krewnych dla mnie w oknie
        self.history_offset = {}
        self.met_count = {}           # metryka: gry z partnerem od początku (zapominanie jej nie rusza)
        self.enc_games = self.enc_rep_rem = self.enc_rep_ever = 0
        self.enc_partners = set()
        self.character = character
        self.enemy = None
        self.forgiveness = 0.05
        self.nb_games = 0
        self.current_node = None
        self.target_node = None
        self.path = None           # polilinia bieżącego ruchu po krawędzi
        self.path_pos = 0.0
        self.move_speed = 2.0
        self.sensitivity = 2.0
        self.social_feedback = {}
        self.social_learning_rate = 0.1
        self.social_sensitivity = 0.0
        self.social_learning_boost = 0.0
        self.env_influence = 0.0
        self.initial_cooperation_bias = min(1.0, max(0.0, rng.gauss(0.5, 0.15)))
        self.base_character = "TFT"
        self.character_strength = 0.0
        self.betrayal_count_at_location = {}
        self.personal_feedback = {}
        self.lists_per_other = {}
        self.my_moves_per_other = {}
        self.q_d_per_other = {}
        self.q_c_per_other = {}
        self.pending_state = {}
        self.pending_action = {}
        self.learning_rate = 0.1
        self.discount = 0.9
        self.epsilon = 0.15
        self.heading = rng.uniform(0, 360)
        self.speed = 1.0           # domyślna prędkość skill moving (wander)
        self.idx = None            # kolejność utworzenia (ustawia Model.create_player)
        self._loc = (rng.uniform(0, model.width), rng.uniform(0, model.height))
        for k, v in attrs.items():
            if not hasattr(self, k):
                raise KeyError("Nieznany atrybut gracza: " + k)
            setattr(self, k, v)

    def __repr__(self):
        return self.name

    @property
    def location(self):
        return self._loc

    @location.setter
    def location(self, value):
        old = self._loc
        self._loc = value
        self.model._moved(self, old)

    # --- parametry i pamięć partnerów -----------------------------------
    def apply_character_params(self):
        P = self.model.p
        self.sensitivity = P.movement_sensitivity
        self.move_speed = P.player_speed
        if self.character == "AQLEARN":
            self.social_sensitivity = P.social_sensitivity_aqlearn
            self.social_learning_boost = P.social_learning_boost_aqlearn
        if self.character in LEARNERS:
            self.env_influence = P.env_influence_qlearn
            self.base_character = P.base_character_qlearn
            self.character_strength = P.character_strength_qlearn

    def ensure_partner(self, other):
        if other not in self.lists_per_other:
            self.init_beliefs_for(other)

    def init_beliefs_for(self, other):
        """Przekonania o nowym/zapomnianym partnerze - jedno miejsce (Faza 6: stereotyp miejsca)."""
        self.lists_per_other[other] = []
        self.my_moves_per_other[other] = []
        self.q_d_per_other[other] = {}
        self.q_c_per_other[other] = {}

    def record_encounter(self, other, rem, ever, cell):
        self.enc_games += 1
        self.enc_rep_rem += rem
        self.enc_rep_ever += ever
        self.enc_partners.add(other)
        self.met_count[other] = self.met_count.get(other, 0) + 1
        if cell is not None:
            cell.record_encounter(rem, ever)

    def setup_lists(self):
        for other in self.model.players:
            if other is not self:
                self.ensure_partner(other)
                other.ensure_partner(self)

    def touch_partner(self, other):
        if other in self.known_others:
            self.known_others.remove(other)
        self.known_others.append(other)
        self.last_met_cycle[other] = self.model.cycle
        limit = self.model.p.dunbar_limit
        if limit > 0:
            while len(self.known_others) > limit:
                self.forget_partner(self.known_others[0])

    def forget_partner(self, other):
        if other in self.known_others:
            self.known_others.remove(other)
        for mp in (self.lists_per_other, self.my_moves_per_other, self.q_c_per_other,
                   self.q_d_per_other, self.pending_state, self.pending_action,
                   self.social_feedback, self.history_offset):
            mp.pop(other, None)
        self.nb_forgotten += 1
        self.model.nb_forgets_total += 1

    def distinct_partners_in_window(self):
        since = self.model.cycle - self.model.p.partner_window
        for k in [k for k, c in self.last_met_cycle.items() if c < since]:
            del self.last_met_cycle[k]
        return len(self.last_met_cycle)

    # --- Moduł 2: ewolucja -----------------------------------------------
    def relatives(self):
        if self.family_id < 0:
            return []
        return [q for q in self.model.families[self.family_id] if q is not self]

    def pick_model(self):
        m = self.model
        if m.p.kin_on and m.p.kin_imitation_bias > 0 and self.flip(m.p.kin_imitation_bias):
            rel = self.relatives()                 # krewni niezależnie od odległości
            if rel:
                return m.rng.choice(rel)
        if m.p.well_mixed:
            pool = [q for q in m.players if q is not self]
        else:
            pool = m.players_within(self, m.p.vision_radius)
        return m.rng.choice(pool) if pool else None

    def evolution_choice(self, model):
        P = self.model.p
        if self.flip(P.mutation_rate):
            return self.model.rng.choice(P.evolvable_characters)
        if model is None or model is self or model.character not in P.evolvable_characters:
            return self.character
        if self.window_games == 0 or model.window_games == 0:
            return self.character
        pi_self = self.compute_pi()
        pi_model = model.compute_pi()
        return model.character if self.flip(self.model.fermi_probability(pi_model, pi_self)) else self.character

    def compute_pi(self):
        """π do ewolucji - jedno miejsce.
        "own": średnia własna wypłata na grę.
        "inclusive" (Moduł 3, DO DECYZJI):
          "add":   π_own + r · Σ(skutek moich ruchów dla krewnych) / gry
          "strip": π_own + r · (Σ skutek moich ruchów dla krewnych - Σ skutek ruchów krewnych dla mnie) / gry
        skutek = wypłata partnera przy moim ruchu minus jego wypłata, gdybym zagrał D (gra dawcy: C -> b)."""
        if not self.window_games:
            return 0.0
        own = self.window_payoff / self.window_games
        P = self.model.p
        if P.kin_on and P.fitness_mode == "inclusive":
            kin_term = self.window_kin_given
            if P.inclusive_variant == "strip":
                kin_term -= self.window_kin_received
            return own + P.family_r * kin_term / self.window_games
        return own

    def change_character(self, new_char):
        if new_char == self.character:
            return
        self.character = new_char
        self.apply_character_params()
        for o, h in self.lists_per_other.items():
            self.history_offset[o] = len(h)
        self.model.nb_character_changes += 1

    # --- pamięć miejsc i relacji ----------------------------------------
    def register_betrayal(self, cell):
        if cell is None:
            return
        self.betrayal_count_at_location[cell] = self.betrayal_count_at_location.get(cell, 0) + 1

    def update_personal_feedback(self, cell, value):
        if cell is None:
            return
        old = self.personal_feedback.get(cell, 0.0)
        self.personal_feedback[cell] = old + self.model.p.cell_learning_rate * (value - old)

    def update_social_feedback(self, opponent, value):
        old = self.social_feedback.get(opponent, 0.0)
        self.social_feedback[opponent] = old + self.social_learning_rate * (value - old)

    @property
    def for_chart(self):
        return (self.score / self.nb_games * 1000) if self.nb_games > 0 else 0.0

    # --- stan Q i kotwica -----------------------------------------------
    def get_state(self, p):
        if self.lists_per_other[p] == []:
            base = "START"
        else:
            base = self.my_moves_per_other[p][-1] + "|" + self.lists_per_other[p][-1]
        here = self.model.cell_at(self.location)
        risky = (here is not None and
                 self.betrayal_count_at_location.get(here, 0) >= self.model.p.generalization_threshold
                 and here in self.betrayal_count_at_location)
        return base + "|" + ("RISKY" if risky else "SAFE")

    def character_suggested_move(self, p):
        fn = {"TFT": self.TFT, "ALLC": self.ALLC, "ALLD": self.ALLD, "FTFT": self.FTFT,
              "TF2T": self.TF2T, "GRIM": self.GRIM, "WSLS": self.WSLS}.get(self.base_character)
        return fn(p) if fn else "C"

    def effective_anchor_strength(self, p):
        P = self.model.p
        n = len(self.lists_per_other[p])
        base = self.character_strength * math.exp(-P.anchor_decay_rate * n)
        here = self.model.cell_at(self.location)
        erosion = (1 - P.broken_windows_sensitivity * here.disorder) if here is not None else 1.0
        erosion = max(0.0, erosion)
        return max(0.0, min(1.0, base * erosion))

    def ensure_q_state(self, opponent, s):
        if s not in self.q_d_per_other[opponent]:
            self.q_d_per_other[opponent][s] = 1 - self.initial_cooperation_bias
            self.q_c_per_other[opponent][s] = self.initial_cooperation_bias

    def update_q(self, opponent, reward):
        s = self.pending_state[opponent]
        a = self.pending_action[opponent]
        old_q = self.q_d_per_other[opponent][s] if a == "D" else self.q_c_per_other[opponent][s]
        next_s = self.get_state(opponent)
        self.ensure_q_state(opponent, next_s)
        max_next_q = max(self.q_d_per_other[opponent][next_s], self.q_c_per_other[opponent][next_s])
        social_pref = self.social_feedback.get(opponent, 0.0)
        effective_lr = self.learning_rate * (1 + self.social_learning_boost * social_pref)
        effective_lr = max(0.01, min(0.99, effective_lr))
        new_q = old_q + effective_lr * (reward + self.discount * max_next_q - old_q)
        if a == "D":
            self.q_d_per_other[opponent][s] = new_q
        else:
            self.q_c_per_other[opponent][s] = new_q

    # --- strategie -----------------------------------------------------
    def flip(self, prob):
        return self.model.rng.random() < prob

    def strategy(self, p):
        P = self.model.p
        if not P.unlimited_games and self.height != 0:
            return None
        ch = self.character
        if ch in LEARNERS:
            base_move = self.QLEARN(p)
        else:
            fn = {"TFT": self.TFT, "ALLC": self.ALLC, "ALLD": self.ALLD, "FTFT": self.FTFT,
                  "TF2T": self.TF2T, "GRIM": self.GRIM, "WSLS": self.WSLS}.get(ch)
            if fn is None:
                raise ModelError("Nieznany charakter: %s" % ch)
            base_move = fn(p)
        if base_move == "C" and P.broken_windows_sensitivity > 0:
            here = self.model.cell_at(self.location)
            local_disorder = here.disorder if here is not None else 0.0
            if self.flip(min(0.9, P.broken_windows_sensitivity * local_disorder)):
                base_move = "D"
        if ch in LEARNERS and p in self.pending_action:
            self.pending_action[p] = base_move   # domknięcie: pending_action = to, co naprawdę zagrano
        return base_move

    def _random_start(self):
        if self.model.p.classic_start_cooperate:
            return "C"
        return "C" if self.flip(0.5) else "D"

    def TFT(self, p):
        h = self.lists_per_other[p]
        if h == []:
            return self._random_start()
        return "C" if h[-1] == "C" else "D"

    def ALLD(self, p):
        return "D"

    def ALLC(self, p):
        return "C"

    def FTFT(self, p):
        h = self.lists_per_other[p]
        if h == []:
            return "C"
        if h[-1] == "C":
            return "C"
        if h[-1] == "D" and self.flip(self.forgiveness):
            return "C"
        return "D"

    def TF2T(self, p):
        h = self.lists_per_other[p]
        if h == []:
            return self._random_start()
        return "C" if h[-2:] != ["D", "D"] else "D"

    def GRIM(self, p):
        since = self.history_offset.get(p, 0)
        h = self.lists_per_other[p]
        return "D" if "D" in (h if since == 0 else h[since:]) else "C"

    def WSLS(self, p):
        h = self.lists_per_other[p]
        if h == []:
            return self._random_start()
        my_last = self.my_moves_per_other[p][-1]
        if h[-1] == "C":
            return my_last
        return "D" if my_last == "C" else "C"

    def QLEARN(self, p):
        s = self.get_state(p)
        self.ensure_q_state(p, s)
        here = self.model.cell_at(self.location)
        env_fb = self.personal_feedback.get(here, 0.0) if here is not None else 0.0
        adjusted_q_d = self.q_d_per_other[p][s] - self.env_influence * env_fb
        adjusted_q_c = self.q_c_per_other[p][s] + self.env_influence * env_fb
        if self.flip(self.epsilon):
            action = "D" if self.flip(0.5) else "C"
        elif adjusted_q_d == adjusted_q_c:
            action = "D" if self.flip(0.5) else "C"   # remis rozstrzygany losowo
        else:
            action = "D" if adjusted_q_d > adjusted_q_c else "C"
        if self.character_strength > 0:
            if self.flip(self.effective_anchor_strength(p)):
                action = self.character_suggested_move(p)
        self.pending_state[p] = s
        self.pending_action[p] = action
        return action

    # --- ruch ------------------------------------------------------------
    def init_on_network(self):
        net = self.model.network
        self.current_node = net.closest_vertex(self.location, largest_only=self.model.p.network_cleanup)
        self.location = net.vertices[self.current_node]

    def social_score(self, candidate):
        s_s = 0.0
        cur = self.model.network.vertices[self.current_node]
        for p, pref in self.social_feedback.items():
            dist_now = _dist(cur, p.location)
            dist_candidate = _dist(candidate, p.location)
            s_s += pref * (dist_now - dist_candidate) / max(1.0, self.move_speed)
        return s_s / max(1, len(self.social_feedback))

    def choose_direction(self, candidates):
        """Wybór następnego węzła - jedno miejsce na tryby ruchu (Faza 5: "schelling")."""
        if self.model.p.movement_mode == "schelling":
            raise ModelError("movement_mode = schelling: do implementacji w Fazie 5.")
        return self.weighted_next_node(candidates)

    def weighted_next_node(self, candidates):
        net = self.model.network
        logits = []
        for c in candidates:
            pt = net.vertices[c]
            cell = self.model.cell_at(pt)
            fb = self.personal_feedback.get(cell, 0.0) if cell is not None else 0.0
            social = self.social_score(pt) if self.social_sensitivity > 0 else 0.0
            logits.append(self.sensitivity * fb + self.social_sensitivity * social)
        mx = max(logits)
        weights = [math.exp(l - mx) for l in logits]   # rnd_choice normalizuje wagi
        return self.model.rng.choices(candidates, weights=weights)[0]

    def _at_target(self):
        return (self.target_node is not None and
                self.location == self.model.network.vertices[self.target_node])

    def reflex_choose_target(self):
        net = self.model.network
        neighbors = net.neighbors(self.current_node)
        if not neighbors:
            self.target_node = self.current_node
            self.path = None
        else:
            new_target = self.choose_direction(neighbors)
            self.path = net.adj[self.current_node][new_target]
            self.path_pos = 0.0
            self.target_node = new_target
            self.current_node = new_target

    def reflex_move_on_network(self):
        # goto(target, on: path_network, speed: move_speed) - wzdłuż polilinii krawędzi
        if not self.path:
            self.location = self.model.network.vertices[self.target_node]
            return
        remaining = self.move_speed
        pts = self.path
        pos = self.path_pos + remaining
        acc = 0.0
        for i in range(len(pts) - 1):
            seg = _dist(pts[i], pts[i + 1])
            if acc + seg >= pos:
                t = (pos - acc) / seg if seg > 0 else 1.0
                self.location = (pts[i][0] + t * (pts[i + 1][0] - pts[i][0]),
                                 pts[i][1] + t * (pts[i + 1][1] - pts[i][1]))
                self.path_pos = pos
                if i == len(pts) - 2 and t >= 1.0:
                    self.location = self.model.network.vertices[self.target_node]
                return
            acc += seg
        self.location = self.model.network.vertices[self.target_node]
        self.path_pos = acc

    def reflex_wander(self):
        rng = self.model.rng
        self.heading += rng.uniform(-45.0, 45.0)
        x = self.location[0] + self.speed * math.cos(math.radians(self.heading))
        y = self.location[1] + self.speed * math.sin(math.radians(self.heading))
        if not (0 <= x <= self.model.width and 0 <= y <= self.model.height):
            self.heading = rng.uniform(0, 360)
            x = min(max(x, 0.0), self.model.width)
            y = min(max(y, 0.0), self.model.height)
        self.location = (x, y)

    def reflex_height_decay(self):
        """Tryb z limitem gier: wypłata trafia do height (blokada) i przechodzi do score po 1 na cykl.
        U7: to, co zostało w height w ostatnim cyklu, nie trafia do score (tak samo w PD.gaml), więc
        mean_for/for_chart lekko zaniżają wynik świeżo grających agentów. Eksperymenty zgodności używają
        unlimited_games=True, gdzie tego efektu nie ma."""
        if self.height > 0:
            self.height -= 1
            self.score += 1

    def reflex_do_you_wanna_play(self):
        m, P = self.model, self.model.p
        if P.well_mixed and P.kin_on and P.kin_matching_prob > 0 and self.flip(P.kin_matching_prob):
            if P.kin_matching_mode == "strategy":  # kontrola P4: partner z tą samą strategią
                nearby = [q for q in m.players if q is not self and q.character == self.character]
            else:
                nearby = self.relatives()          # α: partner spośród krewnych
            if not nearby:
                nearby = [q for q in m.players if q is not self]
        elif P.well_mixed:
            nearby = [q for q in m.players if q is not self]
        else:
            nearby = m.players_within(self, P.vision_radius)
        if not nearby:
            return
        self.enemy = m.rng.choice(nearby)
        enemy = self.enemy
        if enemy is not None and (P.unlimited_games or enemy.height == 0):
            key = m.pair_key(self, enemy)
            if key not in m.active_pairs:
                loc = ((self.location[0] + enemy.location[0]) / 2,
                       (self.location[1] + enemy.location[1]) / 2)
                g = m.create_game(self, enemy, key, loc)
                if P.pair_cooldown > 0:
                    m.active_pairs[key] = g

    def step(self):
        P = self.model.p
        if P.real_env and not P.well_mixed and (self.target_node is None or self._at_target()):
            self.reflex_choose_target()
        if P.real_env and not P.well_mixed and self.target_node is not None and not self._at_target():
            self.reflex_move_on_network()
        if not P.real_env and not P.well_mixed:
            self.reflex_wander()
        if not P.unlimited_games:
            self.reflex_height_decay()
        if P.unlimited_games or self.height == 0:
            self.reflex_do_you_wanna_play()


# ---------------------------------------------------------------------------
# model (global)
# ---------------------------------------------------------------------------

class Model:
    def __init__(self, params=None, seed=None, geojson=None, network=None, echo_games=False, **overrides):
        self.p = params if isinstance(params, Params) else Params(**(params or {}), **overrides)
        self.seed = seed if seed is not None else random.randrange(2 ** 31)
        self.rng = random.Random(self.seed)
        self.echo_games = echo_games
        self.cycle = 0
        self.nb_game = 0
        self.nb_moves_C = 0
        self.nb_moves_D = 0
        self.nb_exploitations = 0
        self.nb_forgets_total = 0
        self.nb_forgets_prev = 0
        self.forgets_last_cycle = 0
        self.nb_character_changes = 0
        self.ts_prev_C = 0
        self.ts_prev_D = 0
        # etap 1: stabilizacja
        self.stab_sum = []
        self.stab_samples = 0
        self.stab_prev = []
        self.stab_last = []
        self.stab_count = 0
        self.stabilized_at = -1
        self.stab_prev_C = 0
        self.stab_prev_D = 0
        self.win_games0 = 0
        self.win_expl0 = 0
        self.exploit_last_window = 0.0
        self.tr = [0, 0.0, 0.0, 0.0, 0.0]   # n, Σt, Σy, Σt², Σty (udział ALLD, 2. połowa przebiegu)
        self.perf_last_time = 0.0
        self.active_pairs = {}
        self.games = []
        self.players = []
        self.character_pool = []
        self._bucket = None        # indeks przestrzenny dla players_within (kubełki o boku = promień)
        self._grid = {}
        # wyjścia (odpowiedniki plików w ../results/)
        self.game_log = []            # PD.csv
        self.ablation_rows = []       # ablation_results.csv
        self.fingerprint_rows = []    # regression_fingerprint.csv
        self.perf_rows = []           # perf.csv
        self.family_rows = []         # family_timeseries.csv
        self.families = []            # Moduł 3: listy graczy wg family_id
        self.kin_stats = KinStats()   # cały przebieg
        self.kin_window_stats = KinStats()
        self.p4_intervals = self.p4_agree = 0   # interwały ewolucji z testem znaku (P4)
        self.kin_first_window = None
        self.kin_last_window = None
        self.timeseries_rows = []     # character_timeseries.csv
        self.compat_rows = []         # compat_results.csv

        P = self.p
        if geojson is None and P.network_file:
            with open(P.network_file, encoding="utf-8") as f:
                geojson = f.read()
        if P.real_env:
            if network is not None:
                self.network = network
            elif geojson is not None:
                self.network = PathNetwork.from_geojson(geojson, drop_loops=P.network_cleanup, crs=P.geojson_crs)
            else:
                self.network = PathNetwork.synthetic(n=P.synthetic_grid, spacing=P.synthetic_spacing)
            self.width, self.height = self.network.width, self.network.height
        else:
            self.network = network or PathNetwork.synthetic(n=P.synthetic_grid, spacing=P.synthetic_spacing)
            self.width = self.height = float(P.world_size)

        if P.real_env and P.network_variant != "baseline":
            # ten sam seed -> ta sama modyfikacja (rng przebiegu, przed tworzeniem agentów - jak w GAML)
            self.network = self.network.variant(P.network_variant, self.rng, P.edge_removal_fraction,
                                                P.shortcut_count, P.shortcut_max_length)
        self.net_stats = self.network.stats(P.net_path_sources) if (P.compat_export and P.real_env) else None
        self.enc_share_remembered = self.enc_share_ever = self.enc_distinct = 0.0
        self.encounter_rows = []      # encounter_cells.csv
        cw, ch = self.width / P.grid_cols, self.height / P.grid_rows
        self.cells = [Cell(r * P.grid_cols + c, c, r, c * cw, r * ch, cw, ch)
                      for r in range(P.grid_rows) for c in range(P.grid_cols)]
        self._init_global()

    # --- global.init ------------------------------------------------------
    def _init_global(self):
        P = self.p
        self.apply_payoff_preset()
        if P.compat_core:
            self.apply_compat_core()
        self.warnings = []
        if P.kin_matching_mode not in ("family", "strategy"):
            raise ModelError("kin_matching_mode musi być family albo strategy: %s" % P.kin_matching_mode)
        if P.payoff_mode not in ("classic", "donation"):
            raise ModelError("payoff_mode musi być classic albo donation: %s" % P.payoff_mode)
        if P.payoff_mode == "donation":
            if not (P.b > P.c > 0):
                raise ModelError("Gra dawcy wymaga b > c > 0 (b=%s, c=%s)." % (P.b, P.c))
            if not P.unlimited_games:
                raise ModelError("Gra dawcy wymaga unlimited_games = true (wypłaty ujemne i ułamkowe).")
            P.game_type = "PD"
            P.payoff_T, P.payoff_R, P.payoff_P, P.payoff_S = P.b, P.b - P.c, 0.0, -P.c
            self.warnings.append("Gra dawcy: T=%s R=%s P=0 S=%s (T, R, P, S z GUI zignorowane)."
                                 % (P.payoff_T, P.payoff_R, P.payoff_S))
        if P.kin_on and not P.evolution_on:
            raise ModelError("Moduł 3 (kin_on) wymaga evolution_on = true - bez ewolucji pokrewieństwo "
                             "nie wpływa na nic.")
        if not self.payoffs_valid():
            raise ModelError("Macierz wypłat niezgodna z game_type=%s (PD: T>R>P>S, weak_PD: T>R>P=S, "
                             "snowdrift: T>R>S>P). Aktualnie : T=%s R=%s P=%s S=%s"
                             % (P.game_type, P.payoff_T, P.payoff_R, P.payoff_P, P.payoff_S))
        if not P.unlimited_games and not self.payoffs_integer():
            raise ModelError("Tryb z ograniczeniem gier (unlimited_games=false) wymaga całkowitych wypłat.")
        if P.game_type == "PD" and not (2 * P.payoff_R > P.payoff_T + P.payoff_S):
            self.warnings.append("OSTRZEŻENIE: 2R <= T+S (%s <= %s) - naprzemienna eksploatacja nie jest "
                                 "gorsza niż stała kooperacja." % (2 * P.payoff_R, P.payoff_T + P.payoff_S))
        if P.game_type == "snowdrift" and (P.movement_sensitivity > 0 or P.env_influence_qlearn > 0):
            self.warnings.append("OSTRZEŻENIE: feedback miejsc (feedback_value) nie zależy od macierzy - w snowdrift "
                                 "ocenia C-D gorzej niż D-D, a ruch/uczenie środowiskowe z niego korzysta.")
        for k in CREATION_ORDER:
            self.character_pool += [k] * int(getattr(P, "nb_" + k))
        for ch in self.character_pool:
            pl = self.create_player(ch)
            pl.apply_character_params()
            if P.real_env:
                pl.init_on_network()
        if P.kin_on:
            self._setup_families()

    def _setup_families(self):
        """Rodziny: losowy podział na grupy family_size; korelacja strategii i skupienie przestrzenne."""
        P = self.p
        perm = list(self.players)
        self.rng.shuffle(perm)
        fs = max(1, int(P.family_size))
        for k in range(0, len(perm), fs):
            fam = perm[k:k + fs]
            fid = len(self.families)
            self.families.append(fam)
            for p in fam:
                p.family_id = fid
            if P.kin_strategy_correlation > 0:
                fam_char = self.rng.choice(fam).character
                for p in fam:
                    if self.rng.random() < P.kin_strategy_correlation and p.character != fam_char:
                        p.character = fam_char
                        p.apply_character_params()
            if P.kin_spatial_clustering > 0 and P.real_env and not P.well_mixed and fam[0].current_node is not None:
                anchor = fam[0].current_node
                for p in fam[1:]:
                    if self.rng.random() < P.kin_spatial_clustering:
                        p.current_node = anchor
                        p.location = self.network.vertices[anchor]

    def payoff_of(self, my_move, opp_move):
        P = self.p
        return {("C", "C"): P.payoff_R, ("D", "D"): P.payoff_P, ("D", "C"): P.payoff_T,
                ("C", "D"): P.payoff_S}.get((my_move, opp_move), 0.0)

    def create_player(self, character=None, **attrs):
        pl = Player(self, "player%d" % len(self.players), character, **attrs)
        pl.idx = len(self.players)
        self.players.append(pl)
        if self._bucket is not None:
            self._grid.setdefault(self._key(pl._loc), set()).add(pl)
        return pl

    def create_game(self, p1, p2, pair_key, location=None):
        g = Game(self, p1, p2, pair_key, location)
        self.games.append(g)
        return g

    # --- funkcje globalne -------------------------------------------------
    def cell_at(self, pt):
        if pt is None:
            return None
        x, y = pt
        if x < 0 or y < 0 or x > self.width or y > self.height:
            return None
        P = self.p
        c = min(int(x / self.width * P.grid_cols), P.grid_cols - 1) if self.width > 0 else 0
        r = min(int(y / self.height * P.grid_rows), P.grid_rows - 1) if self.height > 0 else 0
        return self.cells[r * P.grid_cols + c]

    # --- indeks przestrzenny: ten sam wynik co pełne przeszukanie, w kolejności tworzenia agentów ---
    def _key(self, loc):
        return (int(loc[0] // self._bucket), int(loc[1] // self._bucket))

    def _rebuild_index(self, size):
        self._bucket = size
        self._grid = {}
        for p in self.players:
            self._grid.setdefault(self._key(p._loc), set()).add(p)

    def _moved(self, pl, old):
        if self._bucket is None or pl.idx is None:
            return
        k0, k1 = self._key(old), self._key(pl._loc)
        if k0 != k1:
            self._grid[k0].discard(pl)
            self._grid.setdefault(k1, set()).add(pl)

    def players_within(self, me, radius):
        size = float(radius) if radius > 0 else 1.0
        if self._bucket != size:
            self._rebuild_index(size)
        x, y = me._loc
        kx, ky = self._key(me._loc)
        r2 = radius * radius
        found = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for q in self._grid.get((kx + dx, ky + dy), ()):
                    if q is not me and (q._loc[0] - x) ** 2 + (q._loc[1] - y) ** 2 <= r2:
                        found.append(q)
        found.sort(key=lambda q: q.idx)
        return found

    @staticmethod
    def pair_key(a, b):
        return (a.name + "|" + b.name) if a.name < b.name else (b.name + "|" + a.name)

    def disorder_bump_for(self, m1, m2):
        if m1 == "D" and m2 == "D":
            return self.p.disorder_bump_dd
        if m1 == "D" or m2 == "D":
            return self.p.disorder_bump_d
        return 0.0

    def payoffs_valid(self):
        P = self.p
        T, R, Pn, S = P.payoff_T, P.payoff_R, P.payoff_P, P.payoff_S
        if P.game_type == "PD":
            return T > R > Pn > S
        if P.game_type == "weak_PD":
            return T > R > Pn and Pn == S
        if P.game_type == "snowdrift":
            return T > R > S > Pn
        return False

    def payoffs_integer(self):
        P = self.p
        return all(v == round(v) for v in (P.payoff_T, P.payoff_R, P.payoff_P, P.payoff_S))

    @staticmethod
    def feedback_value(my_move, opp_move):
        # U6: wartości na sztywno, niezależne od macierzy wypłat (jak w PD.gaml). W snowdrift (T>R>S>P)
        # wzajemna defekcja jest najgorsza, a feedback ocenia C-D (-1.0) gorzej niż D-D (-0.8).
        # Działa tylko przez ruch środowiskowy i env_influence; compat_core je zeruje.
        return {("C", "C"): 0.1, ("D", "D"): -0.8, ("D", "C"): 1.0, ("C", "D"): -1.0}.get((my_move, opp_move), 0.0)

    def selected_player(self):
        if not self.players:
            return None
        return self.players[min(self.p.selected_index, len(self.players) - 1)]

    def average_feedback(self, cell):
        vals = [p.personal_feedback[cell] for p in self.players if cell in p.personal_feedback]
        return sum(vals) / len(vals) if vals else 0.0

    def normalized_visual_height(self, pl, _cache=None):
        vals = _cache if _cache is not None else [p.for_chart for p in self.players]
        if not vals:
            return 0.0
        lo, hi = min(vals), max(vals)
        return 0.0 if hi == lo else 10 * (pl.for_chart - lo) / (hi - lo)

    def recent_defection_rate(self, window):
        moves = [m for p in self.players for lst in p.my_moves_per_other.values()
                 for m in lst[-min(window, len(lst)):] if lst]
        return moves.count("D") / len(moves) if moves else 0.0

    def mean_for(self, ch):
        g = [p for p in self.players if p.character == ch and p.nb_games > 0]
        return sum(p.score / p.nb_games * 1000 for p in g) / len(g) if g else 0.0

    def mean_score_all(self):
        g = [p for p in self.players if p.nb_games > 0]
        return sum(p.score / p.nb_games * 1000 for p in g) / len(g) if g else 0.0

    def mean_for_classic(self):
        g = [p for p in self.players if p.nb_games > 0 and p.character in CLASSIC]
        return sum(p.score / p.nb_games * 1000 for p in g) / len(g) if g else 0.0

    def aqlearn_clique_fraction(self):
        aq = [p for p in self.players if p.character == "AQLEARN"]
        total = high = 0
        for p in aq:
            for q in aq:
                if p is not q:
                    total += 1
                    if p.social_feedback.get(q, 0.0) > 0.5:
                        high += 1
        return 0.0 if total == 0 else high / total

    def aqlearn_avg_distance(self):
        aq = [p for p in self.players if p.character == "AQLEARN"]
        if len(aq) < 2:
            return 0.0
        d = [_dist(aq[i].location, aq[j].location) for i in range(len(aq)) for j in range(i + 1, len(aq))]
        return sum(d) / len(d)

    # --- etap 1 -----------------------------------------------------------
    def apply_payoff_preset(self):
        if self.p.payoff_preset in PAYOFF_PRESETS:
            gt, pay = PAYOFF_PRESETS[self.p.payoff_preset]
            self.p.game_type = gt
            for k, v in pay.items():
                setattr(self.p, k, v)

    def apply_compat_core(self):
        P = self.p
        P.nb_QLEARN = P.nb_AQLEARN = 0
        P.movement_sensitivity = 0.0
        P.env_influence_qlearn = 0.0
        P.social_sensitivity_aqlearn = 0.0
        P.social_learning_boost_aqlearn = 0.0
        P.broken_windows_sensitivity = 0.0
        P.character_strength_qlearn = 0.0
        P.unlimited_games = True
        P.classic_start_cooperate = True
        if P.compat_mix == "allc_alld":          # Moduł 3 / P4: bez wzajemności
            P.nb_ALLC = P.compat_N - P.compat_N // 2
            P.nb_ALLD = P.compat_N // 2
            P.nb_TFT = P.nb_FTFT = P.nb_TF2T = P.nb_GRIM = P.nb_WSLS = 0
        elif P.compat_mix == "tft_alld":
            P.nb_ALLD = int(round(P.compat_N * 0.2))
            P.nb_TFT = P.compat_N - P.nb_ALLD
            P.nb_ALLC = P.nb_FTFT = P.nb_TF2T = P.nb_GRIM = P.nb_WSLS = 0
        else:
            base, rest = divmod(P.compat_N, 7)
            for i, ch in enumerate(CLASSIC):
                setattr(P, "nb_" + ch, base + (1 if rest > i else 0))

    def core_violations(self):
        P, v = self.p, []
        if P.nb_QLEARN > 0 or P.nb_AQLEARN > 0 or any(p.character in LEARNERS for p in self.players):
            v.append("Q-learning")
        if P.movement_sensitivity != 0 or any(p.sensitivity != 0 for p in self.players):
            v.append("ruch środowiskowy")
        if P.social_sensitivity_aqlearn != 0 or any(p.social_sensitivity != 0 for p in self.players):
            v.append("ruch społeczny")
        if P.env_influence_qlearn != 0 or P.social_learning_boost_aqlearn != 0:
            v.append("uczenie środowiskowe/społeczne")
        if P.broken_windows_sensitivity != 0:
            v.append("rozbita szyba")
        if P.character_strength_qlearn != 0 or any(p.character_strength != 0 for p in self.players):
            v.append("kotwica")
        if not P.unlimited_games:
            v.append("limit gier")
        return v

    def _reflex_track_stability(self):
        P = self.p
        v = [self.share_of(c) for c in CLASSIC]
        d_c, d_d = self.nb_moves_C - self.stab_prev_C, self.nb_moves_D - self.stab_prev_D
        self.stab_prev_C, self.stab_prev_D = self.nb_moves_C, self.nb_moves_D
        v.append(0.0 if d_c + d_d == 0 else d_d / (d_c + d_d))
        if self.cycle > P.end_cycle / 2:
            t, y = self.cycle, v[2]
            self.tr = [self.tr[0] + 1, self.tr[1] + t, self.tr[2] + y, self.tr[3] + t * t, self.tr[4] + t * y]
        if self.cycle <= P.warmup:
            return
        if not self.stab_sum:
            self.stab_sum = [0.0] * len(v)
        self.stab_sum = [a + b for a, b in zip(self.stab_sum, v)]
        self.stab_samples += 1
        if self.stab_samples * P.sample_interval >= P.stab_window:
            mean_v = [x / self.stab_samples for x in self.stab_sum]
            # U3: stab_count/stabilized_at nie trafiają do CSV - pozostałość po kryterium okien;
            # "stabilized" liczy kryterium trendu (alld_trend_10k). Okna służą do średnich końcowych.
            if self.stab_prev:
                # stabilizacja oceniana na udziale ALLD (indeks 2) i udziale D (indeks 7)
                change = max(abs(mean_v[i] - self.stab_prev[i]) for i in (2, 7))
                self.stab_count = self.stab_count + 1 if change < P.stab_eps else 0
                if self.stab_count >= P.stab_k and self.stabilized_at < 0:
                    self.stabilized_at = self.cycle
            self.stab_prev = self.stab_last = mean_v
            self.stab_sum, self.stab_samples = [], 0
            dg = self.nb_game - self.win_games0
            self.exploit_last_window = 0.0 if dg == 0 else (self.nb_exploitations - self.win_expl0) / dg
            self.win_games0, self.win_expl0 = self.nb_game, self.nb_exploitations

    def alld_trend_10k(self):
        n, st_, sy, stt, sty = self.tr
        den = n * stt - st_ * st_
        return 0.0 if n < 2 or den == 0 else 10000 * (n * sty - st_ * sy) / den

    def _reflex_export_compat(self):
        P = self.p
        fin = self.stab_last or ([self.share_of(c) for c in CLASSIC] + [0.0])
        fixated = any(self.share_of(c) >= 1.0 for c in CLASSIC)
        self.compat_rows.append([
            P.variant_name, P.prediction, self.seed, P.compat_N, P.well_mixed, P.payoff_preset,
            P.payoff_T, P.payoff_R, P.payoff_P, P.payoff_S, P.evolution_on, P.mutation_rate, P.fermi_k,
            P.evolution_interval, P.dunbar_limit, P.vision_radius, P.player_speed, P.end_cycle] + list(fin) + [
            self.exploit_last_window, self.mean_for("ALLD") / 1000, self.mean_for("TFT") / 1000,
            self.mean_score_all() / 1000, self.mean_known_partners(), self.mean_distinct_partners_window(),
            self.mean_games_per_partner(),
            self.share_exceeding_dunbar(), fixated, abs(self.alld_trend_10k()) < P.stab_trend_eps,
            self.alld_trend_10k(),
            self.nb_character_changes]
            + ([P.network_variant] + [self.net_stats[k] for k in NET_STAT_KEYS]
               if (self.net_stats and not P.well_mixed) else ["n/a"] * (1 + len(NET_STAT_KEYS)))
            + [self.enc_share_remembered, self.enc_share_ever, self.enc_distinct]
            + ["n/a" if (P.well_mixed or not P.real_env) else self.network.edges_removed]
            + self._kin_columns())

    def _kin_columns(self):
        P = self.p
        cols = [P.payoff_mode, P.b, P.c, P.c / P.b if P.b else "n/a", P.kin_on]
        if not P.kin_on:
            return cols + ["n/a"] * (len(KIN_HEADER) - 5)
        na = lambda v: "n/a" if v is None else v
        s = self.kin_stats.summary()
        fw = self.kin_first_window or {}
        lw = self.kin_last_window or {}
        return cols + [P.family_size, P.family_r, P.kin_spatial_clustering, P.kin_strategy_correlation,
                       P.kin_imitation_bias, P.kin_matching_prob, P.fitness_mode, P.inclusive_variant,
                       na(s["r_hat_all"]), na(s["r_hat_kin"]), na(fw.get("r_hat_all")), na(lw.get("r_hat_all")),
                       na(s["kin_share"]), na(s["coop_kin"]), na(s["coop_str"]), na(s["r_hat_all_pooled"]),
                       self.p4_intervals, self.p4_agree / self.p4_intervals if self.p4_intervals else "n/a",
                       P.kin_matching_mode]

    # --- zdarzenie po grze i metryka stabilności spotkań ----------------------
    def on_game_played(self, g):
        """Punkt zaczepienia dla obserwatorów (Faza 7); dziś: metryka stabilności spotkań."""
        g.p1.record_encounter(g.p2, g.knew1_rem, g.knew1_ever, g.cell1)
        g.p2.record_encounter(g.p1, g.knew2_rem, g.knew2_ever, g.cell2)

    def _reflex_close_encounter_window(self):
        active = [p for p in self.players if p.enc_games > 0]
        if active:
            self.enc_share_remembered = sum(p.enc_rep_rem / p.enc_games for p in active) / len(active)
            self.enc_share_ever = sum(p.enc_rep_ever / p.enc_games for p in active) / len(active)
            self.enc_distinct = sum(len(p.enc_partners) for p in active) / len(active)
        else:
            self.enc_share_remembered = self.enc_share_ever = self.enc_distinct = 0.0
        for p in self.players:
            p.enc_games = p.enc_rep_rem = p.enc_rep_ever = 0
            p.enc_partners = set()
        for c in self.cells:
            c.close_window()

    def _reflex_export_encounter_cells(self):
        nv = "n/a" if self.p.well_mixed else self.p.network_variant
        for c in self.cells:
            if c.total_games > 0:
                self.encounter_rows.append([self.p.variant_name, self.seed, nv, c.col, c.row, c.total_games,
                                            c.total_rep_rem / c.total_games, c.total_rep_ever / c.total_games,
                                            c.last_share_rem, c.last_share_ever])

    def fermi_probability(self, pi_model, pi_self):
        x = -(pi_model - pi_self) / self.p.fermi_k
        if x > 50:
            return 0.0
        if x < -50:
            return 1.0
        return 1 / (1 + math.exp(x))

    def share_of(self, ch):
        return sum(1 for p in self.players if p.character == ch) / len(self.players) if self.players else 0.0

    def evolution_step(self):
        # synchronicznie: decyzje na starych charakterach i π, potem zmiana; okna zerowane u wszystkich
        evolvable = self.p.evolvable_characters
        decisions = [(p, p.evolution_choice(p.pick_model())) for p in self.players if p.character in evolvable]
        if self.p.kin_on:
            allc0 = self.share_of("ALLC")
            sxy, sxx = KinStats._within(self.kin_stats.blk_all)
        for p, new_char in decisions:
            p.change_character(new_char)
        if self.p.kin_on:
            # test Hamiltona w interwale: znak zmiany udziału ALLC vs znak (r̂_k·b - c)
            d = self.share_of("ALLC") - allc0
            pred = (sxy / sxx) * self.p.b - self.p.c if sxx > 1e-12 else 0.0
            if 0.0 < allc0 < 1.0 and d != 0 and pred != 0:
                self.p4_intervals += 1
                self.p4_agree += int((d > 0) == (pred > 0))
            self.kin_stats.close_block()
            self.kin_window_stats.close_block()
        for p in self.players:
            p.window_payoff = 0.0
            p.window_games = 0
            p.window_kin_given = p.window_kin_received = 0.0

    def _reflex_export_timeseries(self):
        d_c, d_d = self.nb_moves_C - self.ts_prev_C, self.nb_moves_D - self.ts_prev_D
        self.ts_prev_C, self.ts_prev_D = self.nb_moves_C, self.nb_moves_D
        d_share = 0.0 if d_c + d_d == 0 else d_d / (d_c + d_d)
        P = self.p
        self.timeseries_rows.append([P.variant_name, self.seed, P.payoff_preset, P.compat_N, P.well_mixed,
                                     P.mutation_rate, P.dunbar_limit, P.player_speed, self.cycle]
                                    + [self.share_of(c) for c in TIMESERIES_CHARACTERS]
                                    + [d_share, self.nb_character_changes]
                                    + [P.payoff_mode, P.c / P.b if P.payoff_mode == "donation" else "n/a"]
                                    + ([P.kin_matching_mode, P.kin_matching_prob, P.fitness_mode] if P.kin_on
                                       else ["n/a"] * 3))

    def exploitation_rate(self):
        return self.nb_exploitations / self.nb_game if self.nb_game else 0.0

    def mean_games_per_partner(self):
        # U4: met_count (nieprzycinany) zamiast last_met_cycle, które przycina distinct_partners_in_window
        g = [p for p in self.players if p.met_count]
        return sum(p.nb_games / len(p.met_count) for p in g) / len(g) if g else 0.0

    def mean_known_partners(self):
        return sum(len(p.known_others) for p in self.players) / len(self.players) if self.players else 0.0

    def mean_distinct_partners_window(self):
        return (sum(p.distinct_partners_in_window() for p in self.players) / len(self.players)
                if self.players else 0.0)

    def share_exceeding_dunbar(self):
        if not self.players or self.p.dunbar_limit <= 0:
            return 0.0
        return (sum(1 for p in self.players if p.distinct_partners_in_window() > self.p.dunbar_limit)
                / len(self.players))

    # --- reflexy globalne -------------------------------------------------
    def _reflex_export_metrics(self):
        self.ablation_rows.append([self.p.variant_name, self.mean_score_all(), self.mean_for("QLEARN"),
                                   self.mean_for("AQLEARN"), self.mean_for_classic(),
                                   self.aqlearn_clique_fraction(), self.aqlearn_avg_distance()])

    def _reflex_fingerprint(self):
        score_sum = score_weighted = loc_sum = q_sum = 0.0
        for i, p in enumerate(sorted(self.players, key=lambda a: a.name), start=1):
            score_sum += p.score
            score_weighted += i * p.score
            loc_sum += i * (p.location[0] + p.location[1])
            q_sum += sum(sum(m.values()) for m in p.q_c_per_other.values())
            q_sum -= sum(sum(m.values()) for m in p.q_d_per_other.values())
        disorder_sum = sum(c.disorder for c in self.cells)
        self.fingerprint_rows.append([self.p.variant_name, self.p.unlimited_games, self.seed, self.cycle,
                                      self.nb_game, self.nb_moves_C, self.nb_moves_D, score_sum,
                                      score_weighted, loc_sum, q_sum, disorder_sum])

    def _reflex_perf(self):
        now = time.perf_counter() * 1000.0
        if self.cycle > 0:
            ms = (now - self.perf_last_time) / self.p.perf_interval
            self.perf_rows.append([self.p.variant_name, len(self.players), self.cycle, ms])
        self.perf_last_time = now

    def step(self):
        P = self.p
        # świat
        self.forgets_last_cycle = self.nb_forgets_total - self.nb_forgets_prev
        self.nb_forgets_prev = self.nb_forgets_total
        if P.evolution_on and self.cycle > 0 and self.cycle % P.evolution_interval == 0:
            self.evolution_step()
        if self.cycle > 0 and self.cycle % P.encounter_window == 0:
            self._reflex_close_encounter_window()
        if P.encounter_export and self.cycle == P.end_cycle:
            self._reflex_export_encounter_cells()
        if P.kin_on and self.cycle > 0 and self.cycle % P.kin_window == 0:
            summ = self.kin_window_stats.summary()
            if self.kin_first_window is None:
                self.kin_first_window = summ
            self.kin_last_window = summ
            self.kin_window_stats = KinStats()
        if P.kin_on and P.kin_export and self.cycle % P.sample_interval == 0:
            for fam in self.families:
                n = len(fam)
                self.family_rows.append([P.variant_name, self.seed, self.cycle, fam[0].family_id, n,
                                         sum(p.character == "ALLC" for p in fam) / n,
                                         sum(p.character == "ALLD" for p in fam) / n])
        if P.compat_export and self.cycle > 0 and self.cycle % P.sample_interval == 0:
            self._reflex_track_stability()
        if P.compat_export and self.cycle == P.end_cycle:
            self._reflex_export_compat()
        if P.timeseries_export and self.cycle % P.sample_interval == 0:
            self._reflex_export_timeseries()
        if self.cycle == P.end_cycle:
            self._reflex_export_metrics()
        if P.regression_export and self.cycle == P.regression_cycle:
            self._reflex_fingerprint()
        if P.perf_log and self.cycle % P.perf_interval == 0:
            self._reflex_perf()
        # environment_cell: decay_disorder when every(10)
        if self.cycle % 10 == 0:
            for c in self.cells:
                c.apply_decay(self)
        # game
        self.games = [g for g in self.games if g.step()]
        # player
        for pl in list(self.players):
            pl.step()
        self.cycle += 1

    def run(self, n):
        for _ in range(n):
            self.step()
        return self

    # --- dane do wizualizacji (web/index.html) ------------------------------
    def snapshot(self, personal_for=None):
        P = self.p
        heights = [p.for_chart for p in self.players]
        sel = self.selected_player()
        cells_summary, cells_personal, cells_disorder = {}, {}, {}
        touched = set()
        for p in self.players:
            touched.update(c.index for c in p.personal_feedback)
        for idx in touched:
            cells_summary[idx] = self.average_feedback(self.cells[idx])
        if sel is not None:
            for c, v in sel.personal_feedback.items():
                cells_personal[c.index] = v
        cells_enc = {}
        for c in self.cells:
            if c.disorder > 1e-4:
                cells_disorder[c.index] = c.disorder
            if c.last_share_rem >= 0:
                cells_enc[c.index] = c.last_share_rem

        def links(pl):
            cand = [q for q, v in pl.social_feedback.items() if abs(v) > P.social_link_threshold]
            cand.sort(key=lambda q: -abs(pl.social_feedback[q]))
            return [[q.location[0], q.location[1], pl.social_feedback[q]] for q in cand[:3]]

        players = []
        for i, p in enumerate(self.players):
            players.append({
                "i": i, "name": p.name, "ch": p.character, "x": p.location[0], "y": p.location[1],
                "h": self.normalized_visual_height(p, heights), "fc": p.for_chart,
                "score": p.score, "games": p.nb_games, "known": len(p.known_others),
                "links": links(p) if P.show_social_links else [],
            })
        return json.dumps({
            "cycle": self.cycle, "w": self.width, "h": self.height,
            "cols": P.grid_cols, "rows": P.grid_rows,
            "sel": P.selected_index if sel is not None else -1,
            "sel_ch": sel.character if sel is not None else None,
            "players": players,
            "summary": cells_summary, "personal": cells_personal, "disorder": cells_disorder,
            "encounters": cells_enc, "enc_rem": self.enc_share_remembered, "enc_ever": self.enc_share_ever,
            "nb_game": self.nb_game, "moves_C": self.nb_moves_C, "moves_D": self.nb_moves_D,
            "exploit": self.exploitation_rate(),
            "shares": {c: self.share_of(c) for c in CHARACTERS},
            "changes": self.nb_character_changes,
            "known": self.mean_known_partners(),
            "distinct": self.mean_distinct_partners_window(),
            "forgets": self.forgets_last_cycle,
            "exceed": self.share_exceeding_dunbar(),
        })

    def network_json(self):
        return json.dumps({"lines": self.network.polylines if self.p.real_env else [],
                           "source": self.network.source, "w": self.width, "h": self.height})


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

TIMESERIES_CHARACTERS = ["TFT", "ALLC", "ALLD", "FTFT", "TF2T", "GRIM", "WSLS", "QLEARN", "AQLEARN"]

KIN_HEADER = ["payoff_mode", "b", "c", "c_over_b", "kin_on", "family_size", "family_r", "kin_spatial_clustering",
              "kin_strategy_correlation", "kin_imitation_bias", "kin_matching_prob", "fitness_mode",
              "inclusive_variant", "r_hat_all", "r_hat_kin", "r_hat_first_window", "r_hat_last_window",
              "kin_interaction_share", "coop_with_kin", "coop_with_strangers", "r_hat_all_pooled",
              "p4_intervals", "p4_sign_agreement", "kin_matching_mode"]

NET_STAT_KEYS = ["net_nodes", "net_edges", "net_mean_degree", "net_avg_path", "net_density",
                 "net_betw_max", "net_betw_mean"]

COMPAT_HEADER = ["variant_name", "prediction", "seed", "compat_N", "well_mixed", "payoff_preset",
                 "payoff_T", "payoff_R", "payoff_P", "payoff_S", "evolution_on", "mutation_rate", "fermi_k",
                 "evolution_interval", "dunbar_limit", "vision_radius", "player_speed", "end_cycle",
                 "share_TFT", "share_ALLC", "share_ALLD", "share_FTFT", "share_TF2T", "share_GRIM", "share_WSLS",
                 "d_share", "exploit_last_window", "payoff_ALLD", "payoff_TFT", "payoff_all", "known_partners",
                 "distinct_partners", "games_per_partner", "exceeding_dunbar", "fixated", "stabilized", "alld_trend_10k",
                 "nb_character_changes", "network_variant"] + NET_STAT_KEYS + [
                 "enc_share_remembered", "enc_share_ever", "enc_distinct", "net_edges_removed"] + KIN_HEADER

CSV_HEADERS = {
    "family_timeseries.csv": ["variant_name", "seed", "cycle", "family_id", "size", "share_ALLC", "share_ALLD"],
    "encounter_cells.csv": ["variant_name", "seed", "network_variant", "col", "row", "total_games",
                            "share_repeat_remembered", "share_repeat_ever", "last_window_share_remembered",
                            "last_window_share_ever"],
    "compat_results.csv": COMPAT_HEADER,
    "character_timeseries.csv": ["variant_name", "seed", "payoff_preset", "compat_N", "well_mixed",
                                 "mutation_rate", "dunbar_limit", "player_speed", "cycle"] + ["share_" + c for c in TIMESERIES_CHARACTERS]
                                + ["d_share_window", "nb_character_changes", "payoff_mode", "c_over_b",
                                   "kin_matching_mode", "kin_matching_prob", "fitness_mode"],
    "PD.csv": ["nb_game", "cycle", "p1", "p2", "p1_move", "p2_move", "p1.score", "p2.score"],
    "ablation_results.csv": ["variant_name", "mean_score_all", "mean_for_QLEARN", "mean_for_AQLEARN",
                             "mean_for_classic", "aqlearn_clique_fraction", "aqlearn_avg_distance"],
    "regression_fingerprint.csv": ["variant_name", "unlimited_games", "seed", "cycle", "nb_game",
                                   "nb_moves_C", "nb_moves_D", "score_sum", "score_weighted",
                                   "loc_sum", "q_sum", "disorder_sum"],
    "perf.csv": ["variant_name", "N", "cycle", "ms_per_cycle"],
}


def to_csv(name, rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CSV_HEADERS[name])
    w.writerows(rows)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# eksperymenty batch z PD.gaml
# ---------------------------------------------------------------------------

_ABL = dict(log_games=False)
BATCH_EXPERIMENTS = {
    "A_baseline": dict(repeat=30, until="end_cycle", params=dict(
        _ABL, variant_name="A_baseline", nb_QLEARN=20, nb_AQLEARN=0, movement_sensitivity=0.0,
        env_influence_qlearn=0.0, social_sensitivity_aqlearn=0.0, social_learning_boost_aqlearn=0.0)),
    "B_env_movement": dict(repeat=30, until="end_cycle", params=dict(
        _ABL, variant_name="B_env_movement", nb_QLEARN=20, nb_AQLEARN=0, movement_sensitivity=2.0,
        env_influence_qlearn=0.0, social_sensitivity_aqlearn=0.0, social_learning_boost_aqlearn=0.0)),
    "C_social_movement": dict(repeat=30, until="end_cycle", params=dict(
        _ABL, variant_name="C_social_movement", nb_QLEARN=0, nb_AQLEARN=20, movement_sensitivity=2.0,
        env_influence_qlearn=0.0, social_sensitivity_aqlearn=1.5, social_learning_boost_aqlearn=0.0)),
    "D_social_learning": dict(repeat=30, until="end_cycle", params=dict(
        _ABL, variant_name="D_social_learning", nb_QLEARN=0, nb_AQLEARN=20, movement_sensitivity=2.0,
        env_influence_qlearn=0.0, social_sensitivity_aqlearn=1.5, social_learning_boost_aqlearn=2.0)),
    "E1_classic_TFT": dict(repeat=30, until="end_cycle", params=dict(
        _ABL, variant_name="E1_classic_TFT", nb_TFT=20, movement_sensitivity=2.0)),
    "E2_classic_WSLS": dict(repeat=30, until="end_cycle", params=dict(
        _ABL, variant_name="E2_classic_WSLS", nb_WSLS=20, movement_sensitivity=2.0)),
    "E3_classic_GRIM": dict(repeat=30, until="end_cycle", params=dict(
        _ABL, variant_name="E3_classic_GRIM", nb_GRIM=20, movement_sensitivity=2.0)),
    "F_broken_windows_anchor": dict(repeat=30, until="end_cycle", params=dict(
        _ABL, variant_name="F_broken_windows_anchor", nb_AQLEARN=20, movement_sensitivity=2.0,
        social_sensitivity_aqlearn=1.5, social_learning_boost_aqlearn=2.0, broken_windows_sensitivity=0.4,
        base_character_qlearn="TFT", character_strength_qlearn=0.6)),
    "R0_regression": dict(repeat=3, until="regression_cycle", seed=20261123, among={"unlimited_games": [False, True]},
                          params=dict(
        _ABL, variant_name="R0_regression", regression_export=True, regression_cycle=2000,
        nb_QLEARN=6, nb_AQLEARN=6, nb_TFT=2, nb_ALLC=2, nb_ALLD=2, nb_FTFT=2, nb_TF2T=2, nb_GRIM=2,
        nb_WSLS=2, movement_sensitivity=2.0, env_influence_qlearn=0.5, social_sensitivity_aqlearn=1.5,
        social_learning_boost_aqlearn=2.0, broken_windows_sensitivity=0.4, character_strength_qlearn=0.6)),
}

_S1 = dict(log_games=False, compat_core=True, compat_export=True, timeseries_export=True, end_cycle=20000,
           vision_radius=30, network_cleanup=True,
           partner_window=10 ** 9)
for _space, _wm in (("space", False), ("wellmixed", True)):
    BATCH_EXPERIMENTS["S1_P12_" + _space] = dict(
        repeat=15, until="end_cycle", seed=20261123,
        among={"mutation_rate": [0.0, 0.01], "payoff_preset": ["PD_classic", "weak_PD", "snowdrift"],
               "compat_N": [200, 500]},
        params=dict(_S1, variant_name="S1_P12_" + _space, prediction="P1P2", compat_mix="equal",
                    evolution_on=True, well_mixed=_wm, end_cycle=100000))
    BATCH_EXPERIMENTS["S1_P3_" + _space] = dict(
        repeat=15, until="end_cycle", seed=20261123,
        among={"dunbar_limit": [0, 5, 15, 50, 150], "payoff_preset": ["PD_classic", "weak_PD", "snowdrift"],
               "compat_N": [200, 500]},
        params=dict(_S1, variant_name="S1_P3_" + _space, prediction="P3", compat_mix="tft_alld",
                    evolution_on=False, well_mixed=_wm))


BATCH_EXPERIMENTS["S1_P1_mobility"] = dict(
    repeat=15, until="end_cycle", seed=20261123,
    among={"player_speed": [0.5, 0.1], "mutation_rate": [0.0, 0.01],
           "payoff_preset": ["PD_classic", "weak_PD", "snowdrift"], "compat_N": [200, 500]},
    params=dict(_S1, variant_name="S1_P1_mobility", prediction="P1P2", compat_mix="equal",
                evolution_on=True, well_mixed=False, end_cycle=100000))


BATCH_EXPERIMENTS["S2_pairs"] = dict(
    repeat=15, until="end_cycle", seed=20261123,
    among={"dunbar_limit": [0, 5, 15, 50, 150], "mutation_rate": [0.0, 0.01],
           "payoff_preset": ["PD_classic", "weak_PD", "snowdrift"], "compat_N": [200]},
    params=dict(_S1, variant_name="S2_pairs", prediction="S2", compat_mix="equal", evolution_on=True,
                well_mixed=False, end_cycle=100000, player_speed=0.1))


# plan minimalny (CLAUDE.md): rdzeń z prędkością 0,1, N = 200, 10 powtórzeń
_PM = dict(_S1, player_speed=0.1, compat_N=200)
for _space, _wm in (("space", False), ("wellmixed", True)):
    BATCH_EXPERIMENTS["PM2_P12_" + _space] = dict(
        repeat=10, until="end_cycle", seed=20261123,
        among={"mutation_rate": [0.0, 0.01], "payoff_preset": ["PD_classic", "snowdrift"], "compat_N": [200]},
        params=dict(_PM, variant_name="PM2_P12_" + _space, prediction="P1P2", compat_mix="equal",
                    evolution_on=True, well_mixed=_wm, end_cycle=100000))
    BATCH_EXPERIMENTS["PM2_P3_" + _space] = dict(
        repeat=10, until="end_cycle", seed=20261123,
        among={"dunbar_limit": [0, 5, 15, 50, 150], "payoff_preset": ["PD_classic", "snowdrift"], "compat_N": [200]},
        params=dict(_PM, variant_name="PM2_P3_" + _space, prediction="P3", compat_mix="tft_alld",
                    evolution_on=False, well_mixed=_wm, end_cycle=20000))
BATCH_EXPERIMENTS["PM3_P1_network"] = dict(
    repeat=10, until="end_cycle", seed=20261123,
    among={"network_variant": ["baseline", "fragmented", "connected"], "compat_N": [200]},
    params=dict(_PM, variant_name="PM3_P1_network", prediction="P1P2", compat_mix="equal", evolution_on=True,
                mutation_rate=0.01, payoff_preset="PD_classic", well_mixed=False, end_cycle=100000))
BATCH_EXPERIMENTS["PM3_P3_network"] = dict(
    repeat=10, until="end_cycle", seed=20261123,
    among={"dunbar_limit": [0, 5, 15, 50, 150], "network_variant": ["baseline", "fragmented", "connected"],
           "compat_N": [200]},
    params=dict(_PM, variant_name="PM3_P3_network", prediction="P3", compat_mix="tft_alld", evolution_on=False,
                payoff_preset="PD_classic", well_mixed=False, end_cycle=20000))
BATCH_EXPERIMENTS["PM4_heatmap"] = dict(
    repeat=1, until="end_cycle", seed=20261123,
    among={"network_variant": ["baseline", "fragmented", "connected"], "compat_N": [200]},
    params=dict(_PM, variant_name="PM4_heatmap", prediction="heatmap", compat_mix="equal", evolution_on=True,
                mutation_rate=0.01, payoff_preset="PD_classic", well_mixed=False, end_cycle=20000,
                encounter_export=True, timeseries_export=False))


# P3 i heatmapa przy prędkości 2 (przy 0,1 agent ma ok. 5 różnych partnerów - limit Dunbara nie działa)
for _name in ("PM2_P3_space", "PM3_P3_network", "PM4_heatmap"):
    _spec = BATCH_EXPERIMENTS[_name]
    BATCH_EXPERIMENTS[_name + "_speed2"] = dict(_spec, params=dict(_spec["params"], player_speed=2.0,
                                                                  variant_name=_name + "_speed2"))


# Moduł 3 / P4 (well_mixed, ALLC/ALLD, gra dawcy b = 1): kalibracja z doborem wg strategii (r̂ = α z konstrukcji)
# i właściwy test z rodzinami (r̂ zmierzone); ewoluują tylko ALLC i ALLD
_P4 = dict(_PM, prediction="P4", compat_mix="allc_alld", evolution_on=True, well_mixed=True, kin_on=True,
           payoff_mode="donation", b=1.0, pair_cooldown=0, kin_strategy_correlation=1.0, family_size=10,
           family_r=0.5, mutation_rate=0.01, evolvable_characters=["ALLC", "ALLD"], end_cycle=10000,
           timeseries_export=True)
_ALPHAS = [round(0.1 * i, 1) for i in range(10)]
BATCH_EXPERIMENTS["PM5_P4_strategy"] = dict(
    repeat=10, until="end_cycle", seed=20261123,
    among={"kin_matching_prob": _ALPHAS, "c": [0.3, 0.5], "compat_N": [200]},
    params=dict(_P4, variant_name="PM5_P4_strategy", kin_matching_mode="strategy", fitness_mode="own"))
BATCH_EXPERIMENTS["PM5_P4_family"] = dict(
    repeat=10, until="end_cycle", seed=20261123,
    among={"kin_matching_prob": _ALPHAS, "c": [0.3, 0.5], "fitness_mode": ["own", "inclusive"], "compat_N": [200]},
    params=dict(_P4, variant_name="PM5_P4_family", kin_matching_mode="family"))


def park_grid_for(n_agents):
    """Syntetyczny park skalowany z populacją: ta sama gęstość co 20 agentów na siatce 10x10."""
    return max(10, int(round(10 * math.sqrt(n_agents / 20.0))))


class BatchRun:
    """Batch krok po kroku (żeby przeglądarka mogła pokazywać postęp)."""

    def __init__(self, name, repeat=None, end_cycle=None, geojson=None, network=None, seed=None, overrides=None):
        spec = BATCH_EXPERIMENTS[name]
        for k in (overrides or {}):
            if k not in DEFAULTS:
                raise KeyError("Nieznany parametr: " + k)
        self.name = name
        self.repeat = repeat if repeat is not None else spec["repeat"]
        base = dict(spec["params"])
        if end_cycle is not None:
            base[spec["until"]] = end_cycle
            base["end_cycle"] = end_cycle if spec["until"] == "end_cycle" else base.get("end_cycle", DEFAULTS["end_cycle"])
        among = spec.get("among", {})
        combos = [dict(zip(among.keys(), vals)) for vals in itertools.product(*among.values())] or [{}]
        exp_seed = seed if seed is not None else spec.get("seed")
        seeder = random.Random(exp_seed) if exp_seed is not None else random.Random()
        seeds = [seeder.randrange(2 ** 31) for _ in range(self.repeat)]   # keep_seed: te same dla kombinacji
        base.update(overrides or {})
        self.network = network or (PathNetwork.from_geojson(
            geojson, drop_loops=base.get("network_cleanup", False),
            crs=base.get("geojson_crs", DEFAULTS["geojson_crs"])) if geojson else None)
        self._networks = {}
        # parametry z --set wygrywają także z kombinacjami among
        self.jobs = [(dict(dict(base, **c), **(overrides or {})), s) for c in combos for s in seeds]
        self.until_key = spec["until"]
        self.ablation_rows, self.fingerprint_rows, self.perf_rows, self.timeseries_rows = [], [], [], []
        self.compat_rows, self.encounter_rows, self.family_rows = [], [], []
        self.done = 0
        self.current = None

    @property
    def total(self):
        return len(self.jobs)

    def advance(self, max_cycles=2000):
        """Wykonuje do max_cycles kroków; zwraca True, gdy cały batch skończony."""
        budget = max_cycles
        while budget > 0 and self.done < len(self.jobs):
            if self.current is None:
                params, s = self.jobs[self.done]
                net = self.network
                if net is None:
                    key = (params.get("synthetic_grid", DEFAULTS["synthetic_grid"]),
                           params.get("synthetic_spacing", DEFAULTS["synthetic_spacing"]))
                    if key not in self._networks:
                        self._networks[key] = PathNetwork.synthetic(n=key[0], spacing=key[1])
                    net = self._networks[key]
                self.current = Model(Params(**params), seed=s, network=net)
            m = self.current
            limit = getattr(m.p, self.until_key)
            while budget > 0 and not (m.cycle > limit):   # until: cycle > ...
                m.step()
                budget -= 1
            if m.cycle > limit:
                self.ablation_rows += m.ablation_rows
                self.fingerprint_rows += m.fingerprint_rows
                self.perf_rows += m.perf_rows
                self.timeseries_rows += m.timeseries_rows
                self.compat_rows += m.compat_rows
                self.encounter_rows += m.encounter_rows
                self.family_rows += m.family_rows
                self.done += 1
                self.current = None
        return self.done >= len(self.jobs)

    def progress(self):
        cur = self.current.cycle if self.current else 0
        limit = self.jobs[min(self.done, len(self.jobs) - 1)][0].get(self.until_key, DEFAULTS[self.until_key])
        return json.dumps({"done": self.done, "total": len(self.jobs), "cycle": cur, "limit": limit})


# plik CSV -> atrybut z wierszami (BatchRun i Model)
BATCH_OUTPUTS = [("ablation_results.csv", "ablation_rows"), ("regression_fingerprint.csv", "fingerprint_rows"),
                 ("perf.csv", "perf_rows"), ("character_timeseries.csv", "timeseries_rows"),
                 ("compat_results.csv", "compat_rows"), ("encounter_cells.csv", "encounter_rows"),
                 ("family_timeseries.csv", "family_rows")]


def batch_outputs(b):
    """Niepuste zestawy wierszy batcha: [(nazwa_pliku, wiersze)]."""
    return [(name, getattr(b, attr)) for name, attr in BATCH_OUTPUTS if getattr(b, attr)]


def run_batch(name, **kw):
    b = BatchRun(name, **kw)
    while not b.advance(10 ** 9):
        pass
    return b


# --- U10: równoległy batch (tylko CLI; w Pyodide nie ma procesów) ----------------
_WORKER_NETWORKS = {}


def _batch_worker(job):
    """Jeden przebieg batcha w procesie roboczym; funkcja na poziomie modułu (pickle)."""
    params, seed, geojson, until_key = job
    if geojson:
        key = ("geojson", params.get("network_cleanup", False), params.get("geojson_crs", "auto"))
        if key not in _WORKER_NETWORKS:
            _WORKER_NETWORKS[key] = PathNetwork.from_geojson(geojson, drop_loops=key[1], crs=key[2])
    else:
        key = (params.get("synthetic_grid", DEFAULTS["synthetic_grid"]),
               params.get("synthetic_spacing", DEFAULTS["synthetic_spacing"]))
        if key not in _WORKER_NETWORKS:
            _WORKER_NETWORKS[key] = PathNetwork.synthetic(n=key[0], spacing=key[1])
    m = Model(Params(**params), seed=seed, network=_WORKER_NETWORKS[key])
    limit = getattr(m.p, until_key)
    while not (m.cycle > limit):
        m.step()
    return {attr: getattr(m, attr) for _, attr in BATCH_OUTPUTS}


def run_batch_parallel(name, workers=None, geojson=None, **kw):
    """Te same joby i seedy co BatchRun, przebiegi w osobnych procesach; wiersze w kolejności jobów
    (ex.map ją zachowuje), więc wynik identyczny z run_batch."""
    from concurrent.futures import ProcessPoolExecutor   # import tutaj: Pyodide nie ma procesów
    b = BatchRun(name, geojson=geojson, **kw)
    jobs = [(p, s, geojson, b.until_key) for p, s in b.jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(_batch_worker, jobs):
            for _, attr in BATCH_OUTPUTS:
                getattr(b, attr).extend(res[attr])
            b.done += 1
    return b


# ---------------------------------------------------------------------------
# testy (odpowiedniki experiment ... type: test z PD.gaml)
# ---------------------------------------------------------------------------

def _test_model(**overrides):
    # jak test experiment w GAMA: global.init bez agentów (wszystkie nb_* = 0)
    # U8: stały seed wyprowadzony z nazwy testu - testy statystyczne są powtarzalne
    name = sys._getframe(1).f_code.co_name
    return Model(Params(**overrides), seed=zlib.crc32(name.encode("utf-8")))


def _game(m, a, b, key):
    return m.create_game(a, b, key)


def t_disorder_decay():
    m = _test_model()
    c = m.cells[0]
    c.disorder = 1.0
    for _ in range(10):
        c.apply_decay(m)
    assert abs(c.disorder - m.p.disorder_decay ** 10) < 0.001


def t_disorder_bump_asymmetry():
    m = _test_model()
    assert m.disorder_bump_for("D", "D") == m.p.disorder_bump_dd
    assert m.disorder_bump_for("D", "C") == m.p.disorder_bump_d
    assert m.disorder_bump_for("C", "D") == m.p.disorder_bump_d
    assert m.disorder_bump_for("C", "C") == 0.0
    assert m.disorder_bump_for("D", "D") > m.disorder_bump_for("D", "C")


def t_broken_windows_affects_classic():
    m = _test_model(broken_windows_sensitivity=0.5)
    p = m.create_player("ALLC")
    here = m.cell_at(p.location)
    here.disorder = 0.0
    low = sum(p.strategy(p) == "D" for _ in range(1000))
    here.disorder = 1.0
    high = sum(p.strategy(p) == "D" for _ in range(1000))
    assert low == 0
    assert high > 400


def t_reputation_state_dimension():
    m = _test_model(generalization_threshold=3)
    p, opp = m.create_player(), m.create_player()
    p.setup_lists()
    here = m.cell_at(p.location)
    assert "SAFE" in p.get_state(opp)
    p.register_betrayal(here)
    assert "SAFE" in p.get_state(opp)
    p.register_betrayal(here)
    assert "SAFE" in p.get_state(opp)
    p.register_betrayal(here)
    assert "RISKY" in p.get_state(opp)


def t_anchor_decay():
    m = _test_model(broken_windows_sensitivity=0.0, anchor_decay_rate=0.15)
    p = m.create_player("QLEARN", character_strength=0.8)
    opp = m.create_player("QLEARN", character_strength=0.8)
    p.setup_lists()
    s0 = p.effective_anchor_strength(opp)
    assert abs(s0 - 0.8) < 0.001
    p.lists_per_other[opp] += ["C"] * 5
    s5 = p.effective_anchor_strength(opp)
    assert abs(s5 - 0.8 * math.exp(-0.15 * 5)) < 0.001
    assert s5 < s0


def t_anchor_erosion_by_disorder():
    m = _test_model(anchor_decay_rate=0.0)
    p = m.create_player("QLEARN", character_strength=0.8)
    opp = m.create_player("QLEARN", character_strength=0.8)
    p.setup_lists()
    m.p.broken_windows_sensitivity = 2.0
    m.cell_at(p.location).disorder = 1.0
    assert p.effective_anchor_strength(opp) == 0.0


def t_pending_action_sync():
    m = _test_model(anchor_decay_rate=0.0, broken_windows_sensitivity=0.0)
    kw = dict(base_character="ALLD", character_strength=1.0, epsilon=0.0)
    p, opp = m.create_player("QLEARN", **kw), m.create_player("QLEARN", **kw)
    p.setup_lists()
    played = p.QLEARN(opp)
    assert played == "D"
    assert p.pending_action[opp] == played


def t_pending_action_sync_broken_windows():
    m = _test_model()
    kw = dict(character_strength=0.0, epsilon=0.0, initial_cooperation_bias=1.0)
    p, opp = m.create_player("QLEARN", **kw), m.create_player("QLEARN", **kw)
    p.setup_lists()
    m.p.broken_windows_sensitivity = 1.0
    m.cell_at(p.location).disorder = 1.0
    for _ in range(200):
        played = p.strategy(opp)
        assert p.pending_action[opp] == played


def t_anchor_not_applied_to_classic():
    m = _test_model(character_strength_qlearn=0.9)
    classic, learner = m.create_player("TFT"), m.create_player("QLEARN")
    classic.apply_character_params()
    learner.apply_character_params()
    assert classic.character_strength == 0.0
    assert learner.character_strength == 0.9


def t_disorder_persists_not_just_noise():
    m = _test_model()
    hot, cold = m.cells[0], m.cells[49]
    hot.disorder = cold.disorder = 0.0
    for _ in range(20):
        hot.disorder += m.p.disorder_bump_dd
        hot.apply_decay(m)
        cold.apply_decay(m)
    assert hot.disorder > cold.disorder
    assert hot.disorder > 0.3


def t_reputation_creates_self_fulfilling_bias():
    m = _test_model(generalization_threshold=3, broken_windows_sensitivity=0.0)
    kw = dict(epsilon=0.0, character_strength=0.0, env_influence=0.0)
    p, opp = m.create_player("QLEARN", **kw), m.create_player("QLEARN", **kw)
    p.setup_lists()
    here = m.cell_at(p.location)
    p.lists_per_other[opp] += ["C"] * 10
    p.my_moves_per_other[opp] += ["C"] * 10
    p.q_c_per_other[opp]["C|C|SAFE"] = 5.0
    p.q_d_per_other[opp]["C|C|SAFE"] = 1.0
    p.q_c_per_other[opp]["C|C|RISKY"] = 0.0
    p.q_d_per_other[opp]["C|C|RISKY"] = 3.0
    assert p.get_state(opp) == "C|C|SAFE"
    assert p.QLEARN(opp) == "C"
    for _ in range(3):
        p.register_betrayal(here)
    assert p.get_state(opp) == "C|C|RISKY"
    assert p.QLEARN(opp) == "D"


def t_new_state_uses_cooperation_bias():
    m = _test_model(broken_windows_sensitivity=0.0)
    kw = dict(epsilon=0.0, character_strength=0.0, initial_cooperation_bias=0.8)
    p, opp = m.create_player("QLEARN", **kw), m.create_player("QLEARN", **kw)
    p.setup_lists()
    played = p.QLEARN(opp)
    p.lists_per_other[opp].append("C")
    p.my_moves_per_other[opp].append(played)
    p.update_q(opp, m.p.payoff_R)
    next_s = p.get_state(opp)
    assert abs(p.q_c_per_other[opp][next_s] - 0.8) < 0.001
    assert abs(p.q_d_per_other[opp][next_s] - 0.2) < 0.001


def t_tie_broken_randomly():
    m = _test_model(broken_windows_sensitivity=0.0)
    kw = dict(epsilon=0.0, character_strength=0.0, initial_cooperation_bias=0.5)
    p, opp = m.create_player("QLEARN", **kw), m.create_player("QLEARN", **kw)
    p.setup_lists()
    c = sum(p.QLEARN(opp) == "C" for _ in range(1000))
    assert 400 < c < 600


def t_anchor_shifts_early_behavior():
    m = _test_model(anchor_decay_rate=0.15, broken_windows_sensitivity=0.0)
    pa = m.create_player("QLEARN", base_character="ALLC", character_strength=0.9, epsilon=0.0,
                         initial_cooperation_bias=0.1)
    pb = m.create_player("QLEARN", base_character="ALLC", character_strength=0.0, epsilon=0.0,
                         initial_cooperation_bias=0.1)
    opp = m.create_player()
    pa.setup_lists()
    pb.setup_lists()
    ca = cb = 0
    for _ in range(100):
        ca += pa.QLEARN(opp) == "C"
        cb += pb.QLEARN(opp) == "C"
    assert ca > cb


def t_payoff_validation():
    m = _test_model()
    P = m.p
    P.game_type = "PD"
    P.payoff_T, P.payoff_R, P.payoff_P, P.payoff_S = 9.0, 5.0, 1.0, 0.0
    assert m.payoffs_valid() and m.payoffs_integer()
    P.game_type = "weak_PD"
    assert not m.payoffs_valid()
    P.payoff_T, P.payoff_R, P.payoff_P, P.payoff_S = 1.6, 1.0, 0.0, 0.0
    assert m.payoffs_valid() and not m.payoffs_integer()
    P.game_type = "snowdrift"
    assert not m.payoffs_valid()
    P.payoff_T, P.payoff_R, P.payoff_S, P.payoff_P = 4.0, 3.0, 2.0, 0.0
    assert m.payoffs_valid()
    P.game_type = "PD"
    assert not m.payoffs_valid()


def t_classic_start_switch():
    m = _test_model(broken_windows_sensitivity=0.0)
    tft, tf2t, wsls, opp = (m.create_player(c) for c in ("TFT", "TF2T", "WSLS", "ALLC"))
    for pl in m.players:
        pl.setup_lists()
    m.p.classic_start_cooperate = True
    d_on = sum(pl.strategy(opp) == "D" for _ in range(100) for pl in (tft, tf2t, wsls))
    assert d_on == 0
    m.p.classic_start_cooperate = False
    d_off = sum(pl.strategy(opp) == "D" for _ in range(100) for pl in (tft, tf2t, wsls))
    assert 100 < d_off < 200


def t_lazy_partner_init():
    m = _test_model(log_games=False, unlimited_games=True)
    a, b = m.create_player("TFT"), m.create_player("TFT")
    assert b not in a.lists_per_other
    _game(m, a, b, "t")
    assert len(a.lists_per_other[b]) == 1 and len(b.lists_per_other[a]) == 1
    assert a.known_others == [b]


def t_forget_clears_all_maps():
    m = _test_model(log_games=False, unlimited_games=True, broken_windows_sensitivity=0.0, dunbar_limit=0)
    a, b = m.create_player("QLEARN"), m.create_player("QLEARN")
    a.setup_lists()
    _game(m, a, b, "t")
    maps = lambda pl: (pl.lists_per_other, pl.my_moves_per_other, pl.q_c_per_other, pl.q_d_per_other,
                       pl.pending_state, pl.pending_action, pl.social_feedback)
    assert all(b in mp for mp in maps(a)) and b in a.known_others
    a.forget_partner(b)
    assert all(b not in mp for mp in maps(a)) and b not in a.known_others
    assert a.nb_forgotten == 1
    assert a in b.lists_per_other and a in b.known_others


def t_lru_keeps_most_recent():
    m = _test_model(log_games=False, unlimited_games=True, broken_windows_sensitivity=0.0, dunbar_limit=2)
    a, b, c, d = (m.create_player("ALLC") for _ in range(4))
    _game(m, a, b, "ab1")
    _game(m, a, c, "ac1")
    assert a.known_others == [b, c]
    _game(m, a, b, "ab2")
    assert a.known_others == [c, b]
    _game(m, a, d, "ad1")
    assert a.known_others == [b, d]
    assert c not in a.lists_per_other and b in a.lists_per_other
    assert len(a.lists_per_other[b]) == 2
    m.p.dunbar_limit = 1
    _game(m, a, c, "ac2")
    assert a.known_others == [c]


def t_anchor_full_after_forget():
    m = _test_model(log_games=False, unlimited_games=True, broken_windows_sensitivity=0.0, anchor_decay_rate=0.15)
    a = m.create_player("QLEARN", character_strength=0.8)
    b = m.create_player("QLEARN", character_strength=0.8)
    for i in range(1, 6):
        _game(m, a, b, "ab%d" % i)
    assert a.effective_anchor_strength(b) < 0.8
    a.forget_partner(b)
    a.ensure_partner(b)
    assert abs(a.effective_anchor_strength(b) - 0.8) < 0.001


def t_pending_action_sync_with_dunbar():
    m = _test_model(log_games=False, unlimited_games=True, dunbar_limit=1, broken_windows_sensitivity=1.0)
    a = m.create_player("QLEARN", epsilon=0.0, initial_cooperation_bias=1.0)
    opps = [m.create_player("ALLC"), m.create_player("ALLC")]
    for c in m.cells:
        c.disorder = 0.5
    for i in range(1, 51):
        opp = opps[i % 2]
        _game(m, a, opp, "g%d" % i)
        assert a.pending_action[opp] == a.my_moves_per_other[opp][-1]
        assert len(a.known_others) == 1
    assert a.nb_forgotten == 49


def t_disorder_clamp():
    m = _test_model(log_games=False, unlimited_games=True, broken_windows_sensitivity=0.0)
    a, b = m.create_player("ALLD"), m.create_player("ALLD")
    cell_a = m.cell_at(a.location)
    m.p.disorder_clamp = True
    for i in range(20):
        _game(m, a, b, "c%d" % i)
    assert cell_a.disorder == 1.0
    m.p.disorder_clamp = False
    for i in range(20):
        _game(m, a, b, "u%d" % i)
    assert cell_a.disorder > 1.0


def t_exploitation_counter():
    m = _test_model(log_games=False, unlimited_games=True, broken_windows_sensitivity=0.0)
    c, d1, d2 = m.create_player("ALLC"), m.create_player("ALLD"), m.create_player("ALLD")
    _game(m, c, d1, "cd")
    assert m.nb_exploitations == 1
    _game(m, d1, d2, "dd")
    assert m.nb_exploitations == 1
    assert abs(m.exploitation_rate() - 0.5) < 1e-9


def t_fermi_rule():
    m = _test_model(fermi_k=0.5, mutation_rate=0.0)
    me = m.create_player("ALLC", window_payoff=0.0, window_games=10)
    rich = m.create_player("ALLD", window_payoff=90.0, window_games=10)
    equal = m.create_player("TFT", window_payoff=0.0, window_games=10)
    adopt_rich = sum(me.evolution_choice(rich) == "ALLD" for _ in range(1000))
    adopt_equal = sum(me.evolution_choice(equal) == "TFT" for _ in range(1000))
    assert adopt_rich > 990
    assert 430 < adopt_equal < 570
    assert abs(m.fermi_probability(3.0, 3.0) - 0.5) < 1e-9


def t_no_imitation_undefined_or_not_evolvable():
    m = _test_model(mutation_rate=0.0)
    idle = m.create_player("ALLC", window_games=0)
    rich = m.create_player("ALLD", window_payoff=90.0, window_games=10)
    learner = m.create_player("QLEARN", window_payoff=90.0, window_games=10)
    me = m.create_player("ALLC", window_games=10)
    for _ in range(200):
        assert idle.evolution_choice(rich) == "ALLC"
        assert me.evolution_choice(learner) == "ALLC"


def t_mutation_only_evolvable():
    m = _test_model(mutation_rate=1.0, evolvable_characters=["ALLC", "ALLD"])
    me = m.create_player("ALLC")
    assert all(me.evolution_choice(None) in ("ALLC", "ALLD") for _ in range(500))


def t_grim_since_takeover():
    m = _test_model(log_games=False, unlimited_games=True, broken_windows_sensitivity=0.0)
    p, opp = m.create_player("TFT"), m.create_player("ALLD")
    _game(m, p, opp, "g1")
    assert "D" in p.lists_per_other[opp]
    p.change_character("GRIM")
    assert p.character == "GRIM" and len(p.lists_per_other[opp]) == 1
    assert p.GRIM(opp) == "C"
    _game(m, p, opp, "g2")
    assert p.GRIM(opp) == "D"


def t_evolution_step():
    m = _test_model(evolution_on=True, well_mixed=True, fermi_k=0.01, mutation_rate=0.0)
    for _ in range(5):
        m.create_player("ALLC", window_payoff=0.0, window_games=10)
    for _ in range(5):
        m.create_player("ALLD", window_payoff=90.0, window_games=10)
    learner = m.create_player("QLEARN", window_games=10)
    m.evolution_step()
    assert learner.character == "QLEARN"
    assert all(p.window_games == 0 for p in m.players)
    assert sum(p.character == "ALLD" for p in m.players) >= 5


def t_well_mixed_pairing():
    m = _test_model(well_mixed=True, unlimited_games=True, log_games=False, vision_radius=1)
    a = m.create_player("ALLC", _loc=(0.0, 0.0))
    m.create_player("ALLC", _loc=(m.width, m.height))
    a.reflex_do_you_wanna_play()
    assert a.nb_games == 1


def t_pending_action_sync_all_modules():
    m = _test_model(log_games=False, unlimited_games=True, dunbar_limit=2, evolution_on=True,
                    mutation_rate=0.3, well_mixed=True, broken_windows_sensitivity=1.0)
    a = m.create_player("QLEARN", epsilon=0.0, initial_cooperation_bias=1.0)
    opps = [m.create_player("ALLC") for _ in range(3)]
    for c in m.cells:
        c.disorder = 0.5
    for i in range(1, 61):
        opp = opps[i % 3]
        _game(m, a, opp, "g%d" % i)
        assert a.pending_action[opp] == a.my_moves_per_other[opp][-1]
        if i % 10 == 0:
            m.evolution_step()
    assert a.character == "QLEARN"


def t_compat_core_disables_noncore():
    m = _test_model(nb_QLEARN=5, nb_AQLEARN=5, movement_sensitivity=2.0, env_influence_qlearn=0.5,
                    social_sensitivity_aqlearn=1.5, social_learning_boost_aqlearn=2.0,
                    broken_windows_sensitivity=0.4, character_strength_qlearn=0.6, unlimited_games=False,
                    log_games=False)
    assert len(m.core_violations()) == 7
    m.p.compat_N, m.p.compat_mix = 200, "equal"
    m.apply_compat_core()
    assert m.p.nb_QLEARN == 0 and m.p.broken_windows_sensitivity == 0.0
    assert sum(getattr(m.p, "nb_" + c) for c in CLASSIC) == 200 and m.p.classic_start_cooperate
    # pełny model z compat_core: nawet przy "zabrudzonych" parametrach powstaje czysty rdzeń
    full = Model(Params(compat_core=True, compat_N=70, nb_QLEARN=5, movement_sensitivity=2.0,
                        broken_windows_sensitivity=0.4, character_strength_qlearn=0.6, log_games=False), seed=1)
    assert full.core_violations() == []
    assert len(full.players) == 70 and all(p.character in CLASSIC for p in full.players)
    m.p.compat_mix = "tft_alld"
    m.apply_compat_core()
    assert m.p.nb_ALLD == 40 and m.p.nb_TFT == 160
    assert sum(getattr(m.p, "nb_" + c) for c in ("ALLC", "FTFT", "TF2T", "GRIM", "WSLS")) == 0


def t_payoff_presets():
    for pr in PAYOFF_PRESETS:
        m = _test_model(payoff_preset=pr, unlimited_games=True)
        assert m.payoffs_valid()


def t_stability_detection():
    # agenci rozproszeni w ogromnym świecie, bez gier: udziały stałe -> trend 0, stabilizacja
    m = Model(Params(compat_core=True, compat_N=14, compat_export=True, vision_radius=0, real_env=False,
                     world_size=100000, warmup=100,
                     stab_window=200, stab_k=3, end_cycle=2000, log_games=False), seed=3)
    m.run(2001)
    assert m.nb_game == 0
    row = m.compat_rows[0]
    assert len(row) == len(COMPAT_HEADER) and row[COMPAT_HEADER.index("stabilized")] is True
    assert row[COMPAT_HEADER.index("alld_trend_10k")] == 0.0


def t_trend_criterion():
    # sztuczny szereg: ALLD rośnie liniowo o 0,05 na 10 000 cykli -> trend 0,05, brak stabilizacji
    m = _test_model(end_cycle=20000)
    for t in range(10100, 20001, 100):
        y = 0.3 + 0.05 * (t / 10000.0)
        m.tr = [m.tr[0] + 1, m.tr[1] + t, m.tr[2] + y, m.tr[3] + t * t, m.tr[4] + t * y]
    assert abs(m.alld_trend_10k() - 0.05) < 1e-6
    assert not abs(m.alld_trend_10k()) < m.p.stab_trend_eps


def t_network_variants():
    base = PathNetwork.synthetic(n=12)
    c0, n0, e0 = base.components(), len([v for v in base.adj if base.adj[v]]), len(PathNetwork._edges(base.adj))
    frag = base.variant("fragmented", random.Random(7), fraction=0.2)
    assert frag.components() == c0
    assert frag.edges_removed == e0 - len(PathNetwork._edges(frag.adj)) > 0
    assert len([v for v in frag.adj if frag.adj[v]]) == n0          # żaden węzeł nie znika
    assert len(PathNetwork._edges(frag.adj)) < e0
    conn = base.variant("connected", random.Random(7), count=10, max_length=100.0)
    assert len(PathNetwork._edges(conn.adj)) == e0 + 10
    assert conn.components() <= c0
    # ten sam seed -> ta sama sieć; inny seed -> zwykle inna
    again = base.variant("fragmented", random.Random(7), fraction=0.2)
    assert PathNetwork._edges(again.adj) == PathNetwork._edges(frag.adj)
    assert base.variant("baseline", random.Random(1)) is base
    # sieć-drzewo (ścieżka): nie ma czego usunąć bez rozcięcia -> 0 usuniętych mimo fraction 0.5
    tree = PathNetwork([[(i, 0.0), (i + 1.0, 0.0)] for i in range(10)], 10, 1, "t")
    assert tree.variant("fragmented", random.Random(1), fraction=0.5).edges_removed == 0


def t_network_stats_known_graph():
    # ścieżka 4 węzłów: a-b-c-d; średnia najkrótsza ścieżka = (1+2+3+1+1+2+2+1+1+3+2+1)/12 = 20/12
    net = PathNetwork([[(0, 0), (1, 0)], [(1, 0), (2, 0)], [(2, 0), (3, 0)]], 3, 1, "test")
    st = net.stats(100)
    assert st["net_nodes"] == 4 and st["net_edges"] == 3
    assert abs(st["net_avg_path"] - 20 / 12) < 1e-9
    assert abs(st["net_mean_degree"] - 1.5) < 1e-9
    # betweenness środkowych węzłów: 2 pary przez każdy, norm = 3 -> 2/3
    assert abs(st["net_betw_max"] - 2 / 3) < 1e-9


def t_encounter_metric():
    m = _test_model(log_games=False, unlimited_games=True, broken_windows_sensitivity=0.0, dunbar_limit=1)
    a, b, c = (m.create_player("ALLC") for _ in range(3))
    _game(m, a, b, "g1")      # nowy
    _game(m, a, b, "g2")      # pamiętany i znany
    _game(m, a, c, "g3")      # nowy; b zapomniany
    _game(m, a, b, "g4")      # niepamiętany, ale znany
    assert (a.enc_games, a.enc_rep_rem, a.enc_rep_ever) == (4, 1, 2)
    assert len(a.enc_partners) == 2 and a.met_count[b] == 3
    cell = m.cell_at(a.location)
    assert cell.enc_games >= 4
    m._reflex_close_encounter_window()
    # a: pamiętany 1/4, znany 2/4; b (gry g1, g2, g4; pamięta a cały czas): 2/3 i 2/3; c: 0/1 i 0/1
    assert abs(m.enc_share_remembered - (1 / 4 + 2 / 3 + 0) / 3) < 1e-9
    assert abs(m.enc_share_ever - (2 / 4 + 2 / 3 + 0) / 3) < 1e-9
    assert abs(m.enc_distinct - (2 + 1 + 1) / 3) < 1e-9
    assert a.enc_games == 0 and cell.last_share_rem >= 0


def t_hooks_preserve_behaviour():
    m = _test_model()
    me = m.create_player("ALLC", window_payoff=12.0, window_games=4)
    other = m.create_player("ALLD")
    assert me.compute_pi() == 3.0 and other.compute_pi() == 0.0
    me.init_beliefs_for(other)
    assert me.lists_per_other[other] == [] and me.q_c_per_other[other] == {}
    m.p.movement_mode = "schelling"
    try:
        me.choose_direction([0])
        assert False
    except ModelError:
        pass


def t_batch_collects_all_outputs():
    # U1: BatchRun przenosi wszystkie wiersze, łącznie z encounter_rows (PM4_heatmap)
    b = run_batch("PM4_heatmap", repeat=1, end_cycle=300)
    names = [n for n, _ in batch_outputs(b)]
    assert "compat_results.csv" in names and "encounter_cells.csv" in names
    assert len(b.compat_rows) == 3 and b.encounter_rows
    assert all(len(r) == len(CSV_HEADERS["encounter_cells.csv"]) for r in b.encounter_rows)


def t_network_cleanup():
    # U2: odcinki głównej sieci + zamknięty pierścień (izolowany wierzchołek) + mała odłączona składowa
    main = [[(x * 20.0, 50.0), (x * 20.0 + 20.0, 50.0)] for x in range(10)]
    ring = [[(100.0, 10.0), (110.0, 10.0), (110.0, 20.0), (100.0, 10.0)]]
    island = [[(10.0, 90.0), (20.0, 90.0)]]
    polys = main + ring + island
    raw = PathNetwork(polys, 200.0, 100.0, "test")
    assert any(not raw.adj[v] for v in raw.adj)                      # pętla -> wierzchołek bez krawędzi
    clean = PathNetwork(polys, 200.0, 100.0, "test", drop_loops=True)
    assert all(clean.adj[v] for v in clean.adj)
    assert len(clean.largest_component()) == 11
    for net, cleanup in ((raw, False), (clean, True)):
        m = Model(Params(nb_TFT=200, network_cleanup=cleanup, log_games=False), seed=5, network=net)
        stuck = [p for p in m.players if not net.adj[p.current_node]]
        on_island = [p for p in m.players if p.current_node not in net.largest_component()]
        if cleanup:
            assert not stuck and not on_island
        else:
            assert stuck and on_island                                  # zachowanie jak w PD.gaml


def t_games_per_partner_unaffected_by_window():
    # U4: przycięcie okna partnerów (partner_window) nie zmienia gier na partnera
    m = _test_model(log_games=False, unlimited_games=True, broken_windows_sensitivity=0.0, partner_window=1)
    a, b, c = (m.create_player("ALLC") for _ in range(3))
    for i in range(4):
        _game(m, a, b, "ab%d" % i)
    _game(m, a, c, "ac")
    m.cycle = 10
    before = m.mean_games_per_partner()
    m.mean_distinct_partners_window()              # przycina last_met_cycle
    assert m.mean_games_per_partner() == before
    assert abs(before - (5 / 2 + 4 / 1 + 1 / 1) / 3) < 1e-9


def t_snowdrift_feedback_warning():
    # U6: ostrzeżenie tylko gdy snowdrift + ruch/uczenie środowiskowe; compat_core je zeruje
    warn = _test_model(payoff_preset="snowdrift", unlimited_games=True, movement_sensitivity=2.0)
    assert any("feedback" in w for w in warn.warnings)
    core = _test_model(payoff_preset="snowdrift", compat_core=True, compat_N=0)
    assert not any("feedback" in w for w in core.warnings)
    pd = _test_model(movement_sensitivity=2.0)
    assert not any("feedback" in w for w in pd.warnings)


def t_geojson_crs():
    # U8: mały lokalny układ metryczny - "auto" bierze go za lon/lat, "projected" zostawia metry
    gj = {"type": "LineString", "coordinates": [[10.0, 20.0], [50.0, 20.0], [50.0, 60.0]]}
    auto = PathNetwork.from_geojson(gj)
    proj = PathNetwork.from_geojson(gj, crs="projected")
    assert abs(proj.width - 40.0) < 1e-9 and abs(proj.height - 40.0) < 1e-9
    assert auto.width > 1000                      # potraktowane jako stopnie -> tysiące km
    try:
        PathNetwork.from_geojson(gj, crs="utm")
        assert False
    except ModelError:
        pass


def t_batch_overrides():
    # U8: --set nadpisuje parametry batcha (także te z among)
    b = BatchRun("A_baseline", repeat=1, end_cycle=5, overrides={"nb_QLEARN": 3, "vision_radius": 55})
    assert all(p["nb_QLEARN"] == 3 and p["vision_radius"] == 55 for p, _ in b.jobs)
    b2 = BatchRun("R0_regression", repeat=1, end_cycle=5, overrides={"unlimited_games": True})
    assert all(p["unlimited_games"] is True for p, _ in b2.jobs)


def t_parallel_batch_matches_sequential():
    # U10: tryb równoległy daje identyczne wiersze w tej samej kolejności (pomijany w przeglądarce)
    if sys.platform == "emscripten":
        return
    # A_baseline nie ma stałego seedu (keep_seed: false, jak w PD.gaml) - seed podany jawnie
    seq = run_batch("A_baseline", repeat=2, end_cycle=200, seed=123)
    par = run_batch_parallel("A_baseline", workers=2, repeat=2, end_cycle=200, seed=123)
    assert seq.ablation_rows and par.ablation_rows == seq.ablation_rows
    seq2 = run_batch("PM4_heatmap", repeat=1, end_cycle=150)
    par2 = run_batch_parallel("PM4_heatmap", workers=2, repeat=1, end_cycle=150)
    for _, attr in BATCH_OUTPUTS:
        assert getattr(par2, attr) == getattr(seq2, attr), attr


def _kin_model(**kw):
    base = dict(compat_core=True, compat_mix="allc_alld", compat_N=200, well_mixed=True, evolution_on=True,
                evolution_interval=10 ** 9, payoff_mode="donation", b=1.0, c=0.3, kin_on=True, family_size=10,
                log_games=False)
    base.update(kw)
    return Model(Params(**base), seed=zlib.crc32(sys._getframe(1).f_code.co_name.encode("utf-8")))


def t_kin_off_regression():
    # kin_on = false: parametry modułu 3 nic nie zmieniają (te same losowania, te same wyniki)
    p = dict(nb_TFT=6, nb_ALLD=6, nb_ALLC=6, unlimited_games=True, vision_radius=40, log_games=False,
             evolution_on=True, mutation_rate=0.05, evolution_interval=50)
    a = Model(Params(**p), seed=3).run(400)
    b = Model(Params(**p, family_size=3, family_r=0.9, kin_matching_prob=0.7, kin_imitation_bias=0.5,
                     kin_strategy_correlation=1.0, fitness_mode="inclusive"), seed=3).run(400)
    assert (a.nb_game, a.nb_moves_D, [q.character for q in a.players], [q.score for q in a.players]) == \
           (b.nb_game, b.nb_moves_D, [q.character for q in b.players], [q.score for q in b.players])


def t_donation_matrix():
    m = _kin_model(b=2.0, c=0.5)
    assert (m.p.payoff_T, m.p.payoff_R, m.p.payoff_P, m.p.payoff_S) == (2.0, 1.5, 0.0, -0.5)
    assert any("Gra dawcy" in w for w in m.warnings)
    for b, c in ((1.0, 1.0), (1.0, 1.5), (1.0, 0.0)):
        try:
            _kin_model(b=b, c=c)
            assert False, (b, c)
        except ModelError:
            pass


def t_kin_requires_evolution():
    try:
        _kin_model(evolution_on=False)
        assert False
    except ModelError as e:
        assert "evolution_on" in str(e)


def t_family_id_stable():
    m = _kin_model(kin_strategy_correlation=1.0)
    p = m.players[0]
    fid = p.family_id
    assert fid >= 0 and all(len(f) == 10 for f in m.families)
    p.change_character("ALLD" if p.character == "ALLC" else "ALLC")
    assert p.family_id == fid and p in m.families[fid]


def t_kin_matching_shares():
    # α = 1: każda gra inicjowana z krewnym; α = 0: udział krewnych ≈ (fs - 1) / (N - 1)
    one = _kin_model(kin_matching_prob=1.0).run(300)
    assert one.kin_stats.summary()["kin_share"] > 0.99
    zero = _kin_model(kin_matching_prob=0.0).run(300)
    assert abs(zero.kin_stats.summary()["kin_share"] - 9 / 199) < 0.02


def t_r_hat_matches_alpha():
    # rodziny jednorodne (korelacja 1), ALLC/ALLD, bez zmian strategii, bez blokady rewanżu: r̂ ≈ α
    for alpha in (0.0, 0.3, 0.6, 0.9):
        m = _kin_model(kin_matching_prob=alpha, kin_strategy_correlation=1.0, pair_cooldown=0).run(400)
        r = m.kin_stats.summary()["r_hat_all"]
        assert abs(r - alpha) < 0.03, (alpha, r)


def t_strategy_matching_r_hat():
    # kontrola P4: partner z tą samą strategią z prawdopodobieństwem α -> r̂ ≈ α bez względu na rodziny
    for alpha in (0.3, 0.7):
        m = _kin_model(kin_matching_prob=alpha, kin_matching_mode="strategy", pair_cooldown=0).run(400)
        assert abs(m.kin_stats.summary()["r_hat_all"] - alpha) < 0.03, alpha
    try:
        _kin_model(kin_matching_mode="xyz")
        assert False, "zły kin_matching_mode przepuszczony"
    except ModelError:
        pass


def t_pair_cooldown_suppresses_kin_games():
    # blokada rewanżu (10 cykli) tłumi gry z krewnymi (tylko 9 krewnych) -> r̂ < α; stąd pair_cooldown = 0 w P4
    blocked = _kin_model(kin_matching_prob=0.6, kin_strategy_correlation=1.0).run(300)
    assert blocked.kin_stats.summary()["kin_share"] < 0.5
    assert blocked.kin_stats.summary()["r_hat_all"] < 0.5


def t_r_hat_known_values():
    s = KinStats()
    for x, y in ((1, 1), (1, 0), (0, 0), (0, 0)):          # nachylenie = 0,5
        KinStats._add(s.all, x, y)
    assert abs(KinStats.r_hat(s.all) - 0.5) < 1e-12
    s2 = KinStats()
    for m1, m2 in (("C", "C"), ("D", "D"), ("C", "C"), ("D", "D")):   # pełna korelacja
        s2.record(m1, m2, kin=True)
    assert abs(KinStats.r_hat(s2.all) - 1.0) < 1e-12 and s2.summary()["kin_share"] == 1.0
    assert KinStats.r_hat(KinStats().all) is None


def t_r_hat_within_blocks():
    # blok A: same C, blok B: same D (zmiana składu, brak korelacji w bloku), blok C: nachylenie 0,5
    s = KinStats()
    for block in (((1, 1), (1, 1)), ((0, 0), (0, 0)), ((1, 1), (1, 0), (0, 0), (0, 0))):
        for x, y in block:
            KinStats._add(s.all, x, y)
            KinStats._add(s.blk_all, x, y)
        s.close_block()
    assert abs(KinStats.r_hat(s.all) - 0.75) < 1e-12                      # łącznie: zawyżone
    assert abs(KinStats.r_hat_within(s.blk_all, s.fe_all) - 0.5) < 1e-12  # w blokach: 0,5
    t = KinStats()
    for block in (((1, 1), (1, 1)), ((0, 0), (0, 0))):
        for x, y in block:
            KinStats._add(t.blk_all, x, y)
        t.close_block()
    assert KinStats.r_hat_within(t.blk_all, t.fe_all) is None            # brak zmienności w blokach


def t_inclusive_equals_own_at_r0():
    for variant in ("add", "strip"):
        m = _kin_model(fitness_mode="inclusive", inclusive_variant=variant, family_r=0.0, kin_matching_prob=0.5).run(200)
        for p in m.players[:30]:
            m.p.fitness_mode = "own"
            own = p.compute_pi()
            m.p.fitness_mode = "inclusive"
            assert abs(p.compute_pi() - own) < 1e-12


def t_inclusive_components():
    # gra dawcy b=1, c=0.3: krewny ALLC daje partnerowi +1 (skutek), ALLD daje 0
    m = _kin_model(fitness_mode="inclusive", family_r=0.5)
    fam = next(f for f in m.families if len(f) >= 2)
    a, b = fam[0], fam[1]
    a.character, b.character = "ALLC", "ALLD"
    for p in (a, b):
        p.window_payoff = p.window_games = 0
        p.window_kin_given = p.window_kin_received = 0.0
    _game(m, a, b, "k1")
    assert (a.window_kin_given, a.window_kin_received) == (1.0, 0.0)
    assert (b.window_kin_given, b.window_kin_received) == (0.0, 1.0)
    m.p.inclusive_variant = "add"
    assert abs(a.compute_pi() - (-0.3 + 0.5 * 1.0)) < 1e-12           # add
    assert abs(b.compute_pi() - (1.0 + 0.5 * 0.0)) < 1e-12            # add: otrzymane zostaje w π_own
    m.p.inclusive_variant = "strip"
    assert abs(b.compute_pi() - (1.0 + 0.5 * (0.0 - 1.0))) < 1e-12     # strip


def t_smoke_full_run():
    # nie ma odpowiednika w GAML: przebieg całego modelu na syntetycznej sieci bez błędów
    m = Model(Params(nb_QLEARN=4, nb_AQLEARN=4, nb_TFT=2, nb_ALLC=2, nb_ALLD=2, nb_FTFT=2, nb_TF2T=2,
                     nb_GRIM=2, nb_WSLS=2, vision_radius=40, social_sensitivity_aqlearn=1.5,
                     social_learning_boost_aqlearn=2.0, broken_windows_sensitivity=0.4,
                     character_strength_qlearn=0.6, env_influence_qlearn=0.5, dunbar_limit=3,
                     log_games=True, end_cycle=300), seed=7)
    m.run(301)
    assert m.nb_game > 0 and len(m.ablation_rows) == 1
    assert all(len(p.known_others) <= 3 for p in m.players)
    json.loads(m.snapshot())


TESTS = [(name[2:], fn) for name, fn in sorted(globals().items()) if name.startswith("t_") and callable(fn)]


def run_self_tests():
    results = []
    for name, fn in TESTS:
        try:
            fn()
            results.append((name, True, ""))
        except AssertionError as e:
            results.append((name, False, "asercja nie przeszła " + str(e)))
        except Exception as e:  # noqa: BLE001
            results.append((name, False, "%s: %s" % (type(e).__name__, e)))
    return results


def run_self_tests_json():
    return json.dumps([{"name": n, "ok": ok, "msg": msg} for n, ok, msg in run_self_tests()])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_value(v):
    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="SIPD – port PD.gaml do Pythona")
    ap.add_argument("--test", action="store_true", help="uruchom testy")
    ap.add_argument("--experiment", choices=sorted(BATCH_EXPERIMENTS), help="eksperyment batch")
    ap.add_argument("--repeat", type=int)
    ap.add_argument("--end-cycle", type=int, help="nadpisuje end_cycle (lub regression_cycle dla R0)")
    ap.add_argument("--geojson", help="plik sieci ścieżek (drogi.geojson); bez niego sieć syntetyczna")
    ap.add_argument("--gui-demo", action="store_true", help="pojedynczy przebieg z parametrami --set")
    ap.add_argument("--cycles", type=int, default=1000)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--set", nargs="*", default=[], metavar="NAZWA=WARTOŚĆ",
                    help="nadpisanie parametrów (--gui-demo i --experiment)")
    ap.add_argument("--out", default=".", help="katalog na pliki CSV")
    ap.add_argument("--workers", type=int, default=1, help="procesy dla --experiment (1 = sekwencyjnie)")
    a = ap.parse_args(argv)

    geo = open(a.geojson, encoding="utf-8").read() if a.geojson else None
    import os

    def save(name, rows):
        os.makedirs(a.out, exist_ok=True)
        path = os.path.join(a.out, name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(to_csv(name, rows))
        print("zapisano", path, "(%d wierszy)" % len(rows))

    if a.test:
        res = run_self_tests()
        for n, ok, msg in res:
            print(("OK   " if ok else "FAIL ") + n + ("" if ok else "  -> " + msg))
        failed = sum(not ok for _, ok, _ in res)
        print("%d/%d testów przeszło" % (len(res) - failed, len(res)))
        return 1 if failed else 0
    if a.experiment:
        t0 = time.time()
        overrides = {k: _parse_value(v) for k, v in (s.split("=", 1) for s in a.set)}
        kw = dict(repeat=a.repeat, end_cycle=a.end_cycle, geojson=geo, seed=a.seed, overrides=overrides)
        b = (run_batch_parallel(a.experiment, workers=a.workers, **kw) if a.workers and a.workers > 1
             else run_batch(a.experiment, **kw))
        print("%s: %d przebiegów, %.1f s" % (a.experiment, b.total, time.time() - t0))
        for name, rows in batch_outputs(b):
            save(name, rows)
        return 0
    if a.gui_demo:
        overrides = {k: _parse_value(v) for k, v in (s.split("=", 1) for s in a.set)}
        m = Model(Params(**overrides), seed=a.seed, geojson=geo)
        for w in m.warnings:
            print(w)
        t0 = time.time()
        m.run(a.cycles)
        dt = time.time() - t0
        print("cykli: %d, gier: %d, C/D: %d/%d, %.2f ms/cykl" % (m.cycle, m.nb_game, m.nb_moves_C,
                                                                m.nb_moves_D, 1000 * dt / max(1, m.cycle)))
        for ch in CHARACTERS:
            if any(p.character == ch for p in m.players):
                print("  %-8s średnio %.1f pkt/1000 gier" % (ch, m.mean_for(ch)))
        if m.game_log:
            save("PD.csv", m.game_log)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
