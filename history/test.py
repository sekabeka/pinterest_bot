import asyncio
import random

users = [
    {"1" : 1}, {"2" : 2}
]

async def test(user: dict):
    await asyncio.sleep(random.randint(1, 5))
    raise Exception
    print (user)


async def main():
    tasks = [
        asyncio.create_task(test(user), name=list(user.keys())[0]) for user in users
    ]
    done, pending = await asyncio.wait(tasks, return_when='FIRST_EXCEPTION')
    print (pending, done)

asyncio.run(main())