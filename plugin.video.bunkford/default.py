# -*- coding: cp1252 -*-
import urllib,urllib2,re,xbmc,xbmcplugin,xbmcgui,xbmcaddon,sys,os,cookielib,htmlentitydefs,urlresolver
from BeautifulSoup import BeautifulSoup
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
from metahandler import metahandlers



##
# Bunkford - 2013.
#
# TODO:
#    scrape more meta data from sites - cast, etc
#    add preview context menu option for movie sites (scrape)
#    add download option to context menu

helpText = """
For this script to work correctly you need to have valid login information for the following invite only sites:

     http://www.iseri.es
     http://www.bunnymovie.com
     http://www.barwo.com (not updated anymore, switched to bunnymovie)

     Add your login credentials to the plugin settings.

Downloading:

     For downloading to work correctly you need to specify download paths in the plugin settings.
"""
def xbmcpath(path,filename):
     translatedpath = os.path.join(xbmc.translatePath( path ), ''+filename+'')
     return translatedpath

#CONSTANTS
_PLUG = Addon('plugin.video.bunkford', sys.argv)

USER_AGENT = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7"

#iseries constants
iseries_URL = 'http://www.iseri.es'
iseries_LOGIN_URL = 'http://iseri.es/wp-login.php'

#barwo constants
barwo_URL = 'http://www.barwo.com'
barwo_LOGIN_URL = 'http://barwo.com/wp-login.php'

#bunny constants
bunny_URL = 'http://www.bunnymovie.com'
bunny_LOGIN_URL = 'http://bunnymovie.com/wp-login.php'


adatapath = 'special://profile/addon_data/plugin.video.bunkford'
metapath = adatapath+'/mirror_page_meta_cache'
downinfopath = adatapath+'/downloadinfologs'
transdowninfopath = xbmcpath(downinfopath,'')
transmetapath = xbmcpath(metapath,'')
translateddatapath = xbmcpath(adatapath,'')
path = adatapath
datapath = _PLUG.get_profile()

downloadScript = "special://home/addons/plugin.video.bunkford/resources/lib/download.py"
textBoxesScript = "special://home/addons/plugin.video.bunkford/resources/lib/textBoxes.py"

#cookie constants
cookie_path = os.path.join(datapath)
cookiejar = os.path.join(cookie_path,'losmovies.lwp')
net = Net()

# FUNCTIONS USED   

def unescape(text):
##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

def Search(string,url):
     net.set_cookies(cookiejar)
     searchurl = url
     searchstring = string
     form = {"s" : searchstring}
     html = net.http_POST(searchurl, form, headers={'User-Agent':USER_AGENT}).content
     return html

def SearchMovie(string,url):
     net.set_cookies(cookiejar)
     searchurl = url
     searchstring = string
     form = {"s" : searchstring}
     html = net.http_POST(searchurl, form).content
     return html

def cleanUnicode(string):
    try:
        string = string.replace("'","").replace(unicode(u'\u201c'), '"').replace(unicode(u'\u201d'), '"').replace(unicode(u'\u2019'),'').replace(unicode(u'\u2026'),'...').replace(unicode(u'\u2018'),'').replace(unicode(u'\u2013'),'-')
        return string
    except:
        return string


#START MAIN SCRIPT
def STARTPOINT():
        addDir('TV (http://iseri.es)',iseries_URL,10,'')
        addDir('MOVIES (http://barwo.com)',barwo_URL,100,'')
        addDir('MOVIES (http://bunnymovie.com)',bunny_URL,300,'')

#BUNNYMOVIE.COM
def bunny_LoginStartup():
      if _PLUG.get_setting('bunny-username') == '':
           xbmc.executebuiltin("Notification(Need to login!, Please visit http://bunnymovie.com and sign up.)")
                     
      loginurl = bunny_LOGIN_URL
      login = _PLUG.get_setting('bunny-username')
      password = _PLUG.get_setting('bunny-password')
      form = {'log' : login, 'pwd' : password}
      net.http_POST(loginurl, form,{'User-Agent':USER_AGENT})
      net.save_cookies(cookiejar)
        
def BUNNYMAIN():
     bunny_LoginStartup()

     #Name,URL,MODE,Image
     addDir('GENRE',bunny_URL,311,'')
     addDir('Recent MOVIES',bunny_URL,312,'')
     addDir('Search MOVIES',bunny_URL,315,'')

def BUNNYGENRE():
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent',USER_AGENT)
        response = urllib2.urlopen(req)
        soup = BeautifulSoup(response.read())
        data = soup.findAll('div',attrs={'id':'section-slider'});
        for div in data:
             links = div.findAll('a')
             for a in links:
                  print a['href'];

                  name = a['href'][28:-1].capitalize()
                  name = unescape(name)
                  addDir(name,a['href'],312,'')

