# coding=utf-8
# Rewrite (use JSON API, other matching tweaks) by Timmy

import time
import os
import json
import os, string, hashlib, base64, re, plistlib, unicodedata
import config
from collections import defaultdict
from io import open

ARTIST_SEARCH_URL_QQ = 'https://api.qq.jsososo.com/search?t=9&key='
ARTIST_ALBUM_URL_QQ = 'https://api.qq.jsososo.com/singer/album?pageSize=100&singermid='
ALBUM_INFO_URL_QQ = 'https://api.qq.jsososo.com/album?albummid='
ALBUM_SONG_URL_QQ = 'https://api.qq.jsososo.com/album/songs?albummid='
ARTIST_URL_QQ = 'https://api.qq.jsososo.com/singer/desc?singermid='
ARTIST_HOTSONG_QQ = 'https://api.qq.jsososo.com/singer/songs?page=1&num=20&singermid='
ARTIST_SIMILAR_QQ = 'https://api.qq.jsososo.com/singer/sim?singermid='
ARTIST_ALBUM_SEARCH_URL_QQ = 'https://api.qq.jsososo.com/search?t=8&key='
LYRIC_URL_QQ = 'https://api.qq.jsososo.com/lyric?songmid='
SINGERPIC_QQ = 'http://y.gtimg.cn/music/photo_new/T001R150x150M000%s.jpg'
ALBUMPIC_QQ = 'http://y.gtimg.cn/music/photo_new/T002R300x300M000%s.jpg'


ARTIST_SEARCH_URL_WANGYI = 'http://music.163.com/api/search/get/web?csrf_token=hlpretag=&hlposttag=&s='
ARTIST_ALBUM_SEARCH_URL_WANGYI = 'http://music.163.com/api/artist/albums/'
ALBUM_INFO_URL_WANGYI = 'http://music.163.com/api/album/'
SERACH_TYPE = '&type=100'

ARTIST_URL_WANGYI = 'http://music.163.com/api/v1/artist/'
LYRIC_URL_WANGYI = 'https://music.163.com/api/song/lyric?id='

# Tunables.
ARTIST_MATCH_LIMIT = 9 # Max number of artists to fetch for matching purposes.
ARTIST_MATCH_MIN_SCORE = 75 # Minimum score required to add to custom search results.
ARTIST_MANUAL_MATCH_LIMIT = 120 # Number of artists to fetch when trying harder for manual searches.  Multiple API hits.
ARTIST_SEARCH_PAGE_SIZE = 30 # Number of artists in a search result page.  Asking for more has no effect.
ARTIST_ALBUMS_MATCH_LIMIT = 3 # Max number of artist matches to try for album bonus.  Each one incurs an additional API request.
ARTIST_ALBUMS_LIMIT = 50 # Number of albums by artist to grab for artist matching bonus and quick album match.
ARTIST_MIN_LISTENER_THRESHOLD = 250 # Minimum number of listeners for an artist to be considered credible.
ARTIST_MATCH_GOOD_SCORE = 90 # Include artists with this score or higher regardless of listener count.
ALBUM_MATCH_LIMIT = 8 # Max number of results returned from standalone album searches with no artist info (e.g. Various Artists).
ALBUM_MATCH_MIN_SCORE = 75 # Minimum score required to add to custom search results.
ALBUM_MATCH_GOOD_SCORE = 92 # Minimum score required to rely on only Albums by Artist and not search.
ALBUM_TRACK_BONUS_MATCH_LIMIT = 3 # Max number of albums to try for track bonus.  Each one incurs at most one API request per album.
QUERY_SLEEP_TIME = 0.1 # How long to sleep before firing off each API request.

# Advanced tunables.
NAME_DISTANCE_THRESHOLD = 2 # How close do album/track names need to be to match for bonuses?
ARTIST_INITIAL_SCORE = 90 # Starting point for artists before bonus/deductions.
ARTIST_ALBUM_BONUS_INCREMENT = 3 # How much to boost the bonus for a each good artist/album match.
ARTIST_ALBUM_MAX_BONUS = 15 # Maximum number of bonus points to give artists with good album matches.
ARTIST_MAX_DIST_PENALTY = 40 # Maxiumum amount to penalize for Lev ratio difference in artist names.
ALBUM_INITIAL_SCORE = 92 # Starting point for albums before bonus/deductions.
ALBUM_NAME_DIST_COEFFICIENT = 5 # Multiply album Lev. distance to give it a bit more weight.
ALBUM_TRACK_BONUS_INCREMENT = 3 # How much to boost the bonus for a each good album/track match.
ALBUM_TRACK_MAX_BONUS = 20 # Maximum number of bonus points to give to albums with good track name matches.
ALBUM_TRACK_BONUS_MAX_ARTIST_DSIT = 2 # How similar do the parent artist and album search result artist need to be to ask for info?
ALBUM_NUM_TRACKS_BONUS = 1 # How much to boost the bonus if the total number of tracks match.

