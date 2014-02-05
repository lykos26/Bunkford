import sqlite3 as db
import urllib

#Constants
db_location = sys.argv[1]
kind = sys.argv[2]
name = sys.argv[3]
url = sys.argv[4]
mode = sys.argv[5]
iconimage = sys.argv[6]

print db_location
print kind 
print name 
print url 
print mode 
print iconimage

def AddFavorite(kind,name,url,mode,iconimage):
     con = None
     name = urllib.unquote_plus(name)
     #need to make sure this points to a tv show and not an episode and mode points to right spot:
     urlpieces = url.split('/')
     url = urlpieces[0] + '//' + urlpieces[2] + '/' + urlpieces[3] + '/' +urlpieces[4] + '/' + urlpieces[5] + '/'
     if 'shows' in url:
          mode = 22
          url = url + '/url.js'
          try: #try some garbage to get just the name
               SeasonLocation=name.index('- Season')
          except:
               SeasonLocation=0
               try:
                    SeasonLocation=name.index('Season')
               except:
                    pass
          if SeasonLocation > 0:
              name=name[:SeasonLocation-1]
          else:
               name=name
     if 'movies' in url:
          mode = 2
          url = url + '/play.htm'

          
     try:
         con = db.connect(db_location)
         cur = con.cursor()    
         cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='favorites';")
         favorites = cur.fetchone()
         if(favorites is None):
              print "Favorites table not found: Creating tables."
              cur.execute("CREATE TABLE favorites(kind TEXT, name TEXT, url TEXT, mode TEXT, iconimage TEXT);")
         else:
             cur.execute("""SELECT * FROM favorites WHERE url=?""", [url])
             exists = cur.fetchone() 
             if(exists is None): # if already in database, don't update
                  cur.execute("""INSERT INTO favorites(kind, name, url, mode, iconimage) VALUES (?, ?, ?, ?, ?)""", [kind, name, url, str(mode), iconimage])
     except db.Error, e:
         print "Error %s:" % e.args[0]
         sys.exit(1)
     finally:
         if con:
             con.commit()
             con.close()
def RemoveFavorite(url):
     print "REMOVE FAVORITE: RAN"
     con = None
     try:
         con = db.connect(db_location)
         cur = con.cursor()    
         cur.execute("""DELETE FROM favorites WHERE url=?""", [url])
     except db.Error, e:
         print "Error %s:" % e.args[0]
         sys.exit(1)
     finally:
         if con:
             con.commit()
             con.close()
             xbmc.executebuiltin('Container.Refresh',)

if (kind=="favorite"):
    RemoveFavorite(url)
else:
    AddFavorite(kind,name,url,mode,iconimage)
