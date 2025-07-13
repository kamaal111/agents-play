import asyncio

from foreign_exchange.graph import foreign_exchange_graph_async_invoke


async def main() -> None:
    end_state = await foreign_exchange_graph_async_invoke()
    print(end_state)


if __name__ == "__main__":
    asyncio.run(main())
