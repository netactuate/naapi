naapi - NetActuate API
=========

Description
------------

This package makes available both a standard and an asyncio class that allow you to write your code in either style. They are both quite basic and easy to use.

Requirements
------------

request >= 2.21.0

Installation
------------

From pypi (Not just yet)

```bash
pip install naapi
```

From github:

```bash
git clone git@github.com:netactuate/naapi
cd naapi
python setup.py install
```

Examples
------------

First an example using the asyncio class

```python
#!/usr/bin/env python
import os
import sys
import asyncio
import naapi.aioapi as api

API_KEY = os.getenv('NETACTUATE_API_KEY')

async def main():
    """Basic Main"""
    conn = api.NetActuateNodeDriver(API_KEY)
    servers = await conn.servers()
    print(servers)

asyncio.run(main())
```

Next an example of the regular api

```python
#!/usr/bin/env python
import os
import sys
import pprint as pp
import naapi.api as api

API_KEY = os.getenv('NETACTUATE_API_KEY')

def main():
    """Basic main"""
    conn = api.NetActuateNodeDriver(API_KEY)
    servers = conn.servers().json()
    pp.pprint(servers)

if __name__ == '__main__':
    main()
```
