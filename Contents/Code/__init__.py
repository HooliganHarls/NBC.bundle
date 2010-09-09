import re, random
from urlparse import urlparse
from PMS import *

####################################################################################################

PLUGIN_PREFIX     = "/video/NBC"

NBC_URL                     = "http://www.nbc.com"
NBC_FULL_EPISODES_SHOW_LIST = "http://www.nbc.com/Video/library/full-episodes/"
NBC_URL_NEWEST              = "http://www.nbc.com/video/library"
NBC_URL_MV                  = "http://www.nbc.com/video/library/categories/most-viewed/"
NBC_URL_TR                  = "http://www.nbc.com/video/library/categories/top-rated"
PLUGIN_ARTWORK              = 'art-default.jpg'
PLUGIN_ICON_DEFAULT         = 'icon-default.jpg'
CACHE_INTERVAL              = 3600
DEBUG                       = False

####################################################################################################

def Start():
  Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, "NBC", PLUGIN_ICON_DEFAULT, PLUGIN_ARTWORK)
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
  
  MediaContainer.art       = R(PLUGIN_ARTWORK)
  DirectoryItem.thumb = R(PLUGIN_ICON_DEFAULT)
  WebVideoItem.thumb = R(PLUGIN_ICON_DEFAULT)


####################################################################################################
def MainMenu():
    dir = MediaContainer(mediaType='video') 
    dir.Append(Function(DirectoryItem(VideoPage, "Newest"), pageUrl = NBC_URL_NEWEST))
    dir.Append(Function(DirectoryItem(VideoPage, "Most Viewed"), pageUrl = NBC_URL_MV))
    dir.Append(Function(DirectoryItem(VideoPage, "Top Rated"), pageUrl = NBC_URL_TR))
    dir.Append(Function(DirectoryItem(all_shows, "All Shows"), pageUrl = NBC_FULL_EPISODES_SHOW_LIST))
    return dir
    
####################################################################################################
def all_shows(sender, pageUrl):
    dir = MediaContainer(title2=sender.itemTitle)
    content = XML.ElementFromURL(pageUrl, True)
    for item in content.xpath('//div[@class="item-list group-full-eps"]//div/ul/ul/li'):
      titleUrl = item.xpath("a")[0].get('href')
      image = item.xpath("a/img")[0].get('src')
      title = item.xpath("a")[0].get('title')
      art=PLUGIN_ARTWORK
      showart=titleUrl.replace("/video","")
      if showart.count("classic-tv") == 0:
        showart=showart + "/take_it/downloads/wallpaper/1024x768_1.jpg"
        string1 = "/categories*"

      dir.Append(Function(DirectoryItem(VideoPage, title), pageUrl = titleUrl))
    return dir 

####################################################################################################
def VideoPage(sender, pageUrl):
    dir = MediaContainer(title2=sender.itemTitle)
    content = XML.ElementFromURL(pageUrl, True)
    for item2 in content.xpath('//div[@class="group-list"]//ul/li'):
        vidUrl_t = item2.xpath("a")[0].get('href')
        
        if vidUrl_t.count("http://") == 0:
          vidUrl=NBC_URL+vidUrl_t
        art = NBC_URL + vidUrl_t + "images/backgrounds/header-bg.png"
        
        title2 = item2.xpath(".//em")[0].text
        title2 = title2 + " " + item2.xpath("a")[0].get('title')
        if vidUrl_t.count("http://") == 0:
          dir.Append(WebVideoItem(vidUrl, title2))
    return dir
