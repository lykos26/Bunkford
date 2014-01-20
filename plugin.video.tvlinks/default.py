import sys,os
import urllib,urllib2,cookielib,re,urlresolver
from metahandler import metahandlers
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
from operator import itemgetter

#necessary so that the metacontainers.py can use the scrapers
try: import xbmc,xbmcplugin,xbmcgui,xbmcaddon
except:
     xbmc_imported = False
else:
     xbmc_imported = True

##TODO:
# ADD CHECKPTS ERROR HANDELING



#TVLinks - by bunkford 2013.

# global constants
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
TVLinks_REFERRER = 'http://TVLinks.cc'
TVLinks_LOGIN_URL = TVLinks_REFERRER + '/checkin.php?action=login'
TVLinks_SEARCH_URL = TVLinks_REFERRER + '/search.php'

#get path to me
TVLinkspath=os.getcwd()

_PLT = Addon('plugin.video.tvlinks', sys.argv)


def xbmcpath(path,filename):
     translatedpath = os.path.join(xbmc.translatePath( path ), ''+filename+'')
     return translatedpath



#paths etc need sorting out.
TVLinksdatapath = 'special://profile/addon_data/plugin.video.tvlinks'
metapath = TVLinksdatapath+'/mirror_page_meta_cache'
downinfopath = TVLinksdatapath+'/downloadinfologs'
transdowninfopath = xbmcpath(downinfopath,'')
transmetapath = xbmcpath(metapath,'')
translatedTVLinksdatapath = xbmcpath(TVLinksdatapath,'')
tvlinkspath = TVLinksdatapath
datapath = _PLT.get_profile()
cookie_path = os.path.join(datapath)
#art = TVLinkspath+'/resources/art'
artdir = "special://home/addons/plugin.video.tvlinks/resources/media/"

cookiejar = os.path.join(cookie_path,'losmovies.lwp')
net = Net()

downloadScript = "special://home/addons/plugin.video.tvlinks/resources/lib/download.py"

def LoginStartup():
      if _PLT.get_setting('TVLinks-username') == '':
           xbmc.executebuiltin("Notification(Need to login!, Please visit http://tvlinks.cc and sign up.)")
                     
      loginurl = TVLinks_LOGIN_URL
      login = _PLT.get_setting('TVLinks-username')
      password = _PLT.get_setting('TVLinks-password')
      form = {'username' : login, 'password' : password}
      net.http_POST(loginurl, form)
      net.save_cookies(cookiejar)
      
def Search(string):
     net.set_cookies(cookiejar)
     searchurl = TVLinks_SEARCH_URL
     searchstring = string
     form = {'keyword' : searchstring}
     html = net.http_POST(searchurl, form).content
     return html

def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""
     
def f7(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]

def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)


def cleanUnicode(string):
    try:
        string = string.replace("'","").replace(unicode(u'\xc6'), 'Ae').replace(unicode(u'\u201c'), '"').replace(unicode(u'\u201d'), '"').replace(unicode(u'\u2019'),'').replace(unicode(u'\u2026'),'...').replace(unicode(u'\u2018'),'').replace(unicode(u'\u2013'),'-')
        return string
    except:
        return string

def inLibraryMode():
    return xbmc.getCondVisibility("[Window.IsActive(videolibrary)]")

