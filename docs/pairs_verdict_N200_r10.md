# Zestawienia parami i razem – wnioski (port Pythona, N = 200, 10 powtórzeń)

Przestrzeń: PD, ewolucja (Fermi), 100 000 cykli, sieci {baseline, fragmented, connected} × prędkość {0,1; 2}.
Mutacja 0,01 (`PM7_P1P3_network`) i 0 (`PM8_P2_network`, część P2 „ALLC wymiera”). P3 w ewolucji = wzrost
udziału ALLD przy limicie (95% CI). P4: `PM5_P4_*` (`well_mixed`, ALLC/ALLD, gra dawcy).
Port ma inny generator liczb losowych niż GAMA; wyniki do potwierdzenia w GAMA.

## Wnioski

1. **P2+P3 przy limicie 5 – stała kandydacka.** We wszystkich sześciu kolumnach (3 sieci × 2 prędkości) ALLC
   wymiera bez mutacji, utrzymuje się nisko z mutacją (0,01–0,05), a limit 5 podnosi udział ALLD (+0,06 do +0,13).
   Przy limicie 15 efekt P3 znika przy prędkości 0,1 na connected i fragmented (limit ogranicza tylko 63–81%
   agentów), więc werdykt zależy od sieci i mobilności.
2. **P1+P2 (bez limitu) i trójka P1+P2+P3 – parametr kontekstowy.** Rozstrzyga P1: zachodzi tylko przy
   prędkości 0,1 (baseline, fragmented; connected warunkowo). Trójka P1+P2+P3 zachodzi przy prędkości 0,1
   i limicie 5 na baseline i fragmented, przy limicie 15 tylko na baseline.
3. **P1+P3** – osobno w `p1p3_network_verdict_N200_r10.md`; ten sam wzorzec (mobilność rozstrzyga).
4. **P4+P1 – nie odtworzono.** Po obu stronach progu jedna strategia wypiera drugą do ok. 0,97–0,99,
   a P1 wymaga stabilnego udziału w (0,05; 0,95). W `well_mixed` P1 nie odtwarzała się też osobno.
5. **P4+P2** – zgodne po stronie r̂ < c/b (ALLC utrzymuje się nisko, jak przewiduje reguła Hamiltona);
   po stronie r̂ > c/b (kalibracja) ALLC przejmuje populację (ok. 0,97), więc P2 „przetrwanie na niskim poziomie”
   jest warunkowe. To nie sprzeczność reguł, tylko P2 przestaje opisywać ten stan.
6. **P4+P3 – nietestowalna w tej konfiguracji.** Kontrola (ten sam seed, limit 0 i 5, oba tryby doboru, 2000 cykli):
   agent pamięta 5 partnerów zamiast ok. 199, a udziały strategii i wszystkie metryki poza pamięcią spotkań są
   identyczne. ALLC i ALLD nie używają pamięci partnerów, więc limit Dunbara nie ma na co działać. Test wymagałby
   strategii warunkowych w P4 (poza specyfikacją P4 – do decyzji).

**Wspólny wniosek:** we wszystkich zestawieniach czynnikiem, który najczęściej zmienia werdykt, jest mobilność
agentów (prędkość), a nie wariant sieci. Wariant sieci zmienia werdykt tylko przy niskiej mobilności
(connected: słabsze P1; limit 15 działa słabiej na connected i fragmented).

## P1, P2, P3 w przestrzeni (PD, ewolucja)

