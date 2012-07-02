#!/usr/bin/env python

import LT.Client
import LT.Server

import json, time, struct

PROPAGATE = 3


class MurkyWaters( object ):
	def __init__( self, port = 1980 ):
		self.port = port
		self._server = LT.Server.LTServer( port )
		self._client = LT.Client.LTClient()
	
		self._server.register( PROPAGATE, self._handle_propagate )
	
	def server( self, host, port ):
		self._client.server( host, port )
	
	def add( self, resource_id, data ):
		self._server.add( resource_id, data )
	
	def fetch( self, resource_id ):
		data = self._client.fetch( resource_id )
		if data:
			self.add( resource_id, data )
		return data
		
	
	def propagate( self, resource_id ):
		p = struct.pack( "<Q", self.port )
		self._client.broadcast( PROPAGATE, resource_id, p )
	
	def start( self ):
		self._server.start()
	
	def stop( self ):
		self._server.stop()
	
	def _handle_propagate( self, command, resid, addr, data ):
		if command != PROPAGATE:
			return
		port = struct.unpack_from( "<Q", data )[0]
		
		self._client.server( addr[0], port )
		entry = self._client.fetch( resid )
		self.add( resid, entry )
		
		
			
