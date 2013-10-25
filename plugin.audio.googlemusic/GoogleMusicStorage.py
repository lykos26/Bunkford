import os
import sys
import sqlite3

class GoogleMusicStorage():
    def __init__(self):
        self.xbmc     = sys.modules["__main__"].xbmc
        self.settings = sys.modules["__main__"].settings
        self.path     = os.path.join(self.xbmc.translatePath("special://database"), self.settings.getSetting('sqlite_db'))

    def checkDbInit(self):
        # Make sure to initialize database when it does not exist.
        if ((not os.path.isfile(self.path)) or
            (not self.settings.getSetting("firstrun"))):
            self.initializeDatabase()
            self.settings.setSetting("firstrun", "1")

    def clearCache(self):
        if os.path.isfile(self.path):
            os.remove(self.path)
        self.settings.setSetting("fetched_all_songs", "")
        self.settings.setSetting('firstrun', "")

    def getPlaylistSongs(self, playlist_id):
        self._connect()

        result = []
        if playlist_id == 'all_songs':
            result = self.curs.execute("SELECT * FROM songs ORDER BY display_name")
        else:
            result = self.curs.execute("SELECT * FROM songs INNER JOIN playlists_songs ON songs.song_id = playlists_songs.song_id "+
                                       "WHERE playlists_songs.playlist_id = ? ORDER BY display_name", (playlist_id,))

        songs = result.fetchall()
        self.conn.close()

        return songs

    def getFilterSongs(self, filter_type, filter_criteria):
        self._connect()

        order_by = 'title asc'
        if filter_type == 'album':
            order_by = 'track asc'
        elif filter_type == 'artist':
            order_by = 'album asc, track asc'

        query = "SELECT * FROM songs WHERE %s = ? ORDER BY %s, display_name" % (filter_type, order_by)
        result = self.curs.execute(query, (filter_criteria.decode('utf8') if filter_criteria else '',))
        songs = result.fetchall()
        self.conn.close()

        return songs

    def getCriteria(self, criteria, artist):
        self._connect()
        if artist:
            artist = 'WHERE artist = "'+artist+'"'
            print artist
        criterias = self.curs.execute("SELECT "+criteria+", album_art_url FROM "+
                                      "(SELECT "+criteria+", album_art_url FROM songs "+artist+" GROUP BY "+criteria+", album_art_url) "+
                                      "GROUP BY "+criteria).fetchall()
        self.conn.close()
        if artist:
            print repr(criterias)
        return criterias

    def getPlaylistsByType(self, playlist_type):
        self._connect()
        result = self.curs.execute("SELECT playlist_id, name FROM playlists WHERE playlists.type = ? ORDER BY name", (playlist_type,))
        playlists = result.fetchall()
        self.conn.close()

        return playlists

    def getThumbsup(self):
        self._connect()
        result = self.curs.execute("SELECT * FROM songs WHERE rating = 5 ORDER BY display_name")
        results = result.fetchall()
        self.conn.close()
        return results

    def getLastadded(self):
        self._connect()
        result = self.curs.execute("SELECT * FROM songs ORDER BY creation_date desc LIMIT 500")
        results = result.fetchall()
        self.conn.close()
        return results

    def getMostplayed(self):
        self._connect()
        result = self.curs.execute("SELECT * FROM songs ORDER BY play_count desc LIMIT 500")
        results = result.fetchall()
        self.conn.close()
        return results

    def getFreepurchased(self):
        self._connect()
        result = self.curs.execute("SELECT * FROM songs WHERE type = 0 OR type = 1")
        results = result.fetchall()
        self.conn.close()
        return results

    def getSong(self, song_id):
        self._connect()
        result = self.curs.execute("SELECT * FROM songs WHERE song_id = ?", (song_id,)).fetchone()
        self.conn.close()

        return result

    def getSearch(self, query):
        query = '%'+ query.replace('%','') + '%'
        self._connect()
        result = self.curs.execute("SELECT * FROM songs WHERE name like ? OR artist like ? ORDER BY display_name", (query,query,)).fetchall()
        self.conn.close()

        return result


    def storePlaylistSongs(self, playlists_songs):
        self._connect()
        self.curs.execute("PRAGMA foreign_keys = OFF")
        
        self.curs.execute("DELETE FROM playlists_songs")
        self.curs.execute("DELETE FROM playlists")
            
        for playlist in playlists_songs:
            print playlist['name']+' '+playlist['id']+' '+str(len(playlist['name']))
            playlistId = playlist['id']
            if len(playlist['name']) > 0:
               try:
                 self.curs.execute("INSERT INTO playlists (name, playlist_id, type, fetched) VALUES (?, ?, 'user', 1)", (playlist['name'], playlistId) )
                 self.curs.execute("DELETE FROM playlists_songs WHERE playlist_id = ?", (playlistId,))
                 self.curs.executemany("INSERT INTO playlists_songs (playlist_id, song_id) VALUES (?, ?)", [(playlistId, s['trackId']) for s in playlist['tracks']])
               except Exception as ex:
                 print "ERROR: "+repr(ex)
            #for track in playlist['tracks']:
            #   print track['trackId']+' '+track['id']
        self.conn.commit()
        self.conn.close()

    def storeApiSongs(self, api_songs, playlist_id = 'all_songs'):
        self._connect()
        self.curs.execute("PRAGMA foreign_keys = OFF")

        if playlist_id == 'all_songs':
            self.curs.execute("DELETE FROM songs")
        else:
            self.curs.execute("DELETE FROM songs WHERE song_id IN (SELECT song_id FROM playlists_songs WHERE playlist_id = ?)", (playlist_id,))
            self.curs.execute("DELETE FROM playlists_songs WHERE playlist_id = ?", (playlist_id,))
            self.curs.executemany("INSERT INTO playlists_songs (playlist_id, song_id) VALUES (?, ?)", [(playlist_id, s["id"]) for s in api_songs])


        def songs():
          for api_song in api_songs:
              yield {
                  'song_id': api_song["id"],
                  'comment': (api_song["comment"] if "comment" in api_song else 0),
                  'rating': (api_song["rating"] if "rating" in api_song else 0),
                  'last_played': (api_song["lastPlayed"] if "lastPlayed" in api_song else api_song.get("recentTimestamp",None)),
                  'disc': (api_song["disc"] if "disc" in api_song else api_song.get("discNumber",None)),
                  'composer': (api_song["composer"] if "composer" in api_song else 0),
                  'year': (api_song["year"] if "year" in api_song else 0),
                  'album': (api_song["album"] if "album" in api_song else 'album'),
                  'title': api_song["title"],
                  'album_artist': (api_song["albumArtist"] if "albumArtist" in api_song else 'albumArtist'),
                  'type': (api_song["type"] if "type" in api_song else 0),
                  'track': (api_song["track"] if "track" in api_song else api_song.get("trackNumber",None)),
                  'total_tracks': (api_song["total_tracks"] if "total_tracks" in api_song else api_song.get("totalTrackCount",None)),
                  'beats_per_minute': (api_song["beatsPerMinute"] if "beatsPerMinute" in api_song else 0),
                  'genre': (api_song["genre"] if "genre" in api_song else ''),
                  'play_count': (api_song["playCount"] if "playCount" in api_song else 0),
                  'creation_date': (api_song["creationDate"] if "creationDate" in api_song else api_song["creationTimestamp"]),
                  'name': (api_song["name"] if "name" in api_song else api_song["title"]),
                  'artist': (api_song["artist"] if "artist" in api_song else 'artist'),
                  'url': api_song.get("url", None),
                  'total_discs': (api_song["total_discs"] if "total_discs" in api_song else api_song.get("totalDiscCount",None)),
                  'duration_millis': api_song["durationMillis"],
                  'album_art_url': self._getAlbumArtUrl(api_song),
                  'display_name': self._getSongDisplayName(api_song)
              }

        self.curs.executemany("INSERT OR REPLACE INTO songs VALUES ("+
                              ":song_id, :comment, :rating, :last_played, :disc, :composer, :year, :album, :title, :album_artist,"+
                              ":type, :track, :total_tracks, :beats_per_minute, :genre, :play_count, :creation_date, :name, :artist, "+
                              ":url, :total_discs, :duration_millis, :album_art_url, :display_name, NULL)", songs())

        if playlist_id == 'all_songs':
            self.settings.setSetting("fetched_all_songs", "1")
        else:
            self.curs.execute("UPDATE playlists SET fetched = 1 WHERE playlist_id = ?", (playlist_id,))

        self.conn.commit()
        self.conn.close()

    def storePlaylists(self, playlists, playlist_type):
        self._connect()
        self.curs.execute("PRAGMA foreign_keys = OFF")

        # (deletes will not cascade due to pragma)
        self.curs.execute("DELETE FROM playlists WHERE type = ?", (playlist_type,))

        # rebuild table
        def playlist_rows():
          for playlist_name, playlist_ids in playlists.iteritems():
             for playlist_id in playlist_ids:
                yield (playlist_name, playlist_id, playlist_type)

        self.curs.executemany("INSERT INTO playlists (name, playlist_id, type, fetched) VALUES (?, ?, ?, 0)", playlist_rows())

        # clean up dangling songs
        self.curs.execute("DELETE FROM playlists_songs WHERE playlist_id NOT IN (SELECT playlist_id FROM playlists)")
        self.conn.commit()
        self.conn.close()

    def getSongStreamUrl(self, song_id):
        self._connect()
        song = self.curs.execute("SELECT stream_url FROM songs WHERE song_id = ?", (song_id,)).fetchone()
        stream_url = song[0]
        self.conn.close()

        return stream_url

    def isPlaylistFetched(self, playlist_id):
        fetched = False
        if playlist_id == 'all_songs':
            fetched = bool(self.settings.getSetting("fetched_all_songs"))
        else:
            self._connect()
            playlist = self.curs.execute("SELECT fetched FROM playlists WHERE playlist_id = ?", (playlist_id,)).fetchone()
            fetched = bool(playlist[0])
            self.conn.close()

        return fetched

    def updateSongStreamUrl(self, song_id, stream_url):
        self._connect()
        self.curs.execute("UPDATE songs SET stream_url = ? WHERE song_id = ?", (stream_url, song_id))
        self.conn.commit()
        self.conn.close()

    def _connect(self):
        self.conn = sqlite3.connect(self.path)
        self.curs = self.conn.cursor()

    def initializeDatabase(self):
        self._connect()

        self.curs.execute('''CREATE TABLE IF NOT EXISTS songs (
                song_id VARCHAR NOT NULL PRIMARY KEY,           --# 0
                comment VARCHAR,                                --# 1
                rating INTEGER,                                 --# 2
                last_played INTEGER,                            --# 3
                disc INTEGER,                                   --# 4
                composer VARCHAR,                               --# 5
                year INTEGER,                                   --# 6
                album VARCHAR,                                  --# 7
                title VARCHAR,                                  --# 8
                album_artist VARCHAR,                           --# 9
                type INTEGER,                                   --# 10
                track INTEGER,                                  --# 11
                total_tracks INTEGER,                           --# 12
                beats_per_minute INTEGER,                       --# 13
                genre VARCHAR,                                  --# 14
                play_count INTEGER,                             --# 15
                creation_date INTEGER,                          --# 16
                name VARCHAR,                                   --# 17
                artist VARCHAR,                                 --# 18
                url VARCHAR,                                    --# 19
                total_discs INTEGER,                            --# 20
                duration_millis INTEGER,                        --# 21
                album_art_url VARCHAR,                          --# 22
                display_name VARCHAR,                           --# 23
                stream_url VARCHAR                              --# 24
        )''')

        self.curs.execute('''CREATE TABLE IF NOT EXISTS playlists (
                playlist_id VARCHAR NOT NULL PRIMARY KEY,
                name VARCHAR,
                type VARCHAR,
                fetched BOOLEAN
        )''')

        self.curs.execute('''CREATE TABLE IF NOT EXISTS playlists_songs (
                playlist_id VARCHAR,
                song_id VARCHAR,
                FOREIGN KEY(playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE,
                FOREIGN KEY(song_id) REFERENCES songs(song_id) ON DELETE CASCADE
        )''')

        self.curs.execute('''CREATE INDEX IF NOT EXISTS playlistindex ON playlists_songs(playlist_id)''')
        self.curs.execute('''CREATE INDEX IF NOT EXISTS songindex ON playlists_songs(song_id)''')

        self.conn.commit()
        self.conn.close()

    def _getSongDisplayName(self, api_song):
        displayName = ""
        song = api_song.get
        song_name = song("title").strip()
        song_artist = song("artist").strip()

        if ( (len(song_artist) == 0) and (len(song_name) == 0)):
            displayName = "UNKNOWN"
        elif (len(song_artist) > 0):
            displayName += song_artist
            if (len(song_name) > 0):
                displayName += " - " + song_name
        else:
            displayName += song_name

        return displayName

    def _getAlbumArtUrl(self, api_song):
        url = ""
        if "albumArtUrl" in api_song:
            url = "http:"+api_song["albumArtUrl"]
        elif "albumArtRef" in api_song:
            url = api_song["albumArtRef"][0]["url"]
        return url

    def _encodeApiSong(self, api_song):
        encoding_keys = ["id", "comment", "composer", "album", "title", "albumArtist", "titleNorm", "albumArtistNorm",
                         "genre", "name", "albumNorm", "artist", "url", "artistNorm", "albumArtUrl"]

        song = {}
        for key in api_song:
            key = key.encode('utf-8')
            if key in encoding_keys:
                song[key] = api_song[key].encode('utf-8')
            else:
                song[key] = api_song[key]

        return song
