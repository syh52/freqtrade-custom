# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Freqtrade is a cryptocurrency trading bot written in Python. This is a production deployment configured for futures trading with NostalgiaForInfinityX7 strategy on Binance with 14x leverage.

**Key Architecture Components:**
- **FreqtradeBot** (`freqtrade/freqtradebot.py`): Main bot class orchestrating trading logic
- **IStrategy** (`freqtrade/strategy/interface.py`): Abstract base class for trading strategies
- **Exchange** (`freqtrade/exchange/`): Exchange abstraction layer using CCXT
- **Persistence** (`freqtrade/persistence/`): Database models for trades, orders, and pair locks (SQLAlchemy)
- **DataProvider** (`freqtrade/data/`): Historical data management and loading
- **RPC** (`freqtrade/rpc/`): Remote control via Telegram, REST API, and WebSocket

## Environment Setup

**Activate virtual environment (required before all commands):**
```bash
source .venv/bin/activate
```

**Install dependencies:**
```bash
# Core dependencies
pip install -e .

# Development dependencies (includes hyperopt, plotting, and testing tools)
pip install -r requirements-dev.txt

# Individual feature sets
pip install -r requirements-hyperopt.txt  # Strategy optimization
pip install -r requirements-plot.txt      # Plotting functionality
pip install -r requirements-freqai.txt    # Machine learning features
```

## Project-Specific: Startup Scripts

This project uses a modular script architecture for managing services:

### Recommended: ft Command-Line Tool

**Main control script with modular architecture:**
```bash
# Start services
./ft start --bot --ui -d              # Start both Bot and UI in background
./ft start --bot -d                   # Start only Bot
./ft start --ui                       # Start only UI
./ft start --bot --config <file> --strategy <name> -d

# Manage services
./ft status                           # Check service status
./ft stop --all                       # Stop all services
./ft stop --bot                       # Stop only Bot
./ft restart --all                    # Restart all services
./ft help                             # Show all options
```

**Architecture:**
- `ft`: Main controller routing commands to specialized scripts
- `scripts/start-bot.sh`: Bot startup with health checks and graceful shutdown
- `scripts/start-ui.sh`: FreqUI startup (requires FreqUI in `/home/dministrator/Newproject/frequi`)
- `scripts/stop.sh`: Graceful service shutdown
- `scripts/status.sh`: Service status display
- `lib/common.sh`: Shared functions (port management, process handling, health checks)

**Key features:**
- Graceful process termination (TERM → KILL fallback)
- Precise port management (8082 for Bot API, 3000 for UI)
- Real-time health checks via API ping
- Support for custom configs and strategies

### Legacy Scripts (Quick Start)

```bash
./start_all.sh              # One-click start Bot + UI (hardcoded config)
./start_bot_only.sh         # Bot only (no UI)
```

## Configuration Architecture

**Modular configuration system using `add_config_files`:**

```
user_data/
├── config-custom.json              # Main config (loads modules below)
├── config-private.json             # API keys (NOT in git)
└── config-backtest-*.json          # Backtest-specific configs

configs/                             # Config modules (auto-loaded)
├── trading_mode-futures.json       # Futures trading settings
├── pairlist-volume-binance-usdt.json  # Dynamic pairlist (VolumePairList)
└── blacklist-binance.json          # Excluded pairs
```

**Current production config:**
- Trading mode: Futures (isolated margin, 14x leverage)
- Strategy: NostalgiaForInfinityX7 v17.1.94
- Max open trades: 12 (9 long + 3 short)
- Dynamic pairlist: ~73 USDT pairs (30min refresh)
- Timeframe: 5m
- Bot API: http://127.0.0.1:8082
- Credentials: `freqtrade_user` / `freqtrade_pass123`

**Config cascade:**
1. `config-custom.json` loads modules via `add_config_files`
2. `config-private.json` overlays API keys
3. Strategy parameters override config
4. CLI arguments override all

## Testing

**Run all tests:**
```bash
pytest
```

**Run specific test file:**
```bash
pytest tests/test_<file_name>.py
```

**Run specific test method:**
```bash
pytest tests/test_<file_name>.py::test_<method_name>
```

