# Etap 1 – werdykty (port Pythona)

Źródło: `plan_min_speed2_N200_r10.csv`, 203 przebiegów. Wartości: średnia ± odchylenie standardowe między powtórzeniami.

## P3 – limit Dunbara: spadek kooperacji (miara główna) i zysk oszustów (dodatkowa)

| układ | macierz | N | limit | n | różnych partnerów | limit działa | udział D | Δ udziału D vs brak limitu (95% CI) | ALLD / grę | zysk oszustów (95% CI) | TFT / grę |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | PD_classic | 200 | 0 | 10 | 59.9 ± 1.0 | — | 0.338 ± 0.020 | — | 1.855 ± 0.018 | — | 4.176 ± 0.027 |
| baseline | PD_classic | 200 | 5 | 10 | 59.9 ± 1.0 | 100% | 0.323 ± 0.019 | -0.015 [-0.032, +0.003] | 2.271 ± 0.023 | +0.416 [+0.397, +0.434] | 4.163 ± 0.027 |
| baseline | PD_classic | 200 | 15 | 10 | 59.9 ± 1.0 | 100% | 0.330 ± 0.019 | -0.008 [-0.025, +0.010] | 2.026 ± 0.022 | +0.171 [+0.153, +0.189] | 4.171 ± 0.027 |
| baseline | PD_classic | 200 | 50 | 10 | 59.9 ± 1.0 | 83% | 0.336 ± 0.020 | -0.001 [-0.019, +0.016] | 1.865 ± 0.020 | +0.010 [-0.007, +0.027] | 4.176 ± 0.027 |
| baseline | PD_classic | 200 | 150 | 10 | 59.9 ± 1.0 | 0% | 0.338 ± 0.020 | +0.000 [-0.018, +0.018] | 1.855 ± 0.018 | +0.000 [-0.016, +0.016] | 4.176 ± 0.027 |
| baseline | snowdrift | 200 | 0 | 10 | 59.9 ± 1.0 | — | 0.338 ± 0.020 | — | 0.427 ± 0.009 | — | 2.456 ± 0.019 |
| baseline | snowdrift | 200 | 5 | 10 | 59.9 ± 1.0 | 100% | 0.323 ± 0.019 | -0.015 [-0.032, +0.003] | 0.635 ± 0.011 | +0.208 [+0.199, +0.217] | 2.481 ± 0.018 |
| baseline | snowdrift | 200 | 15 | 10 | 59.9 ± 1.0 | 100% | 0.330 ± 0.019 | -0.008 [-0.025, +0.010] | 0.513 ± 0.011 | +0.086 [+0.077, +0.095] | 2.466 ± 0.018 |
| baseline | snowdrift | 200 | 50 | 10 | 59.9 ± 1.0 | 83% | 0.336 ± 0.020 | -0.001 [-0.019, +0.016] | 0.433 ± 0.010 | +0.005 [-0.004, +0.014] | 2.456 ± 0.019 |
| baseline | snowdrift | 200 | 150 | 10 | 59.9 ± 1.0 | 0% | 0.338 ± 0.020 | +0.000 [-0.018, +0.018] | 0.427 ± 0.009 | +0.000 [-0.008, +0.008] | 2.456 ± 0.019 |
| connected | PD_classic | 200 | 0 | 10 | 60.4 ± 1.2 | — | 0.338 ± 0.016 | — | 1.857 ± 0.035 | — | 4.169 ± 0.017 |
| connected | PD_classic | 200 | 5 | 10 | 60.4 ± 1.2 | 100% | 0.322 ± 0.016 | -0.016 [-0.030, -0.002] | 2.291 ± 0.037 | +0.435 [+0.403, +0.466] | 4.155 ± 0.017 |
| connected | PD_classic | 200 | 15 | 10 | 60.4 ± 1.2 | 100% | 0.329 ± 0.016 | -0.009 [-0.023, +0.005] | 2.031 ± 0.036 | +0.174 [+0.143, +0.205] | 4.163 ± 0.017 |
| connected | PD_classic | 200 | 50 | 10 | 60.4 ± 1.2 | 81% | 0.337 ± 0.016 | -0.001 [-0.015, +0.012] | 1.867 ± 0.036 | +0.010 [-0.021, +0.042] | 4.169 ± 0.017 |
| connected | PD_classic | 200 | 150 | 10 | 60.4 ± 1.2 | 0% | 0.338 ± 0.016 | +0.000 [-0.014, +0.014] | 1.857 ± 0.035 | +0.000 [-0.031, +0.031] | 4.169 ± 0.017 |
| fragmented | PD_classic | 200 | 0 | 10 | 49.2 ± 1.7 | — | 0.357 ± 0.014 | — | 1.652 ± 0.031 | — | 4.185 ± 0.028 |
| fragmented | PD_classic | 200 | 5 | 10 | 49.2 ± 1.7 | 100% | 0.344 ± 0.014 | -0.013 [-0.025, -0.000] | 2.025 ± 0.037 | +0.373 [+0.342, +0.403] | 4.174 ± 0.029 |
| fragmented | PD_classic | 200 | 15 | 10 | 49.2 ± 1.7 | 100% | 0.351 ± 0.014 | -0.005 [-0.018, +0.007] | 1.767 ± 0.035 | +0.115 [+0.086, +0.144] | 4.182 ± 0.028 |
| fragmented | PD_classic | 200 | 50 | 10 | 49.2 ± 1.7 | 46% | 0.356 ± 0.014 | -0.000 [-0.013, +0.012] | 1.654 ± 0.032 | +0.001 [-0.026, +0.029] | 4.185 ± 0.028 |
| fragmented | PD_classic | 200 | 150 | 10 | 49.2 ± 1.7 | 0% | 0.357 ± 0.014 | +0.000 [-0.013, +0.013] | 1.652 ± 0.031 | +0.000 [-0.028, +0.028] | 4.185 ± 0.028 |

