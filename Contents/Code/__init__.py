from PMS import Plugin, Log, XML, HTTP, Utils
from PMS.MediaXML import *
from PMS.Shorthand import _L, _R, _E, _D
import re
import pickle

####################################################################################################

PLUGIN_PREFIX     = "/video/NBC"

NBC_URL                     = "http://www.nbc.com"
NBC_FULL_EPISODES_SHOW_LIST = "http://www.nbc.com/Video/library/full-episodes/"
NBC_IMAGE_THUMB_URL         = "http://video.nbc.com/nbcrewind2/thumb/%s_large.jpg"
CACHE_INTERVAL              = 3600
DEBUG                       = False

####################################################################################################

def Start():
  Plugin.AddRequestHandler(PLUGIN_PREFIX, HandleRequest, _L("nbc"), "icon-default.png", "art-default.png")
  Plugin.AddViewGroup("Menu", viewMode="InfoList", contentType="items")

  
####################################################################################################

def HandleRequest(pathNouns, count):

  if count == 0:

    # Top level menu
    # We display the list of all shows in the library here
    # What we do is pull the NBC_FULL_EPISODES_SHOW_LIST, parse the 'Show Library' list on the left hand side
    # and hope to pull in some thumbnails for the shows from the main page, not all will have one at this point
    dir = MenuContainer()

    libraryShowList = XMLElementFromURL(NBC_FULL_EPISODES_SHOW_LIST, True, CACHE_INTERVAL);

    # Show list
    shows = libraryShowList.xpath("//div[@id='scet_video_lib']/ul/li")

    # Pull available thumbnails
    thumbs = libraryShowList.xpath("//div[@id='browse_container']/div[@id='browse_results']/ul[@class='scet_th_list']/li")

    for thumbElement in thumbs:
      # Find the show name and link to the thumbnail
      thumbImgRef = thumbElement.xpath("./a/img")[0]
      thumbUrl = thumbImgRef.get('src')
      thumbShowName = thumbImgRef.get('alt') # Get the show name from the alt tag
   
      # Add the thumbnail to the dictionary if we don't already have it

      if not Plugin.Dict.has_key("%s-thumb" % thumbShowName):
        Plugin.Dict["%s-thumb" % thumbShowName] = thumbUrl

    # We have gathered as many thumbnails as we can at this stage let's process the show list

    # We keep a list of url's we've already processed to prevent duplication
    # Heroes Destiny just directs to the main Heroes page anyway so it's confusing to have in the show list

    showUrls = []

    for show in shows:

      showName = show.xpath("./a/text()")[0]
      showLink = show.xpath("./a")[0]
      showUrl = showLink.get('href')

      if showUrl in showUrls:
        continue
      else:
        showUrls.append(showUrl)

      # The xpath result brings in more entries that we need, as there is no class/id to pull the exact elements we require
      # As such we check that the link is fully qualified into www.nbc.com
      # As a side affect this drops the link to http://www.geminidivision.com/video/ and http://www.jaylenosgarage.com/video/index.shtml
      # which is good as they don't fit the standard layout and would probably be best served by an specific plugin
      # Also we need to ignore 'Costal Dreams' as it has a non standard page, we do this by ensuring the link ends /video/?
      # Some links a terminated with a /, some are not

      if (re.search(r'www.nbc.com.*/video/?$', showUrl)):

        # Ok this show is hosted on wwww.nbc.com, lets add it to the list

        # Reference a thumbnail if we have one
        thumb = ''
        if Plugin.Dict.has_key("%s-thumb" % showName):
          thumb = Plugin.Dict["%s-thumb" % showName]
 
        # Ok add the show to the menu

        dir.AppendItem(FunctionItem("ShowBrowser", str(showName), args=[str(showUrl), str(showName)] , thumb=thumb, summary=''))

    return dir.ToXML()

  # Framework Additions: - borrowed from iPlayer plugin
  elif pathNouns[0] == "FunctionCall":
      return CallNamedFunction(pathNouns[1], pickle.loads(_D(pathNouns[2])))

    
