"""Position tracking for Paradex and Lighter exchanges."""
import asyncio
import json
import logging
import requests
import sys
import time
from decimal import Decimal


class PositionTracker:
    """Tracks positions on both exchanges."""

    def __init__(self, ticker: str, paradex_client, paradex_market: str,
                 lighter_base_url: str, account_index: int, logger: logging.Logger):
        self.ticker = ticker
        self.paradex_client = paradex_client
        self.paradex_market = paradex_market
        self.lighter_base_url = lighter_base_url
        self.account_index = account_index
        self.logger = logger

        self.paradex_position = Decimal('0')
        self.lighter_position = Decimal('0')
        self.refresh_interval = 0.0
        self.min_request_interval = 0.0
        self._last_refresh_ts = 0.0
        self._last_paradex_request_ts = 0.0
        self._last_lighter_request_ts = 0.0

    async def _run_paradex(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def _run_request(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    def set_refresh_config(self, refresh_interval: float, min_request_interval: float):
        self.refresh_interval = max(0.0, refresh_interval)
        self.min_request_interval = max(0.0, min_request_interval)

    async def refresh_positions(self, force: bool = False):
        now = time.monotonic()
        if (not force and self.refresh_interval > 0 and
                (now - self._last_refresh_ts) < self.refresh_interval):
            return self.paradex_position, self.lighter_position

        self.paradex_position = await self.get_paradex_position()
        self.lighter_position = await self.get_lighter_position()
        self._last_refresh_ts = time.monotonic()
        return self.paradex_position, self.lighter_position

    def _parse_paradex_position_size(self, position: dict) -> Decimal:
        for key in ("position", "size", "qty", "net_size", "position_size"):
            value = position.get(key)
            if value is not None:
                try:
                    return Decimal(str(value))
                except Exception:
                    continue

        side = position.get("side") or position.get("direction")
        size = position.get("size") or position.get("qty")
        if size is not None and side:
            try:
                sign = -1 if str(side).upper() in ("SELL", "SHORT") else 1
                return Decimal(str(size)) * sign
            except Exception:
                return Decimal('0')

        return Decimal('0')

    async def get_paradex_position(self) -> Decimal:
        if not self.paradex_client:
            raise Exception("Paradex 客户端未初始化")

        if self.min_request_interval > 0:
            now = time.monotonic()
            wait_time = self.min_request_interval - (now - self._last_paradex_request_ts)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_paradex_request_ts = time.monotonic()

        resp = await self._run_paradex(self.paradex_client.api_client.fetch_positions)
        positions = resp.get("results") or resp.get("positions") or []
        target_market = self.paradex_market or f"{self.ticker}-USD-PERP"

        for position in positions:
            market = position.get("market") or position.get("symbol") or position.get("instrument")
            if market == target_market or (market and market.startswith(self.ticker)):
                return self._parse_paradex_position_size(position)

        return Decimal('0')

    async def get_lighter_position(self) -> Decimal:
        url = f"{self.lighter_base_url}/api/v1/account"
        headers = {"accept": "application/json"}

        current_position = None
        parameters = {"by": "index", "value": self.account_index}
        attempts = 0
        retry_delay = max(0.5, self.min_request_interval)
        while current_position is None and attempts < 10:
            try:
                if self.min_request_interval > 0:
                    now = time.monotonic()
                    wait_time = self.min_request_interval - (now - self._last_lighter_request_ts)
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                    self._last_lighter_request_ts = time.monotonic()

                response = await self._run_request(
                    requests.get,
                    url,
                    headers=headers,
                    params=parameters,
                    timeout=10,
                )
                response.raise_for_status()

                if not response.text.strip():
                    self.logger.warning("Lighter API 仓位检查返回空响应")
                    return self.lighter_position

                data = response.json()

                if 'accounts' not in data or not data['accounts']:
                    self.logger.warning(f"Lighter API 返回格式异常: {data}")
                    return self.lighter_position

                positions = data['accounts'][0].get('positions', [])
                for position in positions:
                    if position.get('symbol') == self.ticker:
                        current_position = Decimal(position['position']) * position['sign']
                        break
                if current_position is None:
                    current_position = 0

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"获取仓位时网络错误: {e}")
            except json.JSONDecodeError as e:
                self.logger.warning(f"仓位响应 JSON 解析错误: {e}")
                self.logger.warning(f"响应内容: {response.text[:200]}...")
            except Exception as e:
                self.logger.warning(f"获取仓位时出现未知错误: {e}")
            finally:
                attempts += 1
                if current_position is None and attempts < 10:
                    await asyncio.sleep(retry_delay)

        if current_position is None:
            self.logger.error(f"获取 Lighter 仓位失败，已重试 {attempts} 次")
            sys.exit(1)

        return current_position

    def update_paradex_position(self, delta: Decimal):
        self.paradex_position += delta

    def update_lighter_position(self, delta: Decimal):
        self.lighter_position += delta

    def get_current_paradex_position(self) -> Decimal:
        return self.paradex_position

    def get_current_lighter_position(self) -> Decimal:
        return self.lighter_position

    def get_net_position(self) -> Decimal:
        return self.paradex_position + self.lighter_position