**P3 łącznie:**

- baseline, PD_classic, N=200: spadek kooperacji **nie** (próg: brak); zysk oszustów **tak** (próg: limit ≤ 15)
- baseline, snowdrift, N=200: spadek kooperacji **nie** (próg: brak); zysk oszustów **tak** (próg: limit ≤ 15)
- connected, PD_classic, N=200: spadek kooperacji **nie** (próg: brak; kooperacja rośnie); zysk oszustów **tak** (próg: limit ≤ 15)
- fragmented, PD_classic, N=200: spadek kooperacji **nie** (próg: brak; kooperacja rośnie); zysk oszustów **tak** (próg: limit ≤ 15)

## Tabela zbiorcza – klasyfikacja

Kolumny: układ × macierz (× prędkość, jeśli w danych jest kilka). Komórka: werdykt i miara (średnia ± odchylenie między powtórzeniami).

| regularność | baseline / PD_classic | baseline / snowdrift | connected / PD_classic | fragmented / PD_classic | klasyfikacja |
|---|---|---|---|---|---|
| P3 kooperacja | **nie** (ΔD@5 -0.015, próg: brak) | **nie** (ΔD@5 -0.015, próg: brak) | **nie** (ΔD@5 -0.016, próg: brak; kooperacja rośnie) | **nie** (ΔD@5 -0.013, próg: brak; kooperacja rośnie) | nie odtworzono |
| P3 zysk oszustów | **tak** (Δwypłaty ALLD@5 +0.416, próg: limit ≤ 15) | **tak** (Δwypłaty ALLD@5 +0.208, próg: limit ≤ 15) | **tak** (Δwypłaty ALLD@5 +0.435, próg: limit ≤ 15) | **tak** (Δwypłaty ALLD@5 +0.373, próg: limit ≤ 15) | stała kandydacka (tak) |

