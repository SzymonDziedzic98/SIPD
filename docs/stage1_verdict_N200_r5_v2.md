# Etap 1 – werdykty (port Pythona)

Źródło: `compat_results_N200_r5_v2.csv`, 240 przebiegów. Wartości: średnia ± odchylenie standardowe między powtórzeniami.

## P1 – oszuści stabilni w (0, 1), P2 – altruiści

| układ | macierz | N | prędkość | mutacja | n | gier/partnera | ALLD | udział D | ALLC | stabilizacja | P1 | P2 (część) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| przestrzeń | PD_classic | 200 | 0.1 | 0 | 5 | 73.8 ± 1.4 | 0.84 ± 0.05 | 0.92 ± 0.03 | 0.024 ± 0.010 | 0% | nie | wymiera: nie |
| przestrzeń | PD_classic | 200 | 0.1 | 0.01 | 5 | 72.9 ± 2.6 | 0.61 ± 0.04 | 0.82 ± 0.05 | 0.052 ± 0.021 | 0% | nie | utrzymuje się: tak |
| przestrzeń | PD_classic | 200 | 0.5 | 0 | 5 | 20.5 ± 0.2 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| przestrzeń | PD_classic | 200 | 0.5 | 0.01 | 5 | 20.1 ± 0.2 | 0.88 ± 0.02 | 0.97 ± 0.01 | 0.018 ± 0.007 | 0% | nie | utrzymuje się: tak |
| przestrzeń | PD_classic | 200 | 2 | 0 | 5 | 7.7 ± 0.2 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| przestrzeń | PD_classic | 200 | 2 | 0.01 | 5 | 7.8 ± 0.1 | 0.91 ± 0.02 | 0.97 ± 0.01 | 0.011 ± 0.005 | 40% | nie | utrzymuje się: tak |
| przestrzeń | snowdrift | 200 | 0.1 | 0 | 5 | 75.1 ± 3.9 | 0.55 ± 0.10 | 0.69 ± 0.10 | 0.056 ± 0.036 | 0% | nie | wymiera: nie |
| przestrzeń | snowdrift | 200 | 0.1 | 0.01 | 5 | 74.9 ± 2.8 | 0.43 ± 0.06 | 0.62 ± 0.06 | 0.065 ± 0.017 | 0% | nie | utrzymuje się: tak |
| przestrzeń | snowdrift | 200 | 0.5 | 0 | 5 | 20.2 ± 0.6 | 0.96 ± 0.02 | 0.99 ± 0.01 | 0.000 ± 0.000 | 0% | nie | wymiera: tak |
| przestrzeń | snowdrift | 200 | 0.5 | 0.01 | 5 | 20.1 ± 0.5 | 0.73 ± 0.03 | 0.89 ± 0.04 | 0.024 ± 0.013 | 20% | nie | utrzymuje się: tak |
| przestrzeń | snowdrift | 200 | 2 | 0 | 5 | 7.8 ± 0.2 | 0.92 ± 0.03 | 0.97 ± 0.01 | 0.000 ± 0.000 | 0% | nie | wymiera: tak |
| przestrzeń | snowdrift | 200 | 2 | 0.01 | 5 | 7.8 ± 0.1 | 0.60 ± 0.09 | 0.78 ± 0.08 | 0.034 ± 0.015 | 0% | nie | utrzymuje się: tak |
| przestrzeń | weak_PD | 200 | 0.1 | 0 | 5 | 73.0 ± 1.7 | 0.65 ± 0.02 | 0.81 ± 0.06 | 0.016 ± 0.013 | 0% | nie | wymiera: nie |
| przestrzeń | weak_PD | 200 | 0.1 | 0.01 | 5 | 72.7 ± 2.9 | 0.40 ± 0.07 | 0.65 ± 0.12 | 0.070 ± 0.030 | 0% | nie | utrzymuje się: tak |
| przestrzeń | weak_PD | 200 | 0.5 | 0 | 5 | 20.6 ± 0.5 | 0.98 ± 0.01 | 1.00 ± 0.00 | 0.000 ± 0.000 | 40% | nie | wymiera: tak |
| przestrzeń | weak_PD | 200 | 0.5 | 0.01 | 5 | 20.3 ± 0.8 | 0.78 ± 0.04 | 0.93 ± 0.03 | 0.021 ± 0.010 | 0% | nie | utrzymuje się: tak |
| przestrzeń | weak_PD | 200 | 2 | 0 | 5 | 7.7 ± 0.1 | 1.00 ± 0.01 | 1.00 ± 0.00 | 0.000 ± 0.000 | 100% | nie | wymiera: tak |
| przestrzeń | weak_PD | 200 | 2 | 0.01 | 5 | 7.6 ± 0.1 | 0.79 ± 0.03 | 0.93 ± 0.02 | 0.015 ± 0.005 | 0% | nie | utrzymuje się: tak |
| well_mixed | PD_classic | 200 | 2 | 0 | 5 | 183.9 ± 0.0 | 0.39 ± 0.54 | 0.41 ± 0.54 | 0.000 ± 0.000 | 40% | nie | wymiera: tak |
| well_mixed | PD_classic | 200 | 2 | 0.01 | 5 | 183.9 ± 0.0 | 0.67 ± 0.27 | 0.88 ± 0.20 | 0.016 ± 0.031 | 0% | nie | utrzymuje się: tak |
| well_mixed | snowdrift | 200 | 2 | 0 | 5 | 183.9 ± 0.0 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.263 ± 0.327 | 100% | nie | wymiera: warunkowo |
| well_mixed | snowdrift | 200 | 2 | 0.01 | 5 | 183.9 ± 0.0 | 0.19 ± 0.17 | 0.20 ± 0.18 | 0.458 ± 0.263 | 20% | nie | utrzymuje się: warunkowo |
| well_mixed | weak_PD | 200 | 2 | 0 | 5 | 183.9 ± 0.0 | 0.35 ± 0.48 | 0.38 ± 0.52 | 0.067 ± 0.149 | 80% | nie | wymiera: tak |
| well_mixed | weak_PD | 200 | 2 | 0.01 | 5 | 183.9 ± 0.0 | 0.48 ± 0.28 | 0.60 ± 0.32 | 0.046 ± 0.059 | 0% | nie | utrzymuje się: tak |

