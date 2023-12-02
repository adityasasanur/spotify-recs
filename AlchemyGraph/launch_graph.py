import os
import requests
import openai
from openai import OpenAI
import base64
import json
import csv
import sys
import webbrowser
from collections import deque
from threading import Timer
import pandas as pd
from flask import Flask, render_template, request, redirect, send_from_directory, jsonify


from user_preference_rank import UserPreferenceEngine

def getToken():
    tokenUrl = 'https://accounts.spotify.com/api/token'
    cid = "84ffbde9b5764c61b02a9cfd5f686a0f"
    secret = "cd3e066799c547f391387ed5e42eca20"

    credentials = f"{cid}:{secret}"
    base64Credentials = base64.b64encode(credentials.encode()).decode()
    config = {
        "headers": {
            "Authorization": f"Basic {base64Credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    }
    data = "grant_type=client_credentials"
    response = requests.post(tokenUrl, data=data, headers=config["headers"])
    return response.json()["access_token"]

def createArtistsNetwork(id, depth):
    apiUrl = 'https://api.spotify.com/v1'

    token = getToken()
    config = {
        "headers": {
            "Authorization": f"Bearer {token}",
        },
    }
    nodes = []
    nodes_set = set()
    edges = []

    initialArtistResponse = requests.get(f"{apiUrl}/artists/{id}", headers=config["headers"])
    prevArtist = initialArtistResponse.json()
    artistQueueResponse = requests.get(f"{apiUrl}/artists/{id}/related-artists", headers=config["headers"])
    artist_data = artistQueueResponse.json()["artists"]
    artist_queue = deque([[prevArtist["id"], artist, 1] for artist in artist_data])

    nodes_set.add(prevArtist["id"])
    nodes.append({
        "id": prevArtist["id"],
        "name": prevArtist["name"],
        "depth": 0
    })

    # for d in range(1, depth+1):
    #     newQueue = []
    while artist_queue:
        prevArtistId, currArtist, d = artist_queue.pop()
        source_target = sorted([prevArtistId, currArtist["id"]])
        new_edge = {
            "source": source_target[0],
            "target": source_target[1]
        }
        new_node = {
            "id": currArtist["id"],
            "name": currArtist["name"],
            "depth": d
        }

        edges.append(new_edge)
        if currArtist["id"] not in nodes_set:
            nodes.append(new_node)
            nodes_set.add(currArtist["id"])
            if d == depth: continue
            connectedArtistsResponse = requests.get(f"{apiUrl}/artists/{new_node['id']}/related-artists", headers=config["headers"])
            connectedArtistsData = connectedArtistsResponse.json()["artists"]

            artist_queue.extendleft([[new_node["id"], artist, d+1] for artist in connectedArtistsData])

    return {
        "nodes": nodes,
        "edges": edges
    }
    

def get_wikipedia_intro(artist_name):
    """
    Get the introduction section of a Wikipedia page for an artist.
    """

    WIKI_API_URL = 'https://en.wikipedia.org/w/api.php'

    params = {
        'action': 'query',
        'format': 'json',
        'titles': artist_name,
        'prop': 'extracts',
        'exintro': True,
        'explaintext': True,
        'redirects': True,
    }

    response = requests.get(WIKI_API_URL, params=params)
    data = response.json()
    pages = data['query']['pages']
    intro = next(iter(pages.values()))
    if 'extract' in intro:
        return intro['extract']
    else:
        return "No biography found for this artist on Wikipedia."
    
def collect_artist_bio(artist_network):
    nodes = artist_network['nodes']
    # openai.api_key = "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"
    client = OpenAI(api_key="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")
    system_prompt = """
    I will provide you with bio/info of a musician and I need you to extract the highlights from the bio. My goal is to compare the extracted highlights with the user's input about their preference over musicians so that I can rank the musicians by the similarity between the extracted highlights and users' inputs.
    Please separate the highlights by semicolons. Output at most 5 highlights. Keep each hight short. Prioritize highlights that users care about the most. Focus on high-level information about the musician. Avoid using full sentences."""
    
    # read csv file to pd
    artist_info = pd.read_csv('data/artistinfo.csv')
        
    
    with open('data/artistinfo_1.csv', 'a', newline='') as csvfile:
        fieldnames = ['artist', 'intro', 'highlights']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for node in nodes:
            artist = node['name']
            if artist in artist_info['artist'].values:
                continue
            else:
                bio = get_wikipedia_intro(artist)   
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": bio}
                    ]
                )
                writer.writerow({'artist': artist, 'intro': get_wikipedia_intro(artist), 'highlights': response.choices[0].message.content})
            
            
        
    
