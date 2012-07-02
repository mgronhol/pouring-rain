#!/usr/bin/env python

import LT.Client
import LT.Server

import json, time, struct

PROPAGATE = 3


class MurkyWaters( object ):
	def __init__( self, storage_handler = None, config = None ):
		if config:
			self.port = config['pouring-rain']['port']
		else:
			self.port = 1980
		
		self._server = LT.Server.LTServer( self.port )
		self._client = LT.Client.LTClient()
		self.config = config
		self.storage_handler = storage_handler
		self._server.register( PROPAGATE, self._handle_propagate )
	
	def server( self, host, port ):
		self._client.server( host, port )
	
	def add( self, resource_id, data ):
		self._server.add( resource_id, data )
	
	def fetch( self, resource_id ):
		data = self._client.fetch( resource_id )
		if data:
			if self.config and self.config['behaviour']['share-content']:
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
		#print "Propagate (resid = %i) from"%resid, addr, "to port", port
		if self.config and self.config['behaviour']['auto-add-peers']:
			#print "Adding peer to cloud"
			self._client.server( addr[0], port )
		
		#print "Fetching entry from cloud"
		entry = self._client.fetch( resid )
		#print "Fetched %i bytes"%len( entry )
		self.add( resid, entry )
		if self.storage_handler:
			self.storage_handler( self.config, resid, entry )
		
		
			
