#!/usr/bin/env python

# Simple server, pretends to be two separate instances

import LT.Server
import sys

server0 = LT.Server.LTServer( 1980 )
server1 = LT.Server.LTServer( 1981 )

server0.add( 1, "Hello World!" )
server1.add( 1, "Hello World!" )

server0.add( 1000, LT.Server.read_file( sys.argv[0] ) )
server1.add( 1000, LT.Server.read_file( sys.argv[0] ) )

server0.start()
server1.start()

print "Server(s) started. Press enter to stop."

raw_input()

server0.stop()
server1.stop()
