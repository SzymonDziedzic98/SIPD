# Etap 1 – werdykty (port Pythona)

Źródło: `plan_min_N200_r10.csv`, 403 przebiegów. Wartości: średnia ± odchylenie standardowe między powtórzeniami.

## P1 – oszuści stabilni w (0, 1), P2 – altruiści

| układ | macierz | N | prędkość | mutacja | n | gier/partnera | ALLD | udział D | ALLC | trend ALLD /10k | stabilizacja | P1 | P2 (część) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | PD_classic | 200 | 0.1 | 0 | 10 | 98.9 ± 4.0 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.000 ± 0.001 | 100% | nie | wymiera: tak |
| baseline | PD_classic | 200 | 0.1 | 0.01 | 10 | 95.6 ± 3.9 | 0.63 ± 0.03 | 0.83 ± 0.04 | 0.046 ± 0.022 | -0.008 ± 0.011 | 90% | tak | utrzymuje się: tak |
| baseline | snowdrift | 200 | 0.1 | 0 | 10 | 96.8 ± 1.7 | 0.99 ± 0.01 | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.020 ± 0.014 | 60% | nie | wymiera: tak |
| baseline | snowdrift | 200 | 0.1 | 0.01 | 10 | 96.3 ± 4.1 | 0.40 ± 0.06 | 0.62 ± 0.11 | 0.052 ± 0.016 | -0.016 ± 0.015 | 60% | warunkowo | utrzymuje się: tak |
| connected | PD_classic | 200 | 0.1 | 0.01 | 10 | 96.7 ± 1.9 | 0.62 ± 0.04 | 0.85 ± 0.05 | 0.045 ± 0.020 | -0.013 ± 0.014 | 70% | warunkowo | utrzymuje się: tak |
| fragmented | PD_classic | 200 | 0.1 | 0.01 | 10 | 125.2 ± 5.4 | 0.57 ± 0.06 | 0.78 ± 0.09 | 0.050 ± 0.014 | -0.009 ± 0.012 | 90% | tak | utrzymuje się: tak |
| well_mixed | PD_classic | 200 | 0.1 | 0 | 10 | 919.5 ± 0.1 | 0.40 ± 0.52 | 0.50 ± 0.52 | 0.000 ± 0.000 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| well_mixed | PD_classic | 200 | 0.1 | 0.01 | 10 | 919.5 ± 0.1 | 0.75 ± 0.27 | 0.88 ± 0.30 | 0.006 ± 0.009 | 0.033 ± 0.093 | 20% | nie | utrzymuje się: tak |
| well_mixed | snowdrift | 200 | 0.1 | 0 | 10 | 919.5 ± 0.1 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.255 ± 0.429 | 0.000 ± 0.000 | 100% | nie | wymiera: warunkowo |
| well_mixed | snowdrift | 200 | 0.1 | 0.01 | 10 | 919.6 ± 0.1 | 0.32 ± 0.01 | 0.34 ± 0.01 | 0.640 ± 0.011 | 0.000 ± 0.002 | 100% | tak | utrzymuje się: warunkowo |

**P2 łącznie** (obie części muszą się utrzymać):

- baseline, PD_classic, N=200, prędkość 0.1: **tak**
- baseline, snowdrift, N=200, prędkość 0.1: **tak**
- connected, PD_classic, N=200, prędkość 0.1: **tak**
- fragmented, PD_classic, N=200, prędkość 0.1: **tak**
- well_mixed, PD_classic, N=200, prędkość 0.1: **tak**
- well_mixed, snowdrift, N=200, prędkość 0.1: **warunkowo**

## P3 – limit Dunbara: spadek kooperacji (miara główna) i zysk oszustów (dodatkowa)