RE_STRIP_PARENS = Regex('\([^)]*\)')

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'origin': 'https://y.qq.com',
    'referer': 'https://y.qq.com/portal/playlist.html'
}

def Start():
  HTTP.CacheTime = CACHE_1WEEK

@expose
def ArtistTopTracks(artist, lang='en'):
  id = String.Quote(artist.decode('utf-8').encode('utf-8')).replace(' ','+')
  return GetArtistTopTracks(id, lang)


@expose
def ArtistGetSimilar(artist, lang='en'):
  id = String.Quote(artist.decode('utf-8').encode('utf-8')).replace(' ','+')
  return GetArtistSimilar(id, lang)


# Change pinyin
def multi_get_letter(str_input): 
  if isinstance(str_input, unicode): 
    unicode_str = str_input 
  else: 
    try: 
      unicode_str = str_input.decode('utf8') 
    except: 
      try: 
        unicode_str = str_input.decode('gbk') 
      except: 
        print 'unknown coding'
        return
  return_list = [] 
  #for one_unicode in unicode_str: 
   # return_list.append(single_get_first(one_unicode)) 
  #return return_list
  return single_get_first(unicode_str)

def single_get_first(unicode1): 
  str1 = unicode1.encode('gbk') 
  try:     
    ord(str1) 
    return str1 
  except: 
    asc = ord(str1[0]) * 256 + ord(str1[1]) - 65536
    if asc >= -20319 and asc <= -20284: 
      return 'a'
    if asc >= -20283 and asc <= -19776: 
      return 'b'
    if asc >= -19775 and asc <= -19219: 
      return 'c'
    if asc >= -19218 and asc <= -18711: 
      return 'd'
    if asc >= -18710 and asc <= -18527: 
      return 'e'
    if asc >= -18526 and asc <= -18240: 
      return 'f'
    if asc >= -18239 and asc <= -17923: 
      return 'g'
    if asc >= -17922 and asc <= -17418: 
      return 'h'
    if asc >= -17417 and asc <= -16475: 
      return 'j'
    if asc >= -16474 and asc <= -16213: 
      return 'k'
    if asc >= -16212 and asc <= -15641: 
      return 'l'
    if asc >= -15640 and asc <= -15166: 
      return 'm'
    if asc >= -15165 and asc <= -14923: 
      return 'n'
    if asc >= -14922 and asc <= -14915: 
      return 'o'
    if asc >= -14914 and asc <= -14631: 
      return 'p'
    if asc >= -14630 and asc <= -14150: 
      return 'q'
    if asc >= -14149 and asc <= -14091: 
      return 'r'
    if asc >= -14090 and asc <= -13119: 
      return 's'
    if asc >= -13118 and asc <= -12839: 
      return 't'
    if asc >= -12838 and asc <= -12557: 
      return 'w'
    if asc >= -12556 and asc <= -11848: 
      return 'x'
    if asc >= -11847 and asc <= -11056: 
      return 'y'
    if asc >= -11055 and asc <= -10247: 
      return 'z'
    return ''

def pinyin(str_input): 
  b = ''
  if isinstance(str_input, unicode): 
    unicode_str = str_input 
  else: 
    try: 
      unicode_str = str_input.decode('utf8')
    except: 
      try: 
        unicode_str = str_input.decode('gbk')
      except: 
        #print 'unknown coding'
        return  
  for i in range(len(unicode_str)):
    b=b+single_get_first(unicode_str[i])
  return b.upper()
  

