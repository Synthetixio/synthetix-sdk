# Examples

Usage examples for the Synthetix Python SDK. Each file is a standalone script.

## Setup

```bash
pip install synthetix-sdk
```

Public examples need no configuration. Authenticated examples require a private key:

```bash
export PRIVATE_KEY="0x..."
```

All examples use **production** by default. To use a different environment, set overrides in `.env`:

```bash
REST_URL_OVERRIDE="https://papi.synthetix.io/v1"
WS_URL_OVERRIDE="wss://papi.synthetix.io/v1/ws"
```

## REST

Synchronous examples using the REST API — market data, trading, account management, and polling patterns.

See [rest/README.md](rest/README.md) for the full list.

## WebSocket

Async examples using the WebSocket API — subscriptions, trading, and queries.

See [ws/README.md](ws/README.md) for the full list.
