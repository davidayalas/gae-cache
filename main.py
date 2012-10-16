from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch

from lib.gae_cache import cache

class MainHandler(webapp.RequestHandler):
	def get(self):
		url = "http://loripsum.net/api/9000/short/headers"; #1.5MB aprox request html		
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

def main():
    application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()