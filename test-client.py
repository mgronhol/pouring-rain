#!/usr/bin/env python

# Simple client, fetches data from two instances

import LT.Client


client = LT.Client.LTClient()

client.server( "127.0.0.1", 1980 )
client.server( "127.0.0.1", 1981 )

print client.fetch( 1000 )

