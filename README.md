# 使用说明

## 1. 安装依赖

```bash
python -m venv venv
```

激活虚拟环境：

**macOS/Linux:**

```bash
source venv/bin/activate
```

**Windows:**

```bash
venv\Scripts\activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

然后安装 Paradex SDK（跳过依赖冲突）：

```bash
pip install --no-deps -r requirements_paradex.txt
```

Windows 可能会遇到 `crypto_cpp_py` 的 `LoadLibraryEx` 报错（缺 DLL）。可安装 MinGW 运行库并确保以下 DLL 位于 `site-packages` 同目录：
`libgcc_s_seh-1.dll`、`libstdc++-6.dll`、`libwinpthread-1.dll`。

## 2. 配置环境变量

复制 `env_example.txt` 为 `.env` 并填写 API 凭证：

```bash
cp env_example.txt .env
```

```env
# Paradex 配置（必需）
PARADEX_ENV=prod
PARADEX_MARKET=BTC-USD-PERP
PARADEX_L2_PRIVATE_KEY=your_l2_private_key_here
PARADEX_L2_ADDRESS=your_l2_address_here

# Paradex L1 配置（可选，用于首次开户）
PARADEX_L1_ADDRESS=
PARADEX_L1_PRIVATE_KEY=

# Lighter 配置（必需）
API_KEY_PRIVATE_KEY=your_api_key_private_key_here
LIGHTER_ACCOUNT_INDEX=your_account_index
LIGHTER_API_KEY_INDEX=your_api_key_index
```

提示：`PARADEX_MARKET` 默认按 `{TICKER}-USD-PERP` 生成，请在币种或合约命名不一致时手动设置。

### 环境变量说明

所有参数写在 `.env`，格式为 `KEY=value`，修改后重启脚本生效。

必填：
- `PARADEX_ENV`：使用的环境（`prod` 或 `testnet`）。
- `PARADEX_MARKET`：交易标的名称（示例：`BTC-USD-PERP`）。
- `PARADEX_L2_PRIVATE_KEY` / `PARADEX_L2_ADDRESS`：Paradex L2 私钥与地址。
- `API_KEY_PRIVATE_KEY`：Lighter API 私钥。
- `LIGHTER_ACCOUNT_INDEX`：Lighter 账户索引。
- `LIGHTER_API_KEY_INDEX`：Lighter API Key 索引。

可选（影响策略/频率/日志）：
- `SPREAD_WINDOW`（默认 120）：统计用的样本数量上限。
- `SPREAD_MIN_SAMPLES`（默认 20）：样本不足时用固定阈值。
- `SPREAD_ENTRY_STD`（默认 1.5）：触发线对“价格波动”的放大倍数，越大越难触发。
- `SPREAD_EXIT_STD`（默认 0.5）：退出线的倍数，越小越容易退出。
- `SPREAD_TIER_STEP_STD`（默认 0.5）：差价变大时加仓的步长系数。
- `SPREAD_MAX_TIERS`（默认 3）：最大加仓档位数量。
- `SPREAD_MIN_STD`（默认 0.1）：最低波动值，防止阈值过低。
- `SPREAD_MIN_TIER_STEP`（默认 0.5）：最小加仓步长。
- `PARADEX_BBO_MIN_INTERVAL`（默认 0.2）：Paradex 价格刷新最小间隔（秒）。
- `POSITION_REFRESH_INTERVAL`（默认 1.5）：仓位刷新间隔（秒）。
- `POSITION_MIN_REQUEST_INTERVAL`（默认 0.5）：请求最小间隔（秒），避免请求过快。
- `LIGHTER_BOOK_STALE_AFTER`（默认 3.0）：盘口超过多少秒算过期。
- `LIGHTER_REST_BBO_CHECK_INTERVAL`（默认 5.0）：用 REST 再校验价格的间隔（秒）。
- `LIGHTER_REST_TIMEOUT`（默认 5.0）：REST 请求超时（秒）。
- `TRADING_LOOP_SLEEP`（默认 0.02）：主循环休眠时间（秒）。
- `LIGHTER_BBO_TOLERANCE`（默认 0）：允许的盘口误差。
- `POSITION_IMBALANCE_MULTIPLIER`（默认 2）：仓位不平衡阈值倍数。
- `LIGHTER_TAKER_SLIPPAGE`（默认 0.0002）：下单允许的滑点。
- `LIGHTER_TAKER_USE_MARKET`（默认 0）：是否强制市价单（1 开启，0 关闭）。
- `LIGHTER_TAKER_FORCE_IOC`（默认 0）：是否强制“立即成交否则取消”（1 开启，0 关闭）。
- 状态通知已固定为每 10 秒 1 条，未触发交易日志默认关闭。

设置示例（追加到 `.env`）：

```env
SPREAD_WINDOW=200
LIGHTER_TAKER_USE_MARKET=0
```

## 3. 运行

### 基本用法

```bash
python arbitrage.py --ticker BTC --size 0.002 --max-position 0.1 --long-threshold 10 --short-threshold 10
```

### 命令行参数

- `--exchange`：交易所名称（默认：paradex）
- `--ticker`：交易对符号（默认：BTC）
- `--size`：每笔订单的交易数量（必需）
- `--max-position`：最大持仓限制（必需）
- `--long-threshold`：做多套利触发阈值（Lighter 买一价高于 Paradex 报价超过多少即做多 Paradex 套利，默认：10）
- `--short-threshold`：做空套利触发阈值（Paradex 报价高于 Lighter 卖一价超过多少即做空 Paradex 套利，默认：10）
- `--fill-timeout`：限价单成交超时时间（秒，默认：5）

### 使用示例

```bash
# 交易 ETH，每笔订单 0.01 ETH，设置 5 秒超时
python arbitrage.py --ticker ETH --size 0.01 --long-threshold 10 --short-threshold 10 --max-position 0.1 --fill-timeout 5

# 交易 BTC，限制最大持仓为 0.1 BTC
python arbitrage.py --ticker BTC --size 0.002 --long-threshold 1 --short-threshold 20 --max-position 0.1
```

## 4. 脚本流程说明

详见 `SCRIPT_FLOW.md`。
