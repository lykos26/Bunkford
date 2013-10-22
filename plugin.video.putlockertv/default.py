import sys,os
import urllib,urllib2,re,urlresolver
from metahandler import metahandlers
from t0mm0.common.addon import Addon

#necessary so that the metacontainers.py can use the scrapers
try: import xbmc,xbmcplugin,xbmcgui,xbmcaddon
except:
     xbmc_imported = False
else:
     xbmc_imported = True




#PutLockerTV - by bunkford 2013.

# global constants
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
PUTLOCKERTV_REFERRER = 'http://putlockertvshows.com'

#get path to me
putlockertvpath=os.getcwd()

_PLT = Addon('plugin.video.putlockertv', sys.argv)


def xbmcpath(path,filename):
     translatedpath = os.path.join(xbmc.translatePath( path ), ''+filename+'')
     return translatedpath

#paths etc need sorting out.
putlockertvdatapath = 'special://profile/addon_data/plugin.video.putlockertv'
metapath = putlockertvdatapath+'/mirror_page_meta_cache'
downinfopath = putlockertvdatapath+'/downloadinfologs'
transdowninfopath = xbmcpath(downinfopath,'')
transmetapath = xbmcpath(metapath,'')
translatedputlockertvdatapath = xbmcpath(putlockertvdatapath,'')
art = putlockertvpath+'/resources/art'

def f7(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]

def cleanUnicode(string):
    try:
        string = string.replace("'","").replace(unicode(u'\u201c'), '"').replace(unicode(u'\u201d'), '"').replace(unicode(u'\u2019'),'').replace(unicode(u'\u2026'),'...').replace(unicode(u'\u2018'),'').replace(unicode(u'\u2013'),'-')
        return string
    except:
        return string

def inLibraryMode():
    return xbmc.getCondVisibility("[Window.IsActive(videolibrary)]")

def addDir(name, url, mode, iconimage, metainfo=False, total=False, season=None):
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
         
         
         u = sys.argv[0] + "?url=" + sysurl + "&mode=" + str(mode) + "&name=" + sysname + "&season="+str(season)
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
             infoLabels['overlay'] = meta['watched'] # watched 7, unwatched 6

            
             
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
        addDir('TV SHOWS','http://putlockertvshows.com/tv-shows-list.html',1,'')
                       
def INDEX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="(.+?)" class="lc"> (.+?) </a>').findall(link)
        for url,name in match:
                meta = None
                
                if _PLT.get_setting('use-meta') == 'true':
                     metaget=metahandlers.MetaData(translatedputlockertvdatapath)
                     meta=metaget.get_meta('tvshow',name)
                

                img_name = re.sub(' ', '-', name)
                img_name = re.sub('[(){}<>::''..!!]','',img_name)
                img_path = '/p/' + img_name + '.jpg'
                img_path = img_path.lower()
                
                if meta is None:
                     #add directories without meta
                     addDir(name,PUTLOCKERTV_REFERRER+url,2,PUTLOCKERTV_REFERRER+img_path)
                else:
                     #add directories with meta
                     addDir(name,PUTLOCKERTV_REFERRER+url,2,meta['cover_url'],metainfo=meta)

def INDEX2(url,name):
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<a href="/watch/.+?/s(.+?)e.+?.html" class="la">WATCH</a>').findall(link)
        match.sort() # sort list so it shows season one first
        match = f7(match)
        for season in match:
                #url = '/watch/'+name+'/s'+season+'e'+episode+'.html'         
                print 'NaMe:'+name
                print 'SeAsOn:'+season
                print 'UrL:'+url
                
                meta = None
                
                if _PLT.get_setting('use-meta') == 'true':
                     metaget=metahandlers.MetaData(translatedputlockertvdatapath)
                     meta=metaget.get_meta('tvshow',name)

                     
                if meta is None:
                     #add directories without meta
                     addDir('SEASON '+season,url+'/',3,'',season=season)
                else:
                     #add directories with meta
                     addDir('SEASON '+season,url+'/',3,meta['cover_url'],metainfo=meta,season=season)

def INDEX3(url,season):
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        season = str(season)
        print 'SeaSon:'+season
        match=re.compile('<a href="/watch/(.+?)/s'+season+'e(.+?).html" class="la">WATCH</a>').findall(link)
        match.sort() # sort list so it shows first episode first
     
        for name,episode in match:
                url = '/watch/'+name+'/s'+season+'e'+episode+'.html'         
                name = re.sub('-', ' ', name)

                meta = None
                
                if _PLT.get_setting('use-meta') == 'true':
                     metaget=metahandlers.MetaData(translatedputlockertvdatapath)
                     meta=metaget.get_meta('tvshow',name)
                     imdbid=meta['imdb_id']
                     s = int(season)
                     e = int(episode)
                     meta=metaget.get_episode_meta(name,imdbid,s,e)
                     
                if meta is None:
                     #add directories without meta
                     addDir('S'+season+'E'+episode,PUTLOCKERTV_REFERRER+url,4,'')
                else:
                     #add directories with meta
                     addDir('S'+season+'E'+episode,PUTLOCKERTV_REFERRER+url,4,meta['backdrop_url'],metainfo=meta)

def VIDEOLINKS(url,name):
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<iframe src="(.+?)" width="600" height="360" frameborder="0" scrolling="no"></iframe>').findall(link)
        media_url = urlresolver.resolve(match[0]) 
        for url in match:
                #if url containt '/ifr/' then re-do video link with second url before resolving video link
                if re.search('ifr', url):
                        print 'iframe detected - more required'
                        url = PUTLOCKERTV_REFERRER+url
                        req = urllib2.Request(url)
                        req.add_header('User-Agent', USER_AGENT)
                        response = urllib2.urlopen(req)
                        link=response.read()
                        response.close()
                        match=re.compile('<iframe src="(.+?)" width="600" height="360" frameborder="0" scrolling="no"></iframe>').findall(link)
                        media_url = urlresolver.resolve(match[0]) 
                        for url in match:
                                url = urlresolver.HostedMediaFile(url=url).resolve()
                else:
                        url = urlresolver.HostedMediaFile(url=url).resolve()
    
                #xbmc.executebuiltin('XBMC.PlayMedia(%s)' % url) automatically starts playback, but isn't clean
                addLink(name,url,'')
        

                
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

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "Season: "+str(season)

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

xbmcplugin.endOfDirectory(int(sys.argv[1]))
