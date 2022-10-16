from flask import Flask, render_template, session, redirect, request, url_for
from numpy import dot
from numpy.linalg import norm
import spotipy
import requests
import spotipy.util as util
import zipcodes
import db
import os
from geopy import distance

datab = db.Database(os.environ["DATABASE_URL"])
datab.create_db_table()

app = Flask(__name__)

API_BASE = 'https://accounts.spotify.com'

app.secret_key = "app sec key"

# Make sure you add this to Redirect URIs in the setting of the application dashboard
REDIRECT_URI = "http://127.0.0.1:5000/api_callback"

SCOPE = 'playlist-modify-private,playlist-modify-public,user-top-read,user-read-email'

CLI_ID = 'ID'

CLI_SEC = 'SEC'


@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/authorize")
def authorize():
    auth_url = f'{API_BASE}/authorize?client_id={CLI_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}&show_dialog=True'
    print(auth_url)
    return redirect(auth_url)

@app.route("/api_callback")
def api_callback():
    session.clear()
    code = request.args.get('code')

    auth_token_url = f"{API_BASE}/api/token"
    res = requests.post(auth_token_url, data={
        "grant_type":"authorization_code",
        "code":code,
        "redirect_uri":"http://127.0.0.1:5000/api_callback",
        "client_id":CLI_ID,
        "client_secret":CLI_SEC
        })

    res_body = res.json()
    print(res.json())
    session["toke"] = res_body.get("access_token")

    return redirect(url_for("location", error='f'))

@app.route("/location/<error>")
def location(error):
    print(error)
    return render_template("location.html", error=error)

@app.route("/processing")
def processing():
    zipcode = request.args.get('zipcode', '')
    if len(zipcode) != 5 or not zipcode.isnumeric() or not zipcodes.is_real(zipcode):
        return redirect(url_for('location', error='t'))
    else:
        session["latlong"] = (zipcodes.matching(zipcode)[0]['lat'], zipcodes.matching(zipcode)[0]['long'])
        add_data()
        return redirect(url_for('home'))
        
@app.route("/home")
@app.route("/home/<user>/<match>/<close>/<email>/<miles>/<common>")
def home(user=None, match=None, close=None, email=None, miles=None, common=None):
    if common:
        common = common.split(',')
        print("KEAFJLKADSJFLKDJFKLDSJF", type(common))
    return render_template('matchings.html', user=user, match=match, close=close, email=email, miles=miles, common=common)

@app.route("/newmatches")
def newmatches():
    # COSINE SIM CALCULATES MATCH
    sp = spotipy.Spotify(auth=session['toke'])
    self_email = sp.me()['email']
    self_email = self_email.replace("@", "_at_")
    rows = datab.return_values()

    min = float('inf') ## lowest cosine similarity score possible, used as default
    maxEmail = "" # holds the email corresponding to the person who is the most similar to the current user

    currentUserInfo = [] # stores current user info
    otherUserInfo = [] # stores the other user's info we're looking at

    for user in rows:
        if user[0] == self_email:
            for i in range(2, 16):
                currentUserInfo.append(user[i])
            break
    
    for user in rows:
        if user[0] != self_email:
            otherUserInfo = []

            for i in range(2, 16):
                otherUserInfo.append(user[i]);

            #similarityScore = cosineSimilarity(currentUserInfo, otherUserInfo)
            diff = []
            for i in range(0, 14):
                diff.append(abs(currentUserInfo[i]-otherUserInfo[i])/((currentUserInfo[i]+otherUserInfo[i])/2))
            similarityScore = sum(diff)/14

            if similarityScore < min:
                min = similarityScore
                maxEmail = user[0]
    

    # maxEmail should hold the email 
    print(maxEmail)
    
    maxEmail2 = maxEmail.replace("_at_", "@")

    self_loc = (datab.return_value_for_email(self_email, 2), datab.return_value_for_email(self_email, 3))
    match_loc = (datab.return_value_for_email(maxEmail, 2), datab.return_value_for_email(maxEmail, 3))

    distance_mi = round(distance.distance(self_loc, match_loc).miles, 2)
    
    self_toke = session["toke"]
    other_toke = datab.return_value_for_email(maxEmail, 16)

    sp_self = spotipy.Spotify(auth=self_toke)
    sp_other = spotipy.Spotify(auth=other_toke)

    self_top = sp_self.current_user_top_artists(limit=50, time_range="medium_term")
    other_top = sp_other.current_user_top_artists(limit=50, time_range="medium_term")

    our_top_artists = []
    their_top_artists = []
    for d in self_top["items"]:
        our_top_artists.append(d["name"])
    
    for d in other_top["items"]:
        their_top_artists.append(d["name"])

    in_common = list(set(their_top_artists) & set(our_top_artists))
    print(in_common)
    return redirect(url_for('home', user=sp.me()['display_name'], match=datab.return_value_for_email(maxEmail, 1), close=round((1-min)*100, 2), email=maxEmail2, miles=distance_mi, common=in_common))

