"""
Service for generating conversation titles using Azure OpenAI.
"""
import os
from typing import Optional
from openai import AsyncAzureOpenAI
import logging

logger = logging.getLogger(__name__)

class TitleGenerationService:
    """Service for generating meaningful conversation titles from user queries."""
    
    def __init__(self):
        """Initialize the title generation service with Azure OpenAI credentials."""
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self.chat_model = os.getenv("AZURE_CHAT_MODEL", "gpt-4o")
        
        if not self.azure_endpoint or not self.azure_api_key:
            logger.warning("Azure OpenAI credentials not found. Title generation will be disabled.")
            self.client = None
        else:
            self.client = AsyncAzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_api_key,
                api_version=self.azure_api_version
            )
    
    async def generate_title(self, user_message: str) -> Optional[str]:
        """
        Generate a concise, meaningful title for a conversation based on the user's first message.
        
        Args:
            user_message (str): The user's first message in the conversation
            
        Returns:
            Optional[str]: Generated title (3-5 words) or None if generation fails
        """
        if not self.client:
            logger.warning("Azure OpenAI client not initialized. Cannot generate title.")
            return None
            
        if not user_message or len(user_message.strip()) == 0:
            return None
            
        try:
            # Create a prompt for title generation
            system_prompt = """You are a helpful assistant that generates concise, meaningful titles for conversations. 
            
            Given a user's message, create a short title (3-5 words maximum) that captures the main topic or intent of their query.
            
            Rules:
            - Keep it under 5 words
            - Make it descriptive and specific
            - Use title case (capitalize important words)
            - Don't use quotes or special characters
            - Focus on the main topic or action
            
            Examples:
            User: "What are the latest iPhone prices?" → "iPhone Pricing Information"
            User: "How do I bake a chocolate cake?" → "Chocolate Cake Recipe"
            User: "Tell me about machine learning algorithms" → "Machine Learning Algorithms"
            User: "What's the weather like today?" → "Today's Weather"
            """
            
            user_prompt = f"Generate a title for this message: {user_message[:200]}"  # Limit to first 200 chars
            
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=20,  # Keep it short
                temperature=0.3,  # Low temperature for consistent results
                timeout=10  # 10 second timeout
            )
            
            if response.choices and response.choices[0].message.content:
                title = response.choices[0].message.content.strip()
                
                # Clean up the title
                title = title.replace('"', '').replace("'", "").strip()
                
                # Ensure it's not too long
                if len(title) > 50:
                    title = title[:47] + "..."
                
                logger.info(f"Generated title: '{title}' for message: '{user_message[:50]}...'")
                return title
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating conversation title: {str(e)}")
            return None
    
    def generate_fallback_title(self, user_message: str) -> str:
        """
        Generate a simple fallback title when AI generation fails.
        
        Args:
            user_message (str): The user's first message
            
        Returns:
            str: A simple fallback title
        """
        if not user_message or len(user_message.strip()) == 0:
            return "New Conversation"
        
        # Take first few words and clean them up
        words = user_message.strip().split()[:4]
        title = " ".join(words)
        
        # Clean up and capitalize
        title = title.replace('\n', ' ').replace('\r', ' ')
        title = ' '.join(title.split())  # Remove extra whitespace
        
        if len(title) > 30:
            title = title[:27] + "..."
        
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        
        return title or "New Conversation"
