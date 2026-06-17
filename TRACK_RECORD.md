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

## Daily recalibration log

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
