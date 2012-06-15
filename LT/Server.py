#!/usr/bin/env python

# Pouring Rain Server library
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




import SocketServer

import threading

import socket

import struct

import sys

import Luby

import json

import time


class OutboundStreamer( threading.Thread ):
	def __init__( self, streams, locks, timeouts, generators ):
		threading.Thread.__init__( self )
		self.streams = streams
		self.locks = locks
		self.timeouts = timeouts
		self.generators = generators
		self.sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
		self.done = False
		self.T = 5.0
	
	def run( self ):
		while not self.done:
			resources = self.streams.keys()
			for resid in resources:
				with self.locks[resid]:
					if len( self.streams[resid] ) > 0:
						(chunk, length) = self.generators[resid].get()
						packet = Luby.encodeChunk( chunk, resid, length )
						
						to_be_removed = []
						for client in self.streams[resid]:
							self.sock.sendto( packet, client )
							key = (client, resid )
							dt = time.time() - self.timeouts[key]
							if dt > self.T:
								to_be_removed.append( key )
						for client in to_be_removed:
							del self.timeouts[key]
							self.streams[ entry[1] ].discard( entry[0] )


class RequestHandler( SocketServer.BaseRequestHandler ):
	def handle( self ):
		data = self.request[0]
		sock = self.request[0]
		addr = self.client_address
		(command, resid ) = struct.unpack_from( "<QQ", data )
	
		if resid not in self.server.streams:
			return

		with self.server.locks[resid]:
			if command == 1:
				#print "Subscribe", resid, addr
				self.server.streams[resid].add( addr )
				self.server.timeouts[(addr, resid)] = time.time()
			else:
				#print "Unsubscribe", resid, addr
				self.server.streams[resid].discard( addr )
				key = (addr, resid)
				if key in self.server.timeouts:
					del self.server.timeouts[key]



class ThreadingUDPServer( SocketServer.ThreadingMixIn, SocketServer.UDPServer ):
		daemon_threads = True
		
		def __init__( self, address, handler_class, streams, locks, timeouts ):
			SocketServer.UDPServer.__init__( self, address, handler_class )
			self.streams = streams
			self.locks = locks
			self.timeouts = timeouts
		

class PacketGenerator( object ):
	def __init__( self, data, Npackets = 64 ):
		self.length = len( data )
		self.Npackets = Npackets
		packets = Luby.split( data, Npackets )
		self.generator = Luby.ChunkGenerator( packets )
	
	def get( self ):
		return (self.generator.chunk(), self.length )


class LTServer( object ):
	def __init__( self, port ):
		self.streams = {}
		self.locks = {}
		self.timeouts = {}
		self.generators = {}
		self.outbound = OutboundStreamer( self.streams, self.locks, self.timeouts, self.generators )
		self.server = ThreadingUDPServer( ("", port), RequestHandler, self.streams, self.locks, self.timeouts )
	
	def start( self ):
		self.outbound.start()
		self.server_thread = threading.Thread( target = self.server.serve_forever )
		self.server_thread.daemon = True
		self.server_thread.start()
	
	
	def stop( self ):
		self.server.shutdown()
		self.outbound.done = True
	
	def add( self, resource_id, data ):
		if resource_id not in self.locks:
			self.locks[ resource_id ] = threading.Lock()
		
		with self.locks[ resource_id ]:
			self.streams[ resource_id ] = set()
			self.generators[ resource_id ] = PacketGenerator( data ) 
		

def read_file( fn ):
	out = ""
	with open( fn, 'rb' ) as handle:
		out = handle.read()
	return out