def ShowBrowser(url, showName):

  # Use has selected a show, we grab the main video page for the show 
  # From this page we list the categories of video available 'All' / 'Full' / 'Webisodes' etc..

  pageUrl = url

  if DEBUG:
    Log.Add ("ShowBrowser url: "+pageUrl)

  page = XMLElementFromURL(pageUrl, True, CACHE_INTERVAL)
  dir = MenuContainer(title2=showName)

  # If we don't already have a thumbnail now is our chance to grab one (links are relative in page)

  showNameLink = page.xpath("//div[@id='scet_top']//a")[0] # //a here as 'Deal or No Deal' hides it's link inside another div - which other shows dont

  # We use the 'showName' that was passed as an argument rather than deriving it from the retrieved page
  # as there can be differences between the show names in the show list and the actual show pages themselves
  # this ensures the thumbnail gets pulled back to the main show list

  # However this doesn't work for some shows
  try:
    thumbUrl = NBC_URL + showNameLink.xpath("./img")[0].get('src');
  except:
    thumbUrl = ''
  if not Plugin.Dict.has_key("%s-thumb" % showName):
    Plugin.Dict["%s-thumb" % showName] = thumbUrl

  categories = page.xpath("//div[@id='scet_video_lib']/h4");
    
  for category in categories:

    categoryName = category.xpath("./text()")[0];

    # The site has a category called 'All Videos', however it only contains clips, so we name it to 'All Clips'
    if categoryName == "All Videos":
      categoryName = 'All Clips'

    if DEBUG:
      Log.Add("categoryName " + categoryName)

    # Reference a thumbnail if we have one
    thumb = ''
    if Plugin.Dict.has_key("%s-thumb" % showName):
      thumb = Plugin.Dict["%s-thumb" % showName]

    if DEBUG:
      Log.Add("thumb=" + thumb)

    dir.AppendItem(FunctionItem("CategoryBrowser", str(categoryName), args=[str(pageUrl), str(showName), str(categoryName)] , thumb=thumb, summary=''))

  return dir.ToXML()

def CategoryBrowser(pageUrl, showName, categoryName):

  # User has selected a category of videos for a show we now show the available collections (eg Series 1, Highlights etc..)
  # Again we pull the main show page

  page = XMLElementFromURL(pageUrl, True, CACHE_INTERVAL)
  dir = MenuContainer(title1=showName, title2=categoryName)

  # Due to the layout of the page we find our category heading in the scet_video_lib div, then use the UL following it

  categories = page.xpath("//div[@id='scet_video_lib']/h4")

  for category in categories:
    # Check if this is the category we are looking for
    currentCategoryName = category.xpath("./text()")[0];
    if DEBUG:
      Log.Add ("Category " + currentCategoryName)

    # Again we need to change 'All Videos' to 'All Clips'
    if currentCategoryName == "All Videos":
      currentCategoryName = 'All Clips'


    if (currentCategoryName == categoryName):

      if DEBUG:
        Log.Add ("Found the category")

      # Find the following <ul> and process that
      collectionList = category.xpath("following-sibling::*")[0]
      collections = collectionList.xpath("./li")
        
      for collection in collections:
        # We should now have a link with the collection name
        collectionName = str(collection.xpath("./a/text()")[0])
        collectionLink = collection.xpath("./a")[0]
        collectionUrl = collectionLink.get('href')
 
        if DEBUG:
          Log.Add ("Found collection " + collectionName + " with url " + collectionUrl)

        # Reference a thumbnail if we have one
        thumb = ''
        if Plugin.Dict.has_key("%s-thumb" % showName):
          thumb = Plugin.Dict["%s-thumb" % showName]
        dir.AppendItem(FunctionItem("CollectionBrowser", collectionName, args=[collectionUrl, categoryName, collectionName, 1 ] , thumb=thumb, summary=""))

  return dir.ToXML()


