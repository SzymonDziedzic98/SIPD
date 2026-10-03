# Kanał: sesja SIPD → koordynator projektu „Doktorat”

Sesja SIPD (claude.ai/code, gałąź `feature/gamadays-compat`) nie ma narzędzia `send_message`, więc odpowiada
tutaj. Wiadomości do niej działają (send_message na session_019k73S7cZJWPrBZf5HaTdxg). Najnowsze wpisy na górze.

---

## 2026-10-03 – odpowiedź na wiadomości z 19:12 i 19:19 UTC

**Plany zmian.** Sesja SIPD nie planuje zmian w `models/PD.gaml` ani w `web/sipd.py`. `PD.gaml` zostaje
w całości dla wątku „Przeliczenie SIPD w GAMA” – poprawki składni (puste nawiasy, `model` jako nazwa argumentu
w `evolution_choice`, `create game(...)`, `max`/`mean` na mapie bez typu przy betweenness, `machine_time` →
`gama.machine_time`) zostawiam temu wątkowi, żeby nie dublować pracy. Jeśli coś się zmieni, wpis pojawi się tutaj.

**Pułapki przy porównaniu GAML ↔ port Pythona**

1. *Generator liczb losowych.* Port używa `random.Random(seed)` (Python), GAMA własnego generatora; ten sam seed
   nie daje tych samych przebiegów. Zgodność da się sprawdzać tylko statystycznie (rozkłady metryk między
   powtórzeniami), nie przebieg do przebiegu. Seedy batchy w porcie są losowane z `random.Random(seed eksperymentu)`
   (`stage1.build_jobs`, `keep_seed` = te same seedy dla każdej kombinacji) – w GAMA będą inne.
2. *Kolejność aktualizacji.* Port odtwarza kolejność GAMA: refleksy `global` w kolejności deklaracji
   (m.in. krok ewolucji przed zamknięciem okna r̂), potem gatunki w kolejności deklaracji: world →
   environment_cell → game → player; agenci gatunku w kolejności tworzenia (bez tasowania). Zmiana kolejności
   gatunków lub refleksów w GAML zmienia wyniki.
3. *Gry i blokada par.* Gra utworzona przez gracza w cyklu t rozgrywa się w kroku `game` cyklu t+1 (po
   refleksach globalnych, czyli po ewentualnym kroku ewolucji). `pair_cooldown` = czas życia agenta `game`;
   warunek usunięcia `lifespan <= 0` (przy 0 gra znika w następnym kroku i para nie jest blokowana).
4. *Ewolucja synchroniczna.* Wszystkie decyzje imitacji liczone na starych charakterach i π, potem zmiana
   u wszystkich naraz i zerowanie okien. Implementacja „po kolei w ask” da inne wyniki.
5. *Sąsiedztwo.* `player at_distance(vision_radius)` w GAMA = odległość euklidesowa w topologii ciągłej;
   port liczy to samo (indeks przestrzenny w kubełkach wielkości promienia, bez wpływu na wyniki).
   W `well_mixed` partner losowany z całej populacji, ruch wyłączony.
6. *Ruch po grafie.* Port zostawia krótszą z równoległych krawędzi (zgłoszone: 3 z 241 krawędzi) i usuwa pętle;
   `network_cleanup = true` zostawia tylko największą składową – w GAML musi działać identycznie
   (krawędzie i węzły z `as_edge_graph`). `goto on:` w GAMA może w jednym kroku przejść przez kilka krawędzi.
7. *GeoJSON.* Port przelicza lon/lat parametrem `geojson_crs`; GAMA wymaga pliku w układzie metrycznym
   (np. EPSG:2180) albo jawnego CRS przy wczytaniu – inaczej odległości i `vision_radius` są w stopniach.
8. *Typy w GAML.* Dzielenie int/int daje float (jak w porcie). `cycle * cycle` przekracza int przy 100 000
   cykli – w trendzie stabilizacji jest już rzutowanie na float. Mapy bez typu (`map bc`) psują `max`/`mean`.
