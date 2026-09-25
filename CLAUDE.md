# SIPD – rozbudowa modelu pod GAMA Days 2026

## Kontekst
Model SIPD (Spatial Iterated Prisoner's Dilemma) w GAMA/GAML. Agenci (species `player`) poruszają się
po sieci ścieżek z GIS (park we Wrocławiu, `path_network`) i grają w iterowany dylemat więźnia.
Charaktery: TFT, ALLC, ALLD, FTFT, TF2T, GRIM, WSLS, QLEARN, AQLEARN.

Mechanizmy już obecne (stan z końca lipca 2026, do weryfikacji):
- Q-learning per przeciwnik (`q_c_per_other`, `q_d_per_other`, `update_q`, `get_state` ze stanami RISKY/SAFE,
  `betrayal_count_at_location`),
- pamięć społeczna (`lists_per_other`, `my_moves_per_other`, `last_move_of`, `ever_defected_against_me`,
  `social_feedback`) i środowiskowa (`personal_feedback`),
- pole `disorder` w `environment_cell` + `broken_windows_sensitivity` (efekt rozbitej szyby, działa na wszystkie charaktery),
- kotwica charakteru (`base_character`, `character_strength`, `effective_anchor_strength`, wykładniczy zanik + erozja przez disorder),
- `pending_action` synchronizowane z faktycznie zagranym ruchem na końcu `strategy()`,
- flaga `unlimited_games`, ablacja batch A–F (+ E1–E3), eksport do `ablation_results.csv`,
- zestaw testów (`experiment ... type: test`).

Cel badawczy (abstrakt GAMA Days, tytuł: „From Iterated Prisoner's Dilemma to Design Standards:
Which Laws of Cooperation Hold When Combined?”): sprawdzić, czy kanoniczne regularności kooperacji
(stabilny udział oszustów, przetrwanie bezwarunkowych altruistów, limit Dunbara, reguła Hamiltona)
pozostają zgodne, gdy działają jednocześnie w jednym modelu, oraz czy ich werdykty zależą od układu przestrzeni.
Regularności odporne na zmiany układu i wypłat są kandydatami na stałe projektowe; zależne od nich –
parametrami kontekstowymi. Model testuje spójność wewnętrzną założeń, nie prawdę empiryczną.

## Krok 0 – rozpoznanie, bez zmian w kodzie
1. Przeczytaj cały plik `.gaml` i wypisz inwentarz: species, zmienne globalne, akcje/reflexy gracza,
   wszystkie mapy indeksowane przeciwnikiem, eksperymenty GUI/batch/test.
2. Sprawdź, czy są obecne wszystkie mechanizmy z listy wyżej oraz czy są naprawione błędy:
   zdublowany `get_state`, `pending_action` zapisywany przed nadpisaniem ruchu przez kotwicę/disorder,
   `return` wewnątrz zewnętrznej pętli w `aqlearn_clique_fraction`, aktualizacja Q także dla AQLEARN.
3. Sprawdź obecny rozmiar populacji i wydajność (czas cyklu); oszacuj czas przebiegu przy N = 200 i N = 500.
4. Zgłoś rozbieżności i zadaj pytania, zanim zaczniesz implementację.

## Zasady pracy
- Pracuj na osobnej gałęzi git: `feature/gamadays-compat`. Wersja pod artykuł do JASSS nie może się zmienić.
- Każdy nowy moduł ma przełącznik; przy wyłączonych modułach model musi zachowywać się identycznie jak dotąd
  (ten sam seed → te same wyniki eksportu). To jest test regresyjny numer 1.
- Preferuję mechanizmy probabilistyczne („soft pull”) zamiast twardych nadpisań.
- Nowe parametry: w `global`, z wartościami domyślnymi wyłączającymi moduł, widoczne w GUI
  jako `parameter` z osobną `category`.
- Każda zmiana ruchu po decyzji bazowej musi zachować synchronizację `pending_action`.
- Pokazuj mi zmiany jako diff/fragmenty kodu z krótkim uzasadnieniem, nie przepisuj całego pliku.
- Komentarze w kodzie po polsku, zwięzłe.
- W miejscach oznaczonych „zapytaj mnie” nie podejmuj decyzji samodzielnie.

## Moduł 1 – limit Dunbara (pamięć partnerów)
- Parametr `dunbar_limit` (int, 0 = brak limitu = moduł wyłączony).
- Każdy gracz trzyma `known_others` uporządkowane wg ostatniej interakcji (LRU).
  Po każdej grze: odśwież partnera na końcu listy; przy przekroczeniu limitu zapomnij najdawniej widzianego.
- Zapomnienie = usunięcie partnera z WSZYSTKICH map indeksowanych przeciwnikiem
  (m.in. `lists_per_other`, `my_moves_per_other`, `last_move_of`, `ever_defected_against_me`,
  `q_c_per_other`, `q_d_per_other`, `social_feedback`, `pending_action` – zweryfikuj pełną listę w kodzie).
  Przy kolejnym spotkaniu partner jest traktowany jak nowy (ponowna inicjalizacja jak w `setup_lists`).
- Kotwica charakteru liczy siłę z długości historii z danym przeciwnikiem – po zapomnieniu
  powinna wrócić do pełnej siły. Potwierdź, że tak się dzieje, i opisz to.
- Metryki: średnia liczba znanych partnerów, liczba zapomnień na cykl, liczba różnych partnerów
  na agenta w oknie czasu.

## Moduł 2 – ewolucyjna zmiana strategii
- Parametry: `evolution_on` (bool, domyślnie false), `evolution_interval` (co ile cykli),
  `fermi_k` (szum selekcji), `mutation_rate`, `evolvable_characters` (lista charakterów podlegających
  zmianie; domyślnie tylko klasyczne: TFT, ALLC, ALLD, FTFT, TF2T, GRIM, WSLS).
- Reguła imitacji Fermiego: co `evolution_interval` każdy ewoluujący gracz wybiera model
  i przejmuje jego charakter z prawdopodobieństwem 1 / (1 + exp(-(π_model - π_self) / fermi_k)).
  Wybór modelu: ostatni przeciwnicy czy sąsiedzi w promieniu – zaproponuj oba warianty i zapytaj mnie.
- π = średnia wypłata na grę w bieżącym oknie (nie skumulowany `score`), okno zerowane po aktualizacji.
  (Moduł 3 dodaje alternatywny sposób liczenia π – przygotuj kod tak, by obliczanie π było jedną akcją.)
- Z prawdopodobieństwem `mutation_rate` zamiast imitacji losowy charakter z `evolvable_characters`.
- Po zmianie charakteru wyczyść stan specyficzny dla strategii (np. flagi GRIM), ale zachowaj pamięć partnerów.
- Agenci QLEARN/AQLEARN domyślnie nie ewoluują. Przejścia do/z nich (co z tablicami Q?) – zapytaj mnie.
- Metryki w czasie: udział każdego charakteru, udział ruchów D, udział ALLC i ALLD.

## Moduł 3 – pokrewieństwo (reguła Hamiltona) – BONUS, po planie minimalnym
Wymaga Modułu 2 (`evolution_on = true`). Bez dynamiki ewolucyjnej moduł nie ma sensu – zablokuj taką
konfigurację z czytelnym komunikatem.

### Założenie koncepcyjne
r w regule Hamiltona to korelacja strategii między dawcą a biorcą, nie etykieta. Moduł musi
(a) wytwarzać asortatywność strategii wśród krewnych i (b) ją mierzyć. Predykcje porównujemy z r zmierzonym,
nie z r zadanym.

### Wypłaty: tryb gry dawcy
- Parametr `payoff_mode` ∈ {"classic", "donation"}; domyślnie "classic" (bez zmian w dotychczasowych wynikach).
- W trybie "donation" parametry `b` i `c` (b > c > 0) wyznaczają macierz: R = b − c, S = −c, T = b, P = 0.
- Walidacja przy starcie: b > c > 0; w trybie "donation" ignoruj T, R, P, S z GUI i wypisz użytą macierz.

### Rodziny
- Parametry: `kin_on` (bool, domyślnie false), `family_size` (int), `family_r` (float, nominalne r
  w rodzinie, np. 0.5), `kin_spatial_clustering` (0–1: 0 = losowe położenia startowe, 1 = rodzina startuje
  w jednym skupisku), `kin_strategy_correlation` (0–1: prawdopodobieństwo, że członek rodziny dostaje
  strategię rodziny zamiast losowej przy inicjalizacji), `kin_imitation_bias` (0–1: udział wyborów modelu
  do imitacji spośród krewnych w Module 2).
- Atrybut gracza `family_id`; stały przez cały przebieg (nie zmienia się przy zmianie charakteru).
- Nie dodawaj reprodukcji ani nowych agentów – rodziny są stałe, asortatywność powstaje przez
  skupienie przestrzenne, korelację startową i imitację preferującą krewnych.

### Kontrola well_mixed z asortatywnością
- Parametr `kin_matching_prob` (α, 0–1), działa tylko w `well_mixed`: z prawdopodobieństwem α partner
  losowany spośród krewnych, w przeciwnym razie z całej populacji.
- W tej konfiguracji uruchamiaj tylko ALLC i ALLD (bez wzajemności), żeby izolować mechanizm pokrewieństwa.

### Dwa warianty dopasowania w Module 2 (parametr `fitness_mode`)
- "own" (domyślny): π = własna średnia wypłata na grę (neighbour-modulated fitness).
- "inclusive": π = własna średnia wypłata + Σ po partnerach-krewnych (family_r × wypłata, którą im
  przyniosła moja akcja) / liczba gier. Zapisuj oba składniki osobno. Uważaj na podwójne liczenie –
  opisz dokładnie, co sumujesz, i zapytaj mnie przed finalizacją.
- Opcjonalnie, domyślnie wyłączone (`kin_reward_learners`): dla QLEARN/AQLEARN nagroda =
  własna wypłata + family_r × wypłata krewnego-partnera. To mechanizm preferencji, nie selekcji –
  nie mieszaj go z testem reguły Hamiltona; zapytaj mnie, zanim go włączysz w jakimkolwiek eksperymencie.

### Metryki
- r̂ (zmierzone): regresja strategii partnera na strategię własną w interakcjach (C = 1, D = 0),
  w oknie czasu, osobno dla wszystkich interakcji i dla interakcji z krewnymi.
- Udział interakcji z krewnymi; poziom kooperacji z krewnymi vs z obcymi;
  udział strategii kooperujących w czasie, osobno w rodzinach.

## Warstwa projektowa – warianty układu przestrzennego
Cel: sprawdzić, czy werdykty regularności zależą od układu przestrzeni. To jedyna zmienna
kontrolowana przez projektanta – pomost do „design standards” w abstrakcie.

### Warianty sieci
- Parametr `network_variant` ∈ {"baseline", "fragmented", "connected"}.
- "baseline": obecna sieć ścieżek parku.
- "fragmented": programowe usunięcie części krawędzi (`edge_removal_fraction`, np. 0.2) z zachowaniem
  spójności grafu – usuwaj tylko krawędzie, których usunięcie nie rozcina sieci (sprawdzaj spójność
  po każdym usunięciu).
- "connected": programowe dodanie skrótów między węzłami w odległości < `shortcut_max_length`
  (`shortcut_count`), jako proste odcinki.
- Ten sam seed → ta sama modyfikacja sieci.
- Zapytaj mnie, czy wolę warianty generowane programowo, czy dostarczę pliki GeoJSON z QGIS;
  obsłuż oba źródła (parametr ścieżki do pliku sieci).

### Charakterystyka wariantów (eksport raz na przebieg)
Liczba węzłów i krawędzi, średni stopień, średnia długość najkrótszej ścieżki, gęstość,
maksymalna i średnia betweenness węzłów.

W `well_mixed` parametr jest ignorowany (w CSV zapisuj "n/a").

## Metryka stabilności sieci spotkań (pomost Dunbar → odporność)
- Dla każdego agenta w oknie czasu: udział spotkań z partnerami już znanymi vs z nowymi;
  liczba różnych partnerów.
- Przestrzennie: dla każdej `environment_cell` średni udział spotkań powtórnych w grach rozegranych
  w tej komórce, w oknie czasu.
- Heatmapa w GUI (osobny display) + eksport macierzy komórek na końcu przebiegu.
- Metryka opisowa – nie dodawaj reguły łączącej ją z bezpieczeństwem ani kooperacją.

## Eksperyment kompatybilności – definicja

### Rdzeń minimalny
Konfiguracja `compat_core`: tylko strategie klasyczne, ruch losowy po sieci; disorder, kotwica,
Q-learning/AQLEARN oraz ruch środowiskowy/społeczny WYŁĄCZONE. Wszystkie testy regularności zaczynają się
od rdzenia. Kontrola `well_mixed`: losowe dobieranie par bez przestrzeni (ten sam rdzeń), żeby oddzielić
efekt struktury przestrzennej.

### Skala
Populacja parametryzowana; docelowo N = 200 i N = 500. Zaproponuj optymalizacje, jeśli przebieg jest zbyt
wolny. Liczba różnych partnerów na agenta musi przekraczać `dunbar_limit`, inaczej limit nie działa –
raportuj to dla każdej konfiguracji.

### Macierze wypłat
Klasyczny PD (T>R>P>S), słaby PD, snowdrift (T>R>S>P); dla P4 dodatkowo gra dawcy.
Nie wyciągaj wniosków z jednej macierzy.

### Predykcje i kryteria
- P1 oszuści: przy ewolucji udział ALLD/defekcji po wygrzaniu stabilizuje się w (0, 1) – brak fiksacji.
- P2 altruiści: przy mutation_rate = 0 ALLC wymiera; przy mutation_rate > 0 utrzymuje się na niskim poziomie.
- P3 Dunbar: poziom kooperacji jako funkcja `dunbar_limit` – kooperacja spada, gdy limit jest mniejszy niż
  liczba powtarzalnych partnerów; raportuj próg.
- P4 Hamilton (wersja predykcyjna, addytywna): w `well_mixed` z ALLC/ALLD i grą dawcy kooperacja przejmuje
  populację, gdy r̂ > c/b, a zanika, gdy r̂ < c/b. Kalibracja: α ∈ {0, 0.1, …, 0.9} przy c/b ∈ {0.3, 0.5};
  oczekiwane r̂ ≈ α – jeśli nie, zatrzymaj się i zgłoś. W przestrzeni i przy grach powtarzanych reguła
  może zawodzić (nieaddytywność, wzajemność sieciowa) – to nie błąd implementacji; raportuj próg
  i odchylenie od c/b. Porównaj `fitness_mode` "own" vs "inclusive".
Stabilizacja: zdefiniuj okno wygrzewania i kryterium (np. zmiana średniej kroczącej udziałów < ε przez K cykli);
raportuj, czy przebieg osiągnął stabilizację.

### Sekwencja
1. Walidacja pojedyncza: każda predykcja osobno w rdzeniu i w `well_mixed`. Jeśli któraś się nie odtwarza,
   zatrzymaj się i zgłoś.
1b. Warstwa projektowa: predykcje odtworzone w punkcie 1 na trzech wariantach sieci.
2. Zestawienia parami: P1+P3, P2+P3, P1+P2, P4+P3, P4+P1, P4+P2.
3. Wszystkie razem.
4. To samo z włączonymi mechanizmami miejskimi (disorder, uczenie, ruch zależny od GIS).

## Eksperymenty batch
- Nie zmieniaj istniejących wariantów A–F i E1–E3.
- Nowe eksperymenty zgodne z sekwencją; parametry kluczowe: `dunbar_limit` ∈ {0, 5, 15, 50, 150},
  `evolution_on`, `mutation_rate` ∈ {0, >0}, macierze wypłat, N, przestrzeń vs `well_mixed`,
  `network_variant`, (Moduł 3) α, c/b, `fitness_mode`.
- Stałe seedy; eksport do `compat_results.csv` (wiersz = przebieg, wszystkie parametry, metryki końcowe,
  charakterystyka sieci, flaga stabilizacji).
- Szeregi czasowe udziałów charakterów do osobnego CSV (wiersz = próbkowany cykl na przebieg).
- Jeśli układ jest za kosztowny obliczeniowo, zaproponuj redukcję i zapytaj mnie.

## Werdykt
Dla każdej regularności i każdej pary klasyfikuj wynik:
- „stała kandydacka” – werdykt taki sam we wszystkich testowanych wariantach sieci i macierzach wypłat;
- „parametr kontekstowy” – werdykt zależy od wariantu sieci lub macierzy; wskaż, od czego;
- „nie odtworzono” – regularność nie odtworzyła się nawet w walidacji pojedynczej.
Tabela zbiorcza: wiersze = regularności i pary, kolumny = warianty sieci × macierze, komórki = werdykt
z przedziałem zmienności między powtórzeniami.

## Testy (`type: test`)
- Każdy test wywołujący metody per przeciwnik musi najpierw wywołać `setup_lists()`.
- Agentów twórz składnią `create player(character: "QLEARN", character_strength: 0.8) number: 2;`.
  Zmienne globalne ustawiaj przed `create`.
- Wymagane testy:
  - regresja przy wyłączonych modułach (identyczne wyniki jak przed zmianami),
  - zapomnienie czyści wszystkie mapy per przeciwnik; LRU nie zapomina ostatnio widzianego partnera,
  - reguła Fermiego: dla π_model ≫ π_self prawie zawsze imitacja, dla π_model = π_self ok. 50%,
  - mutacja zwraca tylko charaktery z `evolvable_characters`,
  - `pending_action` pozostaje zsynchronizowane przy włączonych modułach,
  - `compat_core` rzeczywiście wyłącza wszystkie mechanizmy spoza rdzenia,
  - warianty sieci: graf pozostaje spójny; ten sam seed daje tę samą sieć,
  - Moduł 3: `kin_on = false` → regresja; tryb "donation" buduje poprawną macierz i odrzuca b ≤ c;
    `family_id` nie zmienia się przy zmianie charakteru; `kin_matching_prob` 0 i 1 dają oczekiwane udziały
    interakcji z krewnymi; r̂ ≈ α w `well_mixed`; r̂ na sztucznych sekwencjach daje znaną wartość;
    "inclusive" przy family_r = 0 daje to samo co "own"; `kin_on = true` przy `evolution_on = false` jest blokowane.

## Uruchamianie
Sprawdź, czy jest dostępny GAMA headless. Jeśli nie, nie zgaduj wyników – przygotuj konfigurację,
a uruchomię ją sam w GUI. Nigdy nie raportuj wyników, których nie uzyskałeś z faktycznego przebiegu.

## Plan minimalny na konferencję (23–25.11.2026)
Ten zakres musi być gotowy; wszystko ponad nim jest bonusem. Jeśli brakuje czasu, najpierw zmniejszaj
przegląd parametrów, nie liczbę predykcji.

Minimum:
1. Krok 0, Moduły 1–2, warianty sieci, metryka stabilności spotkań, testy.
2. Walidacja pojedyncza P1, P2, P3: N = 200, macierze {klasyczny PD, snowdrift},
   {przestrzeń "baseline", `well_mixed`}, 10 powtórzeń.
3. Warstwa projektowa dla P1 i P3: N = 200, jedna macierz (ta, w której P1 się odtworzyła),
   warianty {"baseline", "fragmented", "connected"}, 10 powtórzeń.
4. Heatmapa stabilności spotkań dla trzech wariantów sieci (jeden reprezentatywny przebieg każdy).
5. Tabela werdyktów dla wykonanego zakresu.

Bonus, w kolejności:
6. Moduł 3 i kalibracja P4 w `well_mixed`.
7. Para P1+P3 na trzech wariantach sieci.
8. Pozostałe pary i pełny przegląd (N = 500, trzy macierze, 15 powtórzeń).
9. Etap 4 z mechanizmami miejskimi – po konferencji.

Przed startem obliczeń oszacuj czas jednego przebiegu i łączny czas planu minimalnego; jeśli przekracza
dostępny czas, zaproponuj redukcję i zapytaj mnie.

## Na koniec każdej sesji
Krótkie podsumowanie: co dodano, jakie parametry, jak uruchomić eksperymenty, znane ograniczenia,
następny krok, propozycja commit message.

## Rozszerzalność (nie implementuj – tylko przygotuj architekturę)
Model będzie później rozszerzany o fazy z pierwotnej roadmapy. Projektuj Moduły 1–3 tak, żeby można je
było dołożyć bez przepisywania istniejącego kodu:
- Faza 5 (ruch Schellinga): wybór kierunku ruchu wydziel do jednej akcji z przełącznikiem `movement_mode`
  (obecne tryby + miejsce na "schelling").
- Faza 6 (stereotypy przestrzenne): przy spotkaniu nieznanego lub zapomnianego partnera (Moduł 1)
  inicjalizacja przekonań ma przechodzić przez jedną akcję `init_beliefs_for(partner)`, którą później
  można podmienić na wstrzykiwanie stereotypu miejsca.
- Faza 7 (świadkowie, image scoring): każda rozegrana gra ma emitować zdarzenie z danymi
  (gracze, ruchy, miejsce, cykl) do jednej akcji `on_game_played`, na którą później mogą reagować obserwatorzy.
- Faza 8 (plotka): nie wymaga dziś niczego ponad Fazę 7.
- Faza 9 (BDI/BEN): brak przygotowań.
- Faza 1 (labirynt z gałęzi `feature/maze-environment`): obsługa ładowania sieci z pliku (warstwa projektowa)
  ma pozwolić później dodać labirynt jako kolejny `network_variant`.
Na koniec opisz w podsumowaniu, gdzie w kodzie są te punkty zaczepienia.
