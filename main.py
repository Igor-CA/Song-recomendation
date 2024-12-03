from pymongo import MongoClient
import streamlit as st
import time
import os
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
page = st.sidebar.radio("Select Page", ["Search Music", "Your Playlist"])

search_results_placeholder = st.empty()

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