def BUNNYGENRELIST(url,name):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent',USER_AGENT)
        response = urllib2.urlopen(req)
        soup = BeautifulSoup(response.read())
        data = soup.findAll('div',attrs={'class':re.compile(r".*\post section\b.*")});
        for div in data:
            link = div.find('a')['href']
            image = div.find('img')['src']
            name = div.find('a').contents[0]
            name = unescape(name)

            meta = None
            #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
            try:
                 m = [m.start() for m in re.finditer('\\(', name)]
                 showname = name[:m[0]-1]
                 year = name[m[0]+1:-1]
                 meta = getMeta(name=showname,year=year) 
            except:
                 pass
               
            addDir(name,link,313,image,meta=meta)
            
        #LOAD MORE MOVIES
        next_post = soup.find('a',attrs={'class':'load-more-link no-ajax'})['rel'];
        if next_post != "#":
             addDir(next_post,next_post,'312','') #adds dir listing for next page

def BUNNYMOVIE(url,name):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent',USER_AGENT)
        response = urllib2.urlopen(req)
        soup = BeautifulSoup(response.read())
        
        for elem in soup(text=re.compile(r'Play Now')):
              link = elem.parent['href']
              
        if link.find('gf.to') > -1: # BS you have to do because of stupid cloudflare url shortening.
             net.set_cookies(cookiejar)
             req = urllib2.Request(link)
             req.add_header('User-Agent',USER_AGENT)
             response = urllib2.urlopen(req)
             subsoup = BeautifulSoup(response.read())
             link = subsoup.find('meta',attrs={'http-equiv':'refresh'})
             link = link['content'][7:]
             print link
     

        image = soup.find('img',attrs={'class':re.compile(r"aligncenter.+?")})['src'];

        
        plot = soup.findAll('div',attrs={'class':re.compile(r"post.+?section.+?")});
        for div in plot:
             synopsis = div.findAll('p')
             synopsis = synopsis[2].nextSibling
             synopsis = unescape(synopsis)

        trailer = None
        preview = soup.findAll('div',attrs={'class':'video-container'});
        for div in preview:
             trailer = div.find('iframe')['src']
             sources = []
             hosted_media = urlresolver.HostedMediaFile(url=trailer)
             sources.append(hosted_media)
             source = urlresolver.choose_source(sources)
             trailer = source.resolve()
             
        infoLabels = {}
        infoLabels={ "Title": name }
        infoLabels={ "Plot": synopsis }
        #infoLabels={ "Trailer": trailer } Makes Plot disapear for some reason
        
        meta = None
        #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
        try:
             m = [m.start() for m in re.finditer('\\(', name)]
             showname = name[:m[0]-1]
             year = name[m[0]+1:-1]
             meta = getMeta(name=showname,year=year) 
        except:
             pass
               
        addLink(name,link,image,'movie',infoLabels=infoLabels,trailer=trailer,meta=meta) #adds link of episode


def SEARCHSITE(url):
        keyboard = xbmc.Keyboard()

        keyboard.setHeading('Enter a search term')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_string = keyboard.getText()

            link = SearchMovie(search_string,url)
            soup = BeautifulSoup(link)
            print soup.prettify

            
            data = soup.findAll('div',attrs={'class':'thumbnail'});
            for div in data:
                link = div.find('a')['href']
                image = div.find('img')['src']
                name = div.find('img')['alt']
                name = unescape(name)

                meta = None
                #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
                try:
                     m = [m.start() for m in re.finditer('\\(', name)]
                     showname = name[:m[0]-1]
                     year = name[m[0]+1:-1]
                     meta = getMeta(name=showname,year=year) 
                except:
                     pass
               
                addDir(name,link,313,image,meta=meta)
                
                          
#BARWO.COM
def barwo_LoginStartup():
      if _PLUG.get_setting('barwo-username') == '':
           xbmc.executebuiltin("Notification(Need to login!, Please visit http://barwo.com and sign up.)")
                     
      loginurl = barwo_LOGIN_URL
      login = _PLUG.get_setting('barwo-username')
      password = _PLUG.get_setting('barwo-password')
      form = {'log' : login, 'pwd' : password}
      net.http_POST(loginurl, form,{'User-Agent':USER_AGENT})
      net.save_cookies(cookiejar)
        
def BARWOMAIN():
     barwo_LoginStartup()

     #Name,URL,MODE,Image
     addDir('GENRE',barwo_URL,11,'')
     addDir( 'Recent MOVIES',barwo_URL,112,'')
     addDir('Search MOVIES',barwo_URL,315,'')