**P2 łącznie** (obie części muszą się utrzymać):

- przestrzeń, PD_classic, N=200, prędkość 0.1: **warunkowo**
- przestrzeń, PD_classic, N=200, prędkość 0.5: **tak**
- przestrzeń, PD_classic, N=200, prędkość 2: **tak**
- przestrzeń, snowdrift, N=200, prędkość 0.1: **warunkowo**
- przestrzeń, snowdrift, N=200, prędkość 0.5: **tak**
- przestrzeń, snowdrift, N=200, prędkość 2: **tak**
- przestrzeń, weak_PD, N=200, prędkość 0.1: **warunkowo**
- przestrzeń, weak_PD, N=200, prędkość 0.5: **tak**
- przestrzeń, weak_PD, N=200, prędkość 2: **tak**
- well_mixed, PD_classic, N=200, prędkość 2: **tak**
- well_mixed, snowdrift, N=200, prędkość 2: **warunkowo**
- well_mixed, weak_PD, N=200, prędkość 2: **tak**

## P3 – limit Dunbara: zysk oszustów

| układ | macierz | N | limit | n | różnych partnerów | limit działa | ALLD / grę | zysk vs brak limitu (95% CI) | TFT / grę | udział D |
|---|---|---|---|---|---|---|---|---|---|---|
| przestrzeń | PD_classic | 200 | 0 | 5 | 59.5 ± 0.8 | — | 1.844 ± 0.012 | — | 4.181 ± 0.036 | 0.328 ± 0.016 |
| przestrzeń | PD_classic | 200 | 5 | 5 | 59.5 ± 0.8 | 100% | 2.258 ± 0.013 | +0.414 [+0.398, +0.429] | 4.168 ± 0.036 | 0.314 ± 0.016 |
| przestrzeń | PD_classic | 200 | 15 | 5 | 59.5 ± 0.8 | 100% | 2.015 ± 0.014 | +0.170 [+0.154, +0.186] | 4.176 ± 0.036 | 0.320 ± 0.016 |
| przestrzeń | PD_classic | 200 | 50 | 5 | 59.5 ± 0.8 | 82% | 1.854 ± 0.014 | +0.009 [-0.007, +0.026] | 4.181 ± 0.036 | 0.327 ± 0.016 |
| przestrzeń | snowdrift | 200 | 0 | 5 | 59.5 ± 0.8 | — | 0.422 ± 0.006 | — | 2.458 ± 0.024 | 0.328 ± 0.016 |
| przestrzeń | snowdrift | 200 | 5 | 5 | 59.5 ± 0.8 | 100% | 0.629 ± 0.006 | +0.207 [+0.199, +0.214] | 2.484 ± 0.024 | 0.314 ± 0.016 |
| przestrzeń | snowdrift | 200 | 15 | 5 | 59.5 ± 0.8 | 100% | 0.507 ± 0.007 | +0.085 [+0.077, +0.093] | 2.469 ± 0.024 | 0.320 ± 0.016 |
| przestrzeń | snowdrift | 200 | 50 | 5 | 59.5 ± 0.8 | 82% | 0.427 ± 0.007 | +0.005 [-0.003, +0.013] | 2.459 ± 0.024 | 0.327 ± 0.016 |
| przestrzeń | weak_PD | 200 | 0 | 5 | 59.5 ± 0.8 | — | 0.169 ± 0.002 | — | 0.802 ± 0.009 | 0.328 ± 0.016 |
| przestrzeń | weak_PD | 200 | 5 | 5 | 59.5 ± 0.8 | 100% | 0.252 ± 0.003 | +0.083 [+0.080, +0.086] | 0.802 ± 0.009 | 0.314 ± 0.016 |
| przestrzeń | weak_PD | 200 | 15 | 5 | 59.5 ± 0.8 | 100% | 0.203 ± 0.003 | +0.034 [+0.031, +0.037] | 0.802 ± 0.009 | 0.320 ± 0.016 |
| przestrzeń | weak_PD | 200 | 50 | 5 | 59.5 ± 0.8 | 82% | 0.171 ± 0.003 | +0.002 [-0.001, +0.005] | 0.802 ± 0.009 | 0.327 ± 0.016 |
| well_mixed | PD_classic | 200 | 0 | 5 | 199.0 ± 0.0 | — | 1.035 ± 0.000 | — | 4.195 ± 0.000 | 0.361 ± 0.001 |
| well_mixed | PD_classic | 200 | 5 | 5 | 199.0 ± 0.0 | 100% | 7.433 ± 0.003 | +6.398 [+6.395, +6.400] | 3.995 ± 0.001 | 0.200 ± 0.001 |
| well_mixed | PD_classic | 200 | 15 | 5 | 199.0 ± 0.0 | 100% | 7.420 ± 0.003 | +6.385 [+6.382, +6.388] | 3.995 ± 0.001 | 0.200 ± 0.001 |
| well_mixed | PD_classic | 200 | 50 | 5 | 199.0 ± 0.0 | 100% | 6.272 ± 0.002 | +5.237 [+5.235, +5.239] | 4.031 ± 0.001 | 0.229 ± 0.001 |
| well_mixed | snowdrift | 200 | 0 | 5 | 199.0 ± 0.0 | — | 0.017 ± 0.000 | — | 2.399 ± 0.000 | 0.361 ± 0.001 |
| well_mixed | snowdrift | 200 | 5 | 5 | 199.0 ± 0.0 | 100% | 3.216 ± 0.001 | +3.199 [+3.198, +3.200] | 2.799 ± 0.000 | 0.200 ± 0.001 |
| well_mixed | snowdrift | 200 | 15 | 5 | 199.0 ± 0.0 | 100% | 3.210 ± 0.002 | +3.193 [+3.191, +3.194] | 2.798 ± 0.000 | 0.200 ± 0.001 |
| well_mixed | snowdrift | 200 | 50 | 5 | 199.0 ± 0.0 | 100% | 2.636 ± 0.001 | +2.619 [+2.617, +2.620] | 2.726 ± 0.000 | 0.229 ± 0.001 |
| well_mixed | weak_PD | 200 | 0 | 5 | 199.0 ± 0.0 | — | 0.007 ± 0.000 | — | 0.799 ± 0.000 | 0.361 ± 0.001 |
| well_mixed | weak_PD | 200 | 5 | 5 | 199.0 ± 0.0 | 100% | 1.287 ± 0.001 | +1.280 [+1.279, +1.280] | 0.799 ± 0.000 | 0.200 ± 0.001 |
| well_mixed | weak_PD | 200 | 15 | 5 | 199.0 ± 0.0 | 100% | 1.284 ± 0.001 | +1.277 [+1.276, +1.278] | 0.799 ± 0.000 | 0.200 ± 0.001 |
| well_mixed | weak_PD | 200 | 50 | 5 | 199.0 ± 0.0 | 100% | 1.054 ± 0.000 | +1.047 [+1.047, +1.048] | 0.799 ± 0.000 | 0.229 ± 0.001 |