def addLink(name,url,iconimage,mediaType=None,metainfo=False):
        meta = metainfo
        downloadPath = _PLT.get_setting(mediaType+'downpath')

        #encode url and name, so they can pass through the sys.argv[0] related strings
        sysname = urllib.quote_plus(name)
        sysurl = urllib.quote_plus(url)
        dirmode=mode
         
        u = sys.argv[0] + "?url=" + sysurl  + "&name=" + sysname + "&season="+str(season) + "&kind="+str(kind)
        ok = True
        #handle adding context menus
        contextMenuItems = []
        contextMenuItems.append(('Show Information', 'XBMC.Action(Info)',))
        contextMenuItems.append(('Download Video', "RunScript("+downloadScript+","+url.encode('utf-8','ignore')+","+downloadPath+","+name+","+mediaType+")",))
        if meta == False:
             liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
             liz.setProperty('fanart_image', 'special://home/addons/plugin.video.tvlinks/fanart.jpg')
             liz.setInfo( type="Video", infoLabels={ "Title": name } )
        else:
             liz = xbmcgui.ListItem(name, iconImage=str(meta['cover_url']), thumbnailImage=str(meta['cover_url']))


             #liz.setInfo('video', infoLabels=meta)
             liz.setProperty('fanart_image', meta['backdrop_url'])

                
             infoLabels = {}
             infoLabels['title'] = name
             infoLabels['plot'] = cleanUnicode(meta['plot']) # to-check if we need cleanUnicode
             infoLabels['duration'] = str(meta['duration'])
             #infoLabels['premiered'] = str(meta['premiered'])
             infoLabels['mpaa'] = str(meta['mpaa'])
             infoLabels['code'] = str(meta['imdb_id'])
             infoLabels['rating'] = float(meta['rating'])
             #infoLabels['overlay'] = meta['watched'] # watched 7, unwatched 6

            
             
             try:
                     trailer_id = re.match('^[^v]+v=(.{11}).*', meta['trailer_url']).group(1)
                     infoLabels['trailer'] = "plugin://plugin.video.youtube/?action=play_video&videoid=%s" % trailer_id
             except:
                     infoLabels['trailer'] = ''
             
             if meta.has_key('season_num'):
                 infoLabels['Episode'] = int(meta['episode_num'])
                 infoLabels['Season'] =int(meta['season_num'])
                 print 'No refresh for episodes yet'
                   
             
             liz.setInfo(type="Video", infoLabels=infoLabels)

     
        if contextMenuItems:
           liz.addContextMenuItems(contextMenuItems, replaceItems=True)
            
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok
     
def addDir(name, url, mode, iconimage, metainfo=False, total=False, season=None, kind=None, cover=None):
    if xbmc_imported:
         meta = metainfo
         ###  addDir with context menus and meta support  ###

         #encode url and name, so they can pass through the sys.argv[0] related strings
         sysname = urllib.quote_plus(name)
         sysurl = urllib.quote_plus(url)
         dirmode=mode
         
         #get nice unicode name text.
         #name has to pass through lots of weird operations earlier in the script,
         #so it should only be unicodified just before it is displayed.
         #name = htmlcleaner.clean(name)
         
         
         u = sys.argv[0] + "?url=" + sysurl + "&mode=" + str(mode) + "&name=" + sysname + "&season="+str(season) + "&kind="+str(kind)
         ok = True


         #handle adding context menus
         contextMenuItems = []
         contextMenuItems.append(('Show Information', 'XBMC.Action(Info)',))
         
         #handle adding meta
         if meta == False:
             liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
             liz.setProperty('fanart_image', 'special://home/addons/plugin.video.tvlinks/fanart.jpg')
             liz.setInfo(type="Video", infoLabels={"Title": name})

         else:
             if meta['cover_url'] == '': meta['cover_url'] = 'special://home/addons/plugin.video.tvlinks/icon.png'
             if meta['backdrop_url'] == '': meta['backdrop_url'] = 'special://home/addons/plugin.video.tvlinks/fanart.jpg'
             liz = xbmcgui.ListItem(name, iconImage=str(meta['cover_url']), thumbnailImage=str(meta['cover_url']))


             liz.setInfo('video', infoLabels=meta)
             liz.setProperty('fanart_image', meta['backdrop_url'])

                
             infoLabels = {}
             infoLabels['title'] = name
             infoLabels['plot'] = cleanUnicode(meta['plot']) # to-check if we need cleanUnicode
             infoLabels['duration'] = str(meta['duration'])
             #infoLabels['premiered'] = str(meta['premiered'])
             infoLabels['mpaa'] = str(meta['mpaa'])
             infoLabels['code'] = str(meta['imdb_id'])
             infoLabels['rating'] = float(meta['rating'])
             #infoLabels['overlay'] = meta['watched'] # watched 7, unwatched 6

            
             
             try:
                     trailer_id = re.match('^[^v]+v=(.{11}).*', meta['trailer_url']).group(1)
                     infoLabels['trailer'] = "plugin://plugin.video.youtube/?action=play_video&videoid=%s" % trailer_id
             except:
                     infoLabels['trailer'] = ''
             
             if meta.has_key('season_num'):
                 infoLabels['Episode'] = int(meta['episode_num'])
                 infoLabels['Season'] =int(meta['season_num'])
                 print 'No refresh for episodes yet'
                   
             
             liz.setInfo(type="Video", infoLabels=infoLabels)
                           
         if contextMenuItems:
             liz.addContextMenuItems(contextMenuItems, replaceItems=True)
         #########
         #Do some crucial stuff
         if total is False:
             ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
         else:
             ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True, totalItems=int(total))
         return ok


