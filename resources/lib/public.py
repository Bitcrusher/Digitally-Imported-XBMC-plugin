# Import
import os
import sys
import re
import urllib2
import string
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
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

STREAM_URL = "http://www.di.fm"

STREAMCACHE = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), '' ) ) + "cachestream.dat"
CHANNELTITLECACHE = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), '' ) ) + "cachechanneltitle.dat"
STREAMBITRATECACHE = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), '' ) ) + "streamrate.dat"

# Main class
class Main:
	def __init__(self):
		self.getPublicStreams()
		print __addon__.getSetting('sortaz')
		
		# sort A-Z
		if __addon__.getSetting('sortaz') == "true" :
			xbmcplugin.addSortMethod( handle=handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
		
		# End of list
		xbmcplugin.endOfDirectory( handle=handle, succeeded=True )
		
	def getPublicStreams(self) :
		# precompiling regexes that are common
		iconreplacement_re = re.compile('[ \'-]', re.I)
		
		cacheexpiration = (int(__addon__.getSetting("cacheexpire")) * 60)
		
		# if streamcache is too old
		print "cacheexpiration "
		print cacheexpiration
		if (cacheexpiration != 0 and self.checkFileTime(STREAMCACHE, cacheexpiration) == True) or __addon__.getSetting("forceupdate") == "true" :
			
			print "Refreshing streams"
			httpCommunicator = HTTPComm()		
			
			# Get frontpage of di.fm - if it fails, show a dialog in XBMC
			try :
				htmlData     = httpCommunicator.get( STREAM_URL )
			except Exception:
				xbmcgui.Dialog().ok('Connection error', 'Could not connect to di.fm', 'Check your internet connection')
				return False

			# precompiling regexes
			playlist_re		= re.compile('<a href="(http://listen.di.fm/public3/[\w\d-]+\.pls)">96k Broadband', re.I)
			channeltitle_re = re.compile('Title1=([\s\d\w./:?\'-]*)\r?\n', re.I)
			streamurlmp3_re = re.compile('File1=([\d\w./:?-]*)', re.I) # first stream in .pls file
			
			print "Streamquality: 96k"
			stream_bitrate	= 98300
				
			# find all playlists
			try :
				playlists = playlist_re.findall(htmlData)
				print "Found " + str(len(playlists)) + " channels"
			except Exception:
				xbmcgui.Dialog().ok('No streams found', 'Perhaps the sitedesign has changed', 'Check http://qualisoft.dk for a new version')
				return False
							
			streamurls = {}
			channeltitles = {}
			
			itemnumber = 0
			while (itemnumber < len(playlists)) :
				try :
					playlist = httpCommunicator.get( playlists[itemnumber] )
					stream = streamurlmp3_re.findall(playlist)
					channeltitle = channeltitle_re.findall(playlist)
					labelstr = channeltitle[0]
					labelstr = labelstr.replace("Digitally Imported - ", "")
					thumbnail = ART_DIR + string.lower(iconreplacement_re.sub('', labelstr) + ".png")

					# fallback to plugin icon, if no channel art
					if not os.path.exists(thumbnail) and not os.path.isfile(thumbnail) :
						thumbnail = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), '', 'icon.png'))
									
					li = xbmcgui.ListItem(label=labelstr, thumbnailImage=thumbnail)
					li.setInfo("music", { "title": labelstr, "Size": int(stream_bitrate) })
					li.setProperty("mimetype", 'audio/mpeg')
					li.setProperty("IsPlayable", "true")
					xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=stream[0], listitem=li, isFolder=False)
									
					# adds streamurl + title to array so it can be saved to cache
					streamurls[itemnumber] = stream[0]
					channeltitles[itemnumber] = labelstr
				except Exception:
					print "Could not reach the stream at " + playlists[itemnumber]
				itemnumber = itemnumber + 1

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
			print "Cachefile does not exist"
			return True
