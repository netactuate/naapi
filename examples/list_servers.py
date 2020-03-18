"""Basic test for listing your servers"""
#!/usr/bin/env python
import os
import sys
import pprint as pp

import naapi.api as api

API_KEY = os.getenv('NETACTUATE_API_KEY')

if API_KEY is None:
    print("Please set the NETACTUATE_API_KEY environment variable so I can log you in")
    sys.exit(1)

def main():
    """Basic main"""
    conn = api.NetActuateNodeDriver(API_KEY)
    servers = conn.servers().json()
    pp.pprint(servers)

if __name__ == '__main__':
    main()
