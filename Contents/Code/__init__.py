import re, random
from urlparse import urlparse
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
####################################################################################################

PLUGIN_PREFIX     = "/video/NBC_Harley"

NBC_URL                     = "http://www.nbc.com"
NBC_FULL_EPISODES_SHOW_LIST = "http://www.nbc.com/video/library/full-episodes/"
NBC_URL_NEWEST              = "http://www.nbc.com/video/library"
NBC_URL_MV                  = "http://www.nbc.com/video/library/categories/most-viewed/"
NBC_URL_TR                  = "http://www.nbc.com/video/library/categories/top-rated"
PLUGIN_ARTWORK      = 'art-default.jpg'
PLUGIN_ICON_DEFAULT = 'icon-default.jpg'
CACHE_INTERVAL              = 3600
DEBUG                       = False

####################################################################################################

def Start():
  Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, "NBC", "icon-default.jpg", "art-default.jpg")
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
  DirectoryItem.thumb = R("icon-default.png")
  
  MediaContainer.art       = R(PLUGIN_ARTWORK)


####################################################################################################
def MainMenu():
    dir = MediaContainer(mediaType='video') 
    dir.Append(Function(DirectoryItem(VideoPage, "Newest", PLUGIN_ICON_DEFAULT), pageUrl = NBC_URL_NEWEST))
    dir.Append(Function(DirectoryItem(VideoPage, "Most Viewed", thumb=PLUGIN_ICON_DEFAULT), pageUrl = NBC_URL_MV))
    dir.Append(Function(DirectoryItem(VideoPage, "Top Rated" , thumb=PLUGIN_ICON_DEFAULT), pageUrl = NBC_URL_TR))
    dir.Append(Function(DirectoryItem(all_shows, "All Shows", thumb=PLUGIN_ICON_DEFAULT), pageUrl = NBC_FULL_EPISODES_SHOW_LIST))
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
      thumb=item.xpath("a/img")[0].get('src')
      dir.Append(Function(DirectoryItem(VideoPage, title,thumb=thumb), pageUrl = titleUrl))
    return dir 

####################################################################################################
def VideoPage(sender, pageUrl):
    dir = MediaContainer(title2=sender.itemTitle)
    content = XML.ElementFromURL(pageUrl, True)
    for item2 in content.xpath('//div[@class="group-list"]//ul/li'):
        vidUrl = item2.xpath("a")[0].get('href')
        if vidUrl.count("http://") == 0:
          vidUrl=NBC_URL+vidUrl       
        thumb2 = item2.xpath("a/img")[0].get('src')
        title2 = item2.xpath(".//em")[0].text
        title2 = title2 + " " + item2.xpath("a")[0].get('title')
        dir.Append(WebVideoItem(vidUrl, title=title2, thumb=thumb2))
    return dir

