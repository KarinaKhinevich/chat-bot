import logging

from langgraph.graph import StateGraph, START, END
from .nodes import Moderation, RelevanceChecker
from .state import State

logger = logging.getLogger(__name__)


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
        self.__langgraph_init()

    def __langgraph_init(self):
        """Initializes the state graph with nodes and state schema."""

        # Initialize the state graph with the defined state schema
        self.graph = StateGraph(state_schema=State)

        # Add moderation nodes
        self.graph.add_node(
            "moderation_passed",
            self.__moderation.moderation_passed_handler,
        )
        self.graph.add_node(
            "moderation_failed",
            self.__moderation.moderation_failed_handler,
        )

        # Add relevance checking nodes
        self.graph.add_node(
            "relevance_passed",
            self.__relevance_checker.relevance_passed_handler,
        )
        self.graph.add_node(
            "relevance_failed",
            self.__relevance_checker.relevance_failed_handler,
        )

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

        # 2. If moderation passes, check document relevance
        self.graph.add_conditional_edges("moderation_passed", self.__relevance_checker.check_relevance,
            {
                True: "relevance_passed",
                False: "relevance_failed",
            },
        )


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
            # Compile and run the graph
            app = self.graph.compile()
            result = await app.ainvoke({"input": query, "retrieval_k": retrieval_k})

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
