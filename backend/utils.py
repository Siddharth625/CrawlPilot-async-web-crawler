import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
import spacy
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
nltk.download("punkt")
nltk.download("stopwords")

nlp = spacy.load("en_core_web_md")

def clean_links(base_url, url_list):
    cleaned_urls = []
    for url in url_list:
        if url is not None:
            if not url.startswith("https://"):
                cleaned_urls.append(base_url + url)
            else:
                cleaned_urls.append(url)
    return cleaned_urls

def preprocess_text(text):
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    # Tokenize each sentence into words and filter out stop words
    stop_words = set(stopwords.words("english"))
    words = [word_tokenize(sentence.lower()) for sentence in sentences]
    words = [[word for word in sentence if word.isalnum() and word not in stop_words] for sentence in words]
    return sentences, words

def preprocess_text_cosine_matrix(text):
    doc = nlp(text)
    # Extract vector embeddings for each token
    vectors = [token.vector for token in doc]
    return vectors

def summarize_text(sentences, words, compression_percentage):
    # Convert the sentences into a single string for TF-IDF vectorization
    text = [" ".join(sentence) for sentence in words]
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    # Vectorize the text
    tfidf_matrix = vectorizer.fit_transform(text)
    # Calculate cosine similarity matrix
    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
    # Sort sentences based on their similarity scores
    ranked_sentences = sorted(((similarity_matrix[i, j], j) \
                               for i in range(similarity_matrix.shape[0]) \
                                for j in range(similarity_matrix.shape[1])), reverse=True)
    # Select top sentences as summary
    summary_sentences = [sentences[idx] for _, idx in ranked_sentences[:int(len(sentences)*(compression_percentage/100))]]
    return " ".join(summary_sentences)

def calculate_cosine_distance_matrix(vectorized_embeddings: dict) -> np.array:
    # Preprocess text and create vector embeddings for each URL
    number_of_urls = len(vectorized_embeddings)
    embeddings = list(vectorized_embeddings.values())
    # Initialize an empty cosine distance matrix
    distance_matrix = np.zeros((number_of_urls, number_of_urls))
    # Calculate cosine similarity between each pair of URLs
    for i in range(number_of_urls):
        for j in range(i+1, number_of_urls):
            cosine_sim = cosine_similarity(embeddings[i], embeddings[j])[0][0]
            # Cosine distance is 1 - cosine similarity
            distance_matrix[i][j] = 1 - cosine_sim
            distance_matrix[j][i] = distance_matrix[i][j]
    matrix_dict = {
            "matrix": distance_matrix.tolist(),
            "shape": distance_matrix.shape
        }
    json_output = json.dumps(matrix_dict)
    return (json_output)