#!/usr/bin/env python

from MurkyWaters import MurkyWaters

import time, json, sys

import BaseHTTPServer

import os

import zlib

def save_file( config, resid, data ):
	path = os.path.join( config['data-dir'], "%x"%resid )
	with open( path, 'wb' ) as handle:
		handle.write( zlib.compress( data ) ) 


murky = None
files = {}

fn = "murky-config.json"

if len( sys.argv ) > 1:
	fn = sys.argv[1]

config = json.load( open( fn ) )


class MurkyProxy( BaseHTTPServer.BaseHTTPRequestHandler ):
	
	def do_GET( self ):
		global murky, files, config
		
		if len( self.path ) > 1:
			try:
				resid = int( self.path[1:] )
				#print "Fetching", resid
				if resid in files:
					content = files[resid]
				else:
					content = murky.fetch( resid )
				if content:
					self.send_response( 200 )
					self.end_headers()
					self.wfile.write( content )
				else:
					self.send_response( 404 )
					self.end_headers()
					

			except ValueError:
				self.send_response( 404 )
				self.end_headers()
				return
		else:
			self.send_response( 404 )
			self.end_headers()
		#self.send_response( 200 )
		#self.end_headers()
		return

	def do_PUT( self ):
		global murky, files, config
		
		if len( self.path ) > 1:
			try:
				resid = int( self.path[1:] )
				#print resid
				#content = murky.fetch( resid )
				L = int( self.headers['content-length'] )
				data = self.rfile.read( L )
				#print "Adding", resid, ":", data
				murky.add( resid, data )
				murky.propagate( resid )
				
				save_file( config, resid, data )
				
				files[resid] = data
				self.send_response( 200 )
				self.end_headers()
				self.wfile.write( json.dumps( {'response': 'Ok.'} ) + "\n" )

			except ValueError:
				self.send_response( 400 )
				self.end_headers()
				return
		else:
			self.send_response( 404 )
			self.end_headers()
		
if __name__ == '__main__':
	
	server = BaseHTTPServer.HTTPServer( (config['http']['host'], config['http']['port']), MurkyProxy )


	murky = MurkyWaters( save_file, config )
	murky.start()

	servers = json.load( open( config['servers-list'] ) )
	for entry in servers:
		murky.server( entry['host'], entry['port'] )

	local_files = os.listdir( config['data-dir'] )
	for fn in local_files:
		try:
			resid = int( fn, 16 )
			path = os.path.join( config['data-dir'], fn )
			data = zlib.decompress( open( path, 'rb' ).read() )
			files[resid] = data
			murky.add( resid, data )
			if config['behaviour']['propagate-on-startup']:
				murky.propagate( resid )
		except ValueError:
			pass
		
		
	

	
	try:
		print "[%s] Murky Waters started. (press ctrl-c to stop)"% time.strftime( "%Y-%m-%d %H:%M:%S" )
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	server.shutdown()
	murky.stop()
