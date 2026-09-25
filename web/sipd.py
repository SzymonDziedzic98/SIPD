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
import time

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
    "vision_radius": 10,
    "world_size": 10,
    "payoff_R": 5.0, "payoff_P": 1.0, "payoff_T": 9.0, "payoff_S": 0.0,
    "game_type": "PD",
    "classic_start_cooperate": False,
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
        ("unlimited_games", "Ograniczenie rozgrywania gier"),
        ("world_size", "Rozmiar świata (działa przy sztucznym środowisku)"),
        ("grid_cols", "Kolumny siatki"), ("grid_rows", "Wiersze siatki"),
        ("vision_radius", "Zasięg widzenia"),
        ("movement_sensitivity", "Czułość ruchu (środowisko)"),
        ("env_influence_qlearn", "Wpływ środowiska na decyzję QLEARN"),
        ("social_sensitivity_aqlearn", "Czułość społeczna AQLEARN"),
        ("social_learning_boost_aqlearn", "Wzmocnienie uczenia społecznego AQLEARN"),
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
    ("Diagnostyka", [
        ("perf_log", "Pomiar czasu cyklu"),
        ("perf_interval", "Okno pomiaru (cykle)"),
        ("regression_export", "Eksport odcisku regresyjnego"),
        ("regression_cycle", "Cykl odcisku"),
    ]),
]
GAME_TYPES = ["PD", "weak_PD", "snowdrift"]


class ModelError(Exception):
    """Odpowiednik `error` w GAML."""


class Params:
    def __init__(self, **overrides):
        self.__dict__.update(DEFAULTS)
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
    """Graf nieskierowany: wierzchołki = końce odcinków, krawędzie = polilinie."""

    def __init__(self, polylines, width, height, source):
        self.width = width
        self.height = height
        self.source = source
        self.polylines = polylines            # do rysowania (path_segment / park_boundary)
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
            a, b = vid(pl[0]), vid(pl[-1])
            if a == b:
                continue
            length = _polyline_length(pl)
            old = self.adj[a].get(b)
            if old is None or _polyline_length(old) > length:
                self.adj[a][b] = list(pl)
                self.adj[b][a] = list(reversed(pl))

    def closest_vertex(self, pt):
        if not self.vertices:
            return None
        return min(range(len(self.vertices)), key=lambda i: _dist(self.vertices[i], pt))

    def neighbors(self, v):
        return list(self.adj.get(v, {}).keys())

    @classmethod
    def from_geojson(cls, data):
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
        geographic = all(-180 <= x <= 180 for x in xs) and all(-90 <= y <= 90 for y in ys)
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
        return cls(lines, max(xs) - minx, maxy - min(ys), "geojson")

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