| układ | macierz | N | limit | n | różnych partnerów | limit działa | udział D | Δ udziału D vs brak limitu (95% CI) | ALLD / grę | zysk oszustów (95% CI) | TFT / grę |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | PD_classic | 200 | 0 | 10 | 5.3 ± 0.2 | — | 0.369 ± 0.072 | — | 1.102 ± 0.012 | — | 4.174 ± 0.078 |
| baseline | PD_classic | 200 | 5 | 10 | 5.3 ± 0.2 | 43% | 0.368 ± 0.072 | -0.000 [-0.063, +0.063] | 1.103 ± 0.012 | +0.001 [-0.010, +0.012] | 4.174 ± 0.078 |
| baseline | PD_classic | 200 | 15 | 10 | 5.3 ± 0.2 | 0% | 0.369 ± 0.072 | +0.000 [-0.063, +0.063] | 1.102 ± 0.012 | +0.000 [-0.011, +0.011] | 4.174 ± 0.078 |
| baseline | PD_classic | 200 | 50 | 10 | 5.3 ± 0.2 | 0% | 0.369 ± 0.072 | +0.000 [-0.063, +0.063] | 1.102 ± 0.012 | +0.000 [-0.011, +0.011] | 4.174 ± 0.078 |
| baseline | PD_classic | 200 | 150 | 10 | 5.3 ± 0.2 | 0% | 0.369 ± 0.072 | +0.000 [-0.063, +0.063] | 1.102 ± 0.012 | +0.000 [-0.011, +0.011] | 4.174 ± 0.078 |
| baseline | snowdrift | 200 | 0 | 10 | 5.3 ± 0.2 | — | 0.369 ± 0.072 | — | 0.051 ± 0.006 | — | 2.390 ± 0.058 |
| baseline | snowdrift | 200 | 5 | 10 | 5.3 ± 0.2 | 43% | 0.368 ± 0.072 | -0.000 [-0.063, +0.063] | 0.051 ± 0.006 | +0.000 [-0.005, +0.006] | 2.390 ± 0.058 |
| baseline | snowdrift | 200 | 15 | 10 | 5.3 ± 0.2 | 0% | 0.369 ± 0.072 | +0.000 [-0.063, +0.063] | 0.051 ± 0.006 | +0.000 [-0.005, +0.005] | 2.390 ± 0.058 |
| baseline | snowdrift | 200 | 50 | 10 | 5.3 ± 0.2 | 0% | 0.369 ± 0.072 | +0.000 [-0.063, +0.063] | 0.051 ± 0.006 | +0.000 [-0.005, +0.005] | 2.390 ± 0.058 |
| baseline | snowdrift | 200 | 150 | 10 | 5.3 ± 0.2 | 0% | 0.369 ± 0.072 | +0.000 [-0.063, +0.063] | 0.051 ± 0.006 | +0.000 [-0.005, +0.005] | 2.390 ± 0.058 |
| connected | PD_classic | 200 | 0 | 10 | 5.2 ± 0.2 | — | 0.352 ± 0.074 | — | 1.108 ± 0.007 | — | 4.233 ± 0.063 |
| connected | PD_classic | 200 | 5 | 10 | 5.2 ± 0.2 | 42% | 0.352 ± 0.074 | -0.000 [-0.065, +0.064] | 1.108 ± 0.007 | +0.001 [-0.005, +0.007] | 4.233 ± 0.063 |
| connected | PD_classic | 200 | 15 | 10 | 5.2 ± 0.2 | 0% | 0.352 ± 0.074 | +0.000 [-0.065, +0.065] | 1.108 ± 0.007 | +0.000 [-0.006, +0.006] | 4.233 ± 0.063 |
| connected | PD_classic | 200 | 50 | 10 | 5.2 ± 0.2 | 0% | 0.352 ± 0.074 | +0.000 [-0.065, +0.065] | 1.108 ± 0.007 | +0.000 [-0.006, +0.006] | 4.233 ± 0.063 |
| connected | PD_classic | 200 | 150 | 10 | 5.2 ± 0.2 | 0% | 0.352 ± 0.074 | +0.000 [-0.065, +0.065] | 1.108 ± 0.007 | +0.000 [-0.006, +0.006] | 4.233 ± 0.063 |
| fragmented | PD_classic | 200 | 0 | 10 | 4.7 ± 0.2 | — | 0.370 ± 0.074 | — | 1.089 ± 0.005 | — | 4.213 ± 0.070 |
| fragmented | PD_classic | 200 | 5 | 10 | 4.7 ± 0.2 | 34% | 0.370 ± 0.074 | -0.000 [-0.065, +0.064] | 1.090 ± 0.005 | +0.001 [-0.003, +0.006] | 4.213 ± 0.070 |
| fragmented | PD_classic | 200 | 15 | 10 | 4.7 ± 0.2 | 0% | 0.370 ± 0.074 | +0.000 [-0.065, +0.065] | 1.089 ± 0.005 | +0.000 [-0.005, +0.005] | 4.213 ± 0.070 |
| fragmented | PD_classic | 200 | 50 | 10 | 4.7 ± 0.2 | 0% | 0.370 ± 0.074 | +0.000 [-0.065, +0.065] | 1.089 ± 0.005 | +0.000 [-0.005, +0.005] | 4.213 ± 0.070 |
| fragmented | PD_classic | 200 | 150 | 10 | 4.7 ± 0.2 | 0% | 0.370 ± 0.074 | +0.000 [-0.065, +0.065] | 1.089 ± 0.005 | +0.000 [-0.005, +0.005] | 4.213 ± 0.070 |
| well_mixed | PD_classic | 200 | 0 | 10 | 199.0 ± 0.0 | — | 0.361 ± 0.001 | — | 1.035 ± 0.000 | — | 4.195 ± 0.001 |
| well_mixed | PD_classic | 200 | 5 | 10 | 199.0 ± 0.0 | 100% | 0.200 ± 0.001 | -0.161 [-0.162, -0.160] | 7.433 ± 0.004 | +6.398 [+6.396, +6.401] | 3.995 ± 0.001 |
| well_mixed | PD_classic | 200 | 15 | 10 | 199.0 ± 0.0 | 100% | 0.200 ± 0.001 | -0.160 [-0.161, -0.160] | 7.421 ± 0.004 | +6.386 [+6.383, +6.388] | 3.995 ± 0.001 |
| well_mixed | PD_classic | 200 | 50 | 10 | 199.0 ± 0.0 | 100% | 0.229 ± 0.001 | -0.132 [-0.132, -0.131] | 6.273 ± 0.003 | +5.238 [+5.236, +5.240] | 4.031 ± 0.001 |
| well_mixed | PD_classic | 200 | 150 | 10 | 199.0 ± 0.0 | 100% | 0.318 ± 0.001 | -0.043 [-0.044, -0.042] | 2.748 ± 0.002 | +1.713 [+1.712, +1.715] | 4.141 ± 0.001 |
| well_mixed | snowdrift | 200 | 0 | 10 | 199.0 ± 0.0 | — | 0.361 ± 0.001 | — | 0.017 ± 0.000 | — | 2.399 ± 0.000 |
| well_mixed | snowdrift | 200 | 5 | 10 | 199.0 ± 0.0 | 100% | 0.200 ± 0.001 | -0.161 [-0.162, -0.160] | 3.217 ± 0.002 | +3.199 [+3.198, +3.200] | 2.799 ± 0.000 |
| well_mixed | snowdrift | 200 | 15 | 10 | 199.0 ± 0.0 | 100% | 0.200 ± 0.001 | -0.160 [-0.161, -0.160] | 3.210 ± 0.002 | +3.193 [+3.192, +3.194] | 2.798 ± 0.000 |
| well_mixed | snowdrift | 200 | 50 | 10 | 199.0 ± 0.0 | 100% | 0.229 ± 0.001 | -0.132 [-0.132, -0.131] | 2.636 ± 0.002 | +2.619 [+2.618, +2.620] | 2.726 ± 0.000 |
| well_mixed | snowdrift | 200 | 150 | 10 | 199.0 ± 0.0 | 100% | 0.318 ± 0.001 | -0.043 [-0.044, -0.042] | 0.874 ± 0.001 | +0.857 [+0.856, +0.857] | 2.506 ± 0.000 |