# Score lists of artist results.  Permutes artist_results list.
def score_artists(artists, media_artist, media_albums, lang, artist_results):
  
  for i, artist in enumerate(artists):

    # Need to coerce this into a utf-8 string so String.Quote() escapes the right characters.
    #id = String.Quote(artist['name'].decode('utf-8').encode('utf-8')).replace(' ','+')
    Log("???"+ str(i+1) +"???????????????")
    id = str(artist['singerMID'])
    Log("??????ID: " + id)
    # Search returns ordered results, but no numeric score, so we approximate one with Levenshtein ratio.
    Log("??????????????? " + media_artist.lower())
    dist = int(ARTIST_MAX_DIST_PENALTY - ARTIST_MAX_DIST_PENALTY * LevenshteinRatio(artist['singerName'].lower(), media_artist.lower()))
    Log("????????????????????? " + artist['singerName'])
    Log("?????????????????????:" + str(dist))
    try:
      dist_en = int(ARTIST_MAX_DIST_PENALTY - ARTIST_MAX_DIST_PENALTY * LevenshteinRatio((artist['alias'][0]), media_artist.lower()))
      Log("?????????" + artist['alias'][0])
      Log("????????????????????????" + str(dist_en))
      if dist_en < dist :
        dist = dist_en
    except:
      pass
    # If the match is exact, bonus.
    Log("??????dist" + str(dist))
    if artist['singerName'].lower() == media_artist.lower():
      dist = dist - 1
    # Fetching albums in order to apply bonus is expensive, so only do it for the top N artist matches.
    if i < ARTIST_ALBUMS_MATCH_LIMIT:
      bonus = get_album_bonus(media_albums, artist_id=id)
      Log("????????????" + str(bonus))
    else:
      bonus = 0
    

    # Adjust the score.
    score = ARTIST_INITIAL_SCORE + bonus - dist
    Log("???????????????: " + str(score))    
    name = artist['singerName']

    if score >= ARTIST_MATCH_MIN_SCORE:
      artist_results.append(MetadataSearchResult(id=id, name=name, lang=lang, score=score))
    else:
      Log('Skipping artist, didn\'t meet minimum score of ' + str(ARTIST_MATCH_MIN_SCORE))
      
    # Sort the resulting artists.
    artist_results.sort(key=lambda r: r.score, reverse=True)


def GetArtistSimilar(artist_id):
  url = ARTIST_SIMILAR_QQ + artist_id
  try:
    similar_artists_result = GetJSON(url)
    if similar_artists_result.has_key('error'):
      Log('Error receiving similar artists: ' + similar_artists_result['message'])
      return []
    if isinstance(similar_artists_result['data']['list'], list) or isinstance(similar_artists_result['data']['list'], dict):
      return Listify(similar_artists_result['data']['list'])
  except:
    Log('Exception getting similar artists.')
    return []
  

# Get albums by artist and boost artist match score accordingly.  Returns bonus (int) of 0 - ARTIST_ALBUM_MAX_BONUS.
def get_album_bonus(media_albums, artist_id):
  
  Log('???????????????????????????')
  bonus = 0
  albums = GetAlbumsByArtist(artist_id, albums=[], limit=ARTIST_ALBUMS_LIMIT)
  
  try:
    for a in media_albums:    
      media_album = a.lower()
      #Log("??????????????????" + media_album)
      for album in albums:
        # If the album title is close enough to the media title, boost the score.
        #Log("???????????????" + album['name'].lower())
        #Log("?????????" + str(Util.LevenshteinDistance(media_album,album['name'].lower())))
        #Log(Util.LevenshteinDistance(media_album,album['name'].lower()))
        if Util.LevenshteinDistance(media_album, album['album_name'].lower()) < NAME_DISTANCE_THRESHOLD:
          bonus += ARTIST_ALBUM_BONUS_INCREMENT
        
        # This is a cheap comparison, so let's try again with the contents of parentheses removed, e.g. "(limited edition)"
        elif Util.LevenshteinDistance(media_album,RE_STRIP_PARENS.sub('',album['album_name'].lower())) < NAME_DISTANCE_THRESHOLD:
          bonus += ARTIST_ALBUM_BONUS_INCREMENT
        
        # Stop trying once we hit the max bonus.
        if bonus >= ARTIST_ALBUM_MAX_BONUS:
          break
  
  except Exception, e:
    Log('Error applying album bonus: ' + str(e))
  if bonus > 0:
    Log('?????????????????????: ' + str(bonus))
  return bonus


