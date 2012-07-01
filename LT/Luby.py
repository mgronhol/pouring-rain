#!/usr/bin/env python

# Pouring Rain Luby Transform Code implementation
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



import math, random, time, copy
from collections import defaultdict
import struct


def strxor( A, B ):
	out = ""
	#print "A", repr(A), "B", repr(B), "lenA", len(A), "lenB", len(B)
	for (a,b) in zip( A, B ):
			#out.append( chr( ord(a) ^ ord(b) ) )
			out += chr( ord(a) ^ ord(b) )
	return out



class Chunk( object ):
	def __init__( self, keys, value ):
		self.keys = keys
		self.value = value
	

class ChunkStore( object ):
	def __init__( self ):
		self.queue = {}
		self.solved = {}
		self.length = 0
	
	def set_length( self, length ):
		self.length = length
	
	def insert( self, rchunk ):
		chunk = copy.deepcopy( rchunk )
		
		key = tuple(chunk.keys)
		if key in self.queue:
			return
		
		if len( key ) == 1:
			self.solved[key] = chunk
		
		else:
			for (key,sc) in self.solved.iteritems():
				it = chunk.keys.intersection( sc.keys )
				if len( it ) > 0:
					new_keys = sc.keys.symmetric_difference( chunk.keys )
					#new_value = chunk.value ^ sc.value
					
					new_value = strxor( chunk.value, sc.value )

					chunk = Chunk( new_keys, new_value )
			if len( chunk.keys ) == 1:
				self.solved[tuple( chunk.keys)] = chunk
			else:
				if len( chunk.keys ) > 0:
					self.queue[ tuple( chunk.keys )  ] = chunk

		to_be_removed = []
		to_be_inserted = []
		skeleton_key = set( [ k[0] for k in self.solved  ]  )

		#print "chunk:",chunk.keys,"queue:",[k for k in self.queue], "skey", skeleton_key
		#raw_input()
		for (key, entry) in self.queue.iteritems():
			it = entry.keys.intersection(skeleton_key)
			new_key = entry.keys - skeleton_key
			if len( it ) > 0:
				to_be_removed.append( key )
				new_value = entry.value
				for x in it:
					#new_value = new_value ^ self.solved[ tuple( set([x]) ) ].value
					new_value = strxor( new_value, self.solved[ tuple( set([x]) ) ].value )

				to_be_inserted.append( Chunk( new_key, new_value ) )
		
		#print "removed:", to_be_removed
		#print "inserted:", [x.keys for x in to_be_inserted]
		#raw_input()
		for key in to_be_removed:
			del self.queue[key]

		for entry in to_be_inserted:
			self.insert( entry )
		#print ""

	def summon( self ):
		keys = self.solved.keys()
		keys.sort()
		out = ""
		for key in keys:
			out += self.solved[key].value
		return out[:self.length]


class ChunkGenerator( object ):
	def __init__( self, data ):
		self.data = data
		self.dist = []
		self.dist.append( 1.0/len(data) )
		for k in range( 1, len(data) ):
			self.dist.append( 1.0/(k*(k+1)) )
		
		for i in range( len(data)/5 ):
			self.dist[i] += 1.0/(i+1)

		self.dist[len(data)/5] += 0.5

		C = sum( self.dist )
		self.dist = [x/C for x in self.dist]
	
	def chunk(self):
		n = 0
		r = random.random()
		p = 0.0
		while p < r:
			p += self.dist[n]
			n += 1
		
		keys = set()
		while len(keys) < n:
			idx = random.randint( 0, len( self.data) - 1 )
			keys.add( idx )
		lkeys = list(keys)
		value = self.data[lkeys[0]]
			
		for key in lkeys[1:]:
			#value ^= data[key]
			value = strxor( value, self.data[key] )
		
		return Chunk( keys, value )


def split(data, N = 64):
	parts = []
	plen = (len(data) - (len(data) % N )) / N + 1
	for i in range( N ):
		start = i * plen
		bucket = data[start : start + plen ]  
		#parts.append( data[start : start + plen ] )
		Q = plen - len(bucket)
		bucket += chr(0)*Q
		parts.append( bucket )

	return parts


				
def encodeChunk( chunk, resourceId, dataLen, Nkeys = 64 ):
	out = ""
	# resource id
	# key
	# total data len
	# packet len
	# data
	out += struct.pack( "<Q", resourceId )
	key = 0L
	for k in chunk.keys:
		key |= (1 << k)
	#print key, chunk.keys
	out += struct.pack( "<Q", key )
	out += struct.pack( "<Q", dataLen )
	out += struct.pack( "<Q", len( chunk.value ) )
	out += chunk.value
	return out

def decodeChunk( data ):
	header = "<QQQQ"
	hlen = struct.calcsize( header )
	(resourceId, key, dataLen, packetLen ) = struct.unpack_from( header, data )
	value = data[hlen:]
	keys = set()
	for i in range( 64 ):
		if key & (1<<i) != 0:
			keys.add( i )

	return {'resourceId': resourceId, "dataLen": dataLen, 'chunk': Chunk( keys, value ) }
	
	
					
			

#import pprint
#			
#
#data = [1,2,3,4,6,7,8]
#data = [ str( chr( ord('A') + x ) + chr( ord('A') + x + 1 ) ) for x in range( 32*2 ) ]
#raw_input()
#store = ChunkStore()
#
#cgen = ChunkGenerator( data )
#
#cnt = 0
#while len( store.solved.keys() ) != len( data ):
#	chunk = cgen.chunk()
#	store.insert( chunk )
#	cnt += 1
#print "cnt",cnt
#
#z = [str(x) for x in range( 10 ) ]
#
#print split( z, 3 )


#data = ''.join([ str( chr( ord('A') + x ) + chr( ord('A') + x + 1 ) ) for x in range( 32*2 ) ])
#data_packets = split( data, 64 )
#print "data:",data
#print "data_packets", data_packets

#raw_input()
#store = ChunkStore()
#
#cgen = ChunkGenerator( data_packets )
#
#cnt = 0
#while len( store.solved.keys() ) != len( data_packets ):
#	chunk = cgen.chunk()
#	
#	packet = encodeChunk(chunk, 1337, len( data ) )
#	dchunk = decodeChunk( packet )
#	print dchunk
#	#print "in", repr(chunk.value)
#	#print "ou", repr( dchunk['chunk'].value )
#
#
#	
#	store.insert( dchunk['chunk'] )
#	cnt += 1
#print "cnt",cnt
#print "solved:", repr(store.summon()[:len(data)])


