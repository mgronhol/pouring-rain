#!/usr/bin/env python

# Pouring Rain Client library
#
# Copyright (c) 2012, Markus Gronholm <markus@alshain.fi>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Alshain Oy nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL ALSHAIN OY BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 


import socket
import struct

import select

import Luby

import sys
import time
import json


def msg_subscribe( resid ):
	return struct.pack( "<QQ", 1, resid )

def msg_unsubscribe( resid ):
	return struct.pack( "<QQ", 2, resid )


class LTClient( object ):
	def __init__( self, Npackets = 64, timeout = 4.0 ):
		self.servers = []
		self.store = Luby.ChunkStore()
		self.sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
		self.Npackets = Npackets
		self.timeout = timeout
		self.fail_timeout = 1.0
	
	def server( self, host, port ):
		self.servers.append( (host, port ) )
	
	def subscribe( self, resource_id ):
		for addr in self.servers:
			self.sock.sendto( msg_subscribe( resource_id ), addr )
	
	def unsubscribe( self, resource_id ):
		for addr in self.servers:
			self.sock.sendto( msg_unsubscribe( resource_id ), addr )
	
	def fetch( self, resource_id ):
		done = False
		response = None
		last_t = time.time()
		self.subscribe( resource_id )
		while not done:
			result = select.select( [self.sock], [], [], self.fail_timeout )
			if result[0]:
				data, addr = self.sock.recvfrom( 1024 * 1024 )
				response = Luby.decodeChunk( data )
				self.store.insert( response['chunk'] )
				
				if time.time() - last_t > self.timeout:
					self.subscribe( resource_id )
					last_t = time.time()
				
				if len( self.store.solved.keys() ) == self.Npackets:
					done = True
			else:
				self.unsubscribe( resource_id )
				return None
		self.unsubscribe( resource_id )
		
		L = response['dataLen']
		return self.store.summon()[:L]
		

