
import pandas as pd
from typing import List
from src.hypernodes import HyperNode
from hamilton.function_modifiers import extract_columns

@extract_columns("questions", "answers")
def user_queries(queries_path: str) -> pd.DataFrame:
    return pd.read_excel(queries_path)

def llm_responses(questions: pd.Series, texts_path: str, rag_qa_node: HyperNode) -> List[str]:
    responses = []
    inputs = rag_qa_node._instantiated_inputs
    for question in questions:
        inputs.update({"query" : question, "texts_path" : texts_path})
        res = rag_qa_node.execute(final_vars=["llm_response"], inputs=inputs)
        responses.append(res["llm_response"])
    return responses

def accuracy(llm_responses: List[str], answers: pd.Series) -> float:
    correct = pd.Series(llm_responses).str.lower() == answers.astype(str).str.lower()
    return sum(correct) / len(correct)
