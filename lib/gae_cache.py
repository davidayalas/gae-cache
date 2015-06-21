#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from google.appengine.api import memcache
import cloudstorage as gcs
from google.appengine.api import app_identity
import os

from array import array
import time

class cache:

    __memcache_block = 1000000
    __bucket_name = os.environ.get('BUCKET_NAME', "/" + app_identity.get_default_gcs_bucket_name() + "/")
    
    def __init__(cls):
        pass

    @classmethod
    def __getBlobkey(cls, key):
        """ Private method to get the key of a blobstore file
            param @key is String
            return key as String
        """

        r = gcs.listbucket(cls.__bucket_name)
        _key = None
        for a in r:    
            if a.filename[len(cls.__bucket_name):]==key:
                _key = a.filename[len(cls.__bucket_name):]
                break

        return _key

    @classmethod
    def __deleteBlob(cls,key):
        """ Private method to delete a blobstore file from key
            param @key is String
        """
        r = gcs.listbucket(cls.__bucket_name)
        for a in r:    
            if a.filename[len(cls.__bucket_name):]==key:
                gcs.delete(a.filename)
                break

    @classmethod
    def __saveBlob(cls, key, data, expire=0):
        """ Private method to save a key and data value in a blobstore file
            param @key is String
            param @data is String
            param @expire is Integer and Optional
        """

        cls.__deleteBlob(key)

        with gcs.open(cls.__bucket_name + key, 'w', content_type='text/plain', options={'x-goog-meta-uploaded-filename': key}) as f:
            f.write(str(expire)+"\n\r")
            f.write(str(int(round(time.time() * 1000))) + "\n\r")
            f.write(data)
            f.close()

    @classmethod
    def __checkIfExpired(cls, value):
        """ Private method that checks if content from blobstore is expired (checks its ttl and timestamp)
            param @value is String. It contains all the information separated by \n\r
            return tuple (value, tll)
        """
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
        """ Private method that gets blob content
            param @key is String
            return tuple (value, tll)
        """

        if not _key is None:

            _clau = cls.__getBlobkey(_key)
            if not _clau is None:
                br = gcs.open(cls.__bucket_name + _key)
                value = br.read()
                br.close()

                return cls.__checkIfExpired(value);
            else:
                z=0
                _clau = cls.__getBlobkey(_key+"_"+str(z))
                s=[]
                while not _clau is None:
                    br = gcs.open(cls.__bucket_name + _clau)
                    s.append(br.read())
                    br.close()

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
    def get(cls, key):
        """ Public method that gets a key from memcache or blobstore
            param @key is String
            return String
        """

        if memcache.get(key):
            return memcache.get(key)
        else:
            s=[]
            z=0
            
            mk = memcache.get(key+"_"+str(z))
            if mk is None:
                (mk,ttl)=cls.__getBlob(key+"_"+str(z))

                if not mk is None:
                    memcache.add(key+"_"+str(z), mk,time=ttl)

            while mk:
                s.append(mk)
                z=z+1
                mk = memcache.get(key+"_"+str(z))

                if mk is None:
                    (mk,ttl)=cls.__getBlob(key+"_"+str(z))
                    if not mk is None:
                        memcache.add(key+"_"+str(z), mk,time=ttl)
                    else: #item is expired
                        if z==1:
                            s = None
                            break;    

            if z>0:
                if not s is None:
                    s = "".join(s)
                else:
                    cls.remove(key);
                
                return s
            else:
                (content,ttl) = cls.__getBlob(key)
                if content:
                    if ttl is None:
                        ttl=0
                    memcache.add(key, content,time=ttl)
                    return content
                else:
                    cls.remove(key);
                    return None

    @classmethod
    def remove(cls, key):
        """ Public method that removes content from memcache and blobstore
            param @key is String
        """ 
        if memcache.get(key):
            memcache.delete(key)
            cls.__deleteBlob(key)
        else:
            r = gcs.listbucket(cls.__bucket_name)

            _key = None
            for a in r:    
                if a.filename[len(cls.__bucket_name):].find(key+"_")==0:            
                    memcache.delete(a.filename[len(cls.__bucket_name):])
                    gcs.delete(a.filename)
                

    @classmethod
    def set(cls, key, data, ttl=0, maxsize=None):
        """ Public method that sets data into memcache and blobstore
            param @key is String
            param @data is String
            param @ttl is Integer (seconds)
            param @maxsize is Integer
        """ 

        if data is None:
            return

        cls.remove(key)

        data = str(data);

        if ttl and str(ttl).isdigit():
            ttl = int(ttl)
        else:
            ttl = 0    

        if not maxsize is None:
            cls.__memcache_block = maxsize

        ba = array("B",data)
        ln = len(ba)

        if ln>cls.__memcache_block:
            blocks = ln/cls.__memcache_block
            res = ln%cls.__memcache_block
            bls={}
            cont = 0
            while cont < blocks:
                bls[key+"_"+str(cont)] = (ba[cont*cls.__memcache_block:((cont+1)*(cls.__memcache_block))-1]).tostring()
                cls.__saveBlob(key+"_"+str(cont),bls[key+"_"+str(cont)],ttl*1)
                cont=cont+1
            
            if res>0:
                bls[key+"_"+str(cont)]=(ba[cont*cls.__memcache_block-1:(cont*cls.__memcache_block)+res+1]).tostring()
                cls.__saveBlob(key+"_"+str(cont),bls[key+"_"+str(cont)],ttl*1)
            
            memcache.delete_multi(bls)
            memcache.add_multi(bls, time=ttl)
        else:
            memcache.add(key, data, time=ttl)
            cls.__saveBlob(key, data, ttl*1)
