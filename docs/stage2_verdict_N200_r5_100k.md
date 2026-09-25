# Etap 1 – werdykty (port Pythona)

Źródło: `compat_results_S2_N200_r5_100k.csv`, 120 przebiegów. Wartości: średnia ± odchylenie standardowe między powtórzeniami.

## Etap 2 – zestawienia parami (ewolucja + limit Dunbara)

| macierz | mutacja | limit | n | limit działa | ALLD | Δ ALLD vs brak limitu (95% CI) | udział D | ALLC | trend ALLD /10k | stabilizacja | P1 | P2 (część) | P3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PD_classic | 0 | 0 | 5 | — | 1.00 ± 0.00 | — | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.001 ± 0.001 | 100% | — | wymiera: tak | — |
| PD_classic | 0 | 5 | 5 | 100% | 1.00 ± 0.00 | +0.000 [+0.000, +0.000] | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.001 ± 0.001 | 100% | — | wymiera: tak | brak efektu |
| PD_classic | 0 | 15 | 5 | 79% | 1.00 ± 0.00 | +0.000 [+0.000, +0.000] | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.001 ± 0.001 | 100% | — | wymiera: tak | brak efektu |
| PD_classic | 0 | 50 | 5 | 0% | 1.00 ± 0.00 | +0.000 [+0.000, +0.000] | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.001 ± 0.001 | 100% | — | wymiera: tak | brak efektu |
| PD_classic | 0.01 | 0 | 5 | — | 0.62 ± 0.04 | — | 0.82 ± 0.03 | 0.037 ± 0.019 | -0.008 ± 0.008 | 100% | tak | utrzymuje się: tak | — |
| PD_classic | 0.01 | 5 | 5 | 100% | 0.70 ± 0.05 | +0.081 [+0.024, +0.138] | 0.88 ± 0.11 | 0.036 ± 0.017 | 0.010 ± 0.007 | 100% | tak | utrzymuje się: tak | tak |
| PD_classic | 0.01 | 15 | 5 | 79% | 0.64 ± 0.03 | +0.022 [-0.018, +0.062] | 0.89 ± 0.04 | 0.049 ± 0.008 | -0.006 ± 0.018 | 80% | tak | utrzymuje się: tak | brak efektu |
| PD_classic | 0.01 | 50 | 5 | 0% | 0.62 ± 0.04 | +0.000 [-0.044, +0.044] | 0.82 ± 0.03 | 0.037 ± 0.019 | -0.008 ± 0.008 | 100% | tak | utrzymuje się: tak | brak efektu |
| snowdrift | 0 | 0 | 5 | — | 0.99 ± 0.02 | — | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.027 ± 0.016 | 60% | — | wymiera: tak | — |
| snowdrift | 0 | 5 | 5 | 100% | 1.00 ± 0.00 | +0.013 [-0.001, +0.028] | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.022 ± 0.015 | 80% | — | wymiera: tak | brak efektu |
| snowdrift | 0 | 15 | 5 | 78% | 0.99 ± 0.02 | +0.000 [-0.020, +0.020] | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.027 ± 0.016 | 60% | — | wymiera: tak | brak efektu |
| snowdrift | 0 | 50 | 5 | 0% | 0.99 ± 0.02 | +0.000 [-0.020, +0.020] | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.027 ± 0.016 | 60% | — | wymiera: tak | brak efektu |
| snowdrift | 0.01 | 0 | 5 | — | 0.37 ± 0.07 | — | 0.58 ± 0.12 | 0.050 ± 0.011 | -0.023 ± 0.012 | 60% | warunkowo | utrzymuje się: tak | — |
| snowdrift | 0.01 | 5 | 5 | 100% | 0.42 ± 0.03 | +0.050 [-0.018, +0.117] | 0.59 ± 0.09 | 0.072 ± 0.023 | 0.004 ± 0.010 | 100% | tak | utrzymuje się: tak | brak efektu |
| snowdrift | 0.01 | 15 | 5 | 80% | 0.45 ± 0.08 | +0.084 [-0.012, +0.179] | 0.68 ± 0.08 | 0.063 ± 0.019 | 0.002 ± 0.033 | 60% | warunkowo | utrzymuje się: tak | brak efektu |
| snowdrift | 0.01 | 50 | 5 | 0% | 0.37 ± 0.07 | +0.000 [-0.089, +0.089] | 0.58 ± 0.12 | 0.050 ± 0.011 | -0.023 ± 0.012 | 60% | warunkowo | utrzymuje się: tak | brak efektu |
| weak_PD | 0 | 0 | 5 | — | 1.00 ± 0.00 | — | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.013 ± 0.006 | 80% | — | wymiera: tak | — |
| weak_PD | 0 | 5 | 5 | 100% | 1.00 ± 0.00 | +0.001 [-0.002, +0.005] | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.013 ± 0.004 | 100% | — | wymiera: tak | brak efektu |
| weak_PD | 0 | 15 | 5 | 79% | 0.99 ± 0.01 | -0.004 [-0.013, +0.004] | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.010 ± 0.003 | 100% | — | wymiera: tak | brak efektu |
| weak_PD | 0 | 50 | 5 | 0% | 1.00 ± 0.00 | +0.000 [-0.004, +0.004] | 1.00 ± 0.00 | 0.000 ± 0.000 | 0.013 ± 0.006 | 80% | — | wymiera: tak | brak efektu |
| weak_PD | 0.01 | 0 | 5 | — | 0.43 ± 0.04 | — | 0.64 ± 0.09 | 0.070 ± 0.014 | -0.003 ± 0.019 | 80% | tak | utrzymuje się: tak | — |
| weak_PD | 0.01 | 5 | 5 | 100% | 0.45 ± 0.03 | +0.014 [-0.030, +0.059] | 0.61 ± 0.13 | 0.061 ± 0.018 | -0.015 ± 0.007 | 80% | tak | utrzymuje się: tak | brak efektu |
| weak_PD | 0.01 | 15 | 5 | 80% | 0.38 ± 0.08 | -0.047 [-0.124, +0.029] | 0.60 ± 0.13 | 0.052 ± 0.024 | -0.009 ± 0.022 | 80% | tak | utrzymuje się: tak | brak efektu |
| weak_PD | 0.01 | 50 | 5 | 0% | 0.43 ± 0.04 | +0.000 [-0.051, +0.051] | 0.64 ± 0.09 | 0.070 ± 0.014 | -0.003 ± 0.019 | 80% | tak | utrzymuje się: tak | brak efektu |

