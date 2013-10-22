import sys,os
import urllib,urllib2,cookielib,re,urlresolver
from metahandler import metahandlers
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net

#necessary so that the metacontainers.py can use the scrapers
try: import xbmc,xbmcplugin,xbmcgui,xbmcaddon
except:
     xbmc_imported = False
else:
     xbmc_imported = True





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
art = TVLinkspath+'/resources/art'
cookiejar = os.path.join(cookie_path,'losmovies.lwp')
net = Net()


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
        string = string.replace("'","").replace(unicode(u'\u201c'), '"').replace(unicode(u'\u201d'), '"').replace(unicode(u'\u2019'),'').replace(unicode(u'\u2026'),'...').replace(unicode(u'\u2018'),'').replace(unicode(u'\u2013'),'-')
        return string
    except:
        return string

def inLibraryMode():
    return xbmc.getCondVisibility("[Window.IsActive(videolibrary)]")

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
         
         if meta is not False:
             print str(meta)
         #handle adding context menus
         contextMenuItems = []
         contextMenuItems.append(('Show Information', 'XBMC.Action(Info)',))
         
         #handle adding meta
         if meta == False:
             liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
             liz.setInfo(type="Video", infoLabels={"Title": name})

         else:
             
             if meta.has_key('watched') == False :
                 meta['watched']=6
                 
             liz = xbmcgui.ListItem(name, iconImage=str(meta['cover_url']), thumbnailImage=str(meta['cover_url']))


             liz.setInfo('video', infoLabels=meta)
             liz.setProperty('fanart_image', meta['backdrop_url'])

                
             infoLabels = {}
             infoLabels['title'] = name
             infoLabels['plot'] = cleanUnicode(meta['plot']) # to-check if we need cleanUnicode
             infoLabels['duration'] = str(meta['duration'])
             infoLabels['premiered'] = str(meta['premiered'])
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
             #print str(contextMenuItems)
             liz.addContextMenuItems(contextMenuItems, replaceItems=True)
         #########

         print '          Mode=' + str(mode) + ' URL=' + str(url)
         #Do some crucial stuff
         if total is False:
             ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
         else:
             ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True, totalItems=int(total))
         return ok
     
def CATEGORIES():
        LoginStartup()
        if _PLT.get_setting('TVLinks-premium') == 'false':
             addDir('Free Movies',TVLinks_REFERRER+'/freemovies/',100,'')
        else:
             addDir('TV Shows',TVLinks_REFERRER+'/tvlist/',100,'',kind='tvshows')
             addDir('Movies',TVLinks_REFERRER+'/movielist/',100,'',kind='movies')
             addDir('Search All',TVLinks_REFERRER+'/search.php',200,'',kind='all')
        

def SEARCHSITE(url,kind='all'):
        keyboard = xbmc.Keyboard()

        keyboard.setHeading('Enter a search term')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_string = keyboard.getText()
            link = Search(search_string)
            match=re.compile('<a href="(.+?)" title=".+?">(.+?)</a>').findall(link)
            for url, name in match:

                total = len(match) 
                meta = None
                predir = None
                
                if 'shows' in url:
                     mode = 22 #if tv show, search for episodes
                     extention = '/url.js'
                     predir = '[TV SHOW] '
                     
                else:
                     mode = 2 #if movie, serve up play link
                     extention = '/play.htm'
                     predir = '[MOVIE] '
                     
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
                     print year
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
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta,total=total)
                     elif kind == 'movies' and mode == 2:
                         if meta is None:
                              #add directories without meta
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,'')
                         else:
                              #add directories with meta
                              addDir(predir+name,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=met,total=totala)

def GENRES(url,kind=''):
        if kind == '':
             FREEMOVIES()
        elif kind == 'movies':
             urllist = 'movielist/'
        elif kind == 'tvshows':
             urllist = 'tvlist/'
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="' + urllist + '(.+?)">(.+?)</a>').findall(link)
        for url, genre in match:
             url = TVLinks_REFERRER+'/'+urllist+url
             #add directories without meta
             addDir(genre,url,1,'')
             
 