class QQmusicAgent(Agent.Artist):
  name = 'qqmusic'
  languages = [Locale.Language.Chinese]

  def search(self, results, media, lang, manual):

    # Handle a couple of edge cases where artist search will give bad results.
    if media.artist == '[Unknown Artist]': 
      return
    if media.artist == 'Various Artists':
      results.Append(MetadataSearchResult(id = 'Various%20Artists', name= 'Various Artists', thumb = VARIOUS_ARTISTS_POSTER, lang  = lang, score = 100))
      return

    # Search for artist.
    Log('????????????: ' + media.artist)
    if manual:
      Log('Running custom search...')
    artist_results = []

    artists = SearchArtists(media.artist, ARTIST_MATCH_LIMIT)
    media_albums = [a.title for a in media.children]
    Log("???????????????")
    Log(media_albums)

    # Score the first N results.
    score_artists(artists, media.artist, media_albums, lang, artist_results)

    for artist in artist_results:
      results.Append(artist)

  def update(self, metadata, media, lang):
    artist = GetArtist(metadata.id, lang)
    
    # Name.
    try:
      metadata.title = artist['singername']
      Log(metadata.title)
      metadata.title_sort = pinyin(metadata.title)
    except:
      pass
    # Bio.
    try:
      metadata.summary = artist['desc'].strip()
      Log(metadata.summary )
    except:
      pass

    # Artwork.
    try:
      if artist['singername'] == 'Various Artists':
          metadata.posters[VARIOUS_ARTISTS_POSTER] = Proxy.Media(HTTP.Request(VARIOUS_ARTISTS_POSTER))
      else:
          aritst_pic = SINGERPIC_QQ % metadata.id
          Log(SINGERPIC_QQ % metadata.id)
          metadata.posters[aritst_pic] = Proxy.Media(HTTP.Request(aritst_pic))
    except:
        Log('Couldn\'t add artwork for artist.')
        
    # Find similar artists.
    metadata.similar.clear()
    similar_artists = GetArtistSimilar(metadata.id)
    if similar_artists is not None:
      for similar in similar_artists:
        metadata.similar.add(similar['name'])
  