def CATEGORIES():
        LoginStartup()
        if _PLT.get_setting('TVLinks-premium') == 'false':
             addDir('Free Movies',TVLinks_REFERRER+'/freemovies/',100,artdir+'movie.png')
        else:
             addDir('Movies',TVLinks_REFERRER+'/movielist/',100,artdir+'movie.png',kind='movies')
             addDir('TV Shows',TVLinks_REFERRER+'/tvlist/',100,artdir+'tv.png',kind='tvshows')
             addDir('Search All',TVLinks_REFERRER+'/search.php',200,artdir+'search-glass.png',kind='all')
             
        addDir('Viewing Log',TVLinks_REFERRER+'/membercenter.php?sub=history',900,artdir+'log.png')

def SEARCHSITE(url,kind='all'):
        keyboard = xbmc.Keyboard()

        keyboard.setHeading('Enter a search term')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_string = keyboard.getText()
            link = cleanUnicode(Search(search_string))
            match=re.compile('<a href="(.+?)" title=".+?">(.+?)</a>').findall(link)
            total = len(match)
            for url, name in match:

                
                meta = None
                predir = ''

                if 'shows' in url:
                     #METACRAP
                     mode = 22 #if tv show, search for episodes
                     extention = '/url.js'
                     if (kind=='all'):
                          predir = '[TV SHOW] '
                     #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
                     meta = getMeta(name=name,season='0',episode='0')
                else:
                     mode = 2 #if movie, serve up play link
                     extention = '/play.htm'
                     if (kind=='all'):
                          predir = '[MOVIE] '
                     name = name.replace('&nbsp;',' ') #if movie show name with year
                     metaname=name
                     year = name[len(name)-5:-1]
                     #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
                     meta = getMeta(name=metaname,year=year)
     
                     
                #if not premium account only show search results for movies that are 2008 or older
                if _PLT.get_setting('TVLinks-premium') == 'false': 
                     year = name[len(name)-5:-1]
                     if year.isdigit() and int(year) < 2009:
                         if meta is None:
                              #add directories without meta
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,'',total=total)
                         else:
                              #add directories with meta
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta,total=total)

                else:   #else if premium accounts show all results or filtered based on tv or movies
                     if kind == 'all':
                         if meta is None:
                              #add directories without meta
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,'',total=total)
                         else:
                              #add directories with meta
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta,total=total)
                     elif kind == 'tvshows' and mode == 22:
                         if meta is None:
                              #add directories without meta
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,'')
                         else:
                              #add directories with meta
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta)
                     elif kind == 'movies' and mode == 2:
                         if meta is None:
                              #add directories without meta
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,'')
                         else:
                              #add directories with meta
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta)

def GENRES(url,kind=''):
        if kind == '':
             FREEMOVIES()
        elif kind == 'movies':
             urllist = 'movielist/'
             thumb = artdir+'movie.png'
        elif kind == 'tvshows':
             urllist = 'tvlist/'
             thumb = artdir+'tv.png'
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="' + urllist + '(.+?)">(.+?)</a>').findall(link)
        total = len(match)
        for url, genre in match:
             url = TVLinks_REFERRER+'/'+urllist+url
             #add directories without meta
             addDir(genre,url,1,thumb,total=total)
             
 
