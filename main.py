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