class Cell:
    __slots__ = ("index", "col", "row", "disorder", "x0", "y0", "w", "h")

    def __init__(self, index, col, row, x0, y0, w, h):
        self.index, self.col, self.row = index, col, row
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.disorder = 0.0

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
        self.lifespan = 10
        self.location = location
        m, P = model, model.p

        m.nb_game += 1
        p1.ensure_partner(p2)
        p2.ensure_partner(p1)
        self.p1_move = p1.strategy(p2)
        self.p2_move = p2.strategy(p1)
        p1_move, p2_move = self.p1_move, self.p2_move

        fb_p1 = m.feedback_value(p1_move, p2_move)
        fb_p2 = m.feedback_value(p2_move, p1_move)
        cell_p1 = m.cell_at(p1.location)
        cell_p2 = m.cell_at(p2.location)

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

        bump = m.disorder_bump_for(p1_move, p2_move)
        if bump > 0:
            if cell_p1 is not None:
                cell_p1.disorder += bump
            if cell_p2 is not cell_p1 and cell_p2 is not None:
                cell_p2.disorder += bump

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

        if p1.character in LEARNERS:
            p1.update_q(p2, p1_payoff)
        if p2.character in LEARNERS:
            p2.update_q(p1, p2_payoff)

        p1.touch_partner(p2)
        p2.touch_partner(p1)

        if P.log_games:
            row = [m.nb_game, m.cycle, p1.name, p2.name, p1_move, p2_move, p1.score, p2.score]
            m.game_log.append(row)
            if m.echo_games:
                print(",".join(str(x) for x in row))

    def step(self):
        self.lifespan -= 1
        if self.lifespan == 0:
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
        self.location = (rng.uniform(0, model.width), rng.uniform(0, model.height))
        for k, v in attrs.items():
            if not hasattr(self, k):
                raise KeyError("Nieznany atrybut gracza: " + k)
            setattr(self, k, v)

    def __repr__(self):
        return self.name

    # --- parametry i pamięć partnerów -----------------------------------
    def apply_character_params(self):
        P = self.model.p
        self.sensitivity = P.movement_sensitivity
        if self.character == "AQLEARN":
            self.social_sensitivity = P.social_sensitivity_aqlearn
            self.social_learning_boost = P.social_learning_boost_aqlearn
        if self.character in LEARNERS:
            self.env_influence = P.env_influence_qlearn
            self.base_character = P.base_character_qlearn
            self.character_strength = P.character_strength_qlearn

    def ensure_partner(self, other):
        if other not in self.lists_per_other:
            self.lists_per_other[other] = []
            self.my_moves_per_other[other] = []
            self.q_d_per_other[other] = {}
            self.q_c_per_other[other] = {}

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
                   self.social_feedback):
            mp.pop(other, None)
        self.nb_forgotten += 1
        self.model.nb_forgets_total += 1

    def distinct_partners_in_window(self):
        since = self.model.cycle - self.model.p.partner_window
        for k in [k for k, c in self.last_met_cycle.items() if c < since]:
            del self.last_met_cycle[k]
        return len(self.last_met_cycle)

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
        return "D" if "D" in self.lists_per_other[p] else "C"

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
        self.current_node = net.closest_vertex(self.location)
        self.location = net.vertices[self.current_node]

    def social_score(self, candidate):
        s_s = 0.0
        cur = self.model.network.vertices[self.current_node]
        for p, pref in self.social_feedback.items():
            dist_now = _dist(cur, p.location)
            dist_candidate = _dist(candidate, p.location)
            s_s += pref * (dist_now - dist_candidate) / max(1.0, self.move_speed)
        return s_s / max(1, len(self.social_feedback))

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
            new_target = self.weighted_next_node(neighbors)
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
        if self.height > 0:
            self.height -= 1
            self.score += 1

    def reflex_do_you_wanna_play(self):
        m, P = self.model, self.model.p
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
                m.active_pairs[key] = m.create_game(self, enemy, key, loc)

    def step(self):
        P = self.model.p
        if P.real_env and (self.target_node is None or self._at_target()):
            self.reflex_choose_target()
        if P.real_env and self.target_node is not None and not self._at_target():
            self.reflex_move_on_network()
        if not P.real_env:
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
        self.nb_forgets_total = 0
        self.nb_forgets_prev = 0
        self.forgets_last_cycle = 0
        self.perf_last_time = 0.0
        self.active_pairs = {}
        self.games = []
        self.players = []
        self.character_pool = []
        # wyjścia (odpowiedniki plików w ../results/)
        self.game_log = []            # PD.csv
        self.ablation_rows = []       # ablation_results.csv
        self.fingerprint_rows = []    # regression_fingerprint.csv
        self.perf_rows = []           # perf.csv

        P = self.p
        if P.real_env:
            if network is not None:
                self.network = network
            elif geojson is not None:
                self.network = PathNetwork.from_geojson(geojson)
            else:
                self.network = PathNetwork.synthetic()
            self.width, self.height = self.network.width, self.network.height
        else:
            self.network = network or PathNetwork.synthetic()
            self.width = self.height = float(P.world_size)

        cw, ch = self.width / P.grid_cols, self.height / P.grid_rows
        self.cells = [Cell(r * P.grid_cols + c, c, r, c * cw, r * ch, cw, ch)
                      for r in range(P.grid_rows) for c in range(P.grid_cols)]
        self._init_global()

    # --- global.init ------------------------------------------------------
    def _init_global(self):
        P = self.p
        if not self.payoffs_valid():
            raise ModelError("Macierz wypłat niezgodna z game_type=%s (PD: T>R>P>S, weak_PD: T>R>P=S, "
                             "snowdrift: T>R>S>P). Aktualnie : T=%s R=%s P=%s S=%s"
                             % (P.game_type, P.payoff_T, P.payoff_R, P.payoff_P, P.payoff_S))
        if not P.unlimited_games and not self.payoffs_integer():
            raise ModelError("Tryb z ograniczeniem gier (unlimited_games=false) wymaga całkowitych wypłat.")
        self.warnings = []
        if P.game_type == "PD" and not (2 * P.payoff_R > P.payoff_T + P.payoff_S):
            self.warnings.append("OSTRZEŻENIE: 2R <= T+S (%s <= %s) - naprzemienna eksploatacja nie jest "
                                 "gorsza niż stała kooperacja." % (2 * P.payoff_R, P.payoff_T + P.payoff_S))
        for k in CREATION_ORDER:
            self.character_pool += [k] * int(getattr(P, "nb_" + k))
        for ch in self.character_pool:
            pl = self.create_player(ch)
            pl.apply_character_params()
            if P.real_env:
                pl.init_on_network()

    def create_player(self, character=None, **attrs):
        pl = Player(self, "player%d" % len(self.players), character, **attrs)
        self.players.append(pl)
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

    def players_within(self, me, radius):
        x, y = me.location
        r2 = radius * radius
        return [q for q in self.players
                if q is not me and (q.location[0] - x) ** 2 + (q.location[1] - y) ** 2 <= r2]

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
        for c in self.cells:
            if c.disorder > 1e-4:
                cells_disorder[c.index] = c.disorder

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
            "nb_game": self.nb_game, "moves_C": self.nb_moves_C, "moves_D": self.nb_moves_D,
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

