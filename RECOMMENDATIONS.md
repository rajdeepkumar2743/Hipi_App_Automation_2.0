# Recommendations — CI/CD, Parallel Execution, Real Devices, Scalability

Scoped to what a 26-test suite for one app actually needs — not a
hypothetical Fortune-500 buildout. Each section says what I built vs. what's
just a recommendation for you to decide on.

## CI/CD — built: `.github/workflows/mobile-tests.yml`

- Smoke marker (4 tests) runs on every push/PR against a real Android
  emulator on a GitHub-hosted `macos-14` runner (macOS runners have
  hardware-accelerated emulator support — Linux runners don't, and without
  it the emulator is unusably slow).
- Full regression runs nightly via `cron`, not on every push — 26 tests on a
  GitHub-hosted emulator is a bad trade for PR feedback latency.
- `workflow_dispatch` lets you manually pick a marker (`login`, `feed`, etc.)
  for ad-hoc runs.
- `TEST_PHONE`/`TEST_OTP` pulled from GitHub Secrets, not committed anywhere.
- Allure results, HTML report, and failure screenshots all uploaded as
  artifacts with 14-day retention.
- **iOS is deliberately not included yet** — there are no iOS locators
  anywhere in this framework (all `locators/*.py` are Android
  resource-id/UiSelector). Building an iOS CI job before you have iOS
  locators would just be a job that always fails. Add it once
  `locators/ios_*.py` exists — the pattern is `actions/setup-xcode` +
  `xcrun simctl boot` instead of `reactivecircus/android-emulator-runner`.
- **You'll need to decide:** GitHub-hosted `macos-14` runners cost more
  per-minute than Linux runners (this is real budget, not a technicality) —
  if that's a concern, a self-hosted runner with a persistent emulator/real
  device attached avoids per-minute macOS billing entirely at the cost of
  maintaining that machine yourself.

## Parallel execution — built: worker-aware device resolution

This was the one place I wouldn't just flip a switch, because it doesn't
work by default:

**The problem:** `pytest-xdist` parallelizes test *scheduling* across worker
processes. It does nothing about the fact that your `driver` fixture always
requests whatever device `--device` specifies. Run `pytest -n 3` today and
all 3 workers try to attach to the *same* emulator/UDID simultaneously —
that's not a performance win, it's a way to corrupt three test runs at once.

**What I built:** `conftest.py::_resolve_device()` reads `PYTEST_XDIST_WORKER`
(xdist sets this to `gw0`, `gw1`, `gw2`... per worker) and a `PARALLEL_DEVICES`
env var you set, and maps worker → device by index:

```bash
PARALLEL_DEVICES=emulator,real_device_1,real_device_2 \
pytest -n 3 tests/ --device emulator --env qa -m smoke
```

Each worker now gets its own device. Fewer devices than workers → the
excess workers fall back to `--device` and log a warning (so you find out
from the log, not from a mysteriously flaky run).

**What you still need before this actually helps:**
- Physical devices/emulators — 3 workers need 3 real UDIDs, not 3 config
  entries pointing at hardware that doesn't exist. `device_config.py` has
  slots; you need the actual devices.
- **A real risk worth flagging explicitly:** your test data
  (`testdata/test_data.py`) has exactly **one** valid login account. If two
  parallel workers both log into that same account on different devices at
  the same time, you don't know how the HiPi backend handles concurrent
  sessions for one user — it might work fine, might force-logout one
  session, might cause state conflicts on shared data (e.g. two workers
  commenting/following simultaneously as the "same" user). This isn't a
  framework problem I can fix in code — it needs either multiple dedicated
  test accounts (one per parallel worker) or a confirmed answer from
  whoever owns the HiPi backend about concurrent-session behavior. I'd
  resolve this before trusting parallel results, not after.

## Real device execution — built: `core/cloud_driver_factory.py`

Added BrowserStack App Automate support as a working example (Sauce Labs /
LambdaTest are the identical capability shape with `bstack:options` swapped
for `sauce:options` / `lt:options` — trivial to add a sibling function if
you pick a different provider later).

Deliberately **not wired in automatically** — the module docstring explains
why: pointing at a real device farm by accident burns real paid minutes,
and I'd rather you flip that on with one explicit line in `conftest.py`
than have it silently active. Two entries added to `device_config.py`
(`browserstack_android`, `browserstack_ios`) as placeholders — both need a
BrowserStack account, `BROWSERSTACK_USERNAME`/`ACCESS_KEY` env vars, and an
already-uploaded app hash before they'll do anything.

**You'll need to decide:** which provider (if any) — I picked BrowserStack
purely as the most common example, not because I know your budget or
existing vendor relationships. If you're already paying for AWS Device Farm
or Sauce Labs, say so and I'll add that instead of BrowserStack.

## Scalability — recommendation, not built (no code to write yet)

For a 26-test suite, the honest scaling path is:

1. **Now → next month:** local emulator + CI smoke gate + nightly
   regression. This is what's built. Don't add more infrastructure than
   this until something on this list actually hurts.
2. **If the suite grows past ~75-100 tests or multiple people start writing
   tests simultaneously:** worth revisiting test data (multiple accounts,
   as above), and genuinely parallelizing regression in CI (real device
   farm, not GitHub-hosted emulators, at that volume).
3. **If you add a second app or a backend you own:** *then* API-driven
   pre-test setup / data seeding becomes worth the complexity. Not before —
   building it speculatively for one app with no owned backend is the
   "unnecessary enterprise components" trap the original mega-prompt was
   heading toward.

I'd rather revisit this list with you once the current suite has actually
run green a few times, than pre-build for a scale you haven't hit yet.