class QQmusicAgent(Agent.Album):
  name = 'qqmusic'
  languages = [Locale.Language.Chinese]
  accepts_from = ['com.plexapp.agents.localmedia','com.plexapp.agents.lyricfind']
  
  def search(self, results, media, lang, manual):

    # Handle a couple of edge cases where album search will give bad results.
    if media.parent_metadata.id is None:
      return
    if media.parent_metadata.id == '[Unknown Album]':
      return #eventually, we might be able to look at tracks to match the album
    Log(manual)
    # Search for album.
    if manual:
      # If this is a custom search, use the user-entered name instead of the scanner hint.
      try:
        Log('????????????: ' + media.name)
        media.title = media.name
      except:
        pass
    else:
      Log('????????????: ' + media.title)
    Log('????????????: ' + media.title)
    albums = []
    found_good_match = False

    # First try matching in the list of albums by artist for single-artist albums.
    if media.parent_metadata.id != 'Various%20Artists':

      # Start with the first N albums (ideally a single API request).
      if not manual:
        albums = self.score_albums(media, lang, GetAlbumsByArtist(media.parent_metadata.id, albums=[]))
        Log('????????????')
        Log(albums)
        # Check for a good match within these reults.  If we find one, set the flag to stop looking.
        if albums and albums[0]['score'] >= ALBUM_MATCH_GOOD_SCORE:
          found_good_match = True
          Log('Good album match found (quick search) with score: ' + str(albums[0]['score']))

      # If we haven't found a good match yet, or we're running a custom search, get all albums by artist.  May be thousands
      # of albums and several API requests to complete this list, so we use it sparingly.
      if not found_good_match or manual:
        if manual:
          Log('Custom search terms specified, fetching all albums by artist.')
        else:
          Log('No good matches found in first ' + str(len(albums)) + ' albums, fetching all albums by artist.')
        albums = self.score_albums(media, lang, GetAlbumsByArtist(media.parent_metadata.id, albums=[]), manual=manual)
        Log('????????????')
        #Log(albums)
        # If we find a good match this way, set the flag to stop looking.
        if albums and albums[0]['score'] >= ALBUM_MATCH_GOOD_SCORE:
          Log('Good album match found with score: ' + str(albums[0]['score']))
          found_good_match = True
        else:
          Log('No good matches found in ' + str(len(albums)) + ' albums by artist.')


    #???????????????
    if not found_good_match :
      Log("??????")
    if albums:
      Log("??????")
    if not found_good_match or not albums:
    #if  found_good_match == False:
      Log('??????????????????????????? ??????????????????')
      albums = self.score_albums(media, lang, SearchAlbums(media.title.lower(), ALBUM_MATCH_LIMIT), manual=manual) + albums
      
      # If we find a good match for the exact search, stop looking.
      if albums and albums[0]['score'] >= ALBUM_MATCH_GOOD_SCORE:
        found_good_match = True
        Log('Found a good match for album search.')
      
      # If we still haven't found anything, try another match with parenthetical phrases stripped from
      # album title.  This helps where things like '(Limited Edition)' and '(disc 1)' may confuse search.
      if not albums or not found_good_match:
        stripped_title = RE_STRIP_PARENS.sub('',media.title).lower()
        if stripped_title != media.title.lower():
          Log('No good matches found in album search for %s, searching for %s.' % (media.title.lower(), stripped_title))
          # This time we extend the results  and re-sort so we consider the best-scoring matches from both searches.
          albums  = self.score_albums(media, lang, SearchAlbums(stripped_title), manual=manual) + albums
        if albums:
          albums = sorted(albums, key=lambda k: k['score'], reverse=True)

    # Dedupe albums.
    seen = {}
    deduped = []
    for album in albums:
      if album['id'] in seen:
        continue
      seen[album['id']] = True
      deduped.append(album)
    albums = deduped

    Log('Found ' + str(len(albums)) + ' albums...')

    # Limit to 10 albums.
    albums = albums[:10]
    Log(albums)
    for album in albums:
      if album['score'] > 0:
        if album['score'] > 100:
          album['score'] = 99
        Log(album['score'])
        Log(album['id'])
        Log(album['name'])
        Log(album['lang'])
        results.Append(MetadataSearchResult(id = str(album['id']), name = album['name'], lang = album['lang'], score = str(album['score'])))

  # Score a list of albums, return a fresh list of scored matches above the ALBUM_MATCH_MIN_SCORE threshold.
  def score_albums(self, media, lang, albums, manual=False):
    res = []
    matches = []
    for album in albums:
      try:
        name = album['album_name']
        Log("??????????????????" + media.title)
        Log("??????????????????" + name)
        #id = media.parent_metadata.id + '/' + String.Quote(album['name'].decode('utf-8').encode('utf-8')).replace(' ','+')
        id = media.parent_metadata.id + '/' + str(album['album_mid'])
        #Log("??????+?????? id??????" + id)
        dist = Util.LevenshteinDistance(name.lower(),media.title.lower()) * ALBUM_NAME_DIST_COEFFICIENT  #???????????????
        Log("??????????????????" + str(dist))
        artist_dist = 100
        # Freeform album searches will come back with wacky artists.  If they're not close, penalize heavily, skipping them.
        for artist in album['singers']:
          Log("??????????????????" + artist['singer_name'])
          if Util.LevenshteinDistance(artist['singer_name'].lower(),String.Unquote(media.parent_metadata.title).lower()) < artist_dist :     #????????????
              artist_dist = Util.LevenshteinDistance(artist['singer_name'].lower(),String.Unquote(media.parent_metadata.title).lower())
          Log("???????????????" + str(artist_dist))
        if artist_dist > ALBUM_TRACK_BONUS_MAX_ARTIST_DSIT:
          artist_dist = 1000
          Log('????????????????????? ' + album['singer_name'])
        
        # Apply album and artist penalties and append to temp results list.
        score = ALBUM_INITIAL_SCORE - dist - artist_dist
        Log("???????????????" + str(score))
        res.append({'id':id, 'name':name, 'lang':lang, 'score':score})
      
      except:
        Log('Error scoring album.')

    if res:
      res = sorted(res, key=lambda k: k['score'], reverse=True)
      #Log(res)
      for i, result in enumerate(res):
        # Fetching albums to apply track bonus is expensive, so only do it for the top N results. ??????????????????????????????????????????
        if i < ALBUM_TRACK_BONUS_MATCH_LIMIT:
          Log("id="+ result['id'].split('/')[1])
          Log("???????????????"+ result['name'])
          bonus = self.get_track_bonus(media, result['id'].split('/')[1], lang)
          res[i]['score'] = res[i]['score'] + bonus
        # Append albums that meet the minimum score, skip the rest.
        if res[i]['score'] >= ALBUM_MATCH_MIN_SCORE or manual:
          Log('Album result: ' + result['name'] + ' album bonus: ' + str(bonus) + ' score: ' + str(result['score']))
          matches.append(res[i])
        else:
          Log('Skipping %d album results that don\'t meet the minimum score of %d.' % (len(res) - i, ALBUM_MATCH_MIN_SCORE))
          break

    # Sort once more to account for track bonus and return.
    if matches:
      return sorted(matches, key=lambda k: k['score'], reverse=True)
    else:
      return matches
  
  # Get album info in order to compare track listings and apply bonus accordingly.  Return a bonus (int) of 0 - ALBUM_TRACK_MAX_BONUS.
  def get_track_bonus(self, media, album_id, lang):
    tracks = GetTracks(media.parent_metadata.id,str(album_id), lang)
    bonus = 0
    try:
      for i, t in enumerate(media.children):
        media_track = t.title.lower()
        #Log("??????????????????" + media_track)
        for j, track in enumerate(tracks):

          # If the names are close enough, boost the score.
          #Log("??????????????????" + track['name'] + "????????????" + str(Util.LevenshteinDistance(track['name'].lower(), media_track)))
          if Util.LevenshteinDistance(track['name'].lower(), media_track) <  NAME_DISTANCE_THRESHOLD:
            bonus += ALBUM_TRACK_BONUS_INCREMENT

      # If the albums have the same number of tracks, boost more.
      if len(media.children) == len(tracks):
        bonus += ALBUM_NUM_TRACKS_BONUS
      
      # Cap the bonus.
      if bonus >= ALBUM_TRACK_MAX_BONUS:
        bonus = ALBUM_TRACK_MAX_BONUS

    except:
      Log('Didn\'t find any usable tracks in search results, not applying track bonus.')

    if bonus > 0:
      Log('Applying track bonus of: ' + str(bonus))
    return bonus
 
  def update(self, metadata, media, lang):
    album = GetAlbum(metadata.id.split('/')[1], lang)
    album_song = GetAlbumsong(metadata.id.split('/')[1], lang)
    if not album:
      return

    # Title.
    metadata.title = album['name']
    
    # Artwork.
    try:
      album_pic = ALBUMPIC_QQ % metadata.id.split('/')[1]
      valid_keys = album_pic
      metadata.posters[valid_keys] = Proxy.Media(HTTP.Request(valid_keys))
      metadata.posters.validate_keys(valid_keys)
    except:
      Log('Couldn\'t add artwork for album.')

    # Release Date.
    try:
      #Log(Datetime.ParseDate(time.strftime("%Y-%m-%d", time.localtime(int(int(album['publishTime'])/1000)))))
      #metadata.originally_available_at = Datetime.ParseDate(time.strftime("%Y-%m-%d", time.localtime(int(int(album['publishTime'])/1000))))
      metadata.originally_available_at = Datetime.ParseDate(album['publishTime'])
      
    except:
      Log('Couldn\'t add release date to album.')
      
    # ??????
    try:
      metadata.summary = album['desc'].replace('\n',' ')
      Log(metadata.summary)
      Log("?????????id??????")
      Log(metadata.id)
      Log(media.id)
    except:
      Log("??????????????????")

    try:
      metadata.studio = album['company']
      Log(metadata.studio)
    except:
      pass
    # Genres.
    metadata.genres.clear()
    try:
        for genre in Listify(album['toptags']['tag']):
          metadata.genres.add(genre['name'].capitalize())
    except:
        Log('Couldn\'t add genre tags to album.')

    # Top tracks.
    most_popular_tracks = {}
    try:
      top_tracks = GetArtistTopTracks(metadata.id.split('/')[0])
      #Log(top_tracks)
      for track in top_tracks:
        most_popular_tracks[track['name']] = int(track['bpm'])
    except:
      pass
    #Log(most_popular_tracks)
    valid_keys = defaultdict(list)
    for index in media.tracks:
      key = media.tracks[index].guid or int(index)
      #valid_keys.append(key)
      for popular_track in most_popular_tracks.keys():
        #Log(popular_track)
        if popular_track and LevenshteinRatio(popular_track, media.tracks[index].title) > 0.95:
          t = metadata.tracks[key]
          t.rating_count = most_popular_tracks[popular_track]
          #Log(t.rating_count)
      #Log("key:")
      #Log(key)
      #Log(index)
      #Log(media.tracks[index])
      #Log(media.tracks[index].items)

      track_id = '0'
      metadata.tracks[key].original_title = media.parentTitle
      #Log(media.parentTitle)
      for track in album_song :
        #Log(track['name'])
        #Log(media.tracks[index].title)
        #Log(LevenshteinRatio(track["name"], media.tracks[index].title))
        if track and LevenshteinRatio(track["name"], media.tracks[index].title) > 0.9:
          t = metadata.tracks[key]
          #t.rating_count = int(track["popularity"])
          #Log("t.rating_count:")
          #Log(t.rating_count)
          track_id = track["mid"]
          art = []
          for artist in track["singer"] :
            art.append(artist['name'])
          Log('/'.join(art))
          t.original_title = '/'.join(art)
      for item in media.tracks[index].items:
        for part in item.parts:
          filename = part.file
          path = os.path.dirname(filename)
          (file_root, fext) = os.path.splitext(filename)

          path_files = {}

          if len(path) > 0:
            for p in os.listdir(path):
              path_files[p.lower()] = p
          #Log(path_files)
          
          # Look for lyrics.
          lrc_exist = False
          file = (file_root + '.lrc')
          file2 = (file_root + '.txt')
          #Log("file:")
          #Log(file)
          if os.path.exists(file):
            Log('Found a lyric in %s', file)
            metadata.tracks[key].lyrics[file] = Proxy.LocalFile(file, format='lrc')
            valid_keys[key].append(file)
            lrc_exist = True 
          if not lrc_exist :
            Log(track_id)
            Log("???????????????????????? ????????????????????????:")
            if not (track_id == '0') :
              if Prefs['lyc']:
                Log(track_id)
                lyricinfo = DownlodeLyric(track_id)
                lyric = lyricinfo['data']['lyric']
                Log(lyric)
                #tlyric = lyricinfo['tlyric']['lyric']
                #Log(tlyric)
                if lyric is not None :
                    Log("????????????LYRIC")    
                    with open(file,'w+',encoding='utf8') as f:
                        f.write(lyric)
                        f.close()
                    metadata.tracks[key].lyrics[file] = Proxy.LocalFile(file, format='lrc')
                    valid_keys[key].append(file)
                #elif tlyric is not None :
                    #Log("????????????TXT")
                    #with open(file2,'w+',encoding='utf8') as f:
                    #    f.write(tlyric)
                    #    f.close()
                    #metadata.tracks[key].lyrics[file2] = Proxy.LocalFile(file2, format='txt')
                    #valid_keys[key].append(file2)
                else:
                      Log("??????????????????")
            else:
              Log('?????????????????????????????????????????????????????????')                
              
              
      #Log(valid_keys)    
      for k in metadata.tracks:
        metadata.tracks[k].lyrics.validate_keys(valid_keys[k])    
      #for popular_track in most_popular_tracks.keys():
        #Log("popular_track:")
        #Log(popular_track)
        #Log("media.tracks[index].title :")
        #Log(media.tracks[index].title)
        #Log("????????????????????????????????????")
        #Log(LevenshteinRatio(popular_track, media.tracks[index].title))
        #if popular_track and LevenshteinRatio(popular_track, media.tracks[index].title) > 0.95:
        #  t = metadata.tracks[key]
        #  Log("t :")
        #  Log(t)
        #  if Prefs['popular']:
        #    t.rating_count = most_popular_tracks[popular_track]
        #  else:
        #    t.rating_count = 0
        #  Log("t.rating_count:")
        #  Log(t.rating_count)


