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

## 2. 配置环境变量

复制 `env_example.txt` 为 `.env` 并填写 API 凭证：

```bash
cp env_example.txt .env
```

```env
# Variational 账户凭证（必需）
VARIATIONAL_API_KEY=your_api_key_here
VARIATIONAL_API_SECRET=your_api_secret_here

# Variational API 端点（可选）
VARIATIONAL_BASE_URL=https://api.variational.io/v1

# Variational RFQ 配置（可选）
VARIATIONAL_TARGET_COMPANY_IDS=
VARIATIONAL_RFQ_EXPIRES_SECONDS=5

# Lighter 配置（必需）
API_KEY_PRIVATE_KEY=your_api_key_private_key_here
LIGHTER_ACCOUNT_INDEX=your_account_index
LIGHTER_API_KEY_INDEX=your_api_key_index
```

## 3. 运行

### 基本用法

```bash
python arbitrage.py --ticker BTC --size 0.002 --max-position 0.1 --long-threshold 10 --short-threshold 10
```

### 命令行参数

- `--exchange`：交易所名称（默认：variational）
- `--ticker`：交易对符号（默认：BTC）
- `--size`：每笔订单的交易数量（必需）
- `--max-position`：最大持仓限制（必需）
- `--long-threshold`：做多套利触发阈值（Lighter 买一价高于 Variational 报价超过多少即做多 Variational 套利，默认：10）
- `--short-threshold`：做空套利触发阈值（Variational 报价高于 Lighter 卖一价超过多少即做空 Variational 套利，默认：10）
- `--fill-timeout`：限价单成交超时时间（秒，默认：5）

### 使用示例

```bash
# 交易 ETH，每笔订单 0.01 ETH，设置 5 秒超时
python arbitrage.py --ticker ETH --size 0.01 --long-threshold 10 --short-threshold 10 --max-position 0.1 --fill-timeout 5

# 交易 BTC，限制最大持仓为 0.1 BTC
python arbitrage.py --ticker BTC --size 0.002 --long-threshold 1 --short-threshold 20 --max-position 0.1
```
