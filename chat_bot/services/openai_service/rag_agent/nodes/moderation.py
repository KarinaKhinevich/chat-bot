import logging

from langchain.chains import OpenAIModerationChain

from chat_bot.config import OpenAISettings
from chat_bot.core.constants import MODERATION_MESSAGE
from ..state import State

logger = logging.getLogger(__name__)

openai_settings = OpenAISettings()


class Moderation:
    """Moderation class to implement OpenAI Moderation."""

    def __init__(self):
        """Initialize the moderation chain."""
        self.moderation_chain = OpenAIModerationChain(
            openai_api_key=openai_settings.API_KEY
        )

    def moderate(self, state: State) -> bool:
        """
        Performs content moderation edge check using OpenAI's moderation API.

        Args:
            state: The state of the graph.
            
        Returns:
            True if content is safe, False if harmful content is detected.
        """
        try:
            response = self.moderation_chain.invoke({"input": state.get("input")})
            is_safe = response.get("input") == response.get("output")
            
            logger.info(f"Moderation result: {'SAFE' if is_safe else 'FLAGGED'}")
            return is_safe
            
        except Exception as e:
            logger.error(f"Error in moderation: {str(e)}")
            # Default to safe if moderation fails
            return True

    def moderation_passed_handler(self, state: State) -> dict:
        """Handle case where moderation passes."""
        logger.info("Moderation passed")
        return {"moderated": True}

    def moderation_failed_handler(self, state: State) -> dict:
        """Handle case where moderation fails."""
        logger.info("Moderation failed")
        return {
            "moderated": False,
            "answer": MODERATION_MESSAGE,
            "is_last_step": True
        }