def DownlodeLyric(trackid):
  url =LYRIC_URL_QQ + str(trackid)
  try: 
    response = GetJSON(url)
  except:
    Log('Error retrieving lrc search results.')
  return response 
  
      
def SearchArtists(artist, limit=10):
  artists = []

  if not artist:
    Log('Missing artist. Skipping match')
    return artists
  try:
    a = artist.lower().encode('utf-8')
  except:
    a = artist.lower()
  url = ARTIST_SEARCH_URL_QQ + String.Quote(a)
  try: 
    response = GetJSON(url)
    num = int(response['data']['total'])
  except:
    Log('Error retrieving artist search results.')
    
  lim = min(limit,num)
  Log('???????????????????????????' + str(lim))
  for i in range(lim):
    try:
      artist_results = response['data']
      artists = artists + Listify(artist_results['list'])
    except:
      Log('Error retrieving artist search results.')
  # Since LFM has lots of garbage artists that match garbage inputs, we'll only consider ones that have
  # either a MusicBrainz ID or artwork.
  #
  #valid_artists = [a for a in artists if a['mbid'] or (len(a.get('image', [])) > 0 and a['image'][0].get('#text', None))]
  #if len(artists) != len(valid_artists):
  #  Log('Skipping artist results because they lacked artwork or MBID: %s' % ', '.join({a['name'] for a in artists}.difference({a['name'] for a in valid_artists})))

  #return valid_artists
  return artists


