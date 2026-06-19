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
