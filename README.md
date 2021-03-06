Google App Engine Cache with real persistence
==============================================

With this simple cache you can truly persist in GAE cache items: in memcache and in cloud storage. Memcache is volatile, so, with persistence in cloudstorage you can guarantee items are available always.

How to use
-----------

		from lib.gae_cache import cache


* cache.**set**(key, value[, ttl=0][, maxsize=1000000])<br />  

	- ttl: in seconds, default cache ttl is 0, unlimited<br />  

	- maxsize: GAE has a limit for each cache entry. Default is 1000000 of bytes. You can setup other size: gae_cache splits content in blocks of 1000000 of bytes and set cache keys with "_N" (key_1,key_2, ..., key_N)<br />  

* cache.**get**(key)<br /><br />  

* cache.**remove**(key)<br /><br />  


Requirements and dependencies
------------------------------

This new version requires to activate the cloud storage default bucket in your application: https://cloud.google.com/appengine/docs/python/googlecloudstorageclient/activate

You have to put the client library in you applicacion/lib directory: https://cloud.google.com/appengine/docs/python/googlecloudstorageclient/download

Sample code
------------

			import webapp2
			from google.appengine.api import urlfetch

			from lib.gae_cache import cache

			class MainHandler(webapp2.RequestHandler):
				def get(self):
					url = "http://loripsum.net/api/9000/short/headers"; #1.5MB aprox request html, gae_cache.cache will split it in 2 blocks
					c = cache.get("content") 
					
					if c is None:

						try:
							c = urlfetch.fetch(url, deadline=60).content
							cache.set("content", c, 15) #ttl = 15 seconds
							c = "from live <br /><br /><br />" + c
						except:
							c = "Unexpected error"		
					else:
						c = "from cache <br /><br /><br />" + c 

					self.response.out.write(c[0:3000] + "[...]")

			app = webapp2.WSGIApplication([('/', MainHandler)],debug=True)

Sample app
-----------

Sample app is running here: http://gae-cache-testing.appspot.com/