| układ | macierz | prędkość | limit | n (mut. 0 / 0,01) | limit działa | ALLC bez mutacji | ALLC mut. 0,01 | ALLD mut. 0,01 | udział D mut. 0,01 | P1 | P2 | P3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | PD_classic | 0.1 | 0 | 10 / 10 | — | 0.000 ± 0.000 | 0.046 ± 0.022 | 0.63 ± 0.03 | 0.83 ± 0.04 | tak | tak | — |
| baseline | PD_classic | 0.1 | 5 | 10 / 10 | 100% | 0.000 ± 0.000 | 0.040 ± 0.022 | 0.69 ± 0.06 | 0.86 ± 0.11 | tak | tak | tak (ΔALLD +0.067) |
| baseline | PD_classic | 0.1 | 15 | 10 / 10 | 80% | 0.000 ± 0.000 | 0.041 ± 0.012 | 0.65 ± 0.03 | 0.89 ± 0.03 | tak | tak | tak (ΔALLD +0.026) |
| baseline | PD_classic | 0.1 | 50 | 0 / 10 | 0% | — | 0.046 ± 0.022 | 0.63 ± 0.03 | 0.83 ± 0.04 | tak | — | brak efektu (ΔALLD +0.000) |
| baseline | PD_classic | 0.1 | 150 | 0 / 10 | 0% | — | 0.046 ± 0.022 | 0.63 ± 0.03 | 0.83 ± 0.04 | tak | — | brak efektu (ΔALLD +0.000) |
| baseline | PD_classic | 2 | 0 | 10 / 10 | — | 0.000 ± 0.000 | 0.012 ± 0.008 | 0.79 ± 0.03 | 0.96 ± 0.02 | nie | tak | — |
| baseline | PD_classic | 2 | 5 | 10 / 10 | 100% | 0.000 ± 0.000 | 0.010 ± 0.004 | 0.92 ± 0.02 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.132) |
| baseline | PD_classic | 2 | 15 | 10 / 10 | 100% | 0.000 ± 0.000 | 0.008 ± 0.003 | 0.92 ± 0.02 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.127) |
| baseline | PD_classic | 2 | 50 | 0 / 10 | 100% | — | 0.011 ± 0.003 | 0.90 ± 0.03 | 0.97 ± 0.01 | nie | — | tak (ΔALLD +0.107) |
| baseline | PD_classic | 2 | 150 | 0 / 10 | 91% | — | 0.010 ± 0.004 | 0.82 ± 0.05 | 0.96 ± 0.02 | nie | — | brak efektu (ΔALLD +0.026) |
| connected | PD_classic | 0.1 | 0 | 10 / 10 | — | 0.000 ± 0.000 | 0.045 ± 0.020 | 0.62 ± 0.04 | 0.85 ± 0.05 | warunkowo | tak | — |
| connected | PD_classic | 0.1 | 5 | 10 / 10 | 100% | 0.000 ± 0.000 | 0.046 ± 0.012 | 0.69 ± 0.05 | 0.91 ± 0.05 | warunkowo | tak | tak (ΔALLD +0.070) |
| connected | PD_classic | 0.1 | 15 | 10 / 10 | 81% | 0.000 ± 0.000 | 0.041 ± 0.014 | 0.62 ± 0.07 | 0.87 ± 0.08 | warunkowo | tak | brak efektu (ΔALLD +0.007) |
| connected | PD_classic | 0.1 | 50 | 0 / 10 | 0% | — | 0.045 ± 0.020 | 0.62 ± 0.04 | 0.85 ± 0.05 | warunkowo | — | brak efektu (ΔALLD +0.000) |
| connected | PD_classic | 0.1 | 150 | 0 / 10 | 0% | — | 0.045 ± 0.020 | 0.62 ± 0.04 | 0.85 ± 0.05 | warunkowo | — | brak efektu (ΔALLD +0.000) |
| connected | PD_classic | 2 | 0 | 10 / 10 | — | 0.000 ± 0.000 | 0.010 ± 0.005 | 0.79 ± 0.06 | 0.96 ± 0.01 | nie | tak | — |
| connected | PD_classic | 2 | 5 | 10 / 10 | 100% | 0.000 ± 0.000 | 0.009 ± 0.006 | 0.93 ± 0.02 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.131) |
| connected | PD_classic | 2 | 15 | 10 / 10 | 100% | 0.000 ± 0.000 | 0.011 ± 0.006 | 0.91 ± 0.02 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.117) |
| connected | PD_classic | 2 | 50 | 0 / 10 | 100% | — | 0.011 ± 0.006 | 0.90 ± 0.02 | 0.97 ± 0.01 | nie | — | tak (ΔALLD +0.104) |
| connected | PD_classic | 2 | 150 | 0 / 10 | 91% | — | 0.013 ± 0.008 | 0.82 ± 0.04 | 0.96 ± 0.01 | nie | — | brak efektu (ΔALLD +0.020) |
| fragmented | PD_classic | 0.1 | 0 | 10 / 10 | — | 0.000 ± 0.000 | 0.050 ± 0.014 | 0.57 ± 0.06 | 0.78 ± 0.09 | tak | tak | — |
| fragmented | PD_classic | 0.1 | 5 | 10 / 10 | 99% | 0.000 ± 0.000 | 0.040 ± 0.008 | 0.63 ± 0.05 | 0.86 ± 0.06 | tak | tak | tak (ΔALLD +0.061) |
| fragmented | PD_classic | 0.1 | 15 | 10 / 10 | 63% | 0.000 ± 0.000 | 0.050 ± 0.013 | 0.57 ± 0.06 | 0.82 ± 0.07 | tak | tak | brak efektu (ΔALLD +0.008) |
| fragmented | PD_classic | 0.1 | 50 | 0 / 10 | 0% | — | 0.050 ± 0.014 | 0.57 ± 0.06 | 0.78 ± 0.09 | tak | — | brak efektu (ΔALLD +0.000) |
| fragmented | PD_classic | 0.1 | 150 | 0 / 10 | 0% | — | 0.050 ± 0.014 | 0.57 ± 0.06 | 0.78 ± 0.09 | tak | — | brak efektu (ΔALLD +0.000) |
| fragmented | PD_classic | 2 | 0 | 10 / 10 | — | 0.000 ± 0.000 | 0.011 ± 0.005 | 0.81 ± 0.04 | 0.96 ± 0.01 | nie | tak | — |
| fragmented | PD_classic | 2 | 5 | 10 / 10 | 100% | 0.000 ± 0.000 | 0.010 ± 0.005 | 0.92 ± 0.01 | 0.98 ± 0.01 | nie | tak | tak (ΔALLD +0.110) |
| fragmented | PD_classic | 2 | 15 | 10 / 10 | 100% | 0.000 ± 0.000 | 0.010 ± 0.007 | 0.91 ± 0.02 | 0.97 ± 0.01 | nie | tak | tak (ΔALLD +0.100) |
| fragmented | PD_classic | 2 | 50 | 0 / 10 | 100% | — | 0.010 ± 0.009 | 0.88 ± 0.03 | 0.97 ± 0.01 | nie | — | tak (ΔALLD +0.071) |
| fragmented | PD_classic | 2 | 150 | 0 / 10 | 34% | — | 0.009 ± 0.006 | 0.81 ± 0.05 | 0.97 ± 0.01 | nie | — | brak efektu (ΔALLD -0.002) |

