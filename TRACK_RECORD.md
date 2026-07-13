# wkpool — track record

Honest, automated audit trail. Every prediction is logged **before** the
match is played (`output/history.jsonl` + git history), so this accuracy
curve cannot be cherry-picked afterwards. Hits and misses both.

## Cumulative accuracy

| As of | Matches scored | Correct (toto) | Accuracy | RPS |
|---|---|---|---|---|
| 2026-06-11 | 2 | 2 | 100% | 0.0972 |
| 2026-06-12 | 4 | 2 | 50% | 0.1851 |
| 2026-06-13 | 4 | 2 | 50% | 0.1851 |
| 2026-06-14 | 8 | 3 | 38% | 0.2131 |
| 2026-06-15 | 12 | 5 | 42% | 0.2153 |
| 2026-06-16 | 12 | 5 | 42% | 0.2153 |
| 2026-06-17 | 20 | 9 | 45% | 0.1890 |
| 2026-06-18 | 24 | 11 | 46% | 0.1991 |
| 2026-06-19 | 28 | 14 | 50% | 0.1816 |
| 2026-06-20 | 32 | 17 | 53% | 0.1814 |
| 2026-06-21 | 36 | 20 | 56% | 0.1762 |
| 2026-06-22 | 40 | 22 | 55% | 0.1752 |
| 2026-06-23 | 44 | 26 | 59% | 0.1665 |
| 2026-06-24 | 48 | 29 | 60% | 0.1639 |
| 2026-06-25 | 54 | 34 | 63% | 0.1650 |
| 2026-06-26 | 60 | 36 | 60% | 0.1715 |
| 2026-06-27 | 66 | 40 | 61% | 0.1645 |
| 2026-06-28 | 72 | 44 | 61% | 0.1591 |
| 2026-06-29 | 72 | 44 | 61% | 0.1591 |
| 2026-06-30 | 72 | 44 | 61% | 0.1591 |
| 2026-07-01 | 72 | 44 | 61% | 0.1591 |
| 2026-07-02 | 72 | 44 | 61% | 0.1591 |
| 2026-07-03 | 72 | 44 | 61% | 0.1591 |
| 2026-07-04 | 72 | 44 | 61% | 0.1591 |
| 2026-07-05 | 72 | 44 | 61% | 0.1591 |
| 2026-07-06 | 72 | 44 | 61% | 0.1591 |
| 2026-07-07 | 72 | 44 | 61% | 0.1591 |
| 2026-07-08 | 72 | 44 | 61% | 0.1591 |
| 2026-07-09 | 72 | 44 | 61% | 0.1591 |
| 2026-07-10 | 72 | 44 | 61% | 0.1591 |
| 2026-07-11 | 72 | 44 | 61% | 0.1591 |
| 2026-07-12 | 72 | 44 | 61% | 0.1591 |
| 2026-07-13 | 72 | 44 | 61% | 0.1591 |

## Daily recalibration log

### 2026-07-13
- Score so far: 72 matches, 61% correct, RPS 0.1591
- News ingested: 48 teams scanned, 104 out / 74 doubtful, 4 suspensions
  - Suspensions: Assim Madibo (Qatar); Homam El Amin (Qatar); Jarell Quansah (England); Abdokhodir Khusanov (Uzbekistan)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-12
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: Norway 1-2 England [?]; Argentina 3-1 Switzerland [?]
- News ingested: 48 teams scanned, 105 out / 76 doubtful, 5 suspensions
  - Suspensions: Assim Madibo (Qatar); Homam El Amin (Qatar); Jarell Quansah (England); None reported (Switzerland); Unnamed South Africa player (South Africa)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-11
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: Spain 2-1 Belgium [?]
- News ingested: 48 teams scanned, 112 out / 71 doubtful, 3 suspensions
  - Suspensions: None reported (Japan); Jarell Quansah (England); Mohanad Lashin (Egypt)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-10
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: France 2-0 Morocco [?]
- News ingested: 48 teams scanned, 118 out / 70 doubtful, 5 suspensions
  - Suspensions: Jarell Quansah (England); Davinson Sánchez (Colombia); Mohanad Lashin (Egypt); Assim Madibo (Canada); None identified from the provided news (Ecuador)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-09
