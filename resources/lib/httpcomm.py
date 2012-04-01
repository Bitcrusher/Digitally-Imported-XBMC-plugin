import zlib
import httplib
import urllib
import urllib2
import gzip
import StringIO
import cookielib

class HTTPComm :
	# Login
	def post( self, url, postdata ) :
		print "trying to log in"
	
		cj = cookielib.CookieJar()
		# create an opener
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

		# Add useragent, sites don't like to interact with scripts
		opener.addheaders = [
			('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8'),
			('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
			('Accept-Language', 'en-gb,en;q=0.5'),
			('Accept-Encoding', 'gzip,deflate'),
			('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
			('Keep-Alive', '115'),
			('Connection', 'keep-alive'),
			('Cache-Control', 'max-age=0'),
			]
		
		resp = opener.open(url, postdata)
	
		# Compressed (gzip) response...
		if resp.headers.get( "content-encoding" ) == "gzip":
			htmlGzippedData = resp.read()
			stringIO        = StringIO.StringIO( htmlGzippedData )
			gzipper         = gzip.GzipFile( fileobj = stringIO )
			htmlData        = gzipper.read()
		else :
			htmlData = resp.read()
			
		resp.close()
		
		# Return html
		return htmlData

	# GET
	def get( self, url ):
		#create an opener
		opener = urllib2.build_opener()
		#Add useragent, sites don't like to interact with scripts
		opener.addheaders = [
			('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8'),
			('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
			('Accept-Language', 'en-gb,en;q=0.5'),
			('Accept-Encoding', 'gzip,deflate'),
			('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
			('Keep-Alive', '115'),
			('Connection', 'keep-alive'),
			('Cache-Control', 'max-age=0'),
			]

		resp = opener.open(url)

		# Compressed (gzip) response...
		if resp.headers.get( "content-encoding" ) == "gzip":
			htmlGzippedData = resp.read()
			stringIO        = StringIO.StringIO( htmlGzippedData )
			gzipper         = gzip.GzipFile( fileobj = stringIO )
			htmlData        = gzipper.read()
		else :
			htmlData = resp.read()
		
		resp.close()
		
		# Return html
		return htmlData