**Zgodność par** (obie predykcje utrzymane przy danym limicie):

- PD_classic, bez mutacji, limit 5: P2 część (wymiera) tak; P3 brak efektu
- PD_classic, bez mutacji, limit 15: P2 część (wymiera) tak; P3 brak efektu
- PD_classic, bez mutacji, limit 50: P2 część (wymiera) tak; P3 brak efektu
- PD_classic, mutacja 0.01, limit 5: P1+P3 **tak** (P1 tak, P3 tak); P2 część: tak
- PD_classic, mutacja 0.01, limit 15: P1+P3 **warunkowo** (P1 tak, P3 brak efektu); P2 część: tak
- PD_classic, mutacja 0.01, limit 50: P1+P3 **warunkowo** (P1 tak, P3 brak efektu); P2 część: tak
- snowdrift, bez mutacji, limit 5: P2 część (wymiera) tak; P3 brak efektu
- snowdrift, bez mutacji, limit 15: P2 część (wymiera) tak; P3 brak efektu
- snowdrift, bez mutacji, limit 50: P2 część (wymiera) tak; P3 brak efektu
- snowdrift, mutacja 0.01, limit 5: P1+P3 **warunkowo** (P1 tak, P3 brak efektu); P2 część: tak
- snowdrift, mutacja 0.01, limit 15: P1+P3 **warunkowo** (P1 warunkowo, P3 brak efektu); P2 część: tak
- snowdrift, mutacja 0.01, limit 50: P1+P3 **warunkowo** (P1 warunkowo, P3 brak efektu); P2 część: tak
- weak_PD, bez mutacji, limit 5: P2 część (wymiera) tak; P3 brak efektu
- weak_PD, bez mutacji, limit 15: P2 część (wymiera) tak; P3 brak efektu
- weak_PD, bez mutacji, limit 50: P2 część (wymiera) tak; P3 brak efektu
- weak_PD, mutacja 0.01, limit 5: P1+P3 **warunkowo** (P1 tak, P3 brak efektu); P2 część: tak
- weak_PD, mutacja 0.01, limit 15: P1+P3 **warunkowo** (P1 tak, P3 brak efektu); P2 część: tak
- weak_PD, mutacja 0.01, limit 50: P1+P3 **warunkowo** (P1 tak, P3 brak efektu); P2 część: tak


## Warunki i interpretacja

Port Pythona, `S2_pairs`: prędkość 0,1, przestrzeń (park syntetyczny), N = 200, 5 powtórzeń, 100 000 cykli,
limity {0, 5, 15, 50} (uruchomione przed przywróceniem 150). Limit 50 nie działa (0% agentów ma > 50
różnych partnerów), więc jego wiersze są identyczne z brakiem limitu.

- P1 utrzymuje się przy włączonym limicie Dunbara w PD i słabym PD przy każdym limicie; w snowdrifcie
  warunkowo (część przebiegów bez stabilizacji).
- P2 nie zależy od limitu (bez mutacji ALLC wymiera, z mutacją utrzymuje się na 4–7%).
- Limit przesuwa udział ALLD istotnie tylko w PD przy limicie 5 (+0,08; 95% CI [+0,02; +0,14]);
  w pozostałych konfiguracjach różnica jest nieistotna. P1+P3 zgodne w PD przy limicie 5, gdzie oba
  efekty występują naraz; gdzie indziej limit nie ma mierzalnego wpływu na ewolucję.
