import asyncio
from asyncua import Client

async def check():
    client = Client("opc.tcp://127.0.0.1:4840")
    eps = await client.connect_and_get_server_endpoints()
    for ep in eps:
        print("Policy:", ep.SecurityPolicyUri.split("#")[-1], "| Mode:", ep.SecurityMode, "| Tokens:", [t.TokenType for t in ep.UserIdentityTokens])

asyncio.run(check())