**Run tests with coverage:**
```bash
pytest --cov=freqtrade --cov-report=html
```

**Run tests in parallel (faster):**
```bash
pytest -n auto
```

**Run tests with specific markers:**
```bash
# Run only unit tests
pytest tests/test_*.py -k "not test_integration"

# Run with verbose output
pytest -vv
```

## Debugging

**Run bot in debug mode:**
```bash
freqtrade trade --config user_data/config.json --loglevel DEBUG
```

**Dry-run mode (for testing without real money):**
```bash
# Set "dry_run": true in config.json, then:
freqtrade trade --config user_data/config.json
```

**View logs:**
```bash
# Logs are stored in user_data/logs/
tail -f user_data/logs/freqtrade.log
```

**Check Bot API health:**
```bash
curl http://127.0.0.1:8082/api/v1/ping
curl http://127.0.0.1:8082/api/v1/status | python3 -m json.tool
```

## Code Quality

**Pre-commit checks (install once):**
```bash
pre-commit install
```

**Run all checks manually:**
```bash
pre-commit run -a
```

**Individual linting tools:**
```bash
# Code style and linting
ruff check .
ruff format .

# Type checking
mypy freqtrade

# Spell checking
codespell
```

## Common Development Commands

**Create user data directory:**
```bash
freqtrade create-userdir --userdir user_data
```

**Generate new config file (interactive):**
```bash
freqtrade new-config --config user_data/config.json
```

**Create new strategy:**
```bash
freqtrade new-strategy --strategy MyStrategyName
```

**List available strategies:**
```bash
freqtrade list-strategies
```

**Download historical data:**
```bash
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT \
  --timeframes 1h 4h \
  --days 365
```

**Run backtesting:**
```bash
freqtrade backtesting \
  --strategy SampleStrategy \
  --timeframe 1h \
  --timerange 20240101-20241031
```

**Project-specific backtesting (with dynamic pairlist):**
```bash
freqtrade backtesting \
  --config user_data/config-custom.json \
  --config user_data/config-private.json \
  --strategy NostalgiaForInfinityX7 \
  --timerange 20240101-20241231
```

**Hyperparameter optimization:**
```bash
freqtrade hyperopt \
  --strategy SampleStrategy \
  --hyperopt-loss SharpeHyperOptLoss \
  --epochs 100 \
  --spaces buy sell
```

**Test pairlist generation:**
```bash
# Must set proxy for this project
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897

freqtrade test-pairlist \
  --config user_data/config-custom.json \
  --config user_data/config-private.json \
  --quote USDT
```

## Strategy Development

**Strategy structure:**
- Strategies inherit from `IStrategy` (in `freqtrade/strategy/interface.py`)
- Must implement: `populate_indicators()`, `populate_entry_trend()`, `populate_exit_trend()`
- Located in `user_data/strategies/` by default
- Use `@informative()` decorator for multi-timeframe analysis

**Key strategy attributes:**
- `minimal_roi`: Dict defining minimum ROI at different time intervals
- `stoploss`: Float defining stop-loss threshold (e.g., -0.10 for 10%)
- `timeframe`: String defining candle timeframe (e.g., "1h", "15m")
- `startup_candle_count`: Number of candles needed before generating signals
- `can_short`: Boolean enabling short positions (futures trading)
- `position_adjustment_enable`: Boolean for DCA/position adjustment

**NostalgiaForInfinityX7 specifics:**
- Timeframe: 5m (must not be overridden)
- Startup candles: 800
- Supports long and short positions
- Multiple entry modes (normal, pump, quick, rebuy, high profit, rapid, grind, top coins, scalp)
- Recommended: 6-12 open trades, 40-80 pairs, volume-based pairlist
- Must use stable coin pairs (USDT/USDC)
- Must blacklist leveraged tokens

**Testing strategies:**
```bash
# Analyze strategy for lookahead bias
freqtrade lookahead-analysis --strategy MyStrategy

# Check for recursive formula issues
freqtrade recursive-analysis --strategy MyStrategy
```

## Data Management

