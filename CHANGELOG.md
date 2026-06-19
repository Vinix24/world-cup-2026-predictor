# Changelog

## Project overview (state at 2026-06-14)

**What it is.** An open-source FIFA World Cup 2026 predictor, CLI `wkpool`, repo
`github.com/Vinix24/world-cup-2026-predictor`. Built to win a pool and to be
forked: the engine is shared, the weights are yours.

**Pipeline.** martj42 results since 1872 → Elo (eloratings.net K-factors) + form
(exp. decay, 3y half-life) → isotonic-calibrated gradient boosting (W/D/L) +
Poisson goal model → 20k Monte Carlo through the official 2026 bracket (12
groups, round of 32, 8-best-thirds allocation). Calibration re-fits every run.
Holdout: ~61% W/D/L accuracy, RPS ~0.167 on 2,200+ internationals since 2024-06.

**Feature plugins** (rating-point nudges, weights in `weights.yaml`):
`injuries` (news-driven, persists across days, capped per team), `odds`
(bookmaker consensus, off by default), `climate` (off by default). Add your own
in `plugins_user/` (gitignored).

**Data sources** (downloaded at runtime, never redistributed): martj42 results;
football-data.org (faster results feed, closes the lag); Perplexity (daily team
news → injuries/suspensions incl. red cards); The Odds API (outright odds).
All optional ones are key-gated via `.env`.

**Pool scoring.** `weights.yaml: pool_scoring` holds the pool's points table
(default: graded exact-score — 200 exact / 100 any-draw / 95 winner+one-goal /
75 winner / 20 one-team-goals). `wkpool mine` enters the expected-points-optimal
scoreline, not the modal one.

**Automation (macOS launchd, 09:15 + 15:15 daily).** Public run (`--public`,
default weights) writes & commits `PREDICTIONS.md`, `NEWS.md`, `TRACK_RECORD.md`
+ `track_record.jsonl` and pushes — the living document the world watches. Then
`wkpool mine` runs with private weights → gitignored `PREDICTIONS.local.md` +
`output/changes.md`, and emails the changes (only when the score to enter moved).
macOS notification with the day's tips.

**Public vs private split.** Committed artifacts always use public default
weights. Private edge stays local: `weights.local.yaml`, `plugins_user/`,
`PREDICTIONS.local.md` — all gitignored. Secrets in `.env` (gitignored):
`PERPLEXITY_API_KEY`, `FOOTBALL_DATA_API_KEY` (set), `ODDS_API_KEY`,
`MAIL_TO`/`SMTP_USER`/`SMTP_PASS` (Gmail app password, spaces stripped).

**Commands.** `daily [--public --with-news --sims N]`, `download [--force]`,
`news [teams]`, `odds`, `mine [--sims N]`, `simulate [--sims N]`, `score`.
38 tests. Run on the always-on Mac mini; repo lives at `~/wkpool`.

**Open / next.** Knockout scoring counts after extra time — the goal model needs
an ET adjustment once the group stage ends. Pool-strategy layer (contrarian
picks vs the field) still a roadmap item. `weights.local.yaml` not yet created
(private predictions currently equal public).

## v0.2.9 — 2026-06-19

**Added**
- **Pool action log.** Every news-driven change to your entered score is appended
  to a permanent local audit trail (`output/action_log.jsonl`): match, old→new
  score, the team, the Elo move, and the reason (which player out/doubtful).
  Rendered to a readable `output/action_log.md`, newest first. The daily changes.md
  is overwritten each run; this is the durable record of *why* each pick moved.
  `_action_items` now returns structured items, formatted by `_action_line`.

## v0.2.8 — 2026-06-18

**Changed**
- **Committed predictions now use the maintainer's own weights.** The daily run
  dropped `--public`, so `PREDICTIONS.md` and the public track record are generated
  with the maintainer's private `weights.local.yaml` folded in. The weights file
  itself stays gitignored: the public sees the scores move, not the weighting. The
  PREDICTIONS.md header says so plainly. `--public` still exists for a clean
  default-weight run (forkers, reproducible baseline).

## v0.2.7 — 2026-06-18

**Added**
- **Pool track on your real entries.** `wkpool mine` now logs the ENTER score (the
  expected-points-optimal score you actually fill in) to
  `output/enter_history.jsonl` and scores it against results under your pool rubric:
  exact hits + total pool points (`score_pool`). The public TRACK_RECORD measures
  the modal prediction; this measures what you enter, oriented to each result's
  home/away. It starts the day logging begins, so it reflects your real pool
  performance from here on. Shown in the private report header and the run line.

## v0.2.6 — 2026-06-18

**Added**
- **Weight advisor (`wkpool advise`).** Suggest-only, closing the analyze → advise
  loop. It backtests the core weights (Elo K-factors, form half-life, home
  advantage) on the ~2245-match holdout — deterministically, the model has a fixed
  random_state — and proposes a change only when a candidate beats the current
  setting by a real margin (RPS gain >= 0.0005). It never edits `weights.yaml`; the
  last set stays human. Signal weights (injuries/odds/previews) are not
  holdout-validatable and are reported from live measurement (signal_log.jsonl),
  not proposed. Writes `output/weight_advice.md`. On-demand, not in the daily run.
  First run: 0 proposals — the core weights already sit at the holdout optimum, so
  edge has to come from the signals.

