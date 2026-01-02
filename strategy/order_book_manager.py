"""Order book management for Lighter exchange."""
import asyncio
import logging
import time
from decimal import Decimal
from typing import Tuple, Optional


class OrderBookManager:
    """Manages Lighter order book state."""

    def __init__(self, logger: logging.Logger):
        """Initialize order book manager."""
        self.logger = logger

        # Lighter order book state
        self.lighter_order_book = {"bids": {}, "asks": {}}
        self.lighter_best_bid: Optional[Decimal] = None
        self.lighter_best_ask: Optional[Decimal] = None
        self.lighter_order_book_ready = False
        self.lighter_order_book_offset = 0
        self.lighter_order_book_sequence_gap = False
        self.lighter_snapshot_loaded = False
        self.lighter_order_book_lock = asyncio.Lock()
        self.lighter_last_update_ts: Optional[float] = None
        self.lighter_last_snapshot_ts: Optional[float] = None
        self.lighter_ready_event = asyncio.Event()
        self.lighter_update_event = asyncio.Event()

    # Lighter order book methods
    async def reset_lighter_order_book(self):
        """Reset Lighter order book state."""
        async with self.lighter_order_book_lock:
            self.lighter_order_book["bids"].clear()
            self.lighter_order_book["asks"].clear()
            self.lighter_order_book_offset = 0
            self.lighter_order_book_sequence_gap = False
            self.lighter_snapshot_loaded = False
            self.lighter_best_bid = None
            self.lighter_best_ask = None
            self.lighter_order_book_ready = False
            self.lighter_last_update_ts = None
            self.lighter_last_snapshot_ts = None
            self.lighter_ready_event.clear()
            self.lighter_update_event.clear()

    def mark_lighter_snapshot(self):
        """Mark initial snapshot receipt."""
        now = time.monotonic()
        self.lighter_last_snapshot_ts = now
        self.lighter_last_update_ts = now
        self.lighter_ready_event.set()
        self.lighter_update_event.set()

    def mark_lighter_update(self):
        """Mark order book update receipt."""
        self.lighter_last_update_ts = time.monotonic()
        self.lighter_update_event.set()

    def is_lighter_order_book_stale(self, max_age: float) -> bool:
        """Check if the order book is stale."""
        if self.lighter_last_update_ts is None:
            return True
        return (time.monotonic() - self.lighter_last_update_ts) > max_age

    async def wait_for_lighter_ready(self, timeout: float) -> bool:
        """Wait for initial snapshot."""
        try:
            await asyncio.wait_for(self.lighter_ready_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def wait_for_lighter_update(self, timeout: float) -> bool:
        """Wait for next order book update."""
        try:
            await asyncio.wait_for(self.lighter_update_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
        finally:
            self.lighter_update_event.clear()

    def update_lighter_order_book(self, side: str, levels: list):
        """Update Lighter order book with new levels."""
        for level in levels:
            # Handle different data structures - could be list [price, size] or dict {"price": ..., "size": ...}
            if isinstance(level, list) and len(level) >= 2:
                price = Decimal(level[0])
                size = Decimal(level[1])
            elif isinstance(level, dict):
                price = Decimal(level.get("price", 0))
                size = Decimal(level.get("size", 0))
            else:
                self.logger.warning(f"意外的档位格式: {level}")
                continue

            if size > 0:
                self.lighter_order_book[side][price] = size
            else:
                # Remove zero size orders
                self.lighter_order_book[side].pop(price, None)

    def validate_order_book_offset(self, new_offset: int) -> bool:
        """Validate order book offset sequence."""
        if new_offset <= self.lighter_order_book_offset:
            self.logger.warning(
                f"乱序更新: new_offset={new_offset}, "
                f"current_offset={self.lighter_order_book_offset}")
            return False
        return True

    def validate_order_book_integrity(self) -> bool:
        """Validate order book integrity."""
        # Check for negative prices or sizes
        for side in ["bids", "asks"]:
            for price, size in self.lighter_order_book[side].items():
                if price <= 0 or size <= 0:
                    self.logger.error(f"无效的订单簿数据: {side} price={price}, size={size}")
                    return False
        return True

    def get_lighter_best_levels(self) -> Tuple[Optional[Tuple[Decimal, Decimal]],
                                               Optional[Tuple[Decimal, Decimal]]]:
        """Get best bid and ask levels from Lighter order book."""
        best_bid = None
        best_ask = None

        if self.lighter_order_book["bids"]:
            best_bid_price = max(self.lighter_order_book["bids"].keys())
            best_bid_size = self.lighter_order_book["bids"][best_bid_price]
            best_bid = (best_bid_price, best_bid_size)

        if self.lighter_order_book["asks"]:
            best_ask_price = min(self.lighter_order_book["asks"].keys())
            best_ask_size = self.lighter_order_book["asks"][best_ask_price]
            best_ask = (best_ask_price, best_ask_size)

        return best_bid, best_ask

    def get_lighter_bbo(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """Get Lighter best bid/ask prices."""
        return self.lighter_best_bid, self.lighter_best_ask

    def get_lighter_mid_price(self) -> Decimal:
        """Get mid price from Lighter order book."""
        best_bid, best_ask = self.get_lighter_best_levels()

        if best_bid is None or best_ask is None:
            raise Exception("无法计算中间价，订单簿数据缺失")

        mid_price = (best_bid[0] + best_ask[0]) / Decimal('2')
        return mid_price

    def update_lighter_bbo(self):
        """Update Lighter best bid/ask from order book."""
        best_bid, best_ask = self.get_lighter_best_levels()
        if best_bid is not None:
            self.lighter_best_bid = best_bid[0]
        if best_ask is not None:
            self.lighter_best_ask = best_ask[0]