def CollectionBrowser (url, categoryName, collectionName, pageNumber):

  # User has requested a collection so we can display a list of videos in that collection (Season 3, Highlights etc..) 

  pageUrl = NBC_URL + url

  if DEBUG:
    Log.Add ("Collection Browser url: "+ url)

  page = XMLElementFromURL(pageUrl, True, CACHE_INTERVAL)

  # Display a page number in the title if we are on anything other than the first page

  if pageNumber > 1:
    dir = MenuContainer(title1=collectionName, title2=_L("pageNumberPrefix") + " " + str(pageNumber))
  else:
    dir = MenuContainer(title1=categoryName, title2=collectionName)

  # There are two possible styles for this page, either a list (as when viewing full episodes) or as a grid (as when viewing clips)

  episodes =  page.xpath("//div[@id='browse_results']/ul[@class='scet_th_list scet_th_full']/li[@class='list_full_detail']")
  # If we have episodes here then we have the list type
  if ( len(episodes) > 0 ):
    for episode in episodes:

      # Get the URL for the show
      urlAnchor = episode.xpath("./a[@class='list_full_det_thumb']")[0]
      url = NBC_URL + urlAnchor.get('href')

      # Get the thumbnail for the show
      thumbnailImgRef = episode.xpath("./a/img")[0]
      thumb = thumbnailImgRef.get('src')

      # Get the summary and title for the show
      summary = episode.xpath("./p[@class='list_full_des']/em/text()")[0]
      episodeName = urlAnchor.get('title')

      # Check to see if some metadata is available for this view (Original Airdate / Available Until)
      metadataDates = episode.xpath("./div[@class='list_full_det_time']/p/text()")
      subtitle = ''
      if ( len(metadataDates) > 1 ):
        subtitle += "Original Airdate: " + metadataDates[0] + "\n"
        subtitle += "Available Until: " + metadataDates[1]
        summary = "\n" + summary # Insert a blank line before the summary when we have dates, to make the formatting nicer

      Plugin.Dict["%s-thumb" % url] = thumb

      if DEBUG:
        Log.Add("Adding video with url" + url)

      # Add the video to the menu

      video = WebVideoItem(url, episodeName, summary, '0', thumb)
      video.SetAttr("subtitle", subtitle)
      dir.AppendItem(video)

  else:
    # Grid style view
    episodes =  page.xpath("//div[@class='browse_results']/ul[@class='scet_th_list']/li")
    # Check we found some episodes, otherwise return a message
    if len(episodes) == 0:
      dir = MessageContainer(header=_L('nbc'), message=_L('noclips'))
      return dir.ToXML()
    for episode in episodes:

      # Get the URL for the show
      urlAnchor = episode.xpath("./a")[0]
      url = NBC_URL + urlAnchor.get('href')

      # Get the thumbnail for the show
      thumbnailImgRef = episode.xpath("./a/img")[0]
      thumb = thumbnailImgRef.get('src')

      # Get the tile for the show
      episodeName = urlAnchor.get('title')

      # Construct a summary from the 'em' and non 'em' enclosed text, this varies per page
      summary=''
      emText = episode.xpath("./p[@class='scet_th_normal']/em/text()")
      otherText = episode.xpath("./p[@class='scet_th_normal']/text()")
      if (len(emText) > 0):
        summary = emText[0]
      if (len(otherText) > 0):
        summary = summary + otherText[0]
      if (re.search (r'^\s*$', episodeName)):
        # We have a blank episode name, use the summary instead
        episodeName = summary

      if DEBUG:
        Log.Add("Adding video with url" + url)

      # Add the video to the menu
      video = WebVideoItem(url, episodeName, '', '0', thumb)
      dir.AppendItem(video) 

  # Now look for 'Next' links for multipage results

  nextLinkSearch = page.xpath("//div[@id='scet_browse_pager']/div[@class='nbcu_pager']/a[@class='nbcu_pager_next']")
  if ( len(nextLinkSearch) > 0 ):
    nextLink = nextLinkSearch[0]
    if DEBUG:
      Log.Add("Next Page Found");
    # We have a next page
    nextUrl = nextLink.get('href')
    # Get the pge number from the url
    nextPageNumber = re.search(r'\/p\/(\d+)\/', nextUrl).group(1)
    # The next page link is still shown even when we are on the last page so we just check we are not already there
    if ( pageNumber != nextPageNumber):
      dir.AppendItem(FunctionItem("CollectionBrowser", _L("nextPage"), args=[nextUrl, categoryName, collectionName, nextPageNumber ] , thumb='', summary=_L("nextPageSummary")))


  return dir.ToXML()
  
    
####################################################################################################

# FRAMEWORK ADDITIONS:

# The below is borrowed from The Escapist plugin

class MenuContainer(MediaContainer):
  def __init__(self, art="art-default.png", viewGroup="Menu", title1=None, title2=None, noHistory=False, replaceParent=False):
    if title1 is None:
      title1 = _L("nvl")
    MediaContainer.__init__(self, art, viewGroup, title1, title2, noHistory, replaceParent)

def XMLElementFromURL(url, useHtmlParser=False, cacheTime=0, forceUpdate=False):
  if cacheTime == 0:
    return XML.ElementFromURL(url, useHtmlParser)
  else:
    return XML.ElementFromString(HTTP.GetCached(url, cacheTime, forceUpdate), useHtmlParser)


# The below is borrowed from the iPlayer plugin

class FunctionItem(DirectoryItem):
  def __init__(self, func, name, thumb="", summary=None, subtitle=None, args=[]):
    DirectoryItem.__init__(self, "%s/FunctionCall/%s/%s" % (Plugin.Prefixes()[0], func, _E(pickle.dumps(args))), name, thumb, summary)
    if subtitle is not None:
      self.SetAttr("subtitle", subtitle)


def CallNamedFunction(name, args=()):
  try:
    func = globals()[name]
  except:
    Log.Add("CallNamedFunction couldn't find function")
    return
  return func(*args)

