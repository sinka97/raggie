from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from typing_extensions import TypedDict


# Data model
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

class GradeQuestion(BaseModel):
    """Binary score for whether user is asking question."""

    binary_score: str = Field(
        description="User is asking a question, 'yes' or 'no'"
    )

class QuestionType(BaseModel):
    """Binary score for whether user is asking question."""

    questionType: str = Field(
        description="User is asking a question related to either 'TRXX1 Monthly Reports', 'IT001 Assets Lists', 'IM8', or 'Others'"
    )


### Graph State and Nodes ###
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        web_search: whether to add search
        documents: list of documents
    """

    question: str
    generation: str
    web_search: str
    documents: List[str]
    isQuestion: str