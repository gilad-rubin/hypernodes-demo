
from src.hypernodes import HyperNode
from litellm import completion
import litellm
from typing import List
import os

litellm.enable_cache()

import os
from typing import List
import streamlit as st

def texts(texts_path: str) -> List[str]:
    text_files = [f for f in os.listdir(texts_path) if f.endswith('.txt')]
    texts = []
    for file in text_files:
        full_path = os.path.join(texts_path, file)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = []
                for line in f:
                    try:
                        lines.append(line)
                    except UnicodeDecodeError:
                        st.warning(f"Skipped a line in file {file} due to encoding issues.")
                texts.append(''.join(lines))
        except Exception as e:
            st.error(f"Error reading file {file}: {str(e)}")
    return texts

def text_chunks(texts: List[str], chunker: str) -> List[str]:
    if chunker == "paragraph":
        return [chunk for text in texts for chunk in text.split("\n\n")]
    return texts

def top_k_chunks(ranker: HyperNode, text_chunks: List[str], query: str) -> List[str]:
    inputs = ranker._instantiated_inputs
    inputs.update({"text_chunks" : text_chunks, "query" : query})
    res = ranker.execute(final_vars=["top_k_chunks"], inputs=inputs)
    return res["top_k_chunks"]

def query_with_context(query: str, top_k_chunks: List[str]) -> str:
    return (
        "Here's the user query: \n"
        + query
        + "\n and here are the top k chunks: \n"
        + ", ".join(top_k_chunks)
    )

def llm_response(query_with_context: str, llm_model: str, llm_config: dict, system_prompt: str) -> str:
    messages=[{"role": "system", "content": system_prompt},
              {"role": "user", "content": query_with_context}]
    return completion(model=llm_model,
                      messages=messages,
                      **llm_config).choices[0].message.content