def FREEMOVIES(url,kind):
        if kind == 'movies':
             thumb = artdir+'moviegenre-logo.png'
             searchthumb = artdir+'moviesearch-logo.png'
        elif kind == 'tvshows':
             thumb = artdir+'tvgenre-logo.png'
             searchthumb = artdir+'tvsearch-logo.png'
        t = kind
        net.set_cookies(cookiejar)
        addDir('A to Z',url,101,artdir+'atoz.png')
        addDir('Genre',TVLinks_REFERRER,300,thumb,kind=t)
        if kind == 'tvshows':
             addDir('Latest Episodes',TVLinks_REFERRER+'/tvtoplist.htm',201,artdir+'toptvshows.png')
             addDir('Recently Added TV Shows',TVLinks_REFERRER+'/tv.htm',280,artdir+'recentlyaddedshows.png')
             addDir('Top TV Shows',TVLinks_REFERRER+'/tv.htm',281,artdir+'toptvshows.png')
        if kind == 'movies':
             addDir('Popular Movies',TVLinks_REFERRER+'/movietoplist.htm',201,artdir+'popularmovies.png')
             addDir('Recently Added Movies',TVLinks_REFERRER+'/movie.htm',250,artdir+'recentlyaddedmovies.png')
             addDir('Hot Movies',TVLinks_REFERRER+'/movie.htm',251,artdir+'hotmovies.png')
        addDir('Search',TVLinks_REFERRER+'/search.php',200,searchthumb,kind=t)


