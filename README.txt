DESCRIPTION:

This package aims to gather artist data through Spotify's API and visualize the data as an artist network.
The user must first pass in a Spotify Artist ID as well as the depth of the network that they want to create.
Through the Spotify API, we are then able to take the artist ID and find artists that are related to them.
Then, with the specified network depth, we perform a breadth first expansion on the artists and find all connections up to the specified depth.
We then take all the artists and connections between artists and turn it into a graph structure with nodes and edges.
Using Alchemy.JS (a layer on top of d3.js) we are able to visualize the artists and connections in an interactive format.
Users are able to drag nodes around and see the depth of their network. The network depths are color coded in the following way:
Yellow: Original Artist
Orange: Depth 1
Pink: Depth 2
Purple: Depth 3
Blue: Depth 4
White: Depth 5

Here is how the natural language graph filtering works:
The graph/network was built and loaded
For each node (artist) in the network, we pulled its biography from Wikipedia using Wikipedia API and stored the biography locally.
We converted the lengthy biography into key phrases by prompting GPT-4
For each artist, we converted the key phrases into vector representation using SentenceBERT and stored the vectors locally.
Upon receiving a user’s input about their preference over artists
We first converted the potentially complex and long input into key phrases by prompting GPT4.
We converted the key phrases into vector using the same SentenceBERT.
We computed the dot product between the user input key phrases and those of each artist.
We ranked and kept the top-k artist based on the dot products.
The graph was updated accordingly.
User can choose to reset the graph.


INSTALLATION:
To run the program, you will need to install the following packages through pip
- requests
- os
- openai
- base64
- json
- csv
- pandas
- flask
- sentence_transformers

EXECUTION:
To execute the code, navigate into the CODE directory and run the following command:
python launch_graph.py <id> <depth>
id is the Spotify Artist ID that you want to create a network around and depth is the depth of the network you want to create.
This code take a while to run and launch so please be patient (especially if you choose larger depths)
Once it is finished running, you can access the network at http://127.0.0.1:8000
To filter the network graph, you can enter any kind of filtering sentence like the following and hit the enter key on your keyboard:
"I like pop artists"
"I like artists who have black hair"
This filtering can also take some time so please be patient
If you would like to reset the graph to before the filtering, press the rest graph button.