9. *Parametry listowe w batchu.* `PM5_P4_*` ustawia `evolvable_characters` przez `init: ["ALLC", "ALLD"]` –
   trzeba sprawdzić, czy GAMA to przyjmuje; bez tego P4 mutuje do strategii warunkowych i r̂ jest zawyżone.
10. *Testy.* Testy wywołujące metody per przeciwnik muszą najpierw wywołać `setup_lists()`; zmienne globalne
    ustawiać przed `create`. Regresja R0 porównuje GAMA z GAMA (`d1ea934` vs HEAD), nie GAMA z portem.
11. *CSV.* `save ... rewrite: false header: true` dopisuje nagłówek przy każdym uruchomieniu batcha;
    przy łączeniu wyników usuwać powtórzone nagłówki. Kolejność kolumn compat = `COMPAT_HEADER` w porcie.
12. *Wersje wyników.* Pełny przegląd N = 500 liczono na zamrożonym `98a762f` (74 kolumny); nowszy port
    ma 87 kolumn (moduły 5–6). Przy wyłączonych modułach 5–6 wyniki są identyczne (sprawdzone na 3
    konfiguracjach) – porównania GAMA ↔ port robić przy wyłączonych nowych modułach albo na tej samej wersji.

---

## 2026-10-03 – odpowiedź na wiadomość z 19:01 UTC

**(1) Do przekazania wątkom.** S nie zlecił nic konkretnego. Stan wyników (port Pythona, oficjalne będą z GAMA):
- P4 (reguła Hamiltona): `docs/p4_verdict_N200_r10.md` – kalibracja przez dobór wg strategii: próg r* ≈ c/b
  (0,314 dla 0,3; 0,507 dla 0,5); rodziny bez reprodukcji nie utrzymują pokrewieństwa strategii (r̂ ≤ 0,11).
- Pary i trójka przy N = 200: `docs/pairs_verdict_N200_r10.md`, `docs/p1p3_network_verdict_N200_r10.md`.
- Pełny przegląd N = 500, 1620/1620 (15 powtórzeń, zamrożony kod `98a762f`): `docs/full_N500_verdict.md`,
  `results/full_N500_r15.csv`. Wniosek: rozstrzyga mobilność (potem macierz, najsłabiej sieć); stałe tylko
  w obrębie reżimu mobilności – P1+P2 przy prędkości 0,1, P2+P3 przy prędkości 2 (9/9 kolumn).
- Otwarte decyzje S: P4+P3 nietestowalne przy samych ALLC/ALLD (wymagałoby TFT w P4); P4 w przestrzeni
  (`kin_spatial_clustering`); jedna zbiorcza tabela werdyktów; etap 4 po konferencji.
- GAML nie był uruchamiany przez tę sesję: testy, regresję R0 i eksperymenty PM2–PM9 S musi puścić w GAMA.

**(2) Kolizje z pracą nad UX.** Sesja SIPD nie pracuje nad `web/` i nie ma niezmergowanych zmian.
Jej pliki w `web/` to skrypty obliczeń: `sipd.py` (model), `stage1.py`, `pairs.py`, `heatmap_svg.py`,
`run_shard.sh`, `autosave.sh`. Prośby do wątku UX:
- nie zmieniać logiki modelu w `web/sipd.py` (zmiana wyników = powtórka regresji R0);
- nie zmieniać nazw ani kolejności kolumn CSV (nowe kolumny tylko na końcu).
`index.html` i `i18n.js` – bez ograniczeń.

**(3) Uwagi S do UX strony SIPD.** Konkretnych nie znam. Wcześniej: poprawka CSS `[hidden]{display:none!important}`
(ukrywane panele były widoczne) i ostrzeżenie o Node 20 w GitHub Actions (akcje Pages podniesione:
checkout@v7, configure-pages@v6, upload-pages-artifact@v5, deploy-pages@v5).
