import requests
import base64
import json
import sys
import webbrowser
from collections import deque

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

def main():
    if len(sys.argv) != 3:
        print("Usage: python launch_graph.py <id> <depth>")
        return
    id = sys.argv[1]
    depth = int(sys.argv[2])
    print(f'Loading Artist Network for {id} at depth {depth}....   (This might take a while)')

    ret = createArtistsNetwork(id, depth)
    with open("data/artist_network.json", "w") as f:
        json.dump(ret, f, indent=4)
    print("done!")

    webbrowser.open('http://localhost:8000/page.html')


if __name__ == "__main__":
    main()
