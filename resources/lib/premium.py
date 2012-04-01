# Import
import os
import sys
import re
import string
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urllib2
import pickle
import time
from xml.dom import minidom
from urllib import quote_plus
from httpcomm import HTTPComm

handle = int(sys.argv[1])

__addon__ = xbmcaddon.Addon(id='plugin.audio.di.fm')

LIB_DIR = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), 'resources', 'lib' ) )
sys.path.append (LIB_DIR)
ART_DIR = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), 'resources', 'art', '' ) ) # path to channelart
sys.path.append (ART_DIR)

STREAM_URL	= "http://www.di.fm/login"

STREAMCACHE = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), '' ) ) + "cachestream.dat"
CHANNELTITLECACHE = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), '' ) ) + "cachechanneltitle.dat"
STREAMBITRATECACHE = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), '' ) ) + "streamrate.dat"

# Main class
class Main:
	def __init__( self ):
		print "***** premium"
		self.getPremiumStreams()
		print __addon__.getSetting('sortaz')
		
		# sort A-Z
		if __addon__.getSetting('sortaz') == "true" :
			xbmcplugin.addSortMethod( handle=handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
		
		# End of list
		xbmcplugin.endOfDirectory( handle=handle, succeeded=True )
		
	def getPremiumStreams(self) :
		# precompiling regexes that are common
		iconreplacement_re = re.compile('[ \'-]', re.I)
		cacheexpiration = (int(__addon__.getSetting("cacheexpire")) * 60)
		
		# if streamcache is too old
		print "cacheexpiration " + str(cacheexpiration)
		if (cacheexpiration != 0 and self.checkFileTime(STREAMCACHE, cacheexpiration) == True) or __addon__.getSetting("forceupdate") == "true" :
			print "Refreshing streams"
			httpCommunicator = HTTPComm()
			logindata		 = urllib.urlencode({ 'member_session[username]':  __addon__.getSetting('username'),
												  'member_session[password]':  __addon__.getSetting('password') })
			
			print "url " + STREAM_URL
			# Get frontpage of di.fm - if it fails, show a dialog in XBMC
			try :
				htmlData = httpCommunicator.post( STREAM_URL, logindata )
			except Exception:
				xbmcgui.Dialog().ok('Connection error', 'Could not connect to di.fm', 'Check your internet connection or di.fm')
				return False
			
			playlist_re 	= re.compile('xxxyyyzzz', re.I)
			stream_bitrate	= 0
			channeltitle_re = re.compile('xxxyyyzzz', re.I)
			streamurlmp3_re	= re.compile('xxxyyyzzz', re.I)
			
			print "Streamquality " + __addon__.getSetting("streamquality")
			print "Use 'My favorites' " + __addon__.getSetting("usefavorites")
			# precompiling regexes for normal/all stream
			if __addon__.getSetting("usefavorites") == 'false' :
				print "Going for Premium channels"
				if int(__addon__.getSetting("streamquality")) == 0: # Bitrate 256k
					print "Streamquality: 256k"
					playlist_re		= re.compile('<li><a href="(http://listen.di.fm/premium_high/(?!favorites)[\w\d-]+\.pls?[\w\d?&_;=-]+)">256k Broadband', re.I)
					stream_bitrate	= 262144
				elif int(__addon__.getSetting("streamquality")) == 1: # Bitrate 128k
					print "Streamquality: 128k"
					playlist_re		= re.compile('256k Broadband</a>[\s\n]*</li>[\s\n]*<li><a href="(http://listen.di.fm/premium/(?!favorites)[\w\d-]+\.pls?[\w\d?&_;=-]+)">128k Broadband', re.I)
					stream_bitrate	= 131072
				channeltitle_re = re.compile('Title1=([\s\d\w./:?\'-]*)\r?\n', re.I) # first title in .pls file
				streamurlmp3_re = re.compile('File1=([\d\w./:?_-]*)', re.I) # first stream in .pls file
			
			# precompiling regexes for 'My favorites' playlist
			elif __addon__.getSetting("usefavorites") == 'true' :
				print "Going for 'My favorites' playlist"
				if int(__addon__.getSetting("streamquality")) == 0: # Bitrate 256k
					print "Streamquality: 256k"
					playlist_re		= re.compile('<li><a href="(http://listen.di.fm/premium_high/favorites\.pls?[\w\d?&_;=-]+)">256k Broadband', re.I)
					stream_bitrate	= 262144
				elif int(__addon__.getSetting("streamquality")) == 1: # Bitrate 128k
					print "Streamquality: 128k"
					playlist_re		= re.compile('256k Broadband</a>[\s\n]*</li>[\s\n]*<li><a href="(http://listen.di.fm/premium/favorites\.pls?[\w\d?&_;=-]+)">128k Broadband', re.I)
					stream_bitrate	= 131072
				channeltitle_re = re.compile('Title[\d]+=([\s\d\w./:?\'-]*)\r?\n', re.I) # all titles in .pls file
				streamurlmp3_re = re.compile('File[\d]+=([\d\w./:?_-]*)', re.I) # all streams in .pls file
			
			# find all playlists
			playlists = playlist_re.findall(htmlData)
			if len(playlists) != None:
				print "Found " + str(len(playlists)) + " channels"
			else :
				xbmcgui.Dialog().ok('No streams found', 'Perhaps the sitedesign has changed', 'Check http://qualisoft.dk for a new version')
				return False
			
			streamurls = {}
			channeltitles = {}
			
			# List out Premium streams
			if __addon__.getSetting("usefavorites") == 'false' :
				itemnumber = 0
				while (itemnumber < len(playlists)) :
					try :
						playlist = httpCommunicator.get( playlists[itemnumber] )
						stream = streamurlmp3_re.findall(playlist)

						channeltitle = channeltitle_re.findall(playlist)
						labelstr = channeltitle[0]

						labelstr = labelstr.replace("Digitally Imported - ", "") # remove unwanted substring
						thumbnail = ART_DIR + string.lower(iconreplacement_re.sub('', str(labelstr)) + ".png") # lowercase and replace spaces in channelname, use it for channelart filename
						
						# fallback to plugin icon, if no channel art
						if not os.path.exists(thumbnail) and not os.path.isfile(thumbnail) :
							thumbnail = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), '', 'icon.png'))
						li = xbmcgui.ListItem(label=labelstr, thumbnailImage=thumbnail)
						li.setInfo("music", { "title": labelstr, "Size": stream_bitrate })
						li.setProperty("mimetype", 'audio/mpeg')
						li.setProperty("IsPlayable", "true")

						xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=stream[0], listitem=li, isFolder=False)

						# adds streamurl + title to array so it can be saved to cache
						streamurls[itemnumber] = stream[0]
						channeltitles[itemnumber] = labelstr
						
					except Exception:
						print "Could not reach the stream at " + playlists[itemnumber]
					itemnumber = itemnumber + 1
				
				if len(playlists) == 0 :
					xbmcgui.Dialog().ok('No streams found', 'Maybe your login info was incorrect', 'Please doublecheck it')
					return True

			# List 'My favorites' playlist
			elif __addon__.getSetting("usefavorites") == 'true' :
				# get whole favorite.pls
				playlist = httpCommunicator.get( playlists[0] )
				
				stream = streamurlmp3_re.findall(playlist)
				channeltitle = channeltitle_re.findall(playlist)
				print "channels " + str(len(channeltitle))
				print "streams " + str(len(stream))
				
				
				itemnumber = 0
				while (itemnumber < len(stream)) :
					labelstr = channeltitle[itemnumber]
					labelstr = labelstr.replace("Digitally Imported - ", "") # remove unwanted substring
					
					thumbnail = ART_DIR + string.lower(iconreplacement_re.sub('', str(labelstr)) + ".png") # lowercase and replace spaces in channelname, use it for channelart filename
						
					# fallback to plugin icon, if no channel art
					if not os.path.exists(thumbnail) and not os.path.isfile(thumbnail) :
						thumbnail = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), '', 'icon.png'))
					li = xbmcgui.ListItem(label=labelstr, thumbnailImage=thumbnail)
					li.setInfo("music", { "title": labelstr, "Size": stream_bitrate })
					li.setProperty("mimetype", 'audio/mpeg')
					li.setProperty("IsPlayable", "true")
					
					xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=stream[itemnumber], listitem=li, isFolder=False)

					# adds streamurl + title to array so it can be saved to cache
					streamurls[itemnumber] = stream[itemnumber]
					channeltitles[itemnumber] = labelstr
					itemnumber = itemnumber + 1

				if len(stream) == 0 :
					xbmcgui.Dialog().ok('No streams found', 'Maybe your login info was incorrect', 'Please doublecheck it')
					return True
					
			# write channels to cache
			cachefile = open(STREAMCACHE, "w") # Save stream urls
			pickle.dump(streamurls, cachefile, protocol=0)
			cachefile.close()

			cachefile = open(CHANNELTITLECACHE, "w") # Save stream titles
			pickle.dump(channeltitles, cachefile, protocol=0)
			cachefile.close()

			cachefile = open(STREAMBITRATECACHE, "w") # Save streams bitrate
			pickle.dump(stream_bitrate, cachefile, protocol=0)
			cachefile.close()
				
			# resets the refreshing of streamcache setting
			__addon__.setSetting(id="forceupdate", value="false")

			
		else :
			# load streams from cache
			cachefile = open(STREAMCACHE, "r")
			playlists = pickle.load(cachefile)
			cachefile.close()
			
			# load channeltitles from cache
			cachefile = open(CHANNELTITLECACHE, "r")
			channeltitles = pickle.load(cachefile)
			cachefile.close()

			# load stream bitrate from cache
			cachefile = open(STREAMBITRATECACHE, "r")
			stream_bitrate = pickle.load(cachefile)
			cachefile.close()

			print "streamrate " + str(stream_bitrate)
			
			itemnumber = 0
			while (itemnumber < len(playlists)) :
				thumbnail = ART_DIR + string.lower(iconreplacement_re.sub('', channeltitles[itemnumber]) + ".png")

				# fallback to plugin icon, if no channel art
				if not os.path.exists(thumbnail) and not os.path.isfile(thumbnail) :
					thumbnail = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), '', 'icon.png'))
				
				li = xbmcgui.ListItem(label=channeltitles[itemnumber], thumbnailImage=thumbnail)
				li.setInfo("music", { "title": channeltitles[itemnumber], "Size": int(stream_bitrate) })
				li.setProperty("mimetype", 'audio/mpeg')
				li.setProperty("IsPlayable", "true")
				xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=playlists[itemnumber], listitem=li, isFolder=False)
				
				itemnumber = itemnumber + 1
				
		return True
	
	# method that checks if a file is older than x seconds
	def checkFileTime(self, tmpfile, timesince):
		# if file exists, check timestamp
		if os.path.isfile(tmpfile) :
			if os.path.getmtime(tmpfile) > (time.time() - timesince) :
				print "It has not been " + str(timesince) + " seconds since last pagehit, using cache"
				return False
			else :
				print "Refreshing cache"
				return True
		# if file does not exist, return true so the file will be created by scraping the page
		else :
			print "cachefile does not exist"
			return True
