# P4 – reguła Hamiltona: kalibracja i test z rodzinami (port Pythona, N = 200, 10 powtórzeń)

Warunki: `well_mixed`, tylko ALLC i ALLD (ewoluują tylko te dwie), gra dawcy b = 1, c ∈ {0,3; 0,5},
α ∈ {0; 0,1; …; 0,9}, reguła Fermiego `fermi_k` 0,5, mutacja 0,01, 10 000 cykli (100 kroków ewolucji),
rodziny po 10, na starcie jednorodne (`kin_strategy_correlation` 1), `pair_cooldown` 0.
Port ma inny generator liczb losowych niż GAMA: wyniki trzeba potwierdzić w GAMA (`PM5_P4_strategy`, `PM5_P4_family`).

## Wnioski

1. **Kalibracja przeszła.** Przy doborze wg strategii r̂ ≈ α (maks. |r̂ − α| = 0,030). Próg udziału ALLC 0,5
   wypada przy r* = 0,314 dla c/b = 0,3 i r* = 0,507 dla c/b = 0,5 (odchylenie od c/b +0,014 i +0,007).
   Kierunek zgodny z regułą w 180/180 przebiegach poza pasem ±0,05 wokół progu. Implementacja
   reguły Hamiltona w wersji addytywnej (gra dawcy) działa.
2. **Rodziny nie utrzymują pokrewieństwa strategii.** Przy doborze krewnych zmierzone r̂ ≤ 0,11 nawet przy α = 0,9.
   Imitacja modelu z całej populacji szybko miesza strategie w rodzinach (bez reprodukcji nic nie odtwarza
   podobieństwa). Dobór krewnych daje więc partnerów z rodziny, ale nie z tą samą strategią.
   Przy dopasowaniu „own” ALLC zawsze wymiera, zgodnie z regułą (r̂ < c/b), ale progu nie da się wyznaczyć.
3. **„Inclusive” przesuwa próg do nominalnego r.** Przy c/b = 0,3 ALLC wygrywa od α ≈ 0,57 (interpolacja), mimo że
   zmierzone r̂ ≈ 0,01. To zgodne z rachunkiem: składnik krewnych w π daje ALLC przewagę `family_r`·α·b, więc ALLC
   wygrywa, gdy α > c / (`family_r`·b) = 0,6. Przy c/b = 0,5 ten próg wynosi 1,0 i ALLC nie wygrywa.
   Imitacja wg dopasowania łącznego działa jak preferencja (liczy nominalne r), nie jak selekcja na zmierzonym r̂;
   dlatego werdykt „inclusive” zależy od macierzy (parametr kontekstowy).
4. **Test znaku w interwałach jest słaby** (zgodność 0,44–0,78). W stanach bliskich 0 lub 1 zmiany udziału
   ALLC wynikają głównie z mutacji. Werdykt opiera się na wyniku końcowym, nie na teście znaku.

## P4 – reguła Hamiltona (well_mixed, ALLC/ALLD, gra dawcy)

Dobór `strategy` = kalibracja (partner z tą samą strategią z prawdopodobieństwem α, r̂ = α z konstrukcji); `family` = właściwy test z rodzinami (r̂ zmierzone). ALLC = udział na końcu (średnia z ostatniego okna); „ALLC wygrywa” = udział > 0,5. Test znaku = odsetek interwałów ewolucji, w których zmiana udziału ALLC ma znak r̂_k·b − c.

