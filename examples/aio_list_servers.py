"""Test script using asyncio lib"""
#!/usr/bin/env python
import os
import sys
import asyncio
from naapi.aioapi import (
    NetActuateNodeDriver,
)

API_KEY = os.getenv('NETACTUATE_API_KEY')

if API_KEY is None:
    print("Please set the NETACTUATE_API_KEY environment variable so I can log you in")
    sys.exit(1)

async def main():
    """Basic Main"""
    conn = NetActuateNodeDriver(API_KEY)
    servers = await conn.servers()
    print(servers)

asyncio.run(main())
