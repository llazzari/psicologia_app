import streamlit as st
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

from data.models.document_models import (
    CONTENT_MODEL_MAP,
    Document,
    DocumentContent,
    ProntuaryContent,
)

MISTRAL_API_KEY = st.secrets.api_keys.mistral_api_key
SYSTEM_PROMPT: str = """
    You are a neuropsychologist, expert in Applied Behavior Analysis and you work with Cognitive Behavioral Therapy. 
    You will be asked to write psychological documents for a patient, based on their psychological profile and the patient's needs from the psychologist observations.
    Do not make assumptions. 
    Rewrite the document in a better way than the one provided, be more techinical and fill the gaps.
    No need to write a summary. 
    The documents will be written in Brazilian Portuguese.
    Take into account the document category that you are being requested to generate.
    As a header, you may write the document category, the patient's name and the date of the document. In the end of the document, do not include the therapist signature, name or CRP.
    Do not attend to any other topics.
"""

provider = MistralProvider(api_key=MISTRAL_API_KEY)

model = MistralModel(provider=provider, model_name="mistral-small-latest")

agent = Agent(
    model,
    system_prompt=SYSTEM_PROMPT,
    output_type=type[DocumentContent],
    deps_type=Document,
)


@agent.system_prompt
def get_document_category(ctx: RunContext[Document]) -> str:
    """Returns the document category."""
    doc_category = ctx.deps.category
    return f"The document category is {doc_category}"


def generate_content(document: Document, user_input: str) -> DocumentContent:
    content_model: type[DocumentContent] = CONTENT_MODEL_MAP.get(
        document.category, ProntuaryContent
    )
    result = agent.run_sync(
        user_input,
        deps=document,
        output_type=content_model,  # specify the output type for the agent at call time
    )
    return result.output