| dobór | c/b | dopasowanie | α | n | r̂ | r̂ − α | ALLC | ALLC wygrywa | stabilizacja | test znaku |
|---|---|---|---|---|---|---|---|---|---|---|
| family | 0.3 | inclusive | 0 | 10 | -0.005 ± 0.002 | -0.005 | 0.015 ± 0.006 | 0% | 80% | 0.61 ± 0.03 |
| family | 0.3 | inclusive | 0.1 | 10 | 0.004 ± 0.001 | -0.096 | 0.022 ± 0.010 | 0% | 60% | 0.60 ± 0.03 |
| family | 0.3 | inclusive | 0.2 | 10 | 0.007 ± 0.003 | -0.193 | 0.034 ± 0.015 | 0% | 50% | 0.58 ± 0.03 |
| family | 0.3 | inclusive | 0.3 | 10 | 0.009 ± 0.002 | -0.291 | 0.030 ± 0.011 | 0% | 20% | 0.58 ± 0.03 |
| family | 0.3 | inclusive | 0.4 | 10 | 0.009 ± 0.005 | -0.391 | 0.047 ± 0.039 | 0% | 20% | 0.60 ± 0.03 |
| family | 0.3 | inclusive | 0.5 | 10 | 0.006 ± 0.003 | -0.494 | 0.133 ± 0.098 | 0% | 10% | 0.57 ± 0.04 |
| family | 0.3 | inclusive | 0.6 | 10 | 0.006 ± 0.005 | -0.594 | 0.648 ± 0.205 | 70% | 0% | 0.49 ± 0.03 |
| family | 0.3 | inclusive | 0.7 | 10 | 0.015 ± 0.003 | -0.685 | 0.892 ± 0.045 | 100% | 0% | 0.46 ± 0.02 |
| family | 0.3 | inclusive | 0.8 | 10 | 0.033 ± 0.006 | -0.767 | 0.965 ± 0.031 | 100% | 0% | 0.44 ± 0.03 |
| family | 0.3 | inclusive | 0.9 | 10 | 0.054 ± 0.013 | -0.846 | 0.965 ± 0.024 | 100% | 10% | 0.44 ± 0.03 |
| family | 0.3 | own | 0 | 10 | -0.005 ± 0.002 | -0.005 | 0.015 ± 0.006 | 0% | 80% | 0.61 ± 0.03 |
| family | 0.3 | own | 0.1 | 10 | 0.006 ± 0.001 | -0.094 | 0.018 ± 0.008 | 0% | 70% | 0.61 ± 0.04 |
| family | 0.3 | own | 0.2 | 10 | 0.014 ± 0.003 | -0.186 | 0.017 ± 0.005 | 0% | 80% | 0.59 ± 0.04 |
| family | 0.3 | own | 0.3 | 10 | 0.022 ± 0.003 | -0.278 | 0.015 ± 0.006 | 0% | 40% | 0.59 ± 0.04 |
| family | 0.3 | own | 0.4 | 10 | 0.032 ± 0.004 | -0.368 | 0.013 ± 0.010 | 0% | 60% | 0.60 ± 0.05 |
| family | 0.3 | own | 0.5 | 10 | 0.042 ± 0.008 | -0.458 | 0.011 ± 0.005 | 0% | 70% | 0.61 ± 0.04 |
| family | 0.3 | own | 0.6 | 10 | 0.047 ± 0.006 | -0.553 | 0.019 ± 0.010 | 0% | 80% | 0.60 ± 0.05 |
| family | 0.3 | own | 0.7 | 10 | 0.056 ± 0.008 | -0.644 | 0.019 ± 0.008 | 0% | 40% | 0.59 ± 0.03 |
| family | 0.3 | own | 0.8 | 10 | 0.062 ± 0.010 | -0.738 | 0.014 ± 0.009 | 0% | 50% | 0.62 ± 0.03 |
| family | 0.3 | own | 0.9 | 10 | 0.068 ± 0.009 | -0.832 | 0.020 ± 0.012 | 0% | 50% | 0.60 ± 0.03 |
| family | 0.5 | inclusive | 0 | 10 | -0.005 ± 0.002 | -0.005 | 0.011 ± 0.004 | 0% | 90% | 0.62 ± 0.03 |
| family | 0.5 | inclusive | 0.1 | 10 | 0.009 ± 0.002 | -0.091 | 0.012 ± 0.005 | 0% | 70% | 0.63 ± 0.03 |
| family | 0.5 | inclusive | 0.2 | 10 | 0.019 ± 0.003 | -0.181 | 0.013 ± 0.004 | 0% | 90% | 0.61 ± 0.05 |
| family | 0.5 | inclusive | 0.3 | 10 | 0.025 ± 0.003 | -0.275 | 0.014 ± 0.006 | 0% | 50% | 0.60 ± 0.04 |
| family | 0.5 | inclusive | 0.4 | 10 | 0.032 ± 0.006 | -0.368 | 0.014 ± 0.012 | 0% | 80% | 0.60 ± 0.05 |
| family | 0.5 | inclusive | 0.5 | 10 | 0.037 ± 0.009 | -0.463 | 0.013 ± 0.006 | 0% | 70% | 0.59 ± 0.03 |
| family | 0.5 | inclusive | 0.6 | 10 | 0.033 ± 0.005 | -0.567 | 0.027 ± 0.015 | 0% | 30% | 0.59 ± 0.04 |
| family | 0.5 | inclusive | 0.7 | 10 | 0.030 ± 0.003 | -0.670 | 0.032 ± 0.012 | 0% | 20% | 0.61 ± 0.03 |
| family | 0.5 | inclusive | 0.8 | 10 | 0.024 ± 0.004 | -0.776 | 0.053 ± 0.027 | 0% | 20% | 0.58 ± 0.05 |
| family | 0.5 | inclusive | 0.9 | 10 | 0.016 ± 0.005 | -0.884 | 0.116 ± 0.055 | 0% | 10% | 0.57 ± 0.03 |
| family | 0.5 | own | 0 | 10 | -0.005 ± 0.002 | -0.005 | 0.011 ± 0.004 | 0% | 100% | 0.63 ± 0.03 |
| family | 0.5 | own | 0.1 | 10 | 0.011 ± 0.002 | -0.089 | 0.011 ± 0.005 | 0% | 80% | 0.65 ± 0.03 |
| family | 0.5 | own | 0.2 | 10 | 0.024 ± 0.004 | -0.176 | 0.010 ± 0.003 | 0% | 90% | 0.63 ± 0.05 |
| family | 0.5 | own | 0.3 | 10 | 0.037 ± 0.005 | -0.263 | 0.011 ± 0.007 | 0% | 80% | 0.61 ± 0.05 |
| family | 0.5 | own | 0.4 | 10 | 0.051 ± 0.008 | -0.349 | 0.009 ± 0.004 | 0% | 100% | 0.64 ± 0.06 |
| family | 0.5 | own | 0.5 | 10 | 0.067 ± 0.010 | -0.433 | 0.008 ± 0.003 | 0% | 80% | 0.63 ± 0.04 |
| family | 0.5 | own | 0.6 | 10 | 0.074 ± 0.010 | -0.526 | 0.013 ± 0.005 | 0% | 80% | 0.62 ± 0.04 |
| family | 0.5 | own | 0.7 | 10 | 0.085 ± 0.009 | -0.615 | 0.012 ± 0.004 | 0% | 70% | 0.63 ± 0.03 |
| family | 0.5 | own | 0.8 | 10 | 0.098 ± 0.008 | -0.702 | 0.009 ± 0.004 | 0% | 90% | 0.64 ± 0.04 |
| family | 0.5 | own | 0.9 | 10 | 0.110 ± 0.009 | -0.790 | 0.011 ± 0.006 | 0% | 80% | 0.64 ± 0.03 |
| strategy | 0.3 | own | 0 | 10 | -0.005 ± 0.002 | -0.005 | 0.015 ± 0.006 | 0% | 80% | 0.61 ± 0.03 |
| strategy | 0.3 | own | 0.1 | 10 | 0.094 ± 0.001 | -0.006 | 0.018 ± 0.010 | 0% | 60% | 0.59 ± 0.03 |
| strategy | 0.3 | own | 0.2 | 10 | 0.195 ± 0.001 | -0.005 | 0.046 ± 0.022 | 0% | 30% | 0.58 ± 0.04 |
| strategy | 0.3 | own | 0.3 | 10 | 0.297 ± 0.001 | -0.003 | 0.406 ± 0.181 | 30% | 0% | 0.53 ± 0.06 |
| strategy | 0.3 | own | 0.4 | 10 | 0.397 ± 0.001 | -0.003 | 0.942 ± 0.033 | 100% | 20% | 0.60 ± 0.04 |
| strategy | 0.3 | own | 0.5 | 10 | 0.495 ± 0.003 | -0.005 | 0.974 ± 0.013 | 100% | 40% | 0.62 ± 0.05 |
| strategy | 0.3 | own | 0.6 | 10 | 0.591 ± 0.004 | -0.009 | 0.981 ± 0.009 | 100% | 50% | 0.68 ± 0.03 |
| strategy | 0.3 | own | 0.7 | 10 | 0.686 ± 0.005 | -0.014 | 0.985 ± 0.005 | 100% | 70% | 0.70 ± 0.03 |
| strategy | 0.3 | own | 0.8 | 10 | 0.778 ± 0.005 | -0.022 | 0.986 ± 0.004 | 100% | 100% | 0.77 ± 0.04 |
| strategy | 0.3 | own | 0.9 | 10 | 0.870 ± 0.006 | -0.030 | 0.989 ± 0.004 | 100% | 100% | 0.78 ± 0.04 |
| strategy | 0.5 | own | 0 | 10 | -0.005 ± 0.002 | -0.005 | 0.011 ± 0.004 | 0% | 100% | 0.63 ± 0.03 |
| strategy | 0.5 | own | 0.1 | 10 | 0.091 ± 0.002 | -0.009 | 0.013 ± 0.006 | 0% | 70% | 0.61 ± 0.04 |
| strategy | 0.5 | own | 0.2 | 10 | 0.192 ± 0.002 | -0.008 | 0.023 ± 0.007 | 0% | 70% | 0.58 ± 0.04 |
| strategy | 0.5 | own | 0.3 | 10 | 0.294 ± 0.002 | -0.006 | 0.020 ± 0.010 | 0% | 50% | 0.59 ± 0.05 |
| strategy | 0.5 | own | 0.4 | 10 | 0.396 ± 0.001 | -0.004 | 0.041 ± 0.035 | 0% | 10% | 0.59 ± 0.02 |
| strategy | 0.5 | own | 0.5 | 10 | 0.498 ± 0.001 | -0.002 | 0.454 ± 0.156 | 40% | 0% | 0.51 ± 0.02 |
| strategy | 0.5 | own | 0.6 | 10 | 0.598 ± 0.001 | -0.002 | 0.942 ± 0.031 | 100% | 10% | 0.59 ± 0.04 |
| strategy | 0.5 | own | 0.7 | 10 | 0.696 ± 0.002 | -0.004 | 0.969 ± 0.022 | 100% | 40% | 0.63 ± 0.03 |
| strategy | 0.5 | own | 0.8 | 10 | 0.792 ± 0.002 | -0.008 | 0.981 ± 0.007 | 100% | 80% | 0.69 ± 0.02 |
| strategy | 0.5 | own | 0.9 | 10 | 0.884 ± 0.004 | -0.016 | 0.986 ± 0.005 | 100% | 80% | 0.73 ± 0.03 |

