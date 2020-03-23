"""Test script using asyncio lib"""
#!/usr/bin/env python
import os
import sys
import asyncio
import json
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
    servers = json.loads(await conn.servers())
    print("server 0: ", servers[0])
    locations = json.loads(await conn.locations())
    print("location 0: ", locations[0])
    bw_report = json.loads(await conn.bandwidth_report(mbpkgid=servers[0]['mbpkgid']))
    print("bw_report: ", bw_report)

asyncio.run(main())