CSV_HEADERS = {
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


class BatchRun:
    """Batch krok po kroku (żeby przeglądarka mogła pokazywać postęp)."""

    def __init__(self, name, repeat=None, end_cycle=None, geojson=None, network=None, seed=None):
        spec = BATCH_EXPERIMENTS[name]
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
        self.network = network or (PathNetwork.from_geojson(geojson) if geojson else PathNetwork.synthetic())
        self.jobs = [(dict(base, **c), s) for c in combos for s in seeds]
        self.until_key = spec["until"]
        self.ablation_rows, self.fingerprint_rows, self.perf_rows = [], [], []
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
                self.current = Model(Params(**params), seed=s, network=self.network)
            m = self.current
            limit = getattr(m.p, self.until_key)
            while budget > 0 and not (m.cycle > limit):   # until: cycle > ...
                m.step()
                budget -= 1
            if m.cycle > limit:
                self.ablation_rows += m.ablation_rows
                self.fingerprint_rows += m.fingerprint_rows
                self.perf_rows += m.perf_rows
                self.done += 1
                self.current = None
        return self.done >= len(self.jobs)

    def progress(self):
        cur = self.current.cycle if self.current else 0
        limit = self.jobs[min(self.done, len(self.jobs) - 1)][0].get(self.until_key, DEFAULTS[self.until_key])
        return json.dumps({"done": self.done, "total": len(self.jobs), "cycle": cur, "limit": limit})


def run_batch(name, **kw):
    b = BatchRun(name, **kw)
    while not b.advance(10 ** 9):
        pass
    return b


# ---------------------------------------------------------------------------
# testy (odpowiedniki experiment ... type: test z PD.gaml)
# ---------------------------------------------------------------------------

def _test_model(**overrides):
    # jak test experiment w GAMA: global.init bez agentów (wszystkie nb_* = 0)
    return Model(Params(**overrides), seed=random.randrange(2 ** 31))


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
    ap.add_argument("--set", nargs="*", default=[], metavar="NAZWA=WARTOŚĆ")
    ap.add_argument("--out", default=".", help="katalog na pliki CSV")
    a = ap.parse_args(argv)

    geo = open(a.geojson, encoding="utf-8").read() if a.geojson else None
    import os

    def save(name, rows):
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
        b = run_batch(a.experiment, repeat=a.repeat, end_cycle=a.end_cycle, geojson=geo, seed=a.seed)
        print("%s: %d przebiegów, %.1f s" % (a.experiment, b.total, time.time() - t0))
        if b.ablation_rows:
            save("ablation_results.csv", b.ablation_rows)
        if b.fingerprint_rows:
            save("regression_fingerprint.csv", b.fingerprint_rows)
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
