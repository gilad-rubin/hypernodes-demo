
from src.hypernodes import HyperNode
from litellm import completion
import litellm
from typing import List
import os

litellm.enable_cache()

def texts(texts_path: str) -> List[str]:
    text_files = [f for f in os.listdir(texts_path) if f.endswith('.txt')]
    text_chunks = []
    for file in text_files:
        with open(os.path.join(texts_path, file), 'r') as f:
            text_chunks.append(f.read())
    return text_chunks

def text_chunks(texts: List[str], chunker: str) -> List[str]:
    if chunker == "paragraph":
        return [chunk for text in texts for chunk in text.split("\n\n")]
    return texts

def top_k_chunks(ranker: HyperNode, text_chunks: List[str], query: str) -> List[str]:
    inputs = ranker._instantiated_inputs
    inputs.update({"text_chunks" : text_chunks, "query" : query})
    res = ranker.execute(final_vars=["top_k_chunks"], inputs=inputs)
    return res["top_k_chunks"]

def query_with_context(top_k_chunks: List[str], query: str) -> str:
    return (
        "Here's the user query: \n"
        + query
        + "\n and here are the top k chunks: \n"
        + ", ".join(top_k_chunks)
    )

def llm(llm_model: str) -> str:
    return llm_model

def llm_response(query_with_context: str, llm: str, llm_config: dict, system_prompt: str) -> str:
    messages=[{"role": "system", "content": system_prompt},
              {"role": "user", "content": query_with_context}]
    return completion(model=llm,
                      messages=messages,
                      **llm_config).choices[0].message.content
