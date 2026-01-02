import asyncio
import sys
import argparse
from decimal import Decimal
import dotenv

from strategy.paradex_arb import ParadexArb


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='跨交易所套利机器人入口',
        formatter_class=argparse.RawDescriptionHelpFormatter
        )

    parser.add_argument('--exchange', type=str, default='paradex',
                        help='使用的交易所 (paradex)')
    parser.add_argument('--ticker', type=str, default='BTC',
                        help='交易对标的 (默认: BTC)')
    parser.add_argument('--size', type=str, required=True,
                        help='每次下单买/卖的数量')
    parser.add_argument('--fill-timeout', type=int, default=5,
                        help='做市单成交超时(秒) (默认: 5)')
    parser.add_argument('--max-position', type=Decimal, default=Decimal('0'),
                        help='允许持有的最大仓位 (默认: 0)')
    parser.add_argument('--long-threshold', type=Decimal, default=Decimal('10'),
                        help='Paradex 做多阈值 (默认: 10)')
    parser.add_argument('--short-threshold', type=Decimal, default=Decimal('10'),
                        help='Paradex 做空阈值 (默认: 10)')
    return parser.parse_args()


def validate_exchange(exchange):
    """Validate that the exchange is supported."""
    supported_exchanges = ['paradex']
    if exchange.lower() not in supported_exchanges:
        print(f"错误: 不支持的交易所 '{exchange}'")
        print(f"支持的交易所: {', '.join(supported_exchanges)}")
        sys.exit(1)


async def main():
    """Main entry point that creates and runs the cross-exchange arbitrage bot."""
    args = parse_arguments()

    dotenv.load_dotenv()

    # Validate exchange
    validate_exchange(args.exchange)

    try:
        bot = ParadexArb(
            ticker=args.ticker.upper(),
            order_quantity=Decimal(args.size),
            fill_timeout=args.fill_timeout,
            max_position=args.max_position,
            long_ex_threshold=Decimal(args.long_threshold),
            short_ex_threshold=Decimal(args.short_threshold)
        )

        # Run the bot
        await bot.run()

    except KeyboardInterrupt:
        print("\n用户中断跨交易所套利")
        return 1
    except Exception as e:
        print(f"运行跨交易所套利失败: {e}")
        import traceback
        print(f"完整堆栈: {traceback.format_exc()}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