- Score so far: 72 matches, 61% correct, RPS 0.1591
- News ingested: 48 teams scanned, 114 out / 75 doubtful, 1 suspensions
  - Suspensions: Assim Madibo (Qatar)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-08
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: Argentina 3-2 Egypt [?]; Switzerland 0-0 Colombia [?]
- News ingested: 48 teams scanned, 110 out / 74 doubtful, 1 suspensions
  - Suspensions: Assim Madibo (Qatar)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-07
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: Portugal 0-1 Spain [?]; United States 1-4 Belgium [?]
- News ingested: 48 teams scanned, 107 out / 78 doubtful, 2 suspensions
  - Suspensions: None reported (Scotland); Mohamed Hany (Egypt)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-06
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: Brazil 0-2 Norway [?]; Mexico 2-3 England [?]
- News ingested: 48 teams scanned, 108 out / 87 doubtful, 1 suspensions
  - Suspensions: Unnamed Uruguay player (Uruguay)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-05
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: Canada 0-3 Morocco [?]; Paraguay 0-1 France [?]
- News ingested: 48 teams scanned, 105 out / 92 doubtful, 3 suspensions
  - Suspensions: Assim Madibo (Qatar); Homam El Amin (Qatar); Manuel Ugarte (Uruguay)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-04
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: Argentina 3-2 Cape Verde [?]; Australia 1-1 Egypt [?]; Colombia 1-0 Ghana [?]
- News ingested: 48 teams scanned, 98 out / 95 doubtful, 2 suspensions
  - Suspensions: Miguel Almirón (Paraguay); Nathan Ngoy (Belgium)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-03
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: Portugal 2-1 Croatia [?]; Spain 3-0 Austria [?]; Switzerland 2-0 Algeria [?]
- News ingested: 48 teams scanned, 99 out / 99 doubtful, 2 suspensions
  - Suspensions: Billy Gilmour (Scotland); Unnamed Uruguay player (red card vs Spain) (Uruguay)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-02
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: Belgium 3-2 Senegal [?]; England 2-1 DR Congo [?]; United States 2-0 Bosnia and Herzegovina [?]
- News ingested: 48 teams scanned, 87 out / 91 doubtful, 4 suspensions
  - Suspensions: Okay Yokuşlu (Turkey); Assim Madibo (Qatar); Homam El Amin (Qatar); Assim Madibo (Canada)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-07-01
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: France 3-0 Sweden [?]; Ivory Coast 1-2 Norway [?]; Mexico 2-0 Ecuador [?]
- News ingested: 48 teams scanned, 82 out / 78 doubtful, 4 suspensions
  - Suspensions: Assim Madibo (Qatar); Homam El Amin (Qatar); Declan Rice (England); Leonardo Balerdi (Argentina)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-06-30
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: Germany 1-1 Paraguay [?]; Brazil 2-1 Japan [?]; Netherlands 1-1 Morocco [?]
- News ingested: 48 teams scanned, 93 out / 64 doubtful, 1 suspensions
  - Suspensions: Sead Kolašinac (Bosnia and Herzegovina)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-06-29
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: South Africa 0-1 Canada [?]
- News ingested: 48 teams scanned, 91 out / 62 doubtful, 5 suspensions
  - Suspensions: Assim Madibo (Qatar); Homam Al Amin (Qatar); Agustín Canobbio (Uruguay); Assim Madibo (Canada); Tomáš Souček (Czech Republic)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 365d, K_wc=60, sims=20000

### 2026-06-28
- Score so far: 72 matches, 61% correct, RPS 0.1591
- Newly decided: DR Congo 3-1 Uzbekistan [OK, predicted 1-1]; Colombia 0-0 Portugal [X, predicted 1-1]; Panama 0-2 England [OK, predicted 0-2]; Algeria 3-3 Austria [X, predicted 1-1]; Jordan 1-3 Argentina [OK, predicted 0-3]; Croatia 2-1 Ghana [OK, predicted 2-0]
- News ingested: 48 teams scanned, 80 out / 70 doubtful, 3 suspensions
  - Suspensions: Assim Madibo (Qatar); Agustín Canobbio (Uruguay); Joseph Oppong (Croatia)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-27