def BARWOGENRE():
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent',USER_AGENT)
        response = urllib2.urlopen(req)
        soup = BeautifulSoup(response.read())
        data = soup.findAll('div',attrs={'id':'menu-tab2'});
        for div in data:
             links = div.findAll('a')
             for a in links:
                  print a['href'];
                  total= a.find('span').contents[0] #total movies in genre
                  name = a['href'][23:].capitalize()+' '+total
                  name = unescape(name)
                  addDir(name,a['href'],112,'')

def BARWOGENRELIST(url,name):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent',USER_AGENT)
        response = urllib2.urlopen(req)
        soup = BeautifulSoup(response.read())
        data = soup.findAll('div',attrs={'class':re.compile(r".*\post section\b.*")});
        for div in data:
            link = div.find('a')['href']
            image = div.find('img')['src']
            name = div.find('a').contents[0]
            name = unescape(name)

            meta = None
            #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
            try:
                 m = [m.start() for m in re.finditer('\\(', name)]
                 showname = name[:m[0]-1]
                 year = name[m[0]+1:-1]
                 meta = getMeta(name=showname,year=year) 
            except:
                 pass
      
            addDir(name,link,113,image,meta=meta)
            
        #LOAD MORE MOVIES
        next_post = soup.find('a',attrs={'class':'load-more-link no-ajax'})['rel'];
        if next_post != "#":
             addDir(next_post,next_post,'112','') #adds dir listing for next page

def BARWOMOVIE(url,name):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent',USER_AGENT)
        response = urllib2.urlopen(req)
        soup = BeautifulSoup(response.read())


        for elem in soup(text=re.compile(r'Play Now')):
              link = elem.parent['href']
              
        if link.find('gf.to') > -1: # BS you have to do because of stupid cloudflare url shortening.
             net.set_cookies(cookiejar)
             req = urllib2.Request(link)
             req.add_header('User-Agent',USER_AGENT)
             response = urllib2.urlopen(req)
             subsoup = BeautifulSoup(response.read())
             link = subsoup.find('meta',attrs={'http-equiv':'refresh'})
             link = link['content'][7:]
             
        image = soup.find('img',attrs={'class':re.compile(r"aligncenter.+?")})['src'];

        
        plot = soup.findAll('div',attrs={'class':'content'});
        for div in plot:
             synopsis = div.findAll('p')
             synopsis = synopsis[2].nextSibling
             synopsis = unescape(synopsis)

        trailer = None
        preview = soup.findAll('div',attrs={'class':'video-container'});
        for div in preview:
             trailer = div.find('iframe')['src']
             sources = []
             hosted_media = urlresolver.HostedMediaFile(url=trailer)
             sources.append(hosted_media)
             source = urlresolver.choose_source(sources)
             trailer = source.resolve()
             
        infoLabels = {}
        infoLabels={ "Title": name }
        infoLabels={ "Plot": synopsis }

        meta = None
        #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
        try:
             m = [m.start() for m in re.finditer('\\(', name)]
             showname = name[:m[0]-1]
             year = name[m[0]+1:-1]
             meta = getMeta(name=showname,year=year) 
        except:
             pass     
        
        addLink(name,link,image,'movie',infoLabels=infoLabels,trailer=trailer,meta=meta) #adds link of episode

#ISERI.ES

def iseries_LoginStartup():
      if _PLUG.get_setting('iseries-username') == '':
           xbmc.executebuiltin("Notification(Need to login!, Please visit http://iseri.es and sign up.)")
                     
      loginurl = iseries_LOGIN_URL
      login = _PLUG.get_setting('iseries-username')
      password = _PLUG.get_setting('iseries-password')
      form = {'log' : login, 'pwd' : password, 'testcookie' : '1', 'redirect_to' : iseries_URL}
      net.http_POST(loginurl, form,{'User-Agent':USER_AGENT})
      net.save_cookies(cookiejar)
      
def CATEGORIES():
        iseries_LoginStartup()

        #Name,URL,MODE,Image
        addDir('TV Shows',iseries_URL+'/shows/',1,'')
        addDir( 'Recent TV',iseries_URL,2,'')
        addDir('Search TV',iseries_URL,4,'')
        #above works, need to parse returned data. not the same as movie sites               
def INDEX(url):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent',USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="http://iseri.es(.+?)" title=".+?">(.+?)</a>').findall(link)
        for url,name in match:
                name = unescape(name)
                addDir(name,iseries_URL+url,2,'')

