# Plan minimalny – tabela zbiorcza (port Pythona, N = 200, 10 powtórzeń)

Łączy `results/plan_min_N200_r10.csv` (prędkość 0,1: P1, P2, P3) i `results/plan_min_speed2_N200_r10.csv`
(prędkość 2: P3). Przebiegi wspólne dla kilku eksperymentów liczone raz. Szczegółowe tabele:
`plan_min_verdict_N200_r10.md`, `plan_min_speed2_verdict_N200_r10.md`.

## Tabela zbiorcza – klasyfikacja

Kolumny: układ × macierz (× prędkość, jeśli w danych jest kilka). Komórka: werdykt i miara (średnia ± odchylenie między powtórzeniami).

| regularność | baseline / PD_classic / 0.1 | baseline / PD_classic / 2.0 | baseline / snowdrift / 0.1 | baseline / snowdrift / 2.0 | connected / PD_classic / 0.1 | connected / PD_classic / 2.0 | fragmented / PD_classic / 0.1 | fragmented / PD_classic / 2.0 | well_mixed / PD_classic / 0.1 | well_mixed / snowdrift / 0.1 | klasyfikacja |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | **tak** (ALLD 0.63 ± 0.03) | — | **warunkowo** (ALLD 0.40 ± 0.06) | — | **warunkowo** (ALLD 0.62 ± 0.04) | — | **tak** (ALLD 0.57 ± 0.06) | — | **nie** (ALLD 0.75 ± 0.27) | **tak** (ALLD 0.32 ± 0.01) | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat) |
| P2 | **tak** (ALLC 0.046 ± 0.022) | — | **tak** (ALLC 0.052 ± 0.016) | — | **tak** (ALLC 0.045 ± 0.020) | — | **tak** (ALLC 0.050 ± 0.014) | — | **tak** (ALLC 0.006 ± 0.009) | **warunkowo** (ALLC 0.640 ± 0.011) | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat) |
| P3 kooperacja | **nie** (ΔD@5 -0.000, próg: brak) | **nie** (ΔD@5 -0.015, próg: brak) | **nie** (ΔD@5 -0.000, próg: brak) | **nie** (ΔD@5 -0.015, próg: brak) | **nie** (ΔD@5 -0.000, próg: brak) | **nie** (ΔD@5 -0.016, próg: brak; kooperacja rośnie) | **nie** (ΔD@5 -0.000, próg: brak) | **nie** (ΔD@5 -0.013, próg: brak; kooperacja rośnie) | **nie** (ΔD@5 -0.161, próg: brak; kooperacja rośnie) | **nie** (ΔD@5 -0.161, próg: brak; kooperacja rośnie) | nie odtworzono |
| P3 zysk oszustów | **nie** (Δwypłaty ALLD@5 +0.001, próg: brak) | **tak** (Δwypłaty ALLD@5 +0.416, próg: limit ≤ 15) | **nie** (Δwypłaty ALLD@5 +0.000, próg: brak) | **tak** (Δwypłaty ALLD@5 +0.208, próg: limit ≤ 15) | **nie** (Δwypłaty ALLD@5 +0.001, próg: brak) | **tak** (Δwypłaty ALLD@5 +0.435, próg: limit ≤ 15) | **nie** (Δwypłaty ALLD@5 +0.001, próg: brak) | **tak** (Δwypłaty ALLD@5 +0.373, próg: limit ≤ 15) | **tak** (Δwypłaty ALLD@5 +6.398, próg: limit ≤ 150) | **tak** (Δwypłaty ALLD@5 +3.199, próg: limit ≤ 150) | parametr kontekstowy (zależy od: układu przestrzeni, mobilności (prędkość)) |


## Wnioski

- **P1 (stabilny udział oszustów)** odtwarza się tylko przy niskiej mobilności (prędkość 0,1): w PD na
  baseline i fragmented tak, na connected i w snowdrifcie warunkowo; w `well_mixed` zależy od macierzy.
- **P2 (altruiści)** utrzymuje się wszędzie poza snowdriftem w `well_mixed` (tam ALLC dominuje).
- **P3 jako spadek kooperacji – nie odtworzono** w żadnej konfiguracji; przy limicie kooperacja nie spada
  (w `well_mixed` i przy prędkości 2 na connected/fragmented nawet lekko rośnie).
- **P3 jako zysk oszustów** – tak przy prędkości 2 na wszystkich trzech wariantach sieci i obu macierzach
  (próg: limit ≤ 15) oraz w `well_mixed`; przy prędkości 0,1 nie, bo agent ma tylko ok. 5 różnych partnerów.
  Czynnik rozstrzygający to mobilność, nie wariant sieci.
- **Konflikt P1–P3 przez mobilność:** P1 potrzebuje powtarzalnych partnerów (niska mobilność), P3 wielu
  różnych partnerów (wysoka mobilność). Wariant sieci zmienia werdykty słabiej niż mobilność.
- **Stabilność spotkań** (`heatmap_spotkan_PM4_speed2*.svg`): przy prędkości 2 udział spotkań powtórnych
  0,87 (baseline, connected) i 0,90 (fragmented); środek parku bardziej „mieszający” niż brzegi.
  Przy prędkości 0,1 metryka jest nasycona (0,99).
