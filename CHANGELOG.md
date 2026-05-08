# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

While the SDK is pre-1.0 (`0.x.y`), minor version bumps may include breaking
changes. Pin to a compatible range (e.g. `synthetix-sdk>=0.1,<0.2`) to opt out
of breaking updates.

<!-- changelog-next -->

## [0.1.2] - 2026-05-08

### Features

- Add getTiers SDK wrapper (#66)

### Documentation

- Comprehensive PyPI page (README, tagline, sidebar links) (#67)



## [0.1.1] - 2026-05-07

First release published via the automated PyPI publishing pipeline. No SDK code changes versus `0.1.0`.

## [0.1.0] - 2026-05-06

Initial public release on PyPI.

### Added
- `Synthetix` client with REST and WebSocket support for Synthetix V4 perps trading
- Public market data endpoints via `MarketAPI` (`/info`)
- Authenticated account and trading endpoints via `AccountAPI` (`/trade`)
- EIP-712 signing via `Signer`
- Async WebSocket manager with auto-reconnect, auth replay, and subscription replay
- Order placement helpers: `place_orders`, `market_order`, `limit_order`, `twap_order`, `stop_loss_order`, `take_profit_order`
- WebSocket-based async equivalents (`ws_*`) for trade endpoints
- Example scripts under `examples/rest/` and `examples/ws/`