**User data directory structure:**
```
user_data/
├── strategies/           # Custom trading strategies
├── data/                # Historical price data (JSON/feather)
├── backtest_results/    # Backtest output files
├── hyperopt_results/    # Hyperopt optimization results
├── plot/                # Generated plots
└── logs/                # Bot log files
```

**List downloaded data:**
```bash
freqtrade list-data
```

**Convert data formats:**
```bash
freqtrade convert-data --format-from json --format-to feather
```

## Architecture Notes

**Trading Flow:**
1. `FreqtradeBot.__init__()` initializes exchange, strategy, wallets, RPC
2. `_process()` is the main loop checking for entry/exit signals
3. `Strategy.populate_indicators()` adds technical indicators to dataframe
4. `Strategy.populate_entry_trend()` marks entry signals (`enter_long`/`enter_short` columns)
5. `Strategy.populate_exit_trend()` marks exit signals (`exit_long`/`exit_short` columns)
6. `FreqtradeBot.execute_entry()` places orders based on signals
7. `FreqtradeBot.handle_trade()` manages open positions and exit conditions

**Configuration cascade:**
- Strategy parameters override config file settings
- Command-line arguments override config file
- Config validation in `freqtrade/configuration/`

**Exchange abstraction:**
- CCXT wrapper in `freqtrade/exchange/exchange.py`
- Exchange-specific overrides in `freqtrade/exchange/<exchange_name>.py`
- Leverage/margin handling in `freqtrade/leverage/`

**Persistence:**
- SQLAlchemy models: `Trade`, `Order`, `PairLock` in `freqtrade/persistence/models.py`
- Database migrations handled via Alembic-style versioning
- Supports SQLite (default), PostgreSQL, MySQL

## FreqAI (Machine Learning)

**Enable FreqAI in strategy:**
```python
from freqtrade.freqai.prediction_models.PyTorchMLPRegressor import PyTorchMLPRegressor

class MyFreqAIStrategy(IStrategy):
    def __init__(self, config: dict):
        super().__init__(config)
        self.freqai = config.get('freqai', {})
```

**Train FreqAI model during backtesting:**
```bash
freqtrade backtesting \
  --strategy MyFreqAIStrategy \
  --freqaimodel LightGBMRegressor \
  --timerange 20230101-20231231
```

## Contributing

**Create PRs against `develop` branch** (not `stable`).

**Required for new features:**
- Unit tests with good coverage
- Pass all pre-commit checks (`ruff`, `mypy`, `pytest`)
- Documentation updates if user-facing

**Code style:**
- reST format for docstrings (`:param:`, `:return:`, `:raises:`)
- Double quotes for docstrings
- Type hints on all public methods
- English for all comments, variable names, commit messages

## Project-Specific Notes

**Proxy configuration:**
This deployment requires proxy for exchange access:
```bash
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897
```

**FreqUI location:**
FreqUI is located at `/home/dministrator/Newproject/frequi` (separate repository)

**Sensitive files (NOT in git):**
- `user_data/config-private.json` - API keys
- `user_data/tradesv3.sqlite` - Trade database
- `user_data/logs/` - Log files

**Project documentation:**
- `START_HERE.md` - New user onboarding
- `PROJECT_README.md` - Project overview and architecture
- `QUICK_START.md` - Detailed startup guide
- `CONFIG_USAGE_GUIDE.md` - Configuration reference
- `BACKTEST_GUIDE.md` - Backtesting guide
- `docs/plans/2025-11-06-script-simplification-design.md` - Script architecture design

## Important References

- **Documentation:** https://www.freqtrade.io
- **Strategy Customization:** https://www.freqtrade.io/en/stable/strategy-customization/
- **Backtesting Guide:** https://www.freqtrade.io/en/stable/backtesting/
- **Hyperopt Guide:** https://www.freqtrade.io/en/stable/hyperopt/
- **FreqAI Guide:** https://www.freqtrade.io/en/stable/freqai/
- **Exchange Configuration:** https://www.freqtrade.io/en/stable/exchanges/
- **Discord Support:** https://discord.gg/p7nuUNVfP7
- **NostalgiaForInfinity Strategy:** https://iterativv.github.io/NostalgiaForInfinity/
