import numpy as np
import pandas as pd
import spotipy
import spotipy.oauth2 as oauth2
import yaml
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

data = pd.read_csv("dataset.csv")
data = data.drop("Unnamed: 0", axis=1)

print(data.columns)
columns_to_be_dropped = [
    "type",
    "id",
    "uri",
    "track_href",
    "analysis_url",
    "Artist",
    "Name",
    "Popularity",
    "duration_ms",
]
for i in columns_to_be_dropped:
    if i in data.columns:
        data = data.drop(i, axis=1)
print(data.columns)

# data = data[(data['Tag'] != 'Travel') & (data['Tag'] != 'Meetings')]
print(data["Tag"].unique())

Y = data["Tag"]
X = data.drop("Tag", axis=1)

X_train, X_test, y_train, y_test = train_test_split(
    X, Y, test_size=0.25, random_state=2
)
model = XGBClassifier()


def test_accuracy(model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print("Accuracy: %.2f%%" % (accuracy * 100.0))


def train_accuracy(model, X_train, y_train):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_train)
    accuracy = accuracy_score(y_train, y_pred)
    print("Accuracy: %.2f%%" % (accuracy * 100.0))


def songpred(model, X, Y):
    model.fit(X, Y)
    song_url = input()

    # Opening credential file
    with open("creds.yaml") as file:
        creds = yaml.full_load(file)

    cli_id = creds["spotify client id"]
    cli_sec = creds["spotify client secret"]

    # Creating spotify auth object to authenticate spotify object
    auth = oauth2.SpotifyClientCredentials(client_id=cli_id, client_secret=cli_sec)
    # Get access token from spotify
    token = auth.get_access_token(as_dict=False)
    # Create spotify object
    spotify = spotipy.Spotify(auth=token)
    song_x = pd.DataFrame(spotify.audio_features([song_url]))
    keys = list(song_x.keys())
    for i in keys:
        if i in columns_to_be_dropped:
            del song_x[i]
    y_pred = model.predict(song_x)
    print(y_pred)


# test_accuracy(model, X_train, X_test, y_train, y_test)
# train_accuracy(model, X_train, y_train)
songpred(model, X, Y)
