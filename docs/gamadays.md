# SIPD – rozbudowa pod GAMA Days 2026

Gałąź `feature/gamadays-compat`. Wersja pod JASSS (`48b450c`) się nie zmienia: każdy nowy
mechanizm ma przełącznik, a przy wyłączonych przełącznikach odcisk `R0_regression` musi być
identyczny z commitem bazowym `d1ea934`.

## Decyzje

| Nr | Decyzja |
|---|---|
| 1 | Baza gałęzi: `48b450c` (z poprawkami z PR #1). |
| 2 | Eksperymenty zgodności: `unlimited_games = true`. |
| 3 | Macierze: PD (T=9, R=5, P=1, S=0), słaby PD (T=1,6, R=1, P=S=0), snowdrift (T=4, R=3, S=2, P=0). |
| 4 | Przełącznik `classic_start_cooperate`; **w eksperymentach zgodności włączony**. |
| 5 | Zapominanie (Dunbar) jednostronne; pamięć miejsc nie jest zapominana. |
| 6 | GRIM po zmianie charakteru liczy historię tylko od przejęcia. |
| 7 | Imitacja Fermiego: model = losowy sąsiad w `vision_radius`; w `well_mixed` losowy agent z populacji. |
| 8 | QLEARN/AQLEARN nie ewoluują w etapach 1–3; w etapie 4 przejście do Q = nowe tablice, z Q = tablice kasowane. |
| 9 | Przyspieszenia tylko takie, które nie zmieniają wyników (leniwe mapy, sąsiedzi raz na krok, równoległe powtórzenia). |
| 10 | Przełącznik `disorder_clamp` (disorder w [0, 1]); domyślnie wyłączony. |
| 11 | Q-learning poza rdzeniem; jego ograniczenie opisane niżej. |
| 12 | P3 mierzona zyskiem oszustów (wypłata ALLD na grę, `exploitation_rate()`), nie samym udziałem kooperacji. `dunbar_limit` ∈ {0, 5, 15, 50}; 150 tylko przy N, przy którym agenci mają > 150 różnych partnerów. |

## Diagnostyka dynamiki (port Pythona, `web/diagnostics.py`)

Warunki: 200 agentów, syntetyczny park ok. 1,9 × 1,9 km (ta sama gęstość co 20 agentów na
540 × 540 m), `vision_radius` 30, 50 000 cykli (Q-learning 200 000, Dunbar 30 000), 2 seedy.
Port ma ten sam algorytm co `PD.gaml`, ale inny generator liczb losowych; wyniki są orientacyjne
i trzeba je potwierdzić w GAMA na prawdziwej sieci (`drogi.geojson`).

**Spotkania.** Agent rozgrywa ok. 1066 gier z ok. 115 różnymi partnerami; mediana gier na parę
wynosi 7 (przy `vision_radius` 10: 349 gier, 97 partnerów, mediana 2). Gra jest w małym stopniu
„iterowana”: większa populacja nie zwiększa liczby powtórzeń z tym samym partnerem.

**Q-learning per przeciwnik praktycznie się nie uczy.** Po 200 000 cyklach udział D QLEARN wobec
ALLC 0,48, wobec ALLD 0,54 (para gra średnio 23 razy). W teście kontrolnym (jeden QLEARN,
jeden przeciwnik) udział D wobec ALLC wynosi 0,48 po 30 grach, 0,49 po 300 i 0,92 po 3000.
Przy `learning_rate` 0,1 i `discount` 0,9 wartości Q nie odchodzą od prioru, więc QLEARN/AQLEARN
grają zgodnie z `initial_cooperation_bias` i `epsilon`. Dotyczy to też interpretacji wariantów A–F.

**TFT z losowym startem.** Populacja TFT ma udział D 0,49 (wzajemny odwet po losowym pierwszym D);
z `classic_start_cooperate` udział D 0,00 i wypłata 5,00 na grę.

**Rozbita szyba.** Przy `broken_windows_sensitivity` 0,4 udział D 0,99 (pełne załamanie).
Bez ograniczenia `disorder` dochodzi do ok. 800 w najczęściej odwiedzanych punktach (ok. 100
nawet bez efektu szyby); stąd `disorder_clamp`. W populacji samych ALLC efekt się nie uruchamia.

**Tryb z limitem gier.** Bez istotnego zniekształcenia częstości gier między charakterami.

**Limit Dunbara.** W 30 000 cykli agent spotyka ok. 83 różnych partnerów, więc limity 5, 15, 50
działają, 150 nie. Mieszanka 160 TFT (start od C) + 40 ALLD:

| `dunbar_limit` | zapomnień | udział D | TFT / grę | ALLD / grę |
|---|---|---|---|---|
| 0 | 0 | 0,337 | 4,20 | 1,80 |
| 50 | 7 573 | 0,341 | 4,19 | 1,86 |
| 15 | 19 084 | 0,324 | 4,19 | 2,08 |
| 5 | 26 374 | 0,326 | 4,18 | 2,33 |

Zapominanie zwiększa zysk oszustów (do +29%), a udział kooperacji prawie się nie zmienia; brak
wyraźnego progu. Stąd decyzja 12.

## Moduł 2 – ewolucja (implementacja)

- Parametry: `evolution_on` (false), `evolution_interval` (100), `fermi_k` (0,5), `mutation_rate` (0),
  `evolvable_characters` (7 klasycznych), `well_mixed` (false).
- Co `evolution_interval` cykli **synchronicznie**: każdy gracz z `evolvable_characters` wybiera model
  (losowy sąsiad w `vision_radius`; w `well_mixed` losowy agent populacji), z prawdopodobieństwem
  `mutation_rate` bierze losowy charakter z listy, w przeciwnym razie przejmuje charakter modelu
  z prawdopodobieństwem 1 / (1 + exp(−(π_model − π_self) / K)). Potem zmiana u wszystkich naraz
  i wyzerowanie okien wypłat.
- π = średnia wypłata na grę w bieżącym oknie. Gdy gracz lub model nie grał w oknie, π jest
  nieokreślone i imitacji nie ma. Charakteru spoza `evolvable_characters` (np. QLEARN) się nie imituje.
- Po zmianie charakteru pamięć partnerów zostaje; GRIM liczy zdrady od przejęcia (`history_offset`,
  usuwany też przy zapomnieniu partnera).
- `well_mixed`: pary losowane z całej populacji, ruch wyłączony.
- Szeregi czasowe: `timeseries_export`, `sample_interval` → `results/character_timeseries.csv`
  (udział każdego charakteru, udział D w oknie próbkowania, liczba zmian charakteru).
- Pierwsza obserwacja (port Pythona, `well_mixed`, 105 agentów po 15 z każdej strategii klasycznej, PD,
  10 000 cykli, 2 seedy): bez mutacji fiksacja (raz ALLD, raz GRIM + WSLS); z `mutation_rate` 0,01
  ALLD ok. 0,97–0,98. W `well_mixed` para spotyka się ok. 2 razy na okno ewolucji, więc gra jest
  prawie jednorazowa i przewaga ALLD jest oczekiwana. To wstępny sygnał dla P1, nie wynik etapu 1.

## Decyzje po przeglądzie kodu portu (U1–U10)

| Nr | Decyzja |
|---|---|
| 13 | `network_cleanup = true` we wszystkich eksperymentach zgodności (S1, S2, PM): bez pętli, agenci tylko na największej składowej. Domyślnie w modelu `false` (zgodność z JASSS). Dla N = 200 (sieć syntetyczna z jedną składową) wyniki identyczne. |
| 14 | Liczniki okien stabilizacji (`stab_count`, `stabilized_at`) zostają w kodzie, choć nie trafiają do CSV. |
| 15 | Nazwa wariantu `fragmented` zostaje; wariant redukuje redundancję (krawędzie w cyklach), liczba usuniętych krawędzi w `net_edges_removed`. |
| 16 | `feedback_value` pozostaje niezależne od macierzy wypłat; przy snowdrifcie z ruchem/uczeniem środowiskowym model wypisuje ostrzeżenie. |

## Moduł 3 – pokrewieństwo (decyzje)

| Nr | Decyzja |
|---|---|
| 17 | Eksperymenty P4: `pair_cooldown = 0` (bez blokady ponownej gry pary). Domyślnie 10, jak dotąd. Przy 10 zadane α nie odpowiada zmierzonemu r̂ (α 0,3 → r̂ 0,20). |
| 18 | r̂ liczone z ruchów (C = 1, D = 0), także dla strategii warunkowych. |
| 19 | `fitness_mode = "inclusive"` w wariancie `"strip"`: π = własna średnia + r·(Σ skutków moich ruchów dla krewnych − Σ skutków ruchów krewnych dla mnie) / gry. Skutek = wypłata partnera przy moim ruchu − jego wypłata, gdybym zagrał D. `"add"` tylko do porównań. |
| 20 | r̂ liczone w obrębie interwałów ewolucji (skład populacji stały): Σ Sxy / Σ Sxx po blokach. Regresja z całego okna jest zawyżona przez zmiany składu w czasie (np. α = 0 → r̂ 0,3). Wersja łączna zostaje w kolumnie `r_hat_all_pooled`. |
| 21 | Kalibracja P4 z doborem wg strategii (`kin_matching_mode = "strategy"`): r̂ = α z konstrukcji. Rodziny (`"family"`) to właściwy test z r̂ zmierzonym. |
| 22 | W P4 ewoluują tylko ALLC i ALLD (`evolvable_characters`); mutacja do strategii warunkowych zawyżała r̂ liczone z ruchów. P4: b = 1, `fermi_k` 0,5. |

Test znaku (`p4_intervals`, `p4_sign_agreement`): w każdym interwale ewolucji, przy 0 < udział ALLC < 1,
porównanie znaku zmiany udziału ALLC ze znakiem r̂_k·b − c (r̂_k z gier tego interwału). Zmiana obejmuje
też mutacje.

Wyniki P4: `docs/p4_verdict_N200_r10.md`.

## Moduł 4 – strefy odpoczynku i zmęczenie (propozycja, gałąź `feature/rest-zones`)

Cel: zmienna projektowa zamiast globalnej prędkości. Liczba, rozmieszczenie i czas korzystania ze stref
(ławki, place zabaw) mają zmieniać liczbę gier na partnera tak, jak dotąd zmieniała ją prędkość.

- Przełącznik `rest_on` (domyślnie `false`). Przy wyłączonym module odcisk `R0_regression`,
  `ablation_results.csv`, `character_timeseries.csv` i wszystkie dotychczasowe kolumny `compat_results.csv`
  są identyczne jak przed zmianą (sprawdzone). Działa tylko na sieci (w `well_mixed` pomijany z ostrzeżeniem).
- Strefy: `rest_zone_count` węzłów sieci; `rest_zone_placement` = `dispersed` (najdalszy punkt w całej sieci),
  `central` (w promieniu 0,35 od środka), `peripheral` (poza 0,75 promienia), `random`.
- Energia w [0, 1]; spada o `fatigue × przebyta droga`. Zmęczenie z dwóch rozkładów normalnych: zwykli
  N(`fatigue_regular_mean` 0,07; `fatigue_regular_sd` 0,015) i starsi/schorowani N(`fatigue_frail_mean` 0,2;
  `fatigue_frail_sd` 0,05), na 100 m, obcięte od dołu do 0,005. Udział starszych `frail_share` 0,2.
  Energia startowa losowa z [`rest_threshold`, 1].
- Poniżej `rest_threshold` (0,3) agent idzie najkrótszą drogą do najbliższej strefy (Dijkstra z wielu źródeł,
  liczona raz). W strefie stoi, odzyskuje `rest_recovery` (0,005) na cykl do `rest_target` (1,0) i przez cały
  czas gra z sąsiadami w `vision_radius`. Strefy nie mają limitu miejsc.
- Losowanie stref i zmęczenia ma osobny generator (seed przebiegu), więc strategie i węzły startowe są te same
  z modułem i bez niego (porównanie w parach).
- Nowe kolumny `compat_results.csv`: `rest_on`, `rest_zone_count`, `rest_zone_placement`, `rest_time_share`
  (udział agento-cykli w odpoczynku), `rest_games_share` (udział gier z udziałem odpoczywającego),
  `rest_bouts_per_agent`, `frail_share_realised`.
- Kalibracja (decyzja autora, 29.09.2026): 20–30% czasu w strefach. `rest_recovery` 0,005 daje przy prędkości 2
  ok. 25% (zwykli ok. 21%, starsi ok. 40%; N = 200, 10 000 cykli). Przy innej prędkości udział się zmienia,
  bo zmęczenie liczone jest na metr drogi. Pilotaż PM10 liczono jeszcze przy 0,002 (ok. 44% czasu w strefach).
- Eksperymenty: `PM10_rest_off`, `PM10_rest_on` (N = 200, prędkość 2, ewolucja, mutacja 0,01, PD i snowdrift,
  rozmieszczenie × liczba stref {5, 10, 20}, 3 powtórzenia, 100 000 cykli).
- Eksperyment właściwy: `PM11_rest_off` (10 powtórzeń) i `PM11_rest_on` (rozmieszczenie × liczba stref, 5 powtórzeń),
  N = 200, prędkość 2, 100 000 cykli; macierz ustawiana przez `--set payoff_preset=...`.