- Score so far: 66 matches, 61% correct, RPS 0.1645
- Newly decided: Senegal 5-0 Iraq [OK, predicted 1-0]; Norway 1-4 France [OK, predicted 0-1]; Cape Verde 0-0 Saudi Arabia [X, predicted 1-1]; New Zealand 1-5 Belgium [OK, predicted 0-2]; Uruguay 0-1 Spain [OK, predicted 0-2]; Egypt 1-1 Iran [X, predicted 1-1]
- News ingested: 48 teams scanned, 79 out / 69 doubtful, 7 suspensions
  - Suspensions: Assim Madibo (Qatar); Homam El Amin (Qatar); César Montes (Mexico); Agustín Canobbio (Uruguay); Sidnei Lopes Cabral (Cape Verde); Diego Gómez (Paraguay); Rebin Sulaka (Iraq)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-26
- Score so far: 60 matches, 60% correct, RPS 0.1715
- Newly decided: Ecuador 2-1 Germany [X, predicted 0-1]; Curaçao 0-2 Ivory Coast [OK, predicted 0-1]; Japan 1-1 Sweden [X, predicted 1-0]; United States 2-3 Turkey [X, predicted 0-1]; Paraguay 0-0 Australia [X, predicted 1-1]; Tunisia 1-3 Netherlands [OK, predicted 0-2]
- News ingested: 48 teams scanned, 71 out / 72 doubtful, 1 suspensions
  - Suspensions: Assim Madibo (Qatar)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-25
- Score so far: 54 matches, 63% correct, RPS 0.1650
- Newly decided: Bosnia and Herzegovina 3-1 Qatar [OK, predicted 1-1]; Canada 1-2 Switzerland [OK, predicted 1-1]; Scotland 0-3 Brazil [OK, predicted 0-2]; Mexico 3-0 Czech Republic [OK, predicted 0-2]; South Africa 1-0 South Korea [X, predicted 0-1]; Morocco 4-2 Haiti [OK, predicted 2-0]
- News ingested: 48 teams scanned, 72 out / 75 doubtful, 1 suspensions
  - Suspensions: César Montes (Czech Republic)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-24
- Score so far: 48 matches, 60% correct, RPS 0.1639
- Newly decided: Colombia 1-0 DR Congo [OK, predicted 2-0]; England 0-0 Ghana [X, predicted 3-0]; Portugal 5-0 Uzbekistan [OK, predicted 2-0]; Panama 0-1 Croatia [OK, predicted 0-1]
- News ingested: 48 teams scanned, 71 out / 67 doubtful, 3 suspensions
  - Suspensions: Homam El Amin (Homam Ahmed) (Qatar); Assim Madibo (Qatar); Tarik Muharemovic (Bosnia and Herzegovina)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-23
- Score so far: 44 matches, 59% correct, RPS 0.1665
- Newly decided: Norway 3-2 Senegal [OK, predicted 1-0]; Argentina 2-0 Austria [OK, predicted 2-0]; France 3-0 Iraq [OK, predicted 3-0]; Jordan 1-2 Algeria [OK, predicted 0-1]
- News ingested: 48 teams scanned, 74 out / 76 doubtful, 1 suspensions
  - Suspensions: Nathan Ngoy (Belgium)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-22
- Score so far: 40 matches, 55% correct, RPS 0.1752
- Newly decided: New Zealand 1-3 Egypt [OK, predicted 1-1]; Spain 4-0 Saudi Arabia [OK, predicted 3-0]; Belgium 0-0 Iran [X, predicted 1-0]; Uruguay 2-2 Cape Verde [X, predicted 2-0]
- News ingested: 48 teams scanned, 66 out / 88 doubtful, 3 suspensions
  - Suspensions: Assim Madibo (Qatar); Unnamed second Qatar player (Qatar); Nathan Ngoy (Belgium)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-21
- Score so far: 36 matches, 56% correct, RPS 0.1762
- Newly decided: Ecuador 0-0 Curaçao [X, predicted 2-0]; Netherlands 5-1 Sweden [OK, predicted 1-0]; Germany 2-1 Ivory Coast [OK, predicted 1-0]; Tunisia 0-4 Japan [OK, predicted 0-2]
- News ingested: 48 teams scanned, 66 out / 72 doubtful, 5 suspensions
  - Suspensions: Assim Madibo (Qatar); Unnamed Qatar player (Qatar); Lamine Yamal (Algeria); Miguel Almirón (Paraguay); Lucas Bergvall (Sweden)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-20
