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

// Rozwijane menu alfabetycznie, wg bieżącego języka. Opcja z pustą wartością („—”) zostaje na górze,
// „inna nazwa…” (wartość __custom) na dole; <select data-nosort> jest pomijany. Wybrana wartość się nie zmienia.
function sortSelects(root = document) {
  const coll = new Intl.Collator(I18N.lang, { numeric: true, sensitivity: "base" });
  root.querySelectorAll("select:not([data-nosort])").forEach((sel) => {
    const v = sel.value;
    const opts = [...sel.options];
    const top = opts.filter((o) => o.value === "");
    const bottom = opts.filter((o) => o.value === "__custom");
    const mid = opts.filter((o) => o.value !== "" && o.value !== "__custom")
      .sort((a, b) => coll.compare(a.text, b.text));
    sel.append(...top, ...mid, ...bottom);
    sel.value = v;
  });
}

// słownik PL → EN dla tekstów statycznych index.html (klucz: tekst po zwinięciu spacji)
const I18N_EN = {
 "Pobierz ławki i stoły z OSM": "Fetch benches and tables from OSM",
 "Popraw sieć z OSM": "Correct OSM network",
 "Łączenie rozłącznych kawałków (do 50 m), ścieżek równoległych (3 m), skrzyżowań (6 m) i ślepych końców (25 m), jak w PD": "Joins separate parts (up to 50 m), parallel paths (3 m), junctions (6 m) and dead ends (25 m), as in PD",
 "Park z OSM": "Park from OSM",
 "inna nazwa…": "other name…",
 "Nazwa w OSM": "Name in OSM",
 "np. Park Tołpy": "e.g. Park Tołpy",
 "Wczytaj gotowy": "Load ready",
 "Park z biblioteki strony, już po poprawkach, bez pobierania z OSM": "A park from the site's library, already corrected, no OSM download",
 "Pobierz z OSM": "Fetch from OSM",
 "Ścieżki parku z Overpass API (Wrocław), z poprawkami sieci jak w PD": "Park paths from the Overpass API (Wrocław), with network corrections as in PD",
 "Zapisz GeoJSON": "Save GeoJSON",
 "Park": "Park",
 "Link z ustawieniami": "Link with settings",
 "Przywróć domyślne": "Reset to defaults",
 "Strefy odpoczynku": "Rest zones",
 "Plik GeoJSON z punktami": "GeoJSON file with points",
 "Zapisz strefy (GeoJSON)": "Save zones (GeoJSON)",
 "Ławki (amenity=bench) i stoły piknikowe (leisure=picnic_table) z OpenStreetMap w obrysie wczytanej sieci": "Benches (amenity=bench) and picnic tables (leisure=picnic_table) from OpenStreetMap inside the loaded network",
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
 "Moduł 4 – strefy odpoczynku": "Module 4 – rest zones",
 "Moduł 5 – bank odwiedzających": "Module 5 – visitor bank",
 "Moduł 6 – wejścia i cele ruchu": "Module 6 – entrances and destinations",
 "Pozostałe (poza GUI w GAMA)": "Other (not in the GAMA GUI)"
};
const I18N_PARAM_EN = {
 "rest_on": "Rest zones and fatigue",
 "rest_zone_count": "Number of zones",
 "rest_zone_placement": "Zone placement",
 "rest_zone_file": "Zone file (GeoJSON, e.g. OSM benches)",
 "frail_share": "Share of older / frail visitors",
 "fatigue_regular_mean": "Fatigue per 100 m – regular (mean)",
 "fatigue_regular_sd": "Fatigue – regular (SD)",
 "fatigue_frail_mean": "Fatigue per 100 m – older (mean)",
 "fatigue_frail_sd": "Fatigue – older (SD)",
 "rest_threshold": "Energy threshold: seek a zone",
 "rest_recovery": "Energy recovery per cycle",
 "rest_target": "Energy: end of rest",
 "bank_on": "Visitor turnover (bank)",
 "bank_present_share": "Share of pool present in the park",
 "bank_mean_stay": "Mean visit length (cycles)",
 "movement_mode": "Movement mode (default / destinations)",
 "dest_file": "Destination file (GeoJSON points)",
 "dest_count": "Number of destinations (no file)",
 "dest_placement": "Destination placement (no file)",
 "dest_dwell": "Mean stay at a destination (cycles)",
 "dest_per_visit": "Mean destinations per visit",
 "dest_share": "Share of visitors with destinations",
 "entrance_file": "Entrance or park boundary file (GeoJSON)",
 "entrance_dist": "Entrance: distance from boundary (m)",
 "partner_distance": "Partner distance (euclid / network)",
 "bypass_on": "Bypass around the park (bypass layer)",
 "through_share": "Share of people walking through the park",
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

// opisy parametrów (podpowiedź po najechaniu na etykietę i po kliknięciu „?”): klucz -> [pl, en].
// Wartość domyślną i znak ↻ dopisuje strona. Opisy na podstawie web/sipd.py; przy zmianie modelu sprawdź je.
const PARAM_HELP = {
  selected_index: ["Który agent jest pokazany w panelu agent_memory. Możesz też kliknąć agenta na mapie.", "Which agent is shown in the agent_memory panel. You can also click an agent on the map."],
  show_social_links: ["Rysuje linie do partnerów, których wybrany agent ocenia wyraźnie dobrze lub źle (pamięć społeczna).", "Draws lines to partners the selected agent rates clearly well or badly (social memory)."],
  social_link_threshold: ["Linia relacji jest rysowana, gdy |ocena partnera| przekracza ten próg. Tylko podgląd, bez wpływu na model.", "A relation line is drawn when |partner rating| exceeds this threshold. Display only, no effect on the model."],
  nb_QLEARN: ["Liczba agentów QLEARN: uczą się Q-learningiem osobno dla każdego partnera, ze stanem RISKY/SAFE zależnym od zdrad w danym miejscu.", "Number of QLEARN agents: they learn by Q-learning separately for each partner, with a RISKY/SAFE state that depends on betrayals at the place."],
  nb_AQLEARN: ["Liczba agentów AQLEARN: jak QLEARN, ale z pamięcią społeczną, która może kierować ruchem i przyspieszać uczenie.", "Number of AQLEARN agents: like QLEARN, but with social memory that can steer movement and speed up learning."],
  nb_TFT: ["Liczba agentów TFT (wet za wet): powtarzają ostatni ruch partnera.", "Number of TFT (tit for tat) agents: they repeat the partner's last move."],
  nb_FTFT: ["Liczba agentów FTFT (wybaczający wet za wet): jak TFT, ale po zdradzie z prawdopodobieństwem 5% współpracują. Zaczynają od C.", "Number of FTFT (forgiving tit for tat) agents: like TFT, but after a defection they cooperate with 5% probability. They start with C."],
  nb_TF2T: ["Liczba agentów TF2T: zdradzają dopiero po dwóch zdradach partnera z rzędu.", "Number of TF2T agents: they defect only after two partner defections in a row."],
  nb_GRIM: ["Liczba agentów GRIM: współpracują, dopóki partner choć raz nie zdradzi, potem zdradzają zawsze.", "Number of GRIM agents: they cooperate until the partner defects once, then always defect."],
  nb_ALLC: ["Liczba agentów ALLC: zawsze współpracują.", "Number of ALLC agents: they always cooperate."],
  nb_ALLD: ["Liczba agentów ALLD: zawsze zdradzają.", "Number of ALLD agents: they always defect."],
  nb_WSLS: ["Liczba agentów WSLS (wygrana zostaje, przegrana zmienia): powtarzają swój ruch, gdy partner współpracował, a zmieniają go, gdy zdradził.", "Number of WSLS (win-stay, lose-shift) agents: they repeat their move if the partner cooperated and switch it if the partner defected."],
  real_env: ["Wł.: agenci chodzą po sieci ścieżek (z pliku GeoJSON albo syntetycznej). Wył.: błądzą swobodnie po kwadratowym świecie o boku „Rozmiar świata”.", "On: agents walk on the path network (from a GeoJSON file or synthetic). Off: they wander freely in a square world of side “World size”."],
  unlimited_games: ["Wył. (jak w GAMA): wypłata trafia najpierw do bufora height i przechodzi do wyniku po 1 na cykl; dopóki bufor nie jest pusty, agent nie gra. Wł.: wypłata od razu do wyniku i gra w każdym cyklu.", "Off (as in GAMA): the payoff first goes to a height buffer and moves to the score at 1 per cycle; the agent cannot play until it is empty. On: payoff goes straight to the score and agents can play every cycle."],
  world_size: ["Bok kwadratowego świata, gdy „Prawdziwe środowisko” jest wyłączone.", "Side of the square world when “Real environment” is off."],
  grid_cols: ["Liczba kolumn siatki komórek, w której zapisywane są disorder i oceny miejsc.", "Number of columns of the cell grid that stores disorder and place ratings."],
  grid_rows: ["Liczba wierszy siatki komórek.", "Number of rows of the cell grid."],
  vision_radius: ["Promień (m), w którym agent szuka partnera do gry i, przy ewolucji, wzorca do naśladowania.", "Radius (m) within which an agent looks for a game partner and, with evolution, a model to imitate."],
  movement_sensitivity: ["Jak mocno agent wybiera na skrzyżowaniu kierunek ku miejscom, które dobrze ocenia po wcześniejszych grach. 0 = wybór losowy.", "How strongly an agent picks, at a junction, the direction towards places it rates well after earlier games. 0 = random choice."],
  env_influence_qlearn: ["Jak mocno ocena bieżącego miejsca przesuwa decyzję QLEARN/AQLEARN: dobre miejsce sprzyja współpracy, złe zdradzie.", "How strongly the rating of the current place shifts a QLEARN/AQLEARN decision: a good place favours cooperation, a bad one defection."],
  social_sensitivity_aqlearn: ["Jak mocno AQLEARN wybiera kierunek ku partnerom, których dobrze ocenia (ruch społeczny). 0 = wyłączone.", "How strongly AQLEARN heads towards partners it rates well (social movement). 0 = off."],
  social_learning_boost_aqlearn: ["Przyspiesza uczenie AQLEARN z partnerami, których dobrze ocenia: tempo uczenia × (1 + wzmocnienie × ocena).", "Speeds up AQLEARN learning with partners it rates well: learning rate × (1 + boost × rating)."],
  broken_windows_sensitivity: ["Efekt rozbitej szyby: w miejscu z disorder współpraca zamienia się w zdradę z prawdopodobieństwem czułość × disorder (maks. 0,9); disorder osłabia też kotwicę charakteru. 0 = wyłączone.", "Broken windows effect: at a place with disorder, cooperation turns into defection with probability sensitivity × disorder (max 0.9); disorder also weakens the character anchor. 0 = off."],
  disorder_clamp: ["Wł.: disorder komórki nie przekracza 1. Wył.: rośnie bez górnej granicy.", "On: cell disorder never exceeds 1. Off: it grows without an upper bound."],
  game_type: ["Rodzaj gry, który określa wymagany porządek wypłat: PD (T > R > P > S), weak_PD (T > R > P = S) albo snowdrift (T > R > S > P).", "Game type that sets the required payoff order: PD (T > R > P > S), weak_PD (T > R > P = S) or snowdrift (T > R > S > P)."],
  payoff_T: ["Wypłata za zdradę współpracującego partnera (pokusa).", "Payoff for defecting against a cooperator (temptation)."],
  payoff_R: ["Wypłata każdego z graczy za wzajemną współpracę (nagroda).", "Payoff to each player for mutual cooperation (reward)."],
  payoff_P: ["Wypłata każdego z graczy za wzajemną zdradę (kara).", "Payoff to each player for mutual defection (punishment)."],
  payoff_S: ["Wypłata za współpracę ze zdradzającym partnerem (frajer).", "Payoff for cooperating with a defector (sucker)."],
  classic_start_cooperate: ["Wł.: TFT, TF2T i WSLS zaczynają od współpracy, jak w literaturze. Wył.: pierwszy ruch jest losowy (50/50).", "On: TFT, TF2T and WSLS start by cooperating, as in the literature. Off: the first move is random (50/50)."],
  dunbar_limit: ["Ilu partnerów agent pamięta naraz. Po przekroczeniu zapomina najdawniej spotkanego (całą historię i oceny), a przy kolejnym spotkaniu traktuje go jak nowego. 0 = bez limitu.", "How many partners an agent remembers at once. Beyond that it forgets the least recently met one (whole history and ratings) and treats them as new at the next meeting. 0 = no limit."],
  partner_window: ["Okno (w cyklach) metryki „różnych partnerów w oknie”. Nie wpływa na zachowanie agentów.", "Window (cycles) of the “distinct partners in window” metric. Does not affect agent behaviour."],
  evolution_on: ["Wł.: co pewien czas agenci naśladują strategię lepiej zarabiającego wzorca (reguła Fermiego) albo losowo mutują.", "On: from time to time agents copy the strategy of a better-earning model (Fermi rule) or mutate at random."],
  evolution_interval: ["Co ile cykli agenci rozważają zmianę strategii; zarobek liczony jest jako średnia wypłata na grę w tym oknie.", "How often (cycles) agents consider changing strategy; earnings are the mean payoff per game in this window."],
  fermi_k: ["Szum selekcji w regule Fermiego: P(naśladowania) = 1 / (1 + exp(−(π wzorca − π własne) / K)). Małe K = prawie zawsze naśladuje lepszego, duże K = prawie losowo.", "Selection noise in the Fermi rule: P(imitate) = 1 / (1 + exp(−(π model − π own) / K)). Small K = almost always copies the better one, large K = nearly random."],
  mutation_rate: ["Prawdopodobieństwo, że przy aktualizacji agent zamiast naśladować dostaje losowy charakter z listy ewoluujących.", "Probability that at an update an agent takes a random character from the evolvable list instead of imitating."],
  evolvable_characters: ["Charaktery, które mogą się zmieniać i które może dać mutacja (lista po przecinku).", "Characters that can change and that mutation can produce (comma-separated list)."],
  well_mixed: ["Wł.: partnera i wzorzec losuje się z całej populacji, bez przestrzeni i ruchu. Kontrola do oddzielenia efektu przestrzeni.", "On: partners and models are drawn from the whole population, with no space or movement. A control to separate the effect of space."],
  compat_core: ["Rdzeń zgodności: tylko strategie klasyczne, bez Q-learningu, ruchu środowiskowego i społecznego, rozbitej szyby i kotwicy; gry bez limitu, start od C. Liczebności bierze z N i składu rdzenia.", "Compatibility core: classic strategies only, no Q-learning, environmental or social movement, broken windows or anchor; unlimited games, start with C. Agent counts come from N and the core mix."],
  compat_N: ["Liczba agentów w rdzeniu zgodności.", "Number of agents in the compatibility core."],
  compat_mix: ["Skład rdzenia: equal = siedem strategii klasycznych po równo; tft_alld = 80% TFT i 20% ALLD; allc_alld = pół na pół ALLC i ALLD.", "Core mix: equal = seven classic strategies in equal numbers; tft_alld = 80% TFT and 20% ALLD; allc_alld = half ALLC, half ALLD."],
  payoff_preset: ["Gotowa macierz wypłat, która nadpisuje typ gry i T, R, P, S: PD_classic (9, 5, 1, 0), weak_PD (1,6, 1, 0, 0), snowdrift (4, 3, 0, 2). custom = wartości z sekcji Gra.", "Ready payoff matrix that overrides game type and T, R, P, S: PD_classic (9, 5, 1, 0), weak_PD (1.6, 1, 0, 0), snowdrift (4, 3, 0, 2). custom = values from the Game section."],
  compat_export: ["Zapisuje compat_results.csv (wiersz = przebieg) na końcu przebiegu.", "Writes compat_results.csv (one row per run) at the end of the run."],
  player_speed: ["Droga przebyta przez agenta w jednym cyklu (m). Wolniejsi agenci częściej spotykają tych samych partnerów.", "Distance an agent walks per cycle (m). Slower agents meet the same partners more often."],
  network_variant: ["baseline: sieć bez zmian. fragmented: usunięta część krawędzi bez rozcinania sieci. connected: dodane proste skróty między bliskimi węzłami. Ten sam seed daje tę samą zmianę.", "baseline: unchanged network. fragmented: some edges removed without splitting the network. connected: straight shortcuts added between close nodes. The same seed gives the same change."],
  edge_removal_fraction: ["Jaką część krawędzi usunąć w wariancie fragmented. W sieci bliskiej drzewu może się nie udać usunąć tylu.", "Share of edges to remove in the fragmented variant. In a tree-like network fewer may be removable."],
  shortcut_count: ["Ile skrótów dodać w wariancie connected.", "How many shortcuts to add in the connected variant."],
  shortcut_max_length: ["Skróty łączą tylko węzły bliższe niż ta odległość.", "Shortcuts only join nodes closer than this distance."],
  encounter_window: ["Okno (w cyklach) metryki spotkań powtórnych i mapy „komórki: spotkania powtórne”. Nie wpływa na zachowanie.", "Window (cycles) of the repeat-encounter metric and the “cells: repeat encounters” map. Does not affect behaviour."],
  kin_on: ["Rodziny (reguła Hamiltona). Wymaga ewolucji. Rodziny są stałe; podobieństwo strategii w rodzinie powstaje przez skupienie przestrzenne, korelację na starcie i naśladowanie krewnych.", "Families (Hamilton's rule). Requires evolution. Families are fixed; strategy similarity within a family comes from spatial clustering, start correlation and imitating relatives."],
  payoff_mode: ["classic: macierz T, R, P, S. donation: gra dawcy z b i c (R = b − c, S = −c, T = b, P = 0).", "classic: T, R, P, S matrix. donation: donation game with b and c (R = b − c, S = −c, T = b, P = 0)."],
  b: ["Korzyść dla partnera z mojej współpracy w grze dawcy (b > c > 0).", "Benefit to the partner from my cooperation in the donation game (b > c > 0)."],
  c: ["Koszt mojej współpracy w grze dawcy. Reguła Hamiltona przewiduje współpracę, gdy r > c/b.", "Cost of my cooperation in the donation game. Hamilton's rule predicts cooperation when r > c/b."],
  family_size: ["Liczba agentów w jednej rodzinie.", "Number of agents in one family."],
  family_r: ["Nominalne pokrewieństwo r w rodzinie, używane w dopasowaniu inclusive. Wynik porównujemy z r zmierzonym, nie z tym.", "Nominal relatedness r within a family, used by inclusive fitness. Results are compared with measured r, not with this."],
  kin_spatial_clustering: ["0 = rodziny startują w losowych miejscach, 1 = cała rodzina startuje w jednym węźle.", "0 = families start at random places, 1 = the whole family starts at one node."],
  kin_strategy_correlation: ["Prawdopodobieństwo, że członek rodziny dostaje na starcie strategię rodziny zamiast losowej.", "Probability that a family member starts with the family strategy instead of a random one."],
  kin_imitation_bias: ["Prawdopodobieństwo, że wzorzec do naśladowania jest wybierany spośród krewnych (niezależnie od odległości).", "Probability that the model to imitate is chosen among relatives (regardless of distance)."],
  kin_matching_prob: ["α: prawdopodobieństwo, że partner do gry jest losowany spośród krewnych. Działa tylko przy dobrze wymieszanej populacji.", "α: probability that the game partner is drawn among relatives. Works only with a well-mixed population."],
  kin_matching_mode: ["family: α dobiera krewnych. strategy: α dobiera agentów z tą samą strategią (kontrola, w której r = α z konstrukcji).", "family: α picks relatives. strategy: α picks agents with the same strategy (a control where r = α by construction)."],
  fitness_mode: ["own: do ewolucji liczy się własna średnia wypłata. inclusive: dodaje r × skutek moich ruchów dla krewnych.", "own: evolution uses one's own mean payoff. inclusive: adds r × the effect of my moves on relatives."],
  inclusive_variant: ["strip: π + r × (dane krewnym − otrzymane od krewnych), bez podwójnego liczenia. add: π + r × dane krewnym, tylko do porównań.", "strip: π + r × (given to relatives − received from relatives), avoiding double counting. add: π + r × given to relatives, for comparison only."],
  rest_on: ["Strefy odpoczynku i zmęczenie: idąc, agent traci energię; poniżej progu idzie do najbliższej strefy i odpoczywa, grając z sąsiadami.", "Rest zones and fatigue: walking costs energy; below the threshold an agent goes to the nearest zone and rests there, playing with neighbours."],
  rest_zone_count: ["Liczba stref odpoczynku (węzły sieci), gdy nie ma pliku stref.", "Number of rest zones (network nodes) when no zone file is given."],
  rest_zone_placement: ["Rozmieszczenie stref bez pliku: central = w środku sieci, dispersed = rozproszone, peripheral = na obrzeżach, random = losowo.", "Zone placement without a file: central = in the middle, dispersed = spread out, peripheral = at the edges, random = at random."],
  rest_zone_file: ["Plik z punktami stref (np. ławki z OSM). Gdy jest, strefy leżą w najbliższych węzłach, a liczba i rozmieszczenie są pomijane. Ustawiany przyciskami w karcie Strefy odpoczynku.", "File with zone points (e.g. benches from OSM). When set, zones are at the nearest nodes and count and placement are ignored. Set with the buttons in the Rest zones card."],
  frail_share: ["Udział osób starszych lub schorowanych, które męczą się szybciej.", "Share of elderly or frail people, who tire faster."],
  fatigue_regular_mean: ["Średnia utrata energii na 100 m u zwykłych odwiedzających (energia od 0 do 1).", "Mean energy loss per 100 m for regular visitors (energy from 0 to 1)."],
  fatigue_regular_sd: ["Odchylenie standardowe zmęczenia zwykłych odwiedzających.", "Standard deviation of fatigue for regular visitors."],
  fatigue_frail_mean: ["Średnia utrata energii na 100 m u osób starszych lub schorowanych.", "Mean energy loss per 100 m for elderly or frail visitors."],
  fatigue_frail_sd: ["Odchylenie standardowe zmęczenia osób starszych lub schorowanych.", "Standard deviation of fatigue for elderly or frail visitors."],
  rest_threshold: ["Poniżej tej energii agent idzie do najbliższej strefy odpoczynku.", "Below this energy an agent heads to the nearest rest zone."],
  rest_recovery: ["Odzysk energii na cykl w czasie odpoczynku.", "Energy recovered per cycle while resting."],
  rest_target: ["Energia, przy której agent kończy odpoczynek.", "Energy at which an agent stops resting."],
  bank_on: ["Rotacja odwiedzających: N to cała pula, w parku jest średnio jej część, reszta czeka w banku. Wyjście nie kasuje agenta: zachowuje strategię i pamięć partnerów.", "Visitor rotation: N is the whole pool, on average part of it is in the park and the rest waits in a bank. Leaving does not delete an agent: it keeps its strategy and partner memory."],
  bank_present_share: ["Oczekiwany udział puli obecny w parku.", "Expected share of the pool present in the park."],
  bank_mean_stay: ["Średnia długość wizyty w cyklach (rozkład geometryczny).", "Mean visit length in cycles (geometric distribution)."],
  movement_mode: ["default: błądzenie po sieci. destinations: agent wchodzi wejściem, idzie najkrótszą drogą do kolejnych celów, zostaje w każdym chwilę i wychodzi.", "default: wandering on the network. destinations: an agent enters through an entrance, walks the shortest way to successive destinations, stays at each for a while and leaves."],
  dest_file: ["Plik z punktami celów (np. ławki, place zabaw). Pusty = cele w węzłach wybranych według liczby i rozmieszczenia poniżej.", "File with destination points (e.g. benches, playgrounds). Empty = destinations at nodes chosen by the count and placement below."],
  dest_count: ["Liczba celów, gdy nie ma pliku.", "Number of destinations when no file is given."],
  dest_placement: ["Rozmieszczenie celów bez pliku: central, dispersed, peripheral albo random.", "Destination placement without a file: central, dispersed, peripheral or random."],
  dest_dwell: ["Średni pobyt w celu w cyklach (rozkład wykładniczy).", "Mean stay at a destination in cycles (exponential distribution)."],
  dest_per_visit: ["Średnia liczba celów na wizytę (rozkład geometryczny, co najmniej 1).", "Mean number of destinations per visit (geometric distribution, at least 1)."],
  dest_share: ["Udział odwiedzających z celami; reszta spaceruje bez celu.", "Share of visitors with destinations; the rest walk without a goal."],
  entrance_file: ["Plik z punktami wejść albo obrysem parku. Przy obrysie wejściem jest węzeł, z którego ścieżka wychodzi poza obrys, albo ślepy koniec blisko obrysu.", "File with entrance points or the park outline. With an outline, an entrance is a node whose path leaves the outline, or a dead end near the outline."],
  entrance_dist: ["Ślepy koniec ścieżki najwyżej tyle metrów od obrysu liczy się jako wejście.", "A dead end at most this many metres from the outline counts as an entrance."],
  partner_distance: ["Jak mierzyć odległość do partnera: euclid = w linii prostej, network = po ścieżkach.", "How to measure distance to a partner: euclid = straight line, network = along the paths."],
  bypass_on: ["Obejście wokół parku (warstwa bypass w pliku wejść). Korzystają z niego tylko przechodzący.", "Walkway around the park (bypass layer in the entrance file). Only through-walkers use it."],
  through_share: ["Udział przechodzących: wchodzą jednym wejściem i idą najkrótszą drogą do przeciwległego. 0 = brak.", "Share of through-walkers: they enter at one entrance and take the shortest way to the opposite one. 0 = none."],
  timeseries_export: ["Zapisuje character_timeseries.csv: udziały charakterów co „Co ile cykli próbka”.", "Writes character_timeseries.csv: character shares every “sample interval” cycles."],
  sample_interval: ["Co ile cykli zapisywana jest próbka szeregów czasowych i liczona stabilizacja.", "How often (cycles) time series samples are taken and stability is computed."],
  perf_log: ["Mierzy czas cyklu i zapisuje perf.csv.", "Measures cycle time and writes perf.csv."],
  perf_interval: ["Okno pomiaru czasu cyklu (cykle).", "Window of the cycle-time measurement (cycles)."],
  regression_export: ["Zapisuje regression_fingerprint.csv w cyklu odcisku, do porównania z wersją GAMA.", "Writes regression_fingerprint.csv at the fingerprint cycle, for comparison with the GAMA version."],
  regression_cycle: ["Cykl, w którym zapisywany jest odcisk regresyjny.", "Cycle at which the regression fingerprint is written."],
  disorder_bump_dd: ["O ile rośnie disorder komórki po grze, w której obaj zdradzili.", "How much cell disorder rises after a game in which both defected."],
  disorder_bump_d: ["O ile rośnie disorder komórki po grze, w której zdradził jeden gracz.", "How much cell disorder rises after a game in which one player defected."],
  disorder_decay: ["Mnożnik disorder stosowany co 10 cykli (0,98 = zanik o 2%).", "Disorder multiplier applied every 10 cycles (0.98 = 2% decay)."],
  generalization_threshold: ["Po tylu zdradach w danej komórce agent uczący się traktuje ją jako ryzykowną (stan RISKY).", "After this many betrayals in a cell a learning agent treats it as risky (RISKY state)."],
  base_character_qlearn: ["Charakter, do którego ciągnie kotwica agentów QLEARN/AQLEARN.", "Character the anchor of QLEARN/AQLEARN agents pulls towards."],
  character_strength_qlearn: ["Siła kotwicy: z tym prawdopodobieństwem (malejącym z liczbą gier z partnerem i z disorder) agent uczący się gra ruch swojego charakteru bazowego. 0 = brak kotwicy.", "Anchor strength: with this probability (falling with games played with the partner and with disorder) a learning agent plays the move of its base character. 0 = no anchor."],
  anchor_decay_rate: ["Tempo zaniku kotwicy z liczbą gier z danym partnerem: siła × exp(−tempo × n).", "Rate at which the anchor fades with games played with a partner: strength × exp(−rate × n)."],
  end_cycle: ["Cykl, w którym przebieg się kończy (zapis ablation_results.csv).", "Cycle at which the run ends (writes ablation_results.csv)."],
  variant_name: ["Nazwa wariantu w plikach CSV. Nie wpływa na model.", "Variant name in the CSV files. Does not affect the model."],
  log_games: ["Zapisuje każdą grę do PD.csv. Przy długich przebiegach plik bardzo rośnie.", "Logs every game to PD.csv. The file grows large in long runs."],
  prediction: ["Etykieta predykcji (P1, P3, …) w compat_results.csv. Nie wpływa na model.", "Prediction label (P1, P3, …) in compat_results.csv. Does not affect the model."],
  warmup: ["Cykle wygrzewania pomijane przy liczeniu średnich końcowych i stabilizacji.", "Warm-up cycles skipped when computing final means and stability."],
  stab_window: ["Okno (cykle), z którego liczone są średnie udziały charakterów do CSV.", "Window (cycles) used for the mean character shares in the CSV."],
  stab_eps: ["Dawne kryterium stabilizacji (zmiana średnich między oknami); nie trafia do CSV.", "Old stability criterion (change of means between windows); not written to the CSV."],
  stab_k: ["Dawne kryterium stabilizacji: liczba kolejnych spokojnych okien; nie trafia do CSV.", "Old stability criterion: number of consecutive calm windows; not written to the CSV."],
  stab_trend_eps: ["Przebieg uznaje się za ustabilizowany, gdy trend udziału ALLD w drugiej połowie jest mniejszy niż tyle na 10 000 cykli.", "A run counts as stabilised when the ALLD share trend in the second half is below this per 10,000 cycles."],
  network_file: ["Ścieżka do pliku sieci przy uruchamianiu z wiersza poleceń. W przeglądarce sieć wczytuje się w karcie Park.", "Path to the network file when run from the command line. In the browser, load the network in the Park card."],
  geojson_crs: ["Układ współrzędnych GeoJSON: auto (rozpoznanie po zakresie), geographic (lon/lat) albo projected (metry).", "GeoJSON coordinate system: auto (detected from the range), geographic (lon/lat) or projected (metres)."],
  network_cleanup: ["Wł.: pomija zamknięte pętle i osadza agentów tylko na największej spójnej części sieci. Wył.: jak w PD.gaml.", "On: skips closed loops and places agents only on the largest connected part of the network. Off: as in PD.gaml."],
  net_path_sources: ["Z ilu węzłów liczona jest średnia najkrótsza ścieżka w charakterystyce sieci.", "From how many nodes the mean shortest path in the network statistics is computed."],
  encounter_export: ["Zapisuje macierz komórek ze spotkaniami powtórnymi na końcu przebiegu.", "Writes the cell matrix of repeat encounters at the end of the run."],
  kin_reward_learners: ["QLEARN/AQLEARN dostają nagrodę powiększoną o r × wypłatę krewnego. To preferencja, nie selekcja; nie łączyć z testem reguły Hamiltona.", "QLEARN/AQLEARN get a reward increased by r × the relative's payoff. This is a preference, not selection; do not combine with the Hamilton test."],
  kin_window: ["Okno (cykle) pomiaru zmierzonego r.", "Window (cycles) for measuring r."],
  pair_cooldown: ["Ile cykli ta sama para nie może zagrać ponownie (w PD.gaml gra żyje 10 cykli). 0 = bez blokady.", "For how many cycles the same pair cannot play again (in PD.gaml a game lives 10 cycles). 0 = no block."],
  kin_export: ["Zapisuje family_timeseries.csv.", "Writes family_timeseries.csv."],
  synthetic_grid: ["Rozmiar syntetycznej sieci (n × n węzłów), gdy nie wczytano GeoJSON.", "Size of the synthetic network (n × n nodes) when no GeoJSON is loaded."],
  synthetic_spacing: ["Odstęp między węzłami syntetycznej sieci (m).", "Spacing between nodes of the synthetic network (m)."],
  cell_learning_rate: ["Tempo uczenia się oceny miejsc (komórek) po grach.", "Learning rate of place (cell) ratings after games."],
};

// opisy gotowych scenariuszy (eksperymentów batch); liczbę przebiegów i cykli dopisuje strona
const SCENARIO_HELP = {
  A_baseline: ["Ablacja A: 20 agentów QLEARN bez ruchu środowiskowego i bez uczenia społecznego. Punkt odniesienia dla B–F.", "Ablation A: 20 QLEARN agents without environmental movement or social learning. The reference for B–F."],
  B_env_movement: ["Ablacja B: jak A, ale agenci idą ku miejscom, które dobrze oceniają (ruch środowiskowy).", "Ablation B: like A, but agents head towards places they rate well (environmental movement)."],
  C_social_movement: ["Ablacja C: 20 agentów AQLEARN z ruchem środowiskowym i społecznym (idą ku dobrze ocenianym partnerom).", "Ablation C: 20 AQLEARN agents with environmental and social movement (they head towards partners they rate well)."],
  D_social_learning: ["Ablacja D: jak C, plus szybsze uczenie z dobrze ocenianymi partnerami.", "Ablation D: like C, plus faster learning with partners rated well."],
  E1_classic_TFT: ["Kontrola E1: 20 agentów TFT z ruchem środowiskowym, bez uczenia.", "Control E1: 20 TFT agents with environmental movement, no learning."],
  E2_classic_WSLS: ["Kontrola E2: 20 agentów WSLS z ruchem środowiskowym, bez uczenia.", "Control E2: 20 WSLS agents with environmental movement, no learning."],
  E3_classic_GRIM: ["Kontrola E3: 20 agentów GRIM z ruchem środowiskowym, bez uczenia.", "Control E3: 20 GRIM agents with environmental movement, no learning."],
  F_broken_windows_anchor: ["Ablacja F: jak D, plus efekt rozbitej szyby (0,4) i kotwica charakteru TFT (0,6).", "Ablation F: like D, plus the broken windows effect (0.4) and a TFT character anchor (0.6)."],
  R0_regression: ["Test regresyjny R0: mieszanka wszystkich charakterów i mechanizmów, odcisk w cyklu 2000, z limitem gier i bez. Służy do sprawdzenia, że model się nie zmienił.", "Regression test R0: a mix of all characters and mechanisms, fingerprint at cycle 2000, with and without the game limit. Checks that the model has not changed."],
  S1_P12_space: ["Walidacja P1 i P2 w przestrzeni: rdzeń z siedmioma strategiami po równo, ewolucja z mutacją i bez, trzy macierze wypłat, N = 200 i 500. Czy oszuści przetrwają bez fiksacji i czy altruiści wymierają bez mutacji?", "Validation of P1 and P2 in space: core with seven strategies in equal numbers, evolution with and without mutation, three payoff matrices, N = 200 and 500. Do cheaters persist without fixation, and do altruists die out without mutation?"],
  S1_P12_wellmixed: ["Jak S1_P12_space, ale w populacji dobrze wymieszanej (kontrola bez przestrzeni).", "Like S1_P12_space, but in a well-mixed population (control without space)."],
  S1_P3_space: ["Walidacja P3 (limit Dunbara) w przestrzeni: 80% TFT i 20% ALLD bez ewolucji, limit 0, 5, 15, 50, 150, trzy macierze, N = 200 i 500. Czy współpraca spada przy małym limicie?", "Validation of P3 (Dunbar limit) in space: 80% TFT and 20% ALLD without evolution, limit 0, 5, 15, 50, 150, three matrices, N = 200 and 500. Does cooperation fall with a small limit?"],
  S1_P3_wellmixed: ["Jak S1_P3_space, ale w populacji dobrze wymieszanej.", "Like S1_P3_space, but in a well-mixed population."],
  S1_P1_mobility: ["P1 przy niskiej mobilności (prędkość 0,5 i 0,1 m na cykl): czy powolny ruch zmienia los oszustów.", "P1 at low mobility (speed 0.5 and 0.1 m per cycle): does slow movement change the fate of cheaters?"],
  S2_pairs: ["Zestawienia parami: ewolucja z limitem Dunbara (0–150) i mutacją, trzy macierze, prędkość 0,1. Czy regularności zgadzają się, gdy działają razem?", "Pairwise combinations: evolution with a Dunbar limit (0–150) and mutation, three matrices, speed 0.1. Do the regularities agree when acting together?"],
  PM2_P12_space: ["Plan minimalny, P1 i P2 w przestrzeni: N = 200, prędkość 0,1, PD i snowdrift, mutacja 0 i 0,01, 10 powtórzeń.", "Minimal plan, P1 and P2 in space: N = 200, speed 0.1, PD and snowdrift, mutation 0 and 0.01, 10 repeats."],
  PM2_P12_wellmixed: ["Plan minimalny, P1 i P2 w populacji dobrze wymieszanej (kontrola).", "Minimal plan, P1 and P2 in a well-mixed population (control)."],
  PM2_P3_space: ["Plan minimalny, P3 w przestrzeni: 80% TFT i 20% ALLD, limit Dunbara 0–150, PD i snowdrift, prędkość 0,1.", "Minimal plan, P3 in space: 80% TFT and 20% ALLD, Dunbar limit 0–150, PD and snowdrift, speed 0.1."],
  PM2_P3_space_speed2: ["Jak PM2_P3_space, ale przy prędkości 2: przy 0,1 agent ma ok. 5 partnerów i limit Dunbara nie działa.", "Like PM2_P3_space, but at speed 2: at 0.1 an agent has about 5 partners and the Dunbar limit has no effect."],
  PM2_P3_wellmixed: ["Plan minimalny, P3 w populacji dobrze wymieszanej (kontrola).", "Minimal plan, P3 in a well-mixed population (control)."],
  PM3_P1_network: ["Warstwa projektowa dla P1: ewolucja z mutacją, PD, na sieci baseline, fragmented i connected. Czy wynik zależy od układu ścieżek?", "Design layer for P1: evolution with mutation, PD, on baseline, fragmented and connected networks. Does the result depend on the path layout?"],
  PM3_P3_network: ["Warstwa projektowa dla P3: limit Dunbara 0–150 na trzech wariantach sieci, PD, prędkość 0,1.", "Design layer for P3: Dunbar limit 0–150 on three network variants, PD, speed 0.1."],
  PM3_P3_network_speed2: ["Jak PM3_P3_network, ale przy prędkości 2 (limit Dunbara zaczyna działać).", "Like PM3_P3_network, but at speed 2 (the Dunbar limit starts to matter)."],
  PM4_heatmap: ["Mapa spotkań powtórnych: po jednym przebiegu na każdy wariant sieci, eksport macierzy komórek.", "Repeat-encounter map: one run per network variant, exporting the cell matrix."],
  PM4_heatmap_speed2: ["Jak PM4_heatmap, ale przy prędkości 2.", "Like PM4_heatmap, but at speed 2."],
  PM5_P4_strategy: ["Kalibracja P4 (reguła Hamiltona): gra dawcy, ALLC i ALLD, partner z tą samą strategią z prawdopodobieństwem α, więc r = α z konstrukcji. α 0–0,9, c/b 0,3 i 0,5.", "Calibration of P4 (Hamilton's rule): donation game, ALLC and ALLD, partner with the same strategy with probability α, so r = α by construction. α 0–0.9, c/b 0.3 and 0.5."],
  PM5_P4_family: ["Test P4 z rodzinami: partner spośród krewnych z prawdopodobieństwem α, r zmierzone, dopasowanie own i inclusive. Czy współpraca wygrywa, gdy r > c/b?", "P4 test with families: partner among relatives with probability α, measured r, own and inclusive fitness. Does cooperation win when r > c/b?"],
  PM7_P1P3_network: ["Para P1 + P3 na trzech wariantach sieci: ewolucja z mutacją i limit Dunbara, prędkość 0,1 i 2, PD.", "Pair P1 + P3 on three network variants: evolution with mutation and a Dunbar limit, speed 0.1 and 2, PD."],
  PM8_P2_network: ["Pary z P2 na trzech wariantach sieci: ewolucja bez mutacji (czy ALLC wymiera), limit Dunbara 0, 5, 15, prędkość 0,1 i 2.", "Pairs with P2 on three network variants: evolution without mutation (do ALLC die out?), Dunbar limit 0, 5, 15, speed 0.1 and 2."],
  PM9_full_N500: ["Pełny przegląd przy N = 500: trzy macierze, mutacja, limit Dunbara, trzy warianty sieci i dwie prędkości. Bardzo długi.", "Full sweep at N = 500: three matrices, mutation, Dunbar limit, three network variants and two speeds. Very long."],
  PM10_rest_off: ["Pilotaż stref odpoczynku, wariant bez stref: punkt odniesienia z tymi samymi seedami co PM10_rest_on.", "Rest zone pilot, variant without zones: the reference with the same seeds as PM10_rest_on."],
  PM10_rest_on: ["Pilotaż stref odpoczynku: 5, 10 i 20 stref rozmieszczonych centralnie, rozproszone lub na obrzeżach, PD i snowdrift, prędkość 2.", "Rest zone pilot: 5, 10 and 20 zones placed centrally, dispersed or at the edges, PD and snowdrift, speed 2."],
  PM11_rest_off: ["Właściwy eksperyment stref odpoczynku, wariant bez stref (po kalibracji odzysku energii).", "Main rest zone experiment, variant without zones (after calibrating energy recovery)."],
  PM11_rest_on: ["Właściwy eksperyment stref odpoczynku: 5, 10 i 20 stref w trzech rozmieszczeniach.", "Main rest zone experiment: 5, 10 and 20 zones in three placements."],
};
