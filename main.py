from scipy.spatial.distance import cdist
from pymongo import MongoClient
import streamlit as st
import time
import os
import numpy as np
import pickle
import pandas as pd

# MongoDB connection
client = MongoClient(os.getenv("DATABASE_URL"))
db = client['songs']
songs_collection = db['songs']

# Initialize session state
if "popup_message" not in st.session_state:
    st.session_state["popup_message"] = None
if "playlist" not in st.session_state:
    st.session_state["playlist"] = []
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""

# Helper function for showing popup message

def show_popup_message(message):
    st.session_state["popup_message"] = message
    st.experimental_rerun()  # Trigger rerun to refresh UI

# Function to add song to playlist


def add_to_playlist(song):
    st.session_state["playlist"].append(song)
    show_popup_message(f"Added '{song['name']}' to playlist!")


# Display popup message if available
if st.session_state["popup_message"]:
    st.info(st.session_state["popup_message"])
    time.sleep(1)
    st.session_state["popup_message"] = None
    st.experimental_rerun()

# Page selector
page = st.sidebar.radio(
    "Select Page", ["Search Music", "Your Playlist", "Recommendations"])

# Search Music Page
if page == "Search Music":
    st.title("Music Recommender")
    search_query = st.text_input(
        "Search for a song or artist:", value=st.session_state["search_query"])

    if search_query:
        st.session_state["search_query"] = search_query  # Persist search query

        pipeline = [
            {
                "$search": {
                    "index": "song",
                    "compound": {
                        "should": [
                            {"text": {"query": search_query, "path": "name",
                                      "fuzzy": {"maxEdits": 2, "prefixLength": 2}}},
                            {"text": {"query": search_query, "path": "artists",
                                      "fuzzy": {"maxEdits": 2, "prefixLength": 2}}}
                        ]
                    },
                }
            },
            {"$limit": 10}
        ]
        try:
            results = songs_collection.aggregate(pipeline)
            st.subheader("Search Results")

            for song in results:
                col1, col2 = st.columns([4, 1])  # Adjust proportions as needed
                with col1:
                    st.write(
                        f"**{song['name']}** by {', '.join(song['artists'])}")
                with col2:
                    if st.button("Add to Playlist", key=song['_id']):
                        add_to_playlist(song)
        except Exception as e:
            st.error(f"Error: {e}")

# Your Playlist Page
elif page == "Your Playlist":
    st.title("Your Playlist")
    if not st.session_state["playlist"]:
        st.write("Your playlist is empty. Start adding some songs!")
    else:
        for song in st.session_state["playlist"]:
            st.write(f"**{song['name']}** by {', '.join(song['artists'])}")

# Recommendations Page
elif page == "Recommendations":
    st.title("Recommended Songs")
    if not st.session_state["playlist"]:
        st.write("Add songs to your playlist to get recommendations!")
    else:
        # Load PCA model
        with open("pca_model.pkl", "rb") as file:
            pca = pickle.load(file)

        # Extract features for the playlist
        playlist_ids = [song['id'] for song in st.session_state["playlist"]]
        playlist_data = list(songs_collection.find(
            {"id": {"$in": playlist_ids}},
            {
                "acousticness": 1, "danceability": 1, "energy": 1, "instrumentalness": 1,
                "popularity": 1, "year": 1,
                "speechiness": 1, "valence": 1, "tempo": 1, "mode": 1, "key": 1, "loudness": 1, "_id": 0
            }
        ))
        if playlist_data:
            playlist_features = np.array([
                [song["acousticness"], song["danceability"], song["energy"], song["instrumentalness"],
                 song["speechiness"], song["valence"],]
                for song in playlist_data
            ])

            # Calculate PCA position for the playlist
            playlist_pca_positions = pca.transform(playlist_features)
            playlist_position = playlist_pca_positions.mean(axis=0)

            # Fetch all songs' features
            all_songs_data = list(songs_collection.find(
                {},
                {
                    "id": 1, "name": 1, "artists": 1,
                    "popularity": 1, "year": 1,
                    "acousticness": 1, "danceability": 1, "energy": 1, "instrumentalness": 1,
                    "speechiness": 1, "valence": 1,  "_id": 0
                }
            ))
            all_songs_features = np.array([
                [song["acousticness"], song["danceability"], song["energy"], song["instrumentalness"],
                 song["speechiness"], song["valence"],]
                for song in all_songs_data
            ])

            # Calculate distances
            all_songs_pca_positions = pca.transform(all_songs_features)
            distances = cdist([playlist_position],
                              all_songs_pca_positions, metric="euclidean")
            # Get 5 nearest neighbors
            nearest_indices = distances.argsort()[0][:100]

            # Display recommendations
            nearest_songs = [all_songs_data[i] for i in nearest_indices]
            nearest_songs_sorted = sorted(nearest_songs, key=lambda x: x["popularity"], reverse=True)

            # Select the top 10 most popular songs
            recommended_songs = nearest_songs_sorted[:10]

            for song in recommended_songs:
                print(song)
                print(playlist_features[0])
                col1, col2 = st.columns([4, 1])  # Adjust proportions as needed
                with col1:
                    st.write(
                        f"**{song['name']}** by {', '.join(song['artists'])}")
                with col2:
                    if st.button("Add to Playlist", key=f"rec_{song['id']}"):
                        add_to_playlist(song)
        else:
            st.write("Could not retrieve playlist features.")