def FREEMOVIES(url,kind):
        t = kind
        net.set_cookies(cookiejar)
        addDir('A to Z',url,101,'')
        addDir('Genre',TVLinks_REFERRER,300,'',kind=t)
        if kind == 'tvshows':
             addDir('Latest Episodes',TVLinks_REFERRER+'/tvtoplist.htm',201,'')
        if kind == 'movies':
             addDir('Popular Movies',TVLinks_REFERRER+'/movietoplist.htm',201,'')
        addDir('Search',TVLinks_REFERRER+'/search.php',200,'',kind=t)


def FREEMOVIESAZ(url):
        net.set_cookies(cookiejar)
        az = ['#','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        for i in range(len(az)):
             if az[i] == '#':   
                  addDir(az[i],url+'digit.htm',1,'')
             else:
                  addDir(az[i],url+az[i]+'.htm',1,'')
                  
def INDEX(url):     
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="(.+?)" title=".+?">(.+?)</a>(.+?)</a>').findall(link)
        for url, name, year in match:

                meta = None
                
                if _PLT.get_setting('use-meta') == 'true':
                     metaget=metahandlers.MetaData(translatedTVLinksdatapath)
                     meta=metaget.get_meta('movie',name,year=year[2:-1])

                if 'shows' in url:
                     mode = 22 #if tv show, search for episodes
                     extention = '/url.js'
                else:
                     mode = 2 #if movie, serve up play link
                     extention = '/play.htm'

                if meta is None:
                     #add directories without meta
                     addDir(name+year,TVLinks_REFERRER+url+extention,mode,'')
                else:
                     #add directories with meta
                     addDir(name+year,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta)
def LATEST(url):     
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        link = link.replace('\\','')
        match=re.compile('<p><a href="(.+?)" title="(.+?)">(.+?)</a></p>').findall(link)
        for url, name, name2 in match:

                meta = None
                
                if _PLT.get_setting('use-meta') == 'true':
                     metaget=metahandlers.MetaData(translatedTVLinksdatapath)
                     meta=metaget.get_meta('movie',name,year=year[2:-1])

                if 'shows' in url:
                     mode = 22 #if tv show, search for episodes
                     extention = '/url.js'
                else:
                     mode = 2 #if movie, serve up play link
                     extention = '/play.htm'
                     name = name2.replace('&nbsp;',' ') #if movie show name with year

                if meta is None:
                     #add directories without meta
                     addDir(name,TVLinks_REFERRER+url+extention,mode,'')
                else:
                     #add directories with meta
                     addDir(name,TVLinks_REFERRER+url+extention,mode,meta['cover_url'],metainfo=meta)
                    
     
def INDEXTV(url):
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
        if (rs[0] == 'var urlarray = new Array();urlarray[1]="201'):
                num = len(rs)
                season = 1
                for i in range(1,num):
                     if ';urlarray[' in rs[i]:
                          season = str(find_between(rs[i],'[',']'))
                     episode=''
                     url=''
                     name=''
                     
                     us=rs[i].split('*|=*')

                     for a in range(1,len(us)):
                          episode = str(us[2])
                          url = us[0] #need to strip a string to a delimiter and get rid of certain strings
                          url = url.split('.htm',1)[0] + '.htm'
                          name = us[3]

                     meta = None


                     if _PLT.get_setting('use-meta') == 'true':
                          metaget=metahandlers.MetaData(translatedTVLinksdatapath)
                          meta=metaget.get_meta('tvshow',name,year=year[2:-1])

                     if meta is None:
                          if episode != '': # this line only gets rid of junk right now
                               #add directories without meta
                               addDir('Season ' + str(season) + ' - Episode ' + episode+' - '+name,TVLinks_REFERRER+url,2,cover)
                     else:
                          #add directories with meta
                          addDir(str(season) + ' - ' + episode+' - '+name,TVLinks_REFERRER+url,2,meta['cover_url'],metainfo=meta)                    
        
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
             addLink(name,link,cover)



        

                
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




def addLink(name,url,iconimage):
        ok=True
        win = xbmcgui.Window(10000)
        win.setProperty('1ch.playing.title', name)
        win.setProperty('1ch.playing.year', '2069')
        #win.setProperty('pltv.playing.imdb', )
        win.setProperty('1ch.playing.season', name[2:3])
        win.setProperty('1ch.playing.episode', name[5:6])
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok
        
              
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
        INDEXTV(url)

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

elif mode==300:
        print ""+url
        GENRES(url,kind)
        
xbmcplugin.endOfDirectory(int(sys.argv[1]))
