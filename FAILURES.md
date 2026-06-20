# Channel Profitability Analysis — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason, not "it broke." If the
failure mode was technical, name the specific issue. If the failure
mode was scope or approach, name that.]

**What we tried instead:** [The next attempt, which may also have
failed and may have its own entry below]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search]

---

## Entries

### 2026-05-17 — flyctl DB password extraction fails on Windows

**Attempted:** Tried `flyctl ssh console -C "echo $OPERATOR_PASSWORD"`, `flyctl ssh console -C "env | grep -i pass"`, and `flyctl secrets list` to get the postgres password for use with `flyctl proxy` + local psql/python connection.

**Why it didn't work:** SSH console on Windows doesn't handle shell expansion or pipes in the `-C` argument (treats `|` as a filename). `flyctl secrets list` only shows digests, not values. The `-c` flag on `flyctl postgres connect` is for config file path, not SQL commands.

**What we tried instead:** Piped SQL directly through stdin to `flyctl postgres connect -a cinderhaven-db --database cinderhaven`. This works because fly handles auth internally via wireguard — no password needed. Requires `\pset pager off` first or output truncates at `--More--`.

**Status:** Resolved

**Tags:** flyctl, postgres, windows, database, export, password

---

### 2026-06-19 — PowerShell here-strings break with Python f-string curly braces

**Attempted:** Used PowerShell `@'...'@` here-strings to pass multi-line Python scripts containing f-strings (e.g., `print(f"value={x:.1f}")`) via `python -c`.

**Why it didn't work:** PowerShell's single-quoted here-string `@'...'@` doesn't expand variables, but the Python f-string `{}` braces still confused the parser — the script failed with `SyntaxError: '(' was never closed` or similar brace-matching errors.

**What we tried instead:** Wrote the Python code to a temp `.py` file, ran it with `python tmp_compute.py`, then deleted the file. Clean separation of languages.

**Status:** Resolved

**Tags:** powershell, python, f-string, here-string, windows, escaping

---

### 2026-06-19 — flyctl postgres connect password auth failure

**Attempted:** Queried cinderhaven-db schema via `flyctl postgres connect -a cinderhaven-db` with piped SQL (same pattern that worked in previous sessions). flyctl auth is valid (`flyctl auth whoami` returns correct user).

**Why it didn't work:** Server reachable (`Connecting to fdaa:74:6a73:a7b:896:c9af:d934:2...`) but returns `FATAL: password authentication failed for user "postgres"`. Likely cause: Fly.io rotated the internal postgres password since last successful connection, or the unmanaged Postgres instance needs a credential reset.

**What we tried instead:** Answered the scouting question from existing query patterns in `refresh_data.py` instead. All 5 waterfall layers have date columns in Postgres — confirmed from the SQL already in the codebase.

**Status:** Open — needs credential reset before next data refresh

**Tags:** flyctl, postgres, auth, password, fly.io, database

---

### 2026-06-20 — Action cards computed overhead from time-filtered data (returned $0)

**Attempted:** Computed capital-allocation card metrics (dispute overhead, Walmart disputes) from the time-filtered `channels`/`layers` data, same as the rest of the landing view.

**Why it didn't work:** Synthesized data from trends.json has `disputes_filed = 0` and combines all post-COGS erosion into a single "deductions" field. The overhead and dispute breakdown only exists in the full-range `baseLayers`/`baseChannels` data. Card showed "$0 annual dispute overhead" and "0 disputes/yr."

**What we tried instead:** Passed `baseChannels` as a new prop to LandingView. Computed all action card metrics from full-range data (`baseLayers`/`baseChannels`) since these are strategic recommendations that shouldn't change with time filter. Figures now match the MDX source exactly.

**Status:** Resolved

**Tags:** time-filter, synthesized-data, trends-json, action-cards, data-granularity

---

### 2026-06-20 — Preview tool viewport collapsed to 3px mid-session

**Attempted:** Used `preview_eval` to measure chart container widths after removing maxWidth constraints. Expected 1152px widths.

**Why it didn't work:** The headless browser viewport silently collapsed to `innerWidth: 3`. All `offsetWidth`/`clientWidth` measurements returned 0. The "desktop" preset in `preview_resize` didn't restore it. Earlier measurements in the same session had worked correctly at 1152px.

**What we tried instead:** Used `preview_resize` with explicit pixel dimensions (1280×800) instead of the "desktop" preset. This restored the viewport and measurements returned correct values.

**Status:** Resolved

**Tags:** preview-tool, viewport, headless-browser, measurement, debugging