**P3 łącznie:**

- baseline, PD_classic, N=200: spadek kooperacji **nie** (próg: brak); zysk oszustów **nie** (próg: brak)
- baseline, snowdrift, N=200: spadek kooperacji **nie** (próg: brak); zysk oszustów **nie** (próg: brak)
- connected, PD_classic, N=200: spadek kooperacji **nie** (próg: brak); zysk oszustów **nie** (próg: brak)
- fragmented, PD_classic, N=200: spadek kooperacji **nie** (próg: brak); zysk oszustów **nie** (próg: brak)
- well_mixed, PD_classic, N=200: spadek kooperacji **nie** (próg: brak; kooperacja rośnie); zysk oszustów **tak** (próg: limit ≤ 150)
- well_mixed, snowdrift, N=200: spadek kooperacji **nie** (próg: brak; kooperacja rośnie); zysk oszustów **tak** (próg: limit ≤ 150)

## Tabela zbiorcza – klasyfikacja

Kolumny: układ × macierz (× prędkość, jeśli w danych jest kilka). Komórka: werdykt i miara (średnia ± odchylenie między powtórzeniami).

| regularność | baseline / PD_classic | baseline / snowdrift | connected / PD_classic | fragmented / PD_classic | well_mixed / PD_classic | well_mixed / snowdrift | klasyfikacja |
|---|---|---|---|---|---|---|---|
| P1 | **tak** (ALLD 0.63 ± 0.03) | **warunkowo** (ALLD 0.40 ± 0.06) | **warunkowo** (ALLD 0.62 ± 0.04) | **tak** (ALLD 0.57 ± 0.06) | **nie** (ALLD 0.75 ± 0.27) | **tak** (ALLD 0.32 ± 0.01) | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat) |
| P2 | **tak** (ALLC 0.046 ± 0.022) | **tak** (ALLC 0.052 ± 0.016) | **tak** (ALLC 0.045 ± 0.020) | **tak** (ALLC 0.050 ± 0.014) | **tak** (ALLC 0.006 ± 0.009) | **warunkowo** (ALLC 0.640 ± 0.011) | parametr kontekstowy (zależy od: układu przestrzeni, macierzy wypłat) |
| P3 kooperacja | **nie** (ΔD@5 -0.000, próg: brak) | **nie** (ΔD@5 -0.000, próg: brak) | **nie** (ΔD@5 -0.000, próg: brak) | **nie** (ΔD@5 -0.000, próg: brak) | **nie** (ΔD@5 -0.161, próg: brak; kooperacja rośnie) | **nie** (ΔD@5 -0.161, próg: brak; kooperacja rośnie) | nie odtworzono |
| P3 zysk oszustów | **nie** (Δwypłaty ALLD@5 +0.001, próg: brak) | **nie** (Δwypłaty ALLD@5 +0.000, próg: brak) | **nie** (Δwypłaty ALLD@5 +0.001, próg: brak) | **nie** (Δwypłaty ALLD@5 +0.001, próg: brak) | **tak** (Δwypłaty ALLD@5 +6.398, próg: limit ≤ 150) | **tak** (Δwypłaty ALLD@5 +3.199, próg: limit ≤ 150) | parametr kontekstowy (zależy od: układu przestrzeni) |

