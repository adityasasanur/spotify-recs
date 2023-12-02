import openai
import pandas as pd
from sentence_transformers import SentenceTransformer, util

class UserPreferenceEngine():
    def __init__(self, artist_bio):
        openai.api_key = "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"
        self.sentence_encoder = SentenceTransformer('multi-qa-mpnet-base-dot-v1')
        self.artist_bio = pd.read_csv(artist_bio).set_index('artist').to_dict()['highlights']
        
        self.artist_highlights_embedding = dict()
        for artist in self.artist_bio:
            try:
                self.artist_highlights_embedding[artist] = self.sentence_encoder.encode(self.artist_bio[artist])
            except:
                self.artist_highlights_embedding[artist] = self.sentence_encoder.encode(" ")
        
    def get_ranked_artists(self, user_input):
        """
        Get the ranked artists based on the user input.
        """
        system_prompt = "I will provide you with a user's textual input on their preference for musicians. You need to extract key phrases as highlights of the user's preference. Separate the key phrases by semicolons."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        user_input_phrases = response["choices"][0]["message"]["content"]
        artist_similarity = dict()
        for artist in self.artist_bio:
            artist_similarity[artist] = self.similarity(user_input_phrases, artist).item()
        return sorted(artist_similarity.items(), key=lambda x: x[1], reverse=True)
    
    
    def similarity(self, user_input, artist):
        user_input_embedding = self.sentence_encoder.encode(user_input)
        return util.dot_score(user_input_embedding, self.artist_highlights_embedding[artist])
    
    
# Example usage
if __name__ == "__main__":
    engine = UserPreferenceEngine('artistinfo.csv')
    print(engine.get_ranked_artists('I like American Rock players who have won Grammy Awards'))