"""
Maintain a local orderbook from diff-mode WebSocket updates.

Subscribes in diff mode and:
  1. Builds the initial book from the first snapshot message.
  2. Applies diffs using meseq/prevMeseq to detect gaps.
  3. Validates each update with a CRC32 checksum.

If a sequence gap or checksum mismatch is detected, the book is
reset and rebuilt from the next snapshot (by resubscribing).
"""

import asyncio
import binascii
import os

from dotenv import load_dotenv

from synthetix import Synthetix

load_dotenv()

SYMBOL = "BTC-USDT"
DEPTH = 50


def compute_checksum(bids: list, asks: list) -> str:
    """Reproduce the CRC32-IEEE orderbook checksum.

    Format: ``b{price}:{qty}|`` for each bid, then ``a{price}:{qty}|``
    for each ask.  Returns an 8-char lowercase hex string.
    """
    parts = []
    for level in bids:
        parts.append(f"b{level['price']}:{level['quantity']}|")
    for level in asks:
        parts.append(f"a{level['price']}:{level['quantity']}|")
    crc = binascii.crc32("".join(parts).encode()) & 0xFFFFFFFF
    return f"{crc:08x}"


class ManagedOrderbook:
    def __init__(self):
        self.bids: dict[str, str] = {}  # price -> quantity
        self.asks: dict[str, str] = {}  # price -> quantity
        self.meseq: int | None = None
        self.ready = False

    def apply_snapshot(self, data: dict, meseq: int) -> None:
        self.bids = {lvl["price"]: lvl["quantity"] for lvl in data.get("bids", [])}
        self.asks = {lvl["price"]: lvl["quantity"] for lvl in data.get("asks", [])}
        self.meseq = meseq
        self.ready = True

    def apply_diff(self, data: dict, meseq: int) -> None:
        for level in data.get("bids", []):
            if level["quantity"] == "0":
                self.bids.pop(level["price"], None)
            else:
                self.bids[level["price"]] = level["quantity"]
        for level in data.get("asks", []):
            if level["quantity"] == "0":
                self.asks.pop(level["price"], None)
            else:
                self.asks[level["price"]] = level["quantity"]
        self.meseq = meseq

    def sorted_bids(self) -> list[dict]:
        """Bids sorted descending by price, truncated to DEPTH."""
        levels = [{"price": p, "quantity": q} for p, q in self.bids.items()]
        levels.sort(key=lambda lvl: float(lvl["price"]), reverse=True)
        return levels[:DEPTH]

    def sorted_asks(self) -> list[dict]:
        """Asks sorted ascending by price, truncated to DEPTH."""
        levels = [{"price": p, "quantity": q} for p, q in self.asks.items()]
        levels.sort(key=lambda lvl: float(lvl["price"]))
        return levels[:DEPTH]

    def verify_checksum(self, expected: str) -> bool:
        return compute_checksum(self.sorted_bids(), self.sorted_asks()) == expected


async def main():
    snx = Synthetix(rest_url=os.environ.get("REST_URL_OVERRIDE"), ws_url=os.environ.get("WS_URL_OVERRIDE"))
    book = ManagedOrderbook()
    sub_id_holder: list[int] = []
    resubscribing = False

    async def resubscribe():
        """Unsub/resub in a separate task so we don't mutate state mid-dispatch."""
        nonlocal resubscribing
        if resubscribing or not sub_id_holder:
            return
        resubscribing = True
        try:
            old = sub_id_holder[0]
            new = await snx.subscribe(
                "orderbook",
                on_orderbook,
                symbol=SYMBOL,
                format="diff",
                depth=DEPTH,
            )
            sub_id_holder[0] = new
            await snx.unsubscribe(old)
        finally:
            resubscribing = False

    def on_orderbook(msg):
        msg_type = msg.get("type")
        data = msg.get("data")
        meseq = msg.get("meseq")
        prev_meseq = msg.get("prevMeseq")
        checksum = msg.get("checksum")

        # Subscribe ack — ignore
        if data is None or meseq is None:
            return

        if msg_type == "snapshot":
            book.apply_snapshot(data, meseq)
            print(f"[snapshot] meseq={meseq}  bids={len(book.bids)}  asks={len(book.asks)}")

        elif msg_type == "diff":
            if not book.ready:
                return

            # Detect sequence gap
            if book.meseq is not None and prev_meseq != book.meseq:
                print(f"[gap] expected prevMeseq={book.meseq}, got {prev_meseq} — resubscribing")
                book.ready = False
                asyncio.create_task(resubscribe())
                return

            book.apply_diff(data, meseq)

        # Verify checksum
        if book.ready and checksum:
            if book.verify_checksum(checksum):
                bids = book.sorted_bids()
                asks = book.sorted_asks()
                best_bid = bids[0]["price"] if bids else "-"
                best_ask = asks[0]["price"] if asks else "-"
                print(f"[ok] meseq={meseq}  bid={best_bid}  ask={best_ask}  checksum={checksum}")
            else:
                local = compute_checksum(book.sorted_bids(), book.sorted_asks())
                print(f"[checksum mismatch] server={checksum} local={local} — resubscribing")
                book.ready = False
                asyncio.create_task(resubscribe())

    print(f"Subscribing to {SYMBOL} orderbook (diff, depth={DEPTH})...")
    sub_id = await snx.subscribe(
        "orderbook",
        on_orderbook,
        symbol=SYMBOL,
        format="diff",
        depth=DEPTH,
    )
    sub_id_holder.append(sub_id)

    try:
        await asyncio.sleep(30)
    finally:
        await snx.unsubscribe(sub_id_holder[0])
        await snx.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
