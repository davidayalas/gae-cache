import webapp2
from google.appengine.api import urlfetch
import time

from lib.gae_cache import cache

class MainHandler(webapp2.RequestHandler):

	def get(self):

		init_time = time.time()
		url = "http://loripsum.net/api/9000/short/headers"; #1.5MB aprox request html, gae_cache.cache will split it in 2 blocks
		c = cache.get("content")
		
		ttl = 15

		if c is None:

			try:
				c = urlfetch.fetch(url, deadline=60).content
				cache.set("content", c, ttl) #ttl = 15 seconds
				cache.set("time", str(int(round(time.time() * 1000))))
				c = " - content is <strong style='color:red'>from live</strong> <br /><br /><br />" + c
			except:
				c = "Unexpected error"		
		else:
			c = " - content is <strong style='color:red'>from cache</strong> <br /><br /><br />" + c 


		last_cache = cache.get("time")

		if last_cache is not None:
			last_cache = ttl-((int(round(time.time() * 1000))-int(last_cache))/1000)
			if last_cache > ttl or last_cache<1:
				last_cache = ttl
		else:
			last_cache = ttl			

		c = " - cache is set to ttl=<strong style='color:red'>" + str(ttl) + "s</strong><br /><br /> - content will expire in <strong style='color:red'>" + str(last_cache) + "s</strong><br /><br />- load time: <strong style='color:red'>" + str(round((time.time()-init_time)*100)/100) + "s</strong><br /><br />" + c 


		self.response.out.write(c[0:c[0:3000].rfind(" ")] + "[...]")

app = webapp2.WSGIApplication([('/', MainHandler)],debug=True)