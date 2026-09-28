// Przełącznik języka PL/EN.
// Teksty statyczne strony są po polsku w index.html; słownik I18N_EN (niżej) podaje ich angielskie odpowiedniki.
// Kluczem jest tekst (albo HTML elementu z mieszaną treścią) po zwinięciu białych znaków.
// Teksty ustawiane z JavaScriptu wybiera L(pl, en); po zmianie języka wołane są funkcje z I18N.onChange.
// Elementy z atrybutem data-noi18n są pomijane (ich treść ustawia kod).
"use strict";
const I18N = (() => {
  const INLINE = new Set(["CODE", "B", "I", "EM", "STRONG", "BR", "A", "SUB", "SUP", "KBD", "SPAN"]);
  const ATTRS = ["placeholder", "aria-label", "title"];
  const norm = (s) => s.replace(/\s+/g, " ").trim();
  const entries = [];
  const hooks = [];
  let dict = {};
  let titlePl = "";
  let lang = pick();

  function pick() {
    try {
      const q = new URLSearchParams(location.search).get("lang");
      if (q === "pl" || q === "en") return q;
      const s = localStorage.getItem("lang");
      if (s === "pl" || s === "en") return s;
    } catch (e) { /* brak dostępu do localStorage */ }
    return (navigator.language || "").toLowerCase().startsWith("pl") ? "pl" : "en";
  }

  function scan(el) {
    if (el.tagName === "SCRIPT" || el.tagName === "STYLE" || el.hasAttribute("data-noi18n")) return;
    for (const a of ATTRS) {
      const v = el.getAttribute(a);
      if (v && dict[norm(v)] !== undefined) entries.push({ el, attr: a, pl: v, en: dict[norm(v)] });
    }
    const kids = [...el.childNodes];
    const elKids = kids.filter((n) => n.nodeType === 1);
    const hasText = kids.some((n) => n.nodeType === 3 && norm(n.nodeValue));
    if (hasText && elKids.length && elKids.every((n) => INLINE.has(n.tagName))) {
      const k = norm(el.innerHTML);
      if (dict[k] !== undefined) { entries.push({ el, html: true, pl: el.innerHTML, en: dict[k] }); return; }
    }
    for (const n of kids) {
      if (n.nodeType === 3) {
        const k = norm(n.nodeValue);
        if (k && dict[k] !== undefined) entries.push({ node: n, pl: n.nodeValue, en: dict[k] });
      } else if (n.nodeType === 1) scan(n);
    }
  }

  function apply() {
    const en = lang === "en";
    document.documentElement.lang = lang;
    for (const e of entries) {
      const v = en ? e.en : e.pl;
      if (e.attr) e.el.setAttribute(e.attr, v);
      else if (e.html) e.el.innerHTML = v;
      else e.node.nodeValue = v;
    }
    if (dict.__title) document.title = en ? dict.__title : titlePl;
    document.querySelectorAll("[data-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
    for (const f of hooks) f(lang);
  }

  return {
    get lang() { return lang; },
    init(d) {
      dict = d;
      titlePl = document.title;
      scan(document.body);
      document.querySelectorAll("[data-lang]").forEach((b) => b.addEventListener("click", () => I18N.set(b.dataset.lang)));
      apply();
    },
    set(l) {
      if (l === lang) return;
      lang = l;
      try { localStorage.setItem("lang", l); } catch (e) { /* tryb prywatny */ }
      apply();
    },
    onChange(f) { hooks.push(f); },
    // klucze słownika, których nie znaleziono na stronie (do sprawdzania słownika)
    unused() {
      const used = new Set(entries.map((e) => norm(e.pl)));
      return Object.keys(dict).filter((k) => k !== "__title" && !used.has(k));
    },
  };
})();
const L = (pl, en) => (I18N.lang === "en" ? en : pl);

// słownik PL → EN dla tekstów statycznych index.html (klucz: tekst po zwinięciu spacji)
const I18N_EN = {
 "Ładowanie Pythona (Pyodide)…": "Loading Python (Pyodide)…",
 "Nie udało się wczytać <code>sipd.py</code> obok strony (strona otwarta jako plik?). Wskaż plik ręcznie albo uruchom <code>python -m http.server</code> w katalogu <code>web/</code>.": "Could not load <code>sipd.py</code> next to the page (opened as a local file?). Pick the file by hand or run <code>python -m http.server</code> in the <code>web/</code> folder.",
 "SIPD – przestrzenny dylemat więźnia": "SIPD – spatial prisoner's dilemma",
 "Port modelu <code>PD.gaml</code> do Pythona, uruchamiany w przeglądarce. Parametry z oznaczeniem ↻ działają po ponownej inicjalizacji.": "Python port of the <code>PD.gaml</code> model, running in the browser. Parameters marked ↻ take effect after re-initialisation.",
 "Symulacja": "Simulation",
 "Eksperymenty batch": "Batch experiments",
 "Testy": "Tests",
 "O porcie": "About the port",
 "Inicjalizuj": "Initialise",
 "Krok": "Step",
 "Cykli na klatkę": "Cycles per frame",
 "Seed (puste = losowy)": "Seed (empty = random)",
 "losowy": "random",
 "Wczytaj ustawienia z": "Load settings from",
 "Sieć ścieżek (GeoJSON)": "Path network (GeoJSON)",
 "abc – mapa i relacje": "abc – map and relations",
 "komórki: średni feedback": "cells: mean feedback",
 "komórki: disorder": "cells: disorder",
 "komórki: spotkania powtórne": "cells: repeat encounters",
 "Warstwa komórek": "Cell layer",
 "kliknij agenta na mapie, żeby go wybrać": "click an agent on the map to select it",
 "Score (wynik na 1000 gier)": "Score (payoff per 1000 games)",
 "Pamięć partnerów (Dunbar)": "Partner memory (Dunbar)",
 "Udziały charakterów (ewolucja)": "Character shares (evolution)",
 "Pliki wynikowe": "Output files",
 "Odpowiedniki plików z <code>results/</code> dla bieżącego przebiegu. <code>ablation_results.csv</code> powstaje w cyklu <code>end_cycle</code>.": "Counterparts of the files in <code>results/</code> for the current run. <code>ablation_results.csv</code> is written at cycle <code>end_cycle</code>.",
 "Eksperymenty batch z PD.gaml": "Batch experiments from PD.gaml",
 "Oryginalne ustawienia to 30 powtórzeń × 50 000 cykli, co w przeglądarce zajmie bardzo długo. Domyślnie skracam je poniżej; wpisz pełne wartości, jeśli chcesz odtworzyć eksperyment wiernie.": "The original settings are 30 repetitions × 50,000 cycles, which takes very long in the browser. They are shortened below by default; enter the full values to reproduce the experiment faithfully.",
 "Eksperyment": "Experiment",
 "Powtórzenia": "Repetitions",
 "Seed eksperymentu": "Experiment seed",
 "Uruchom": "Run",
 "Zatrzymaj": "Stop",
 "Testy (odpowiedniki <code>experiment … type: test</code>)": "Tests (counterparts of <code>experiment … type: test</code>)",
 "Uruchom testy": "Run tests",
 "Co odwzorowuje ten port": "What this port reproduces",
 "Plik <code>sipd.py</code> zawiera cały model z <code>models/PD.gaml</code>: sieć ścieżek, siatkę komórek z polem disorder, 9 charakterów, Q-learning per przeciwnik ze stanami RISKY/SAFE, pamięć społeczną i środowiskową, efekt rozbitej szyby, kotwicę charakteru, ograniczenie gier (height), limit Dunbara, typ gry, klasyczny start od C, metryki, eksporty CSV, eksperymenty batch i testy.": "The file <code>sipd.py</code> contains the whole model from <code>models/PD.gaml</code>: the path network, the cell grid with the disorder field, 9 characters, per-opponent Q-learning with RISKY/SAFE states, social and environmental memory, the broken-windows effect, the character anchor, the game limit (height), the Dunbar limit, the game type, the classic start with C, metrics, CSV exports, batch experiments and tests.",
 "Różnice względem GAMA": "Differences from GAMA",
 "Inny generator liczb losowych: wyniki zgadzają się statystycznie, nie liczba w liczbę. W obrębie tej wersji ten sam seed daje te same wyniki.": "A different random number generator: results agree statistically, not number for number. Within this version the same seed gives the same results.",
 "GeoJSON w stopniach jest rzutowany lokalnie na metry (GAMA używa UTM); różnica w skali parku jest pomijalna.": "GeoJSON in degrees is projected locally to metres (GAMA uses UTM); the difference at park scale is negligible.",
 "Ruch po sieci idzie krawędzią do sąsiedniego wierzchołka; <code>wander</code> w sztucznym świecie przy krawędzi losuje nowy kierunek.": "Movement on the network goes along an edge to the neighbouring vertex; <code>wander</code> in the artificial world picks a new direction at the edge.",
 "Bez pliku <code>drogi.geojson</code> używana jest syntetyczna sieć parkowa 540 × 540 m.": "Without the <code>drogi.geojson</code> file a synthetic 540 × 540 m park network is used.",
 "Uruchamianie poza przeglądarką": "Running outside the browser",
 "<code>python sipd.py --test</code>, <code>python sipd.py --experiment A_baseline --repeat 2 --end-cycle 2000 --geojson drogi.geojson</code>. Stronę lokalnie: <code>python -m http.server</code> w katalogu <code>web/</code>, potem <code>http://localhost:8000</code>.": "<code>python sipd.py --test</code>, <code>python sipd.py --experiment A_baseline --repeat 2 --end-cycle 2000 --geojson drogi.geojson</code>. To serve the page locally: <code>python -m http.server</code> in the <code>web/</code> folder, then <code>http://localhost:8000</code>.",
 "__title": "SIPD in the browser",
 "cykl": "cycle",
 "gier": "games",
 "sieć": "network"
};

// kategorie i etykiety parametrów z sipd.GUI_PARAMETERS (po polsku w sipd.py)
const I18N_CAT_EN = {
 "Podgląd pamięci": "Memory view",
 "Ilości agentów": "Numbers of agents",
 "Środowisko": "Environment",
 "Gra": "Game",
 "Moduł 1 – Dunbar": "Module 1 – Dunbar",
 "Moduł 2 – ewolucja": "Module 2 – evolution",
 "Etap 1 – zgodność": "Stage 1 – compatibility",
 "Warstwa projektowa": "Design layer",
 "Stabilność spotkań": "Encounter stability",
 "Moduł 3 – pokrewieństwo": "Module 3 – kinship",
 "Diagnostyka": "Diagnostics",
 "Pozostałe (poza GUI w GAMA)": "Other (not in the GAMA GUI)"
};
const I18N_PARAM_EN = {
 "selected_index": "Selected agent (index)",
 "show_social_links": "Show social relation lines",
 "social_link_threshold": "Line drawing threshold",
 "nb_QLEARN": "Number of QLEARN agents",
 "nb_AQLEARN": "Number of AQLEARN agents",
 "nb_TFT": "Number of TFT agents",
 "nb_FTFT": "Number of FTFT agents",
 "nb_TF2T": "Number of TF2T agents",
 "nb_GRIM": "Number of GRIM agents",
 "nb_ALLC": "Number of ALLC agents",
 "nb_ALLD": "Number of ALLD agents",
 "nb_WSLS": "Number of WSLS agents",
 "real_env": "Real environment",
 "unlimited_games": "Unlimited games (no height lock)",
 "world_size": "World size (artificial environment only)",
 "grid_cols": "Grid columns",
 "grid_rows": "Grid rows",
 "vision_radius": "Vision radius",
 "movement_sensitivity": "Movement sensitivity (environment)",
 "env_influence_qlearn": "Environment influence on QLEARN decisions",
 "social_sensitivity_aqlearn": "AQLEARN social sensitivity",
 "social_learning_boost_aqlearn": "AQLEARN social learning boost",
 "broken_windows_sensitivity": "Broken-windows sensitivity",
 "disorder_clamp": "Disorder clamped to [0, 1]",
 "game_type": "Game type",
 "payoff_T": "T (temptation)",
 "payoff_R": "R (reward)",
 "payoff_P": "P (punishment)",
 "payoff_S": "S (sucker)",
 "classic_start_cooperate": "TFT/TF2T/WSLS start with C",
 "dunbar_limit": "Dunbar limit (0 = none)",
 "partner_window": "Partner metric window (cycles)",
 "evolution_on": "Strategy evolution",
 "evolution_interval": "Every how many cycles",
 "fermi_k": "Selection noise K (Fermi)",
 "mutation_rate": "Mutation probability",
 "evolvable_characters": "Characters subject to evolution",
 "well_mixed": "Well-mixed population (no space)",
 "compat_core": "Compatibility core (compat_core)",
 "compat_N": "Core population N",
 "compat_mix": "Core composition",
 "payoff_preset": "Payoff matrix",
 "compat_export": "Export compat_results.csv",
 "player_speed": "Player speed (m/cycle)",
 "network_variant": "Network variant",
 "edge_removal_fraction": "Share of removed edges (fragmented)",
 "shortcut_count": "Number of shortcuts (connected)",
 "shortcut_max_length": "Max. shortcut length (m)",
 "encounter_window": "Encounter metric window (cycles)",
 "kin_on": "Families (requires evolution)",
 "payoff_mode": "Payoff mode",
 "b": "b (benefit)",
 "c": "c (cost)",
 "family_size": "Family size",
 "family_r": "r within family",
 "kin_spatial_clustering": "Spatial clustering of families",
 "kin_strategy_correlation": "Strategy correlation within family",
 "kin_imitation_bias": "Imitation of kin",
 "kin_matching_prob": "α: kin matching (well_mixed)",
 "kin_matching_mode": "α matching: family / strategy",
 "fitness_mode": "Fitness",
 "inclusive_variant": "Inclusive variant",
 "timeseries_export": "Export time series",
 "sample_interval": "Sample every (cycles)",
 "perf_log": "Cycle timing",
 "perf_interval": "Timing window (cycles)",
 "regression_export": "Export regression fingerprint",
 "regression_cycle": "Fingerprint cycle"
};
