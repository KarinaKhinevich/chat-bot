from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from chat_bot.config import OpenAISettings


openai_settings = OpenAISettings()


# Initialize OpenAI client
llm = ChatOpenAI( 
    api_key=openai_settings.API_KEY,
    model=openai_settings.MODEL_NAME,
    temperature=openai_settings.TEMPERATURE)

# System prompt for summarization
SUMMARIZATION_PROMPT = PromptTemplate.from_template(
    "You will receive a document as input. " 
    "Your task is to create a summary that is 2-3 times shorter than the original text, while keeping all the key points and the overall meaning."

    "The summary must be written in the same language as the original document."
    "Do not add any new information that is not in the document."
    "You may rephrase and condense sentences, but make sure all important details remain."
    "The style should be concise and clear, preserving the document's intent."

    "Return only the summary, nothing else. "
    "Document content: {document_content}"
)

# Summarization chain
summarizer_chain = SUMMARIZATION_PROMPT | llm

async def summarize_document(content: str) -> str:
    """
    Summarize the given document content using OpenAI.
    
    Args:
        content (str): The content of the document to summarize.

    Returns:
        str: The generated summary.
    """
    summary = await summarizer_chain.ainvoke({"document_content": content})

    # Extract and return the summary text
    return summary.content
        