## Interpretacja (plan minimalny, port Pythona)

Warunki: rdzeń `compat_core`, N = 200, prędkość 0,1, 10 powtórzeń, park syntetyczny 32 × 32, P1/P2 100 000
cykli, P3 20 000 cykli. Przebiegi wspólne dla PM2 i PM3 (ten sam seed i konfiguracja) liczone raz (403 z 463).

- **P1 – parametr kontekstowy.** Odtwarza się w PD na sieci baseline (ALLD 0,63) i fragmented (0,57); na
  connected i w snowdrifcie na baseline warunkowo (część przebiegów bez stabilizacji); w `well_mixed`
  PD nie (wynik dwubiegunowy: fiksacja ALLD albo jej brak), snowdrift tak.
- **P2 – parametr kontekstowy (od macierzy).** Utrzymuje się wszędzie poza snowdriftem w `well_mixed`, gdzie
  ALLC dominuje (0,64) zamiast wymierać – zgodnie z teorią snowdriftu.
- **P3 w przestrzeni jest nietestowalne przy prędkości 0,1.** Agent spotyka w 20 000 cykli tylko ok. 5
  różnych partnerów (4,7–5,3), więc limit 5 obejmuje ok. 40% agentów, a limity 15–150 nikogo. Efekt P3
  pojawia się tylko w `well_mixed` (199 partnerów): zysk oszustów tak (próg ≤ 150), spadek kooperacji nie
  (kooperacja rośnie).
- **Konflikt P1–P3 przez mobilność:** P1 wymaga niskiej mobilności (powtarzalni partnerzy), P3 wymaga wielu
  różnych partnerów. Przy jednej wspólnej prędkości oba nie są jednocześnie testowalne w przestrzeni.
- **Heatmapa stabilności spotkań** (`heatmap_spotkan_PM4.svg`) przy prędkości 0,1 jest nasycona (udział
  spotkań powtórnych ok. 0,99 we wszystkich wariantach) – pokazuje głównie, gdzie toczą się gry.
