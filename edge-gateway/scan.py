import asyncio
from asyncua import Client

async def main():
    async with Client("opc.tcp://localhost:4840") as client:
        async def walk(node, depth=0):
            if depth > 7:
                return
            for child in await node.get_children():
                bname = await child.read_browse_name()
                nid = child.nodeid.to_string()
                if "PLC_PRG" in nid or "CODESYS" in bname.Name or bname.Name in ["nSystemState", "nTotalCount", "nSortedACount", "nSortedBCount", "eState"]:
                    print(f"{'  '*depth}{bname.Name}  -->  {nid}")
                await walk(child, depth + 1)
        await walk(client.nodes.objects)

asyncio.run(main())