def INDEX2(url,name):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent',USER_AGENT)
        response = urllib2.urlopen(req)
        soup = BeautifulSoup(response.read())
        data = soup.findAll('article',attrs={'class':'post text_block clearfix'});
        for div in data:
            link = div.find('a')['href']
            image = div.find('img')['src']
            name = div.find('img')['alt']
            name = cleanUnicode(name) #need to clean or error.
            name = unescape(name)

            meta = None
            #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
            try:
                 m = [m.start() for m in re.finditer('-', name)]
                 showname = name[:m[0]-1]
                 seasonepisode = name[m[0]+2:]
                 season = int(seasonepisode[1:3])
                 episode = int(seasonepisode[4:6])
                 meta = getMeta(name=showname,season=season,episode=episode) 
            except:
                 pass
            addDir(name,link,3,image,meta=meta) #adds dir listing of episodes
            
        more = soup.findAll('div',attrs={'class':'more_posts'});
        for div in more:
            next_post = div.find('a')['href']
            if next_post != "#":
                 addDir(next_post,next_post,'2','',meta=meta) #adds dir listing for next page

        more = soup.findAll('div',attrs={'class':'alignleft'});
        for div in more:
                if div.find('a') is not None:
                        next_post = div.find('a')['href']
                        addDir(next_post,next_post,'2','',meta=meta) #adds dir listing for next page

def INDEX3(url,name):
        net.set_cookies(cookiejar)
        req = urllib2.Request(url)
        req.add_header('User-Agent',USER_AGENT)
        response = urllib2.urlopen(req)
        soup = BeautifulSoup(response.read())
        data = soup.findAll('a',href=re.compile('.mp4'));
        data = unicode.join(u'\n',map(unicode,data))
        link = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', data)
        link = unicode.join(u'\n',map(unicode,link))
        link = link.replace("&amp;","&")
        showtitle = soup.find('h1').contents[0]
        showtitle = showtitle.replace('&#8211;','-')
        
        showtitle=unescape(showtitle)
        data = soup.findAll('div',attrs={'class':'main_post_text'});
        for div in data:
                image = div.find('img')['src']
                name = div.findAll('p')[4]
                name = unicode.join(u'\n',map(unicode,name))
                name = unescape(name)
                plot = div.findAll('p')[1]
                plot = unicode.join(u'\n',map(unicode,plot))
                plot = unescape(plot)
        infoLabels = {}
        infoLabels={ "TVShowTitle": name }
        infoLabels={ "Plot": plot }


        meta = None
        #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
        try:
             m = [m.start() for m in re.finditer('-', showtitle)]
             showname = showtitle[:m[0]-1]
             seasonepisode = showtitle[m[0]+2:]
             season = int(seasonepisode[1:3])
             episode = int(seasonepisode[4:6])
             meta = getMeta(name=showname,season=season,episode=episode) 
        except:
             pass
          
        #previous and next episodes
        try:
             nextep = soup.find('a',attrs={'rel':'next'})['href'];
        except:
             nextep = None
        try:
             prevep = soup.find('a',attrs={'rel':'prev'})['href'];
        except:
             prevep = None
        
        addLink(showtitle + ' - ' + name[1:-1],link,image,'tv',infoLabels=infoLabels,meta=meta) #adds link of episode

        if nextep is not None:
             addDir('Next Episode',nextep,3,'',meta=meta)
        if prevep is not None:
             addDir('Previous Episode',prevep,3,'',meta=meta)