### Tabela zbiorcza – pary i trójka z P1, P2, P3

Kolumny: układ × macierz × prędkość. P1+P3 osobno: `p1p3_network_verdict_N200_r10.md`.

| zestawienie | baseline / PD_classic / 0.1 | baseline / PD_classic / 2.0 | connected / PD_classic / 0.1 | connected / PD_classic / 2.0 | fragmented / PD_classic / 0.1 | fragmented / PD_classic / 2.0 | klasyfikacja |
|---|---|---|---|---|---|---|---|
| P1+P2 (bez limitu) | **tak** | **nie** | **warunkowo** | **nie** | **tak** | **nie** | parametr kontekstowy (zależy od: układu przestrzeni, mobilności (prędkość)) |
| P2+P3, limit 5 | **tak** | **tak** | **tak** | **tak** | **tak** | **tak** | stała kandydacka (tak) |
| P2+P3, limit 15 | **tak** | **tak** | **warunkowo** | **tak** | **warunkowo** | **tak** | parametr kontekstowy (zależy od: układu przestrzeni, mobilności (prędkość)) |
| P1+P2+P3, limit 5 | **tak** | **nie** | **warunkowo** | **nie** | **tak** | **nie** | parametr kontekstowy (zależy od: układu przestrzeni, mobilności (prędkość)) |
| P1+P2+P3, limit 15 | **tak** | **nie** | **warunkowo** | **nie** | **warunkowo** | **nie** | parametr kontekstowy (zależy od: układu przestrzeni, mobilności (prędkość)) |