## v0.2.5 — 2026-06-18

**Added**
- **Public market-odds feed (`ODDS.md`).** Bookmaker-consensus title odds and the
  margin-stripped implied champion probabilities, rendered to a committed `ODDS.md`
  with full source attribution (The Odds API). Published like the NEWS.md digest:
  the data is shared, how the model weights it is not. Added to the daily push.

**Changed**
- **Private weighting split from the public feed.** The model's signal weighting
  lives in `weights.local.yaml` (gitignored) and stays private; the public `ODDS.md`
  feed publishes the market data itself with source attribution. The data is shared,
  the weighting is not.

## v0.2.4 — 2026-06-18

**Added**
- **Forward-looking match previews (`wkpool previews`).** A second Perplexity
  scrape, this one looking ahead: for each upcoming fixture it gathers the
  aggregate press/pundit consensus (predicted result, who is favored, the
  reasons, source count) into `data/previews/*.json`. Reuses the existing
  PERPLEXITY_API_KEY.
- **Previews plugin** turns that consensus into an Elo nudge (favored team up,
  underdog down, scaled by the press lean and confidence). Weight-gated, **off by
  default** — odds are the quantitative market consensus, previews the qualitative
  layer on top. `wkpool analyze` records the raw preview signal each run so its
  value can be measured on results before the weight ever goes up. Wired into the
  daily pipeline behind `--with-news`.

## v0.2.3 — 2026-06-18

**Added**
- **Schommelingen-analyse (`wkpool analyze`).** A read-only agent that reports how
  the predictions move day-to-day, which ones moved most, and whether the movement
  helped or hurt once results came in. It changes no weights — that stays a human
  call — and appends a per-run signal snapshot to `output/signal_log.jsonl` (per-team
  news adjustment + active weights), the durable substrate a later weight-advisor
  needs. Runs automatically at the end of the daily pipeline; writes
  `output/analysis.md`. First read: 24 played, 3 exact, every prediction adjustment
  so far net-neutral (news-driven wobble, no edge).
- **`Congo DR` football-data alias** so Portugal–DR Congo merges (last name mismatch).

## v0.2.2 — 2026-06-17

**Fixed**
- **Faster results feed dropped fresh results.** `merge_results` deduped against
  the full martj42 history (matches since 1872), so any nation pair that had ever
  met was treated as already-known and the new WC2026 score was discarded — only
  the never-before-played Iraq–Norway got through. Dedup is now scoped to WC2026
  matches, and the "Cape Verde Islands" football-data alias is mapped. Scored WC
  matches jumped 12 → 20 once the backlog merged; accuracy 42% → 45%.

**Added**
- **News-driven pool-action alert.** When fresh injury/suspension news shifts the
  expected-points-optimal score of an *upcoming* match, the private change report
  (`output/changes.md`) now leads with an ACTIE block naming the entries to
  re-fill, the old→new score, and the news behind it; the mailer marks the subject
  (⚠️) so it stands out. Keys on the injuries plugin only (the news signal), gated
  on the ENTER score actually moving, scoped to not-yet-played matches.

## v0.2.1 — 2026-06-14

**Added**
- **Expected-points-optimal scoreline** (`wkpool/scoring.py`). Your pool rewards
  the exact score far above the bare winner, so `wkpool mine` now fills in the
  scoreline that *maximises expected points* under your pool's rubric
  (configurable in `weights.yaml: pool_scoring`) — often different from the most
  likely score (e.g. enter a draw when any draw scores 100). The private change
  report and `PREDICTIONS.local.md` lead with this "ENTER" score and its
  expected points.

## v0.2 — 2026-06-14

Iterating on the MVP with the highest-leverage data improvements.

**Added**
- **Bookmaker-consensus odds plugin** — the strongest single covariate in the
  literature. Reads `data/odds/outright.json`, strips the margin, and nudges
  each team's rating toward the market. Off by default; `wkpool odds` fills the
  file from The Odds API.
- **Faster results feed** — optional football-data.org source merges
  same-day World Cup results that the martj42 CSV hasn't picked up yet,
  closing the ~1-2 day upstream lag.
- **News stabilisation** — injuries now persist across days (configurable
  `persist_days`) unless a player is reported fit, dampening the day-to-day
  noise of LLM scraping; total injury penalty per team is capped
  (`max_team_penalty`).
- Twice-daily scheduled run (09:15 + 15:15) to catch late upstream results.

**Fixed**
- W/D/L scoring used the wrong goal-difference sign when a result's home/away
  orientation differed from the logged prediction (latent bug, surfaced by a
  new test).

**Changed**
- Repository renamed to `world-cup-2026-predictor` (CLI stays `wkpool`).

## v0.1 — 2026-06-11

MVP. Elo + form → isotonic-calibrated gradient boosting → 20k Monte Carlo
through the official 2026 bracket. Daily Perplexity news feed, user-tunable
`weights.yaml`, plugin system, living audit trail (`PREDICTIONS.md`,
`NEWS.md`, `TRACK_RECORD.md`). Holdout: 61% accuracy, RPS 0.167.
