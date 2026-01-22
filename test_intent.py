import asyncio
from app.main import detect_intent

async def test():
    print('Testing intent detection:')
    tests = ['Hi', 'hello', 'Internship', 'pdf', 'eligible schemes', 'I am a student']
    for t in tests:
        intent = await detect_intent(t)
        print(f'  "{t}" -> {intent}')

asyncio.run(test())
