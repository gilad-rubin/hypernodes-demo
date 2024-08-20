
from typing import List, Callable, Any, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def fitted_vectorizer(vectorizer: TfidfVectorizer, text_chunks: List[str]) -> TfidfVectorizer:
    return vectorizer.fit(text_chunks)

def vectorized_texts(fitted_vectorizer: TfidfVectorizer, text_chunks: List[str]) -> Any:
    return fitted_vectorizer.transform(text_chunks)

def vectorized_query(fitted_vectorizer: TfidfVectorizer, query: str) -> Any:
    return fitted_vectorizer.transform([query])

def similarities(vectorized_query: Any, vectorized_texts: Any) -> Any:
    cosine_similarities = cosine_similarity(vectorized_query, vectorized_texts)
    return cosine_similarities

def top_k_chunks(text_chunks: List[str], similarities: Any, top_k: int) -> List[str]:
    sorted_indices = np.argsort(similarities[0])[::-1]
    top_k_indices = sorted_indices[:top_k]
    return [text_chunks[i] for i in top_k_indices] 
