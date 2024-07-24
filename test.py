import asyncio

import awaitlet

class N:
    @property
    def nick(self):
        return awaitlet.awaitlet(self.get_nick())

    async def get_nick(self):
        def test():
            return asyncio.sleep(1)
    
        print(test())
        return "232323"

def asyncio_sleep():
    return N().nick

print(asyncio.run(awaitlet.async_def(asyncio_sleep)))