- Score so far: 32 matches, 53% correct, RPS 0.1814
- Newly decided: Brazil 3-0 Haiti [OK, predicted 2-0]; United States 2-0 Australia [OK, predicted 1-1]; Scotland 0-1 Morocco [OK, predicted 0-1]; Turkey 0-1 Paraguay [X, predicted 1-1]
- News ingested: 48 teams scanned, 75 out / 62 doubtful, 6 suspensions
  - Suspensions: Homam Ahmed (Qatar); Assim Madibo (Qatar); Miguel Almirón (Paraguay); Tani Oluwaseyi (Canada); Tarik Muharemovic (Bosnia and Herzegovina); Shankland (Morocco)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-19
- Score so far: 28 matches, 50% correct, RPS 0.1816
- Newly decided: Mexico 1-0 South Korea [OK, predicted 1-0]; Switzerland 4-1 Bosnia and Herzegovina [OK, predicted 2-0]; Czech Republic 1-1 South Africa [X, predicted 1-0]; Canada 6-0 Qatar [OK, predicted 2-0]
- News ingested: 48 teams scanned, 73 out / 62 doubtful, 5 suspensions
  - Suspensions: Homam Ahmed (Qatar); Assim Madibo (Qatar); Teboho Mokoena (South Africa); Abdukodir Khusanov (Uzbekistan); Tarik Muharemovic (Bosnia and Herzegovina)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-18
- Score so far: 24 matches, 46% correct, RPS 0.1991
- Newly decided: Uzbekistan 1-3 Colombia [OK, predicted 0-1]; England 4-2 Croatia [OK, predicted 1-0]; Portugal 1-1 DR Congo [X, predicted 1-0]; Ghana 1-0 Panama [X, predicted 0-1]
- News ingested: 48 teams scanned, 73 out / 55 doubtful, 2 suspensions
  - Suspensions: Sphephelo (Yaya) Sithole (South Africa); Themba Zwane (South Africa)
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-17
- Score so far: 20 matches, 45% correct, RPS 0.1890
- Newly decided: Spain 0-0 Cape Verde [X, predicted 3-0]; Saudi Arabia 1-1 Uruguay [X, predicted 0-1]; Belgium 1-1 Egypt [X, predicted 1-0]; Iran 2-2 New Zealand [X, predicted 1-0]; Iraq 1-4 Norway [OK, predicted 0-1]; Argentina 3-0 Algeria [OK, predicted 2-0]; France 3-1 Senegal [OK, predicted 1-0]; Austria 3-1 Jordan [OK, predicted 1-0]
- News ingested: 48 teams scanned, 79 out / 58 doubtful
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-16
- Score so far: 12 matches, 42% correct, RPS 0.2153
- News ingested: 48 teams scanned, 52 out / 54 doubtful
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-15
- Score so far: 12 matches, 42% correct, RPS 0.2153
- Newly decided: Ivory Coast 1-0 Ecuador [X, predicted 0-1]; Netherlands 2-2 Japan [X, predicted 1-1]; Germany 7-1 Curaçao [OK, predicted 2-0]; Sweden 5-1 Tunisia [OK, predicted 1-1]
- News ingested: 48 teams scanned, 41 out / 51 doubtful
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-14
- Score so far: 8 matches, 38% correct, RPS 0.2131
- Newly decided: Canada 1-1 Bosnia-Herzegovina [?]; Brazil 1-1 Morocco [X, predicted 1-1]; Haiti 0-1 Scotland [OK, predicted 0-1]; Qatar 1-1 Switzerland [X, predicted 0-2]; Australia 2-0 Turkey [X, predicted 1-1]
- News ingested: 48 teams scanned, 28 out / 27 doubtful
- Active weights: injuries ×1.0 (12/out, 6/doubtful), climate ×0.0, form half-life 1095d, K_wc=60, sims=20000

### 2026-06-13
- Score so far: 4 matches, 50% correct, RPS 0.1851
- News ingested: 0 teams scanned, 0 out / 0 doubtful
- Active weights: injuries x1.0 (12/out, 6/doubtful), form half-life 1095d, K_wc=60, sims=20000

### 2026-06-12
- Score so far: 4 matches, 50% correct, RPS 0.1851
- News ingested: 0 teams scanned, 0 out / 0 doubtful
- Active weights: injuries x1.0 (12/out, 6/doubtful), form half-life 1095d, K_wc=60, sims=20000

### 2026-06-11
- Score so far: 2 matches, 100% correct, RPS 0.0972
- News ingested: 0 teams scanned, 0 out / 0 doubtful
- Active weights: injuries x1.0 (12/out, 6/doubtful), form half-life 1095d, K_wc=60, sims=20000
