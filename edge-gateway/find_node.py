import asyncio
from asyncua import Client

async def find_exact_node():
    async with Client("opc.tcp://localhost:4840") as client:
        # 1. Tulostetaan nimiavaruudet (Namespaces)
        ns_array = await client.get_namespace_array()
        for idx, uri in enumerate(ns_array):
            print(f"ns={idx}: {uri}")

        # 2. Kokeillaan yleisimmät CODESYS-etuliitteet
        candidates = [
            "Device",
            "CODESYS Control Win V3 x64",
            "CODESYS Control Win V3",
        ]
        for dev in candidates:
            nid = f"ns=4;s=|var|{dev}.Application.PLC_PRG.nTotalCount"
            try:
                val = await client.get_node(nid).read_value()
                print(f"\nOSUMA! Oikea Node ID on:\n{nid}  (arvo: {val})")
                return
            except Exception as e:
                print(f"Ei osumaa ({dev}): {type(e).__name__}")

asyncio.run(find_exact_node())
