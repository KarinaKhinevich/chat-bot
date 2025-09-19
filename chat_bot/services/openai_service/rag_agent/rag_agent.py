import logging

from langchain_core.tracers.context import tracing_v2_enabled
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from chat_bot.config import LangchainSettings
from chat_bot.core.constants import RETRIEVAL_TOP_K
from .nodes import Moderation, RelevanceChecker, AnswerGenerator
from .state import State
from .tools import retrieve_documents

logger = logging.getLogger(__name__)

langchain_settings = LangchainSettings()

class RAGAgent:
    """
    Represents a stateful graph for handling conversational AI flows with RAG.

    This class implements a complete RAG pipeline with:
    1. Content moderation
    2. Document retrieval 
    3. Relevance checking
    4. Answer generation

    The graph ensures that only relevant documents are used to generate answers,
    and provides appropriate responses when documents don't contain relevant information.
    """

    def __init__(self, streaming_mode: bool = False):
        """
        Initializes the RAG graph with all necessary nodes.

        Args:
            streaming_mode: If True, enables streaming responses.
        """
        self.__moderation = Moderation()
        self.__relevance_checker = RelevanceChecker()
        self.__answer_generator = AnswerGenerator()
        self.__langgraph_init()

    def __langgraph_init(self):
        """Initializes the state graph with nodes and state schema."""

        # Initialize the state graph with the defined state schema
        self.graph = StateGraph(state_schema=State)

        # Add moderation nodes
        self.graph.add_node(
            "moderation_passed",
            self._create_retrieval_message,
        )
        self.graph.add_node(
            "moderation_failed",
            self.__moderation.moderation_failed_handler,
        )

        # Add relevance checking nodes
        self.graph.add_node(
            "relevance_checker",
            self.__relevance_checker.check_relevance,
        )
        self.graph.add_node(
            "relevance_passed",
            self.__relevance_checker.relevance_passed_handler,
        )
        self.graph.add_node(
            "relevance_failed",
            self.__relevance_checker.relevance_failed_handler,
        )
        
        # Add answer generation node
        self.graph.add_node(
            "generate_answer",
            self.__answer_generator.generate_answer,
        )


        # Add document retrieval tool node
        self.graph.add_node("retriever", ToolNode([retrieve_documents]))
        
        # Add node to process tool results and extract documents to state
        self.graph.add_node("process_documents", self._process_documents)

        # Define the graph flow
        
        # 1. Start with moderation
        self.graph.add_conditional_edges(
            START,
            self.__moderation.moderate,
            {
                True: "moderation_passed",
                False: "moderation_failed",
            },
        )

        # 2. If moderation passes, go to retriever
        self.graph.add_edge("moderation_passed", "retriever")

        # 3. Process tool results to extract documents
        self.graph.add_edge("retriever", "process_documents")

        # 4. After processing documents, check relevance
        self.graph.add_conditional_edges(
            "process_documents",
            self.__relevance_checker.check_relevance,
            {   
                True: "relevance_passed",
                False: "relevance_failed",
            },
        )

        # 4. If relevant, generate answer
        self.graph.add_edge("relevance_passed", "generate_answer")

        # 5. End edges
        self.graph.add_edge("moderation_failed", END)
        self.graph.add_edge("relevance_failed", END)
        self.graph.add_edge("generate_answer", END)

    def _create_retrieval_message(self, state: State) -> dict:
        """Create an AIMessage with tool call for document retrieval."""
        query = state.get("input", "")
        retrieval_k = state.get("retrieval_k", 5)
        
        # Create an AIMessage with a tool call for document retrieval
        ai_message = AIMessage(
            content="I'll search for relevant documents to answer your question.",
            tool_calls=[{
                "name": "retrieve_documents",
                "args": {"query": query, "k": retrieval_k},
                "id": "retrieve_docs_call_1"
            }]
        )
        
        return {
            "messages": [ai_message],
            "moderated": True
        }

    async def _process_documents(self, state: State) -> dict:
        """Extract documents from tool call results and add to state."""
        try:
            messages = state.get("messages", [])
            documents = []
            
            logger.info(f"Processing {len(messages)} messages to extract documents")
            
            # Look for different types of messages that might contain tool results
            for i, message in enumerate(messages):
                logger.info(f"Message {i}: type={type(message)}, hasattr_type={hasattr(message, 'type')}")
                
                if hasattr(message, 'type'):
                    logger.info(f"Message {i} type: {message.type}")
                
                if hasattr(message, 'content'):
                    logger.info(f"Message {i} content type: {type(message.content)}, content: {str(message.content)[:200]}...")
                
                # Check for ToolMessage
                if hasattr(message, 'type') and message.type == 'tool':
                    logger.info("Found ToolMessage")
                    if hasattr(message, 'content'):
                        try:
                            if isinstance(message.content, str):
                                import json
                                tool_result = json.loads(message.content)
                            elif isinstance(message.content, dict):
                                tool_result = message.content
                            else:
                                tool_result = message.content
                            
                            if isinstance(tool_result, dict) and 'documents' in tool_result:
                                documents.extend(tool_result['documents'])
                                logger.info(f"Extracted {len(tool_result['documents'])} documents from ToolMessage")
                        except Exception as e:
                            logger.error(f"Error parsing ToolMessage content: {e}")
                
                # Check for AIMessage with additional_kwargs (some tool results might be here)
                elif hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                    logger.info(f"Found AIMessage with additional_kwargs: {message.additional_kwargs}")
                
                # Check message attributes for any tool-related content
                for attr in dir(message):
                    if 'tool' in attr.lower() and not attr.startswith('_'):
                        attr_value = getattr(message, attr, None)
                        if attr_value:
                            logger.info(f"Message {i} has tool-related attribute '{attr}': {str(attr_value)[:100]}...")
            
            # If no documents found, try to call the tool directly as fallback
            if not documents:
                logger.warning("No documents found in tool results, trying direct tool call as fallback")
                query = state.get("input", "")
                retrieval_k = state.get("retrieval_k", 5)
                
                # Import and call the tool function directly
                result = await retrieve_documents.ainvoke({"query": query, "k": retrieval_k})
                if isinstance(result, dict) and 'documents' in result:
                    documents = result['documents']
                    logger.info(f"Retrieved {len(documents)} documents via direct tool call")
            
            logger.info(f"Final document count: {len(documents)}")
            
            return {
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"Error processing documents from tool results: {str(e)}")
            return {
                "documents": [],
                "error_message": f"Error processing retrieved documents: {str(e)}"
            }

    async def invoke_agent(self, query: str, retrieval_k: int = 5) -> dict:
        """
        Executes the RAG graph with the given user query and returns the final state.

        This method initializes the state, compiles the graph, and runs the complete
        RAG pipeline including moderation, document retrieval, relevance checking,
        and answer generation.

        Args:
            query: The user input message.
            retrieval_k: Number of documents to retrieve (default: 5).
            
        Returns:
            A dictionary containing the final state of the graph execution.
        """
        try:
            # Initialize state with user input and retrieval parameters
            initial_state = {
                "input": query, 
                "retrieval_k": RETRIEVAL_TOP_K,
                "messages": [HumanMessage(content=query)],
                 }
            # Compile and run the graph
            app = self.graph.compile()

            # Enable tracing for enhanced observability of entire RAG process
            with tracing_v2_enabled(project_name=langchain_settings.PROJECT_NAME):
                result = await app.ainvoke(initial_state)

            logger.info(f"RAG agent completed processing for query: {query[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"RAG agent processing failed: {str(e)}")
            return {
                "input": query,
                "answer": f"I encountered an error while processing your request: {str(e)}",
                "error_message": str(e),
                "is_last_step": True
            }