def SearchAlbums(album, limit=10, legacy=False):
  albums = []

  if not album:
    Log('Missing album. Skipping match')
    return albums

  try:
    a = album.lower().encode('utf-8')
  except:
    a = album.lower()
  Log("??????????????????" + a)
  url = ARTIST_ALBUM_SEARCH_URL_QQ + String.Quote(a)
  try:
    response = GetJSON(url)
    if response.has_key('error'):
      Log('??????????????????: ' + response['message'])
      return albums
    else:
      album_results = response['data']
      albums = Listify(album_results['list'])
  except:
    Log('Error retrieving album search results.')

  return albums


def GetAlbumsByArtist(artist_id, limit=ARTIST_ALBUMS_LIMIT*4,albums=[], legacy=True):
  Log("????????????id" + artist_id)
  url = ARTIST_ALBUM_URL_QQ + artist_id
  response = GetJSON(url)
  try:
    albums.extend(Listify(response['data']['list']))
  except:
    # Sometimes the API will lie and say there's an Nth page of results, but the last one will return garbage.
    pass
  return albums


def GetArtist(id, lang='en'):
  url =ARTIST_URL_QQ + id
  try:
    artist_results = GetJSON(url)
    if artist_results.has_key('error'):
      Log('Error retrieving artist metadata: ' + artist_results['message'])
      return {}
    return artist_results['data']
  except:
    Log('Error retrieving artist metadata.')
    return {}


