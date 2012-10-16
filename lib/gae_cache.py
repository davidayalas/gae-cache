#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from google.appengine.api import memcache
from google.appengine.ext import blobstore
from google.appengine.api import files
from array import array
import time

class cache:

	__memcache_block = 1000000

	def __init__(cls):
		pass

	@classmethod
	def __getBlobkey(cls, key):
		r = blobstore.BlobInfo.all()
		_key = None
		for a in r:	
			if a.filename==key:
				_key = a.key()
				break

		return _key

	@classmethod
	def __deleteBlob(cls,key):
		r = blobstore.BlobInfo.all()
		for a in r:	
			if a.filename==key:
				blobstore.delete(a.key())
				break

	@classmethod
	def __saveBlob(cls, key, data, expire=0):
		#try:
		cls.__deleteBlob(key)
		file_name = files.blobstore.create(mime_type='text/plain',_blobinfo_uploaded_filename=key)
		with files.open(file_name, 'a') as f:
			f.write(str(expire)+"\n\r")
			f.write(str(int(round(time.time() * 1000))) + "\n\r")
			f.write(data)
		files.finalize(file_name)	
		#except Exception,e:
		#	pass

	@classmethod
	def __checkIfExpired(cls, value):

		ttl = value[0:value.find("\n\r")]
		if ttl and ttl.isdigit():
			ttl = int(ttl)

		value = value[value.find("\n\r")+2:]	
		timestamp = value[0:value.find("\n\r")]	

		if timestamp and timestamp.isdigit():
			timestamp = int(timestamp)

		value = value[value.find("\n\r")+2:]
		if ttl==0 or (timestamp+(ttl*1000))>int(round(time.time()*1000)):
			
			if ttl!=0:
				if int(((timestamp+(ttl*1000))-int(round(time.time()*1000)))/1000)>0:
					ttl = int(((timestamp+(ttl*1000))-int(round(time.time()*1000)))/1000)
				else:
					ttl = 1

			return (value,ttl)

		return (None,None)
			
	@classmethod
	def __getBlob(cls, _key):
		if not _key is None:

			_clau = cls.__getBlobkey(_key)
			if not _clau is None:
				bi =  blobstore.get(_clau)
				br = bi.open()
				value = br.read()
				return cls.__checkIfExpired(value);
			else:
				z=0
				_clau = cls.__getBlobkey(_key+"_"+str(z))
				s=[]
				while not _clau is None:
					bl = blobstore.get(_clau)
					br = bl.open()
					s.append(br.read())
					z=z+1
					_clau = cls.__getBlobkey(_key+"_"+str(z))

				if z>0:	
					value = "".join(s)
					return cls.__checkIfExpired(value);

				else:
					return (None,None)
		else:
			return (None,None)		
			
	@classmethod
	def get(cls, key, maxsize=None):
		if not maxsize is None:
			cls.__memcache_block = maxsize
	
		if memcache.get(key):
			return memcache.get(key)
		else:
			#s=bytearray()
			s=[]
			z=0
			
			mk = memcache.get(key+"_"+str(z))
			if mk is None:
				(mk,ttl)=cls.__getBlob(key+"_"+str(z))
				if not mk is None:
					memcache.add(key+"_"+str(z), mk,time=ttl)

			while mk:
				#s[z*cls.memcache_block:((z+1)*(cls.memcache_block))] = mk
				s.append(mk)
				z=z+1
				mk = memcache.get(key+"_"+str(z))

				if mk is None:
					(mk,ttl)=cls.__getBlob(key+"_"+str(z))
					if not mk is None:
						memcache.add(key+"_"+str(z), mk,time=ttl)
					else: #item is expired
						if z==0:
							s = None
							break;	
			if z>0:
				if not s is None:
					s = "".join(s)
				
				return s
			else:
				(content,ttl) = cls.__getBlob(key)
				if content:
					if ttl is None:
						ttl=0
					memcache.add(key, content,time=ttl)
					return content
				else:
					return None

	@classmethod
	def remove(cls, key):
		if memcache.get(key):
			memcache.delete(key)
			cls.__deleteBlob(key)
		else:
			r = blobstore.BlobInfo.all()
			_key = None
			for a in r:	
				if a.filename.find(key)==0:
					memcache.delete(a.filename)
					blobstore.delete(a.key())
				

	@classmethod
	def set(cls, key, data, ttl=0, backup=True, maxsize=None):
		if data is None:
			return

		if ttl and str(ttl).isdigit():
			ttl = int(ttl)
		else:
			ttl = 0	

		if not maxsize is None:
			cls.__memcache_block = maxsize

		#ba = bytearray(data)
		ba = array("B",data)
		ln = len(ba)

		if ln>cls.__memcache_block:
			blocks = ln/cls.__memcache_block
			res = ln%cls.__memcache_block
			bls={}
			cont = 0
			while cont < blocks:
				bls[key+"_"+str(cont)] = (ba[cont*cls.__memcache_block:((cont+1)*(cls.__memcache_block))-1]).tostring()
				if backup:
					cls.__deleteBlob(key+"_"+str(cont))
					cls.__saveBlob(key+"_"+str(cont),bls[key+"_"+str(cont)],str(ttl))
				cont=cont+1
			
			if res>0:
				bls[key+"_"+str(cont)]=(ba[cont*cls.__memcache_block-1:(cont*cls.__memcache_block)+res+1]).tostring()
				if backup:
					cls.__deleteBlob(key+"_"+str(cont))
					cls.__saveBlob(key+"_"+str(cont),bls[key+"_"+str(cont)],ttl)
			
			memcache.delete_multi(bls)
			memcache.add_multi(bls, time=ttl)
		else:
			cls.remove(key)
			memcache.add(key, data, time=ttl)
			if backup:
				cls.__saveBlob(key, data, ttl*1)