def SEARCHSITETV(url):
        keyboard = xbmc.Keyboard()

        keyboard.setHeading('Enter a search term')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_string = keyboard.getText()

            link = Search(search_string,url)
            soup = BeautifulSoup(link)
            print soup.prettify
            
            data = soup.findAll('article',attrs={'class':'post text_block clearfix'});
            print data[0]
            for div in data:
                link = div.find('a')['href']
                image = div.find('img')['src']
                name = div.find('img')['alt']
                name = cleanUnicode(name) #need to clean or error.
                name = unescape(name)

                meta = None
                #getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
                try:
                     m = [m.start() for m in re.finditer('-', name)]
                     showname = name[:m[0]-1]
                     seasonepisode = name[m[0]+2:]
                     season = int(seasonepisode[1:3])
                     episode = int(seasonepisode[4:6])
                     meta = getMeta(name=showname,season=season,episode=episode) 
                except:
                     pass
               
                addDir(name,link,3,image,meta=meta) #adds dir listing of episodes
                 
            more = soup.findAll('div',attrs={'class':'more_posts'});
            for div in more:
                next_post = div.find('a')['href']
                if next_post != "#":
                     addDir(next_post,next_post,'2','') #adds dir listing for next page

            more = soup.findAll('div',attrs={'class':'alignleft'});
            for div in more:
                    if div.find('a') is not None:
                            next_post = div.find('a')['href']
                            addDir(next_post,next_post,'2','') #adds dir listing for next page
                 
            
             
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

 
def addLink(name,url,iconimage,mediaType=None,infoLabels=False,trailer=None,meta=None):
        ok=True

        downloadPath = _PLUG.get_setting(mediaType+'downpath')
                
        #handle adding context menus
        contextMenuItems = []
        contextMenuItems.append(('Show Information', 'XBMC.Action(Info)',))
        contextMenuItems.append(('Download Video', "RunScript("+downloadScript+","+url.encode('utf-8','ignore')+","+downloadPath+","+name+","+mediaType+")",))
        if trailer is not None:
             contextMenuItems.append(('Watch Trailer', 'xbmc.PlayMedia('+trailer+')',))

        if meta is None:     
             liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        else:

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

             if meta.has_key('season_num'):
                 infoLabels['Episode'] = int(meta['episode_num'])
                 infoLabels['Season'] =int(meta['season_num'])
                 print 'No refresh for episodes yet'
             
        liz.setInfo( type="Video", infoLabels=infoLabels )

        if contextMenuItems:
             #print str(contextMenuItems)
             liz.addContextMenuItems(contextMenuItems, replaceItems=True)
             
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok
     
def getMeta(name=None,season=None,episode=None,year=None,imdbid=None,tvdbid=None):
        print 'getMeta() ran',name,season,episode,year,imdbid,tvdbid
        useMeta = _PLUG.get_setting('use-meta')
        print useMeta
        if useMeta == 'true':
             print 'use-meta = true'
             metaget=metahandlers.MetaData(translateddatapath)
             if episode and season is not None:
                  print 'getMeta() is tvshow'
                  #get_episode_meta(self, tvshowtitle, imdb_id, season, episode, air_date='', episode_title='', overlay=''):
                  #get season and episode
                  meta=metaget.get_meta('tvshow',name)
                  #meta=megaget.get_episode_meta(name,meta['imdbid'],season,episode)
                  
                  #_get_tv_extra(self, meta):
                  #meta=metaget.get_tv_extra(meta)
             else:
                  #get_meta(self, media_type, name, imdb_id='', tmdb_id='', year='', overlay=6):
                  #get regular
                  meta=metaget.get_meta('movie',name,year=year)
        return meta
     
def addDir(name,url,mode,iconimage,meta=None):

        
        #handle adding context menus
        contextMenuItems = []
        contextMenuItems.append(('HELP', "RunScript("+textBoxesScript+",HELP,"+helpText+")",))

        
        u=sys.argv[0]+"?url="+urllib.quote_plus(url.encode('utf-8','ignore'))+"&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode('utf-8','ignore'))
        ok=True
        
        if meta is None:     
             liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
     
        else:

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

             if meta.has_key('season_num'):
                 infoLabels['Episode'] = int(meta['episode_num'])
                 infoLabels['Season'] =int(meta['season_num'])
                 print 'No refresh for episodes yet'
                 
        liz.setInfo( type="Video", infoLabels={ "Title": name } )

        if contextMenuItems:
             #print str(contextMenuItems)
             liz.addContextMenuItems(contextMenuItems, replaceItems=False)
             
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
        
#for passing parameters between menus              
params=get_params()
url=None
name=None
mode=None

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

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

#main exicution of menu navigation
if mode==None or url==None or len(url)<1:
        print ""
        STARTPOINT()
        
elif mode==1:
        print ""+url
        INDEX(url)
        
elif mode==2:
        print ""+url
        INDEX2(url,name)

elif mode==3:
        print ""+url
        INDEX3(url,name)

elif mode==10:
        print ""
        CATEGORIES()

elif mode==100:
        print""
        BARWOMAIN()
        
elif mode==11:
        print""
        BARWOGENRE()

elif mode==112:
        print""
        BARWOGENRELIST(url,name)

elif mode==113:
        print""
        BARWOMOVIE(url,name)
       
elif mode==300:
        print""
        BUNNYMAIN()
        
elif mode==311:
        print""
        BUNNYGENRE()

elif mode==312:
        print""
        BUNNYGENRELIST(url,name)

elif mode==313:
        print""
        BUNNYMOVIE(url,name)

elif mode==315:
        print""
        SEARCHSITE(url)

elif mode==4:
        print""
        SEARCHSITETV(url)



xbmcplugin.endOfDirectory(int(sys.argv[1]))
