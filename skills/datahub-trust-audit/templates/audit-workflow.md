# Worked example — auditing a backtest claim

**User:** "Our `backtest_roi` on `main.matches` shows +40% ROI. Can we trust it before we ship?"

**Agent (this skill):**

1. Target URN = `urn:li:dataset:(urn:li:dataPlatform:sqlite,main.matches,PROD)`.
2. `audit_dataset(urn)` → engine reads query history and finds the split was built with
   `WHERE rand() < 0.7`. Classifies **RANDOM** → temporal leakage.
3. User supplies in-sample ROI 0.40, holdout −0.12, 677 strategies scanned → overfit flags fire.
4. Verdict:

   ```
   TRUST LAYER AUDIT — 🔴 NOT TRUSTWORTHY
   ❌ temporal_leakage — split built by a RANDOM query (from DataHub query history)
   ❌ overfit_flags — in-sample ROI 0.40 > 0.20 alarm; holdout collapsed to -0.12; 677 cells → ~16 false winners
   ```

5. Write-back confirmed: FAILURE assertion + ACTIVE incident + tags `audit-failed`,
   `temporal-leakage` on `main.matches`.
6. Explanation + fix: "The +40% is an artifact of a random split leaking future matches into
   training. Rebuild train/test with `WHERE date < '<cutoff>'` (walk-forward) and re-audit."

**Contrast — a clean case:** the same tool on a UCI Bike Sharing forecast with a proper
time-ordered split and a generalizing model returns 🟢 TRUSTWORTHY. The skill does not
false-alarm on an honest model with a modest train/test gap.
