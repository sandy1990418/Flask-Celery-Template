import asyncio


def async_generator_to_sync(async_gen):
    """A function for converting asynchronous to synchronous"""
    loop = asyncio.new_event_loop()
    try:
        while True:
            try:
                yield loop.run_until_complete(async_gen.__anext__())
            except StopAsyncIteration:
                break
    finally:
        loop.close()