## P4 z P1 i P2 (well_mixed, ALLC/ALLD, gra dawcy, mutacja 0,01)

Przebiegi podzielone wg strony progu (pominięte |r̂ − c/b| ≤ 0,05).

| dobór | c/b | dopasowanie | strona progu | n | ALLC | ALLD | udział D | P4 (kierunek) | P1 | P2 (ALLC nisko, obecny) |
|---|---|---|---|---|---|---|---|---|---|---|
| family | 0.3 | inclusive | r̂ < c/b | 100 | 0.375 ± 0.420 | 0.625 ± 0.420 | 0.624 ± 0.420 | warunkowo | nie | warunkowo |
| family | 0.3 | own | r̂ < c/b | 100 | 0.016 ± 0.008 | 0.984 ± 0.008 | 0.984 ± 0.009 | tak | nie | tak |
| family | 0.5 | inclusive | r̂ < c/b | 100 | 0.031 ± 0.037 | 0.969 ± 0.037 | 0.969 ± 0.037 | tak | nie | tak |
| family | 0.5 | own | r̂ < c/b | 100 | 0.010 ± 0.005 | 0.990 ± 0.005 | 0.989 ± 0.005 | tak | nie | tak |
| strategy | 0.3 | own | r̂ < c/b | 30 | 0.026 ± 0.020 | 0.974 ± 0.020 | 0.974 ± 0.021 | tak | nie | tak |
| strategy | 0.3 | own | r̂ > c/b | 60 | 0.976 ± 0.022 | 0.024 ± 0.022 | 0.024 ± 0.022 | tak | nie | warunkowo |
| strategy | 0.5 | own | r̂ < c/b | 50 | 0.022 ± 0.019 | 0.978 ± 0.019 | 0.979 ± 0.020 | tak | nie | tak |
| strategy | 0.5 | own | r̂ > c/b | 40 | 0.969 ± 0.025 | 0.031 ± 0.025 | 0.030 ± 0.025 | tak | nie | warunkowo |

### Tabela zbiorcza – pary z P4

| zestawienie | well_mixed / c/b = 0.3 | well_mixed / c/b = 0.5 | klasyfikacja |
|---|---|---|---|
| P4+P1 (family / inclusive, r̂ < c/b) | **nie** | **nie** | nie odtworzono |
| P4+P2 (family / inclusive, r̂ < c/b) | **warunkowo** | **tak** | parametr kontekstowy (zależy od: macierzy wypłat) |
| P4+P1 (family / own, r̂ < c/b) | **nie** | **nie** | nie odtworzono |
| P4+P2 (family / own, r̂ < c/b) | **tak** | **tak** | stała kandydacka (tak) |
| P4+P1 (strategy / own, r̂ < c/b) | **nie** | **nie** | nie odtworzono |
| P4+P2 (strategy / own, r̂ < c/b) | **tak** | **tak** | stała kandydacka (tak) |
| P4+P1 (strategy / own, r̂ > c/b) | **nie** | **nie** | nie odtworzono |
| P4+P2 (strategy / own, r̂ > c/b) | **warunkowo** | **warunkowo** | stała kandydacka (warunkowo) |

