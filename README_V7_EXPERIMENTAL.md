# Binance Early-Pump Scanner V7 — Experimental / Paper Testing Only

V7 is an isolated experimental fork built from the supplied V6 archive. It uses V7-specific source filenames, GitHub Actions workflows, state, logs, and result CSVs. It does not overwrite V5 or V6. Historical V6 signal rows and state were intentionally not copied, so V7 starts with a clean evaluation history.

## Safety-first changes in this fork
- Automatic threshold changes are **disabled by default** (`AUTO_LEARN=0`).
- The self-learning workflow is configured as dry-run, so it reports proposed changes without applying them.
- V7 has independent workflow concurrency groups and V7-specific state/output paths.
- Existing signal logic is retained as a baseline initially; no profitability improvement is claimed. This avoids combining unvalidated strategy changes before a clean V7 baseline is measured.

## Before enabling
1. Review `.github/workflows/scanner-v7.yml` and `.github/workflows/backtest-v7.yml`.
2. Configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as repository Actions secrets if Telegram alerts are wanted. Never put tokens in source files.
3. Run the V7 backtest workflow first, inspect the report and costs, then use paper alerts only. Do not trade real funds based on unvalidated signals.
4. Keep `AUTO_LEARN=0` until a separate walk-forward test shows that learned thresholds improve net expectancy after fees/slippage across more than one period.

## Current known limitation
The supplied V6 report showed negative net expectancy after modeled fees and slippage. V7 is therefore a safe isolated baseline, not a claimed fix for signal quality. The next research step is to align live/backtest gates and run clean walk-forward experiments, with all rejected candidates and outcomes logged.