**P3 łącznie:**

- przestrzeń, PD_classic, N=200: **tak** (próg: limit ≤ 15)
- przestrzeń, snowdrift, N=200: **tak** (próg: limit ≤ 15)
- przestrzeń, weak_PD, N=200: **tak** (próg: limit ≤ 15)
- well_mixed, PD_classic, N=200: **tak** (próg: limit ≤ 50)
- well_mixed, snowdrift, N=200: **tak** (próg: limit ≤ 50)
- well_mixed, weak_PD, N=200: **tak** (próg: limit ≤ 50)

## Analiza szeregów czasowych (P1)

W konfiguracjach z udziałem ALLD wewnątrz przedziału udział ALLD pod koniec 20 000 cykli nadal
rośnie (+0,01 do +0,03 na 1000 cykli), więc przebiegi są za krótkie; to dryf, nie szum.

Długie przebiegi (`web/p1_long_check.py`: 100 000 cykli, prędkość 0,1, mutacja 0,01, N = 200,
2 seedy na macierz), średni udział ALLD w oknach 10 000 cykli:

| macierz | seed | 0–10k | 10–20k | 20–30k | 30–40k | … | 90–100k | udział D (koniec) |
|---|---|---|---|---|---|---|---|---|
| PD | 11 | 0,35 | 0,64 | 0,67 | 0,68 | 0,60–0,71 | 0,60 | 0,90 |
| PD | 22 | 0,39 | 0,63 | 0,61 | 0,65 | 0,59–0,67 | 0,62 | 0,94 |
| słaby PD | 11 | 0,25 | 0,37 | 0,45 | 0,50 | 0,40–0,45 | 0,41 | 0,57 |
| słaby PD | 22 | 0,15 | 0,30 | 0,45 | 0,44 | 0,42–0,49 | 0,49 | 0,85 |
| snowdrift | 11 | 0,29 | 0,41 | 0,40 | 0,47 | 0,42–0,51 | 0,39 | 0,59 |
| snowdrift | 22 | 0,18 | 0,33 | 0,44 | 0,44 | 0,44–0,49 | 0,44 | 0,66 |

Po ok. 30 000 cykli udział ALLD przestaje rosnąć i waha się o ok. ±0,05 wokół poziomu wewnątrz (0, 1),
co odpowiada P1. Kryterium stabilizacji (okna 1000 cykli, ε = 0,02) nie jest jednak spełnione,
bo wahania między oknami 1000 cykli są większe niż ε.