# calculates the similarity score between current user and other user based on the 2 lists provided
# def cosineSimilarity(currentUserInfo, otherUserInfo):

#     scaledCurrInfo, scaledOtherInfo = [], []
#     for i in range(len(currentUserInfo)):
#         avg_score = (currentUserInfo[i] + otherUserInfo[i]) / 2
#         scaledCurrVal = abs(currentUserInfo[i] - avg_score)/avg_score
#         scaledOtherVal = abs(otherUserInfo[i] - avg_score)/avg_score
#         scaledCurrInfo.append(scaledCurrVal)
#         scaledOtherInfo.append(scaledOtherVal)


#     return dot(scaledCurrInfo, scaledOtherInfo) / (norm(scaledCurrInfo) * norm(scaledOtherInfo))

@app.route("/secretroute")
def secretroute():
    return datab.return_values()


def add_data():
    sp = spotipy.Spotify(auth=session['toke'])
    response = sp.current_user_top_tracks(limit=50, time_range='medium_term')
    id_list = []
    # print(type(response['items']))
    for d in response['items']:
        id_list.append(d['id'])
        print(d['id'])
    features = sp.audio_features(tracks=id_list)
    avg_feats = {"acousticness": 0, "danceability": 0, "duration_ms": 0, "energy": 0, "instrumentalness": 0, "key": 0, "liveness": 0, "loudness": 0, "mode": 0, "speechiness": 0, "tempo": 0, "time_signature": 0, "valence": 0}
    for song in features:
        avg_feats["acousticness"] = avg_feats["acousticness"] + song["acousticness"]
        avg_feats["danceability"] = avg_feats["danceability"] + song["danceability"]
        avg_feats["duration_ms"] = avg_feats["duration_ms"] + song["duration_ms"]
        avg_feats["energy"] = avg_feats["energy"] + song["energy"]
        avg_feats["instrumentalness"] = avg_feats["instrumentalness"] + song["instrumentalness"]
        avg_feats["key"] = avg_feats["key"] + song["key"]
        avg_feats["loudness"] = avg_feats["loudness"] + song["loudness"]
        avg_feats["mode"] = avg_feats["mode"] + song["mode"]
        avg_feats["speechiness"] = avg_feats["speechiness"] + song["speechiness"]
        avg_feats["tempo"] = avg_feats["tempo"] + song["tempo"]
        avg_feats["time_signature"] = avg_feats["time_signature"] + song["time_signature"]
        avg_feats["valence"] = avg_feats["valence"] + song["valence"]

    for k in avg_feats:
        avg_feats[k] = avg_feats[k] / 50

    print(avg_feats)
    print(sp.me()['email'])
    datab.add_user(sp.me()['email'], sp.me()['display_name'], session['latlong'][0], session['latlong'][1], avg_feats, session['toke'])
    datab.show_values()
