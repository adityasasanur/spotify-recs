from flask import Flask, render_template, request, redirect, send_from_directory, jsonify
import pandas as pd
from user_preference_rank import UserPreferenceEngine   

app = Flask(__name__)
perference_engine = UserPreferenceEngine('data/artistinfo.csv')

@app.route('/')
def index():
    return render_template('artist_network.html')

@app.route('/output.csv')
def get_csv():
    return send_from_directory('./data', 'output_filtered.csv')

user_inputs = []
@app.route('/process-text', methods=['POST'])
def filter_artists():
    data = request.json
    user_input = data['userInput']
    # Save the user input to your desired storage. Here it's just a list.
    user_inputs.append(user_input)
    # For demo purposes, print to console   
    
    preferences = perference_engine.get_ranked_artists(user_input)
    keep_top_k_artists(preferences, 10)
    
    # Respond with a success message
    return jsonify({"status": "success", "message": "Text saved."})

def keep_top_k_artists(preferences, k):
    # keep top k artists in artist_network_df
    top_k_artists = preferences[:k]
    top_k_artists = top_k_artists[0]
    artist_network_df = pd.read_csv('data/output.csv')
    artist_network_df = artist_network_df[artist_network_df['x'].isin(top_k_artists) | artist_network_df['y'].isin(top_k_artists)]
    artist_network_df.to_csv('data/output_filtered.csv', index=False)
    


if __name__ == '__main__':
    app.run(debug=True)