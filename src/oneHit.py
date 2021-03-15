import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import sys
import pymongo
from pymongo import MongoClient
from flask import Flask
from flask import jsonify

CLIENT = pymongo.MongoClient("mongodb+srv://dsub:aAjMEPZhR4bLrm5@cluster0.vc7si.mongodb.net/OHW?retryWrites=true&w=majority")
DB = CLIENT['OHW']
COL = DB['cluster0']

app = Flask(__name__)

def fix(name):
   nameTag = name.replace("(","-").split("-")[0].strip().upper()
   return nameTag

@app.route('/one_hit/<string:band>',methods=["GET"])
def one_hit(band):
   response_json = jsonify(message="Simple server is running")
    # Enable Access-Control-Allow-Origin
   response_json.headers.add("Access-Control-Allow-Origin", "*")
   #response.headers.add("Access-Control-Allow-Origin", "*")
   #return band
   credentials = json.load(open('authorization.json'))
   client_id = credentials['client_id']
   client_secret = credentials['client_secret']

   client_credentials_manager = SpotifyClientCredentials(client_id=client_id,client_secret=client_secret)
   sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

   songs = {}
   most_pop_song = ""
   max_pop = -1
   output = {}

   resp_uri = sp.search(q=band,type='artist')
   while(len(resp_uri['artists']['items']) == 0):
      print("ERROR: BAND NOT FOUND. PLEASE TRY ANOTHER")
      band = raw_input("Which band: ")
      resp_uri = sp.search(q=band,limit=10,type='artist')
   uri = resp_uri['artists']['items'][0]['uri']
   img = resp_uri['artists']['items'][0]['images'][0]['url']
   response = sp.artist_top_tracks(uri)
   if(len(response['tracks']) < 10):
      print("Artist does not have enough songs")
   else:
      for i in range(10):
         song_name = fix(response['tracks'][i]['name'])
         song_pop = response['tracks'][i]['popularity']

         if(song_pop > max_pop):
            max_pop = song_pop
            most_pop_song = song_name

         if(song_name in songs.keys()):
            if(songs[song_name] < song_pop):
               songs[song_name] = song_pop
         else:
            songs[song_name] = song_pop
      items = songs.values()
      items.sort()
      #print(songs)
      #print(items)

   output['img'] = img
   output["band"] = band
   output["song"] = most_pop_song
   output['uri'] = uri
   print(band + "'s most popular song is " + most_pop_song)
   if(items[-1] > 30 and items[-1]-9 >= items[-2]):
      output["is_one_hit"] = True
      print(band + " is a One Hit Wonder")
   else:
      output["is_one_hit"] = False
      print(band + " is not a One Hit Wonder")

   print(output)
   return output

@app.route('/db/<string:uri>/<string:band>/<string:resp>',methods=["GET"])
def db(uri,band,resp):
   db_lookup = COL.find_one({"_id":uri}) #{id:XXXX,band:NNNN,score:[Y,N]}
   print(db_lookup)
   if(db_lookup != None):
      if(resp == "y"):
         db_lookup['score'][0]+=1
         COL.update({"_id":uri},db_lookup)
         print("YES")
      else:
         db_lookup['score'][1]+=1
         COL.update({"_id":uri},db_lookup)
         print("NO")
      print(db_lookup)
      return db_lookup
   else:
      print("NEW ITEM")
      if(resp == "y"):
         COL.insert_one({"_id":uri,"uri":uri,"band":band,"score":[1,0]})
         return {"uri":uri,"band":band,"score":[1,0]}
      else:
         COL.insert_one({"_id":uri,"uri":uri,"band":band,"score":[0,1]})
         return {"uri":uri,"band":band,"score":[0,1]}


if __name__ == "__main__":
   app.run(debug=True, host="127.0.0.1", port=28990)