app = Flask(__name__)
perference_engine = UserPreferenceEngine('data/artistinfo.csv')

@app.route('/')
def index():
    return render_template('page.html')

# @app.route('/.csv')
# def get_csv():
#     return send_from_directory('./data', 'output_filtered.csv')


@app.route('/data/artist_network.json')
def artist_network():
    try:
        return send_from_directory('data', 'artist_network.json')
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    
@app.route('/data/artist_network_filtered.json')
def artist_network_filtered():
    try:
        return send_from_directory('data', 'artist_network_filtered.json')
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


user_inputs = []
@app.route('/endpoint', methods=['POST'])
def filter_artists():
    # For demo purposes, print to console   
    user_input = request.json.get('text')
    print(user_input)
    
    preferences = perference_engine.get_ranked_artists(user_input)
    keep_top_k_artists(preferences, 10)
    
    # Respond with a success message
    return jsonify({"status": "success", "message": "Text saved."})

def keep_top_k_artists(preferences, k):
    # keep top k artists in artist_network_df
    top_k_artists = preferences[:k]
    top_k_artists = [artist[0] for artist in top_k_artists]
    artist_network_dict = json.load(open('data/artist_network.json'))
    nodes = artist_network_dict['nodes']
    id_to_name = dict()
    for node in nodes:
        id_to_name[node['id']] = node['name']
    id_to_depth = dict()
    for node in nodes:
        id_to_depth[node['id']] = node['depth']
    
    nodes_filtered = []
    artist_ids_filtered = []
    for node in nodes:
        if node['name'] in top_k_artists:
            nodes_filtered.append(node)
            artist_ids_filtered.append(node['id'])
    edges_filtered = []
    for edge in artist_network_dict['edges']:
        if edge['source'] in artist_ids_filtered or edge['target'] in artist_ids_filtered:
            edges_filtered.append(edge)
            if edge['source'] not in artist_ids_filtered:
                nodes_filtered.append({'id': edge['source'], 'name': id_to_name[edge['source']], 'depth': id_to_depth[edge['source']]})
            if edge['target'] not in artist_ids_filtered:
                nodes_filtered.append({'id': edge['target'], 'name': id_to_name[edge['target']], 'depth': id_to_depth[edge['target']]})
                
    
    
    json.dump({'nodes': nodes_filtered, 'edges': edges_filtered}, open('data/artist_network_filtered.json', 'w'))


def main():
    if len(sys.argv) != 3:
        print("Usage: python launch_graph.py <id> <depth>")
        return
    id = sys.argv[1]
    depth = int(sys.argv[2])
    print(f'Loading Artist Network for {id} at depth {depth}....   (This might take a while)')

    # check if data/artist_network.json exists
    ret = createArtistsNetwork(id, depth)
    with open("data/artist_network.json", "w") as f:
        json.dump(ret, f, indent=4)
    
    if not os.path.exists('data/artistinfo.csv'):
        collect_artist_bio(ret)
        
    print("done!")
    # Timer(10, webbrowser.open('http://localhost:8000/')).start()
    app.run(debug=True, port=8000)

if __name__ == "__main__":
    main()