**P4 łącznie:**

- family, c/b = 0.3, inclusive: kierunek zgodny z regułą w 63/100 przebiegów (poza ±0.05 od progu; z r̂ > c/b: 0) → **warunkowo**; próg r* = 0.005 (odchylenie od c/b -0.295); r̂ ≈ α: NIE (maks. |r̂ − α| = 0.846)
- family, c/b = 0.3, own: kierunek zgodny z regułą w 100/100 przebiegów (poza ±0.05 od progu; z r̂ > c/b: 0) → **tak, tylko r̂ < c/b**; próg r* = brak przejścia (maks. średnie r̂ = 0.068); r̂ ≈ α: NIE (maks. |r̂ − α| = 0.832)
- family, c/b = 0.5, inclusive: kierunek zgodny z regułą w 100/100 przebiegów (poza ±0.05 od progu; z r̂ > c/b: 0) → **tak, tylko r̂ < c/b**; próg r* = brak przejścia (maks. średnie r̂ = 0.037); r̂ ≈ α: NIE (maks. |r̂ − α| = 0.884)
- family, c/b = 0.5, own: kierunek zgodny z regułą w 100/100 przebiegów (poza ±0.05 od progu; z r̂ > c/b: 0) → **tak, tylko r̂ < c/b**; próg r* = brak przejścia (maks. średnie r̂ = 0.110); r̂ ≈ α: NIE (maks. |r̂ − α| = 0.790)
- strategy, c/b = 0.3, own: kierunek zgodny z regułą w 90/90 przebiegów (poza ±0.05 od progu; z r̂ > c/b: 60) → **tak**; próg r* = 0.314 (odchylenie od c/b +0.014); r̂ ≈ α: tak (maks. |r̂ − α| = 0.030)
- strategy, c/b = 0.5, own: kierunek zgodny z regułą w 90/90 przebiegów (poza ±0.05 od progu; z r̂ > c/b: 40) → **tak**; próg r* = 0.507 (odchylenie od c/b +0.007); r̂ ≈ α: tak (maks. |r̂ − α| = 0.016)

### Tabela zbiorcza P4

| wariant | well_mixed / c/b = 0.3 | well_mixed / c/b = 0.5 | klasyfikacja |
|---|---|---|---|
| P4 family / inclusive | **warunkowo** | **tak, tylko r̂ < c/b** | parametr kontekstowy (zależy od: macierzy wypłat) |
| P4 family / own | **tak, tylko r̂ < c/b** | **tak, tylko r̂ < c/b** | stała kandydacka (tak, tylko r̂ < c/b) |
| P4 strategy / own | **tak** | **tak** | stała kandydacka (tak) |

