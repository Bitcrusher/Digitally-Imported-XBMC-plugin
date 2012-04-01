########################################
# di.fm - Digitally Imported
# by Tim C. 'Bitcrusher' Steinmetz - qualisoft.dk
########################################

# plugin constants
__plugin__       = "Digitally Imported - DI.fm"
__author__       = "Tim C. Steinmetz"
__url__          = "http://qualisoft.dk/"
__platform__     = "xbmc media center, [LINUX, OS X, WIN32]"
__date__         = "1. April 2012"
__version__      = "1.0.1"

import os
import time
import sys
import ConfigParser
import xbmc, xbmcplugin, xbmcgui, xbmcaddon

__addon__ = xbmcaddon.Addon(id='plugin.audio.di.fm')

LIB_DIR = xbmc.translatePath( os.path.join( __addon__.getAddonInfo('path'), 'resources', 'lib' ) )
sys.path.append (LIB_DIR)

xbmc.log( "[PLUGIN] %s v%s (%s)" % ( __plugin__, __version__, __date__ ), xbmc.LOGNOTICE )
if __addon__.getSetting('username') == "" :
	import public as plugin
if __addon__.getSetting('username') != "" :
	import premium as plugin

plugin.Main()