def GetAlbum(album_id, lang='en'):
  url = ALBUM_INFO_URL_QQ + album_id
  try:
    album_results = GetJSON(url)
    if album_results.has_key('error'):
      Log('Error retrieving album metadata: ' + album_results['message'])
      return {}
    return album_results['data']
  except:
    Log('Error retrieving album metadata.')
    return {}


def GetAlbumsong(album_id, lang='en'):
  url = ALBUM_SONG_URL_QQ + album_id
  try:
    album_results = GetJSON(url)
    if album_results.has_key('error'):
      Log('Error retrieving album metadata: ' + album_results['message'])
      return {}
    return album_results['data']['list']
  except:
    Log('Error retrieving album metadata.')
    return {}


def GetTracks(artist_id, album_id, lang='en'):
  url = ALBUM_SONG_URL_QQ + album_id
  try:
    tracks_result = GetJSON(url)
    return Listify(tracks_result['data']['list'])
  except:
    Log('Error retrieving tracks.')
    return []


def GetArtistTopTracks(artist_id):
  result = []
  try:
    url = ARTIST_HOTSONG_QQ + artist_id
    top_tracks_result = GetJSON(url)

    # Get out if we have an error.
    if top_tracks_result.has_key('error'):
      Log('Error receiving top tracks: ' + top_tracks_result['message'])
      break
    new_results = Listify(top_tracks_result['data']['list'])
    result.extend(new_results)
  except:
    Log('Exception getting top tracks.')

  return result


def GetJSON(url, sleep_time=QUERY_SLEEP_TIME, cache_time=CACHE_1MONTH):
  d = None
  try:
    d = JSON.ObjectFromURL(url, sleep=sleep_time, cacheTime=cache_time, headers=headers)
    if isinstance(d, dict):
      return d
  except:
    Log('Error fetching JSON.')
    return None


def LevenshteinRatio(first, second):
  return 1 - (Util.LevenshteinDistance(first, second) / float(max(len(first), len(second))))

def NormalizeArtist(name):
  return Core.messaging.call_external_function('com.plexapp.agents.plexmusic', 'MessageKit:NormalizeArtist', kwargs = dict(artist=name))

# Utility functions for sanitizing Last.fm API responses.
def Listify(obj):
  if isinstance(obj, list):
    return obj
  else:
    return [obj]

def Dictify(obj, key=''):
  if isinstance(obj, dict):
    return obj
  else:
    return {key:obj}