def FREEMOVIESAZ(url):
        net.set_cookies(cookiejar)
        az = ['#','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        for i in range(len(az)):
             if az[i] == '#':   
                  addDir(az[i],url+'digit.htm',1,artdir+'movie.png')
             else:
                  addDir(az[i],url+az[i]+'.htm',1,artdir+'movie.png')
                  
def INDEX(url):     
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="(.+?)" title=".+?">(.+?)</a>(.+?)</a>').findall(link)
        total = len(match)
        for url, name, year in match:

                meta = None
                

                if 'shows' in url:
                     mode = 22 #if tv show, search for episodes
                     extention = '/url.js'
                     thumb = artdir+'tv.png'
                else:
                     mode = 2 #if movie, serve up play link
                     extention = '/play.htm'
                     thumb = artdir+'movie.png'

                if meta is None:
                     #add directories without meta
                     addDir(name+year,TVLinks_REFERRER+url+extention,mode,thumb,total=total)
                else:
                     #add directories with meta
                     addDir(name+year,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta,total=total)
def LATEST(url):     
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        link = link.replace('\\','')
        match=re.compile('<p><a href="(.+?)" title="(.+?)">(.+?)</a></p>').findall(link)
        total = len(match)
        for url, name, name2 in match:

                meta = None
                

                if 'shows' in url:
                     thumb = artdir+'tv.png'
                     mode = 22 #if tv show, search for episodes
                     extention = '/url.js'
                     try:
                          SeasonLocation=name.index('Season')
                     except:
                          SeasonLocation=0
                           
                     if SeasonLocation > 0:
                         metaname=name[:SeasonLocation-1]
                     else:
                          metaname=name
                     meta=getMeta(metaname,season='0',episode='0')
                else:
                     mode = 2 #if movie, serve up play link
                     thumb = artdir+'movie.png'
                     extention = '/play.htm'
                     name = name2.replace('&nbsp;',' ') #if movie show name with year
                     meta=getMeta(name[:-7],year=name[-5:-1])

                if meta is None:
                     #add directories without meta
                     addDir(name,TVLinks_REFERRER+url+extention,mode,thumb,total=total)
                else:
                     #add directories with meta
                     addDir(name,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta,total=total)
                    
     
def INDEXTV(url,name):
        #net.set_cookies(cookiejar)
        showurl = url[:-7]
        req = urllib2.Request(showurl)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        cover = 'http://img.moviesdata.net/' + str(find_between(link,'<img src="http://img.moviesdata.net/','"'))

        req = urllib2.Request(url)
        #req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        rs = link.split('%=+=%')
        tvlist=[]
        if (len(rs[0]) > 0):
                num = len(rs)
                season = 1
                for i in range(1,num):
                     if ';urlarray[' in rs[i]:
                          season = str(find_between(rs[i],'[',']'))
                     episode=''
                     url=''
                     epname=''
                     
                     us=rs[i].split('*|=*')

                     for a in range(1,len(us)):
                          episode = str(us[2])
                          url = us[0] #need to strip a string to a delimiter and get rid of certain strings
                          url = url.split('.htm',1)[0] + '.htm'
                          epname = us[3]
                         
                     
                     
                     if (episode>""):
                          tvlist.append([name,season,episode,epname,url])
     
                     
                     
        reverseTV = _PLT.get_setting('reverse-tv')
        if reverseTV == 'true':
             tvlist = sorted(tvlist, key=itemgetter(1,2), reverse=True)
        else:
             tvlist = sorted(tvlist, key=itemgetter(1,2))
             
        for p in tvlist:
            name = p[0]
            season = p[1]
            episode = p[2]
            epname = p[3]
            url = p[4]
            
            meta = None

            #METACRAP
            #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
            try:
                 name = name.replace("[TV SHOW] ","")
            except:
                 pass
                
            try:
                 SeasonLocation=name.index('Season')
            except:
                 SeasonLocation=0
                 
            if SeasonLocation > 0:
                metaname=name[:SeasonLocation-1]
            else:
                 metaname=name
                 
            meta = getMeta(name=metaname,season=season,episode=episode)  


            if meta is None:
                 if episode != '': # this line only gets rid of junk right now
                      #add directories without meta
                      addDir(metaname+' - ' + 'Season ' + str(season) + ' - Episode ' + episode+' - '+epname,TVLinks_REFERRER+url,2,cover,total=num)
            else:
                 if episode != '': # this line only gets rid of junk right now
                      #add directories with meta
                      addDir(metaname+' - ' + 'Season ' + str(season) + ' - Episode ' + episode+' - '+epname,TVLinks_REFERRER+url,2,meta['cover_url'],metainfo=meta,total=num)                    


             

def INDEX2(url,name):
        try: 
             net.set_cookies(cookiejar)
             showurl = url[:-9]
             req = urllib2.Request(showurl)
             req.add_header('User-Agent', USER_AGENT)
             response = urllib2.urlopen(req)
             link=response.read()
             response.close()
             cover = 'http://img.moviesdata.net/' + str(find_between(link,'<img src="http://img.moviesdata.net/','"'))
        except:
             cover = ''
             
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link = response.read()
        response.close()
        match = re.compile('code=(.+?)/').findall(link)
        regexp = re.compile(r'\((.+?)\)')
        if regexp.search(name) is not None:
            mediatype = "movie"
            Meta = None
            meta = getMeta(name=name[:-6],year=name[-5:-1])
        else:
            mediatype = "tv"
            Meta = None
            meta = getMeta(name=name[:name.index('- Season')-1],season='0',episode='0')
        for code in match:
             code = code[:-1]
             #get play link
             url = 'http://tvlinks.cc/checkpts.php?code='+code
             net.set_cookies(cookiejar)
             req = urllib2.Request(url)
             req.add_header('User-Agent', USER_AGENT)
             response = urllib2.urlopen(req)
             link = response.read()
             #turn play link into usable url
             link = link.replace(".cc/",".cc/newipad.mp4?url=")
             
             

             if meta is None:
                  addLink(name,link,cover,mediaType=mediatype)
             else:
                  addLink(name,link,meta['cover_url'],mediaType=mediatype,metainfo=meta)
                  
def VIEWLOG(url):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="/(shows|movies)/(.+?)" target="_blank">(.+?)</a>').findall(link)
        match2=re.compile('<a class="p_redirect" href="(.+?)" title="(.+?)"').findall(link)
        #<a href="/shows/20130124/771" target="_blank">Legit Season 1x11</a>
        total = len(match) + len(match2)
        for mediatype, url, name in match:

                meta = None
                url = "/"+mediatype+"/"+url
                if 'shows' in url:
                     thumb = artdir+'tv.png'
                     #METACRAP
                     mode = 22 #if tv show, search for episodes
                     extention = '/url.js'
                     #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
                     SeasonLocation=name.index('Season')
                     SeasonAndEpisode=name[SeasonLocation+7:]
                     Episode=SeasonAndEpisode[SeasonAndEpisode.index('x')+1:]
                     Season=SeasonAndEpisode[:SeasonAndEpisode.index('x')]
                     metaname=name[:SeasonLocation-1]
                     meta = getMeta(name=metaname,season=Season,episode=Episode)
                else:
                     thumb = artdir+'movie.png'
                     mode = 2 #if movie, serve up play link
                     extention = '/play.htm'
                     name = name.replace('&nbsp;',' ') #if movie show name with year
                     metaname=name[:-5]
                     year = name[len(name)-5:-1]
                     #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
                     meta = getMeta(name=metaname,year=year)

                if meta is None:
                     #add directories without meta
                     addDir(name,TVLinks_REFERRER+url+extention,mode,thumb,total=total)
                else:
                     #add directories with meta
                     addDir(name,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta,total=total)

        #Next/Previous
        for url, name in match2:
                 if name == 'Next': thumb = artdir + 'next.png'
                 if name == 'Previous': thumb = artdir + 'previous.png'
                 if name == 'Home': thumb = artdir + 'home.png'
                 if name == 'End': thumb = artdir + 'end.png'
                 addDir(name,TVLinks_REFERRER+'/membercenter.php'+url,900,thumb,total=total)

def getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
        useMeta = _PLT.get_setting('use-meta')
        if useMeta == 'true':
             print 'getMeta() ran',name,season,episode,year,imdbid,tvdbid
             metaget=metahandlers.MetaData(translatedTVLinksdatapath)
             if episode and season is not None:
                  #get_episode_meta(self, tvshowtitle, imdb_id, season, episode, air_date='', episode_title='', overlay=''):
                  #get season and episode
                  
                  meta=metaget.get_meta('tvshow',name)
             else:
                  #get_meta(self, media_type, name, imdb_id='', tmdb_id='', year='', overlay=6):
                  #get regular
                  meta=metaget.get_meta('movie',name,year=year)
        return meta
     
def NEWMOVIES(url):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="(.+?)" title="(.+?)">.+?&nbsp;\((.+?)\)</a>').findall(link)
        #<a href="/movies/20131218/105731" title="The Grudge">The Grudge&nbsp;(2004)</a>
        counter = 0
        total = len(match)
        for url, name, year in match:

                counter += 1
                if (counter is 40):
                     break
                meta = None
                year = " ("+year+")"


                if 'shows' in url:
                     mode = 22 #if tv show, search for episodes
                     extention = '/url.js'
                else:
                     mode = 2 #if movie, serve up play link
                     extention = '/play.htm'
                     meta=getMeta(name,year=year[2:-1])

                if meta is None:
                     #add directories without meta
                     addDir(name+year,TVLinks_REFERRER+url+extention,mode,'',total=total)
                else:
                     #add directories with meta
                     addDir(name+year,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta,total=total)

def HOTMOVIES(url):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="(.+?)" title="(.+?)">.+?&nbsp;\((.+?)\)</a>').findall(link)
        #<a href="/movies/20131218/105731" title="The Grudge">The Grudge&nbsp;(2004)</a>
        counter = 0
        total = len(match)
        for url, name, year in match:

                counter += 1
                if (counter > 39): 
                          
                     meta = None
                     year = " ("+year+")"

                     if 'shows' in url:
                          mode = 22 #if tv show, search for episodes
                          extention = '/url.js'
                     else:
                          mode = 2 #if movie, serve up play link
                          extention = '/play.htm'
                          meta=getMeta(name,year=year[2:-1])

                     if meta is None:
                          #add directories without meta
                          addDir(name+year,TVLinks_REFERRER+'/'+url+extention,mode,'',total=total)
                     else:
                          #add directories with meta
                          addDir(name+year,TVLinks_REFERRER+'/'+url+extention,mode,meta['cover_url'],metainfo=meta,total=total)   

def NEWTVSHOWS(url):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="(.+?)" title="(.+?)">').findall(link)
        #<a href="/shows/20131110/939" title="Ground Floor">Ground Floor</a>
        counter = 0
        total = len(match)
        for url, name in match:

                counter += 1
                if (counter is 39):
                     break
                if (counter is 2):
                     continue
                if (counter is 4):
                     continue
                    
                meta = None
                year = ''

                if 'shows' in url:
                     mode = 22 #if tv show, search for episodes
                     extention = '/url.js'
                     meta=getMeta(name,season='0',episode='0')
                else:
                     mode = 2 #if movie, serve up play link
                     extention = '/play.htm'

                if meta is None:
                     #add directories without meta
                     addDir(name+year,TVLinks_REFERRER+url+extention,mode,'',total=total)
                else:
                     #add directories with meta
                     addDir(name+year,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta,total=total)

def TOPTVSHOWS(url):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="(.+?)" title="(.+?)">').findall(link)
        #<a href="/shows/20131110/939" title="Ground Floor">Ground Floor</a>
        counter = 0
        total = len(match)
        for url, name in match:

                counter += 1
                if (counter > 34):
                    
                     if (counter is 36):
                          continue
                     if (counter is 38):
                          continue
                         
                     meta = None
                     year = ''

                     if 'shows' in url:
                          mode = 22 #if tv show, search for episodes
                          extention = '/url.js'
                          meta=getMeta(name,season='0',episode='0')                          
                     else:
                          mode = 2 #if movie, serve up play link
                          extention = '/play.htm'

                     if meta is None:
                          #add directories without meta
                          addDir(name+year,TVLinks_REFERRER+url+extention,mode,'',total=total)
                     else:
                          #add directories with meta
                          addDir(name+year,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta,total=total)                     
def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param






    
              
params=get_params()
url=None
name=None
mode=None
season=None
kind=None

try:
        season=urllib.unquote_plus(params["season"])
except:
        pass
try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass
try:
        kind=urllib.unquote_plus(params["kind"])
except:
        pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "Type: "+str(kind)


if mode==None or url==None or len(url)<1:
        print ""
        CATEGORIES()
       
elif mode==1:
        print ""+url
        INDEX(url)

elif mode==2:
        print ""+url
        INDEX2(url,name)
        
elif mode==3:
        print ""+url
        INDEX3(url,season)
            
elif mode==4:
        print ""+url
        VIDEOLINKS(url,name)
        
elif mode==22:
        print ""+url
        INDEXTV(url,name)

elif mode==100:
        print ""+url
        FREEMOVIES(url,kind)

elif mode==101:
        print ""+url
        FREEMOVIESAZ(url)

elif mode==200:
        print ""+url
        SEARCHSITE(url,kind)

elif mode==201:
        print ""+url
        LATEST(url)
        
elif mode==250:
        print ""+url
        NEWMOVIES(url)

elif mode==251:
        print ""+url
        HOTMOVIES(url)

elif mode==280:
        print ""+url
        NEWTVSHOWS(url)

elif mode==281:
        print ""+url
        TOPTVSHOWS(url)

elif mode==300:
        print ""+url
        GENRES(url,kind)

elif mode==900:
        print ""+url
        VIEWLOG(url)
        
xbmcplugin.endOfDirectory(int(sys.argv[1]))
