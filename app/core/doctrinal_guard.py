"""Core functionality for ensuring doctrinal accuracy and AI responses."""

from typing import Dict, List, Optional
import openai
from app.config import Config

class DoctrinalGuard:
    """Ensures AI responses align with SDA teachings."""
    
    TOPICS = {
        'sabbath': {
            'key_verses': [
                'Genesis 2:2-3',
                'Exodus 20:8-11',
                'Isaiah 58:13-14'
            ],
            'principles': [
                'Seventh day (Saturday) observance',
                'Sunset to sunset timing',
                'Rest from secular work',
                'Worship and fellowship'
            ]
        },
        'health': {
            'key_verses': [
                '1 Corinthians 6:19-20',
                '3 John 1:2'
            ],
            'principles': [
                'Plant-based diet emphasis',
                'Abstinence from harmful substances',
                'Exercise and rest',
                'Water, air, sunlight benefits'
            ]
        }
    }
    
    def __init__(self):
        """Initialize the DoctrinalGuard with OpenAI configuration."""
        self.api_key = Config.OPENAI_API_KEY
        openai.api_key = self.api_key
    
    def validate_response(self, topic: str, response: str) -> Dict[str, any]:
        """Validate an AI response against SDA doctrinal standards.
        
        Args:
            topic: The doctrinal topic
            response: The AI response to validate
            
        Returns:
            Dictionary containing validation results
        """
        if topic not in self.TOPICS:
            raise ValueError(f"Invalid topic: {topic}")
        
        # Use OpenAI to check doctrinal alignment
        prompt = self._create_validation_prompt(topic, response)
        validation = self._check_with_ai(prompt)
        
        return {
            'is_valid': validation['is_valid'],
            'confidence': validation['confidence'],
            'concerns': validation.get('concerns', []),
            'suggested_corrections': validation.get('corrections', [])
        }
    
    def _create_validation_prompt(self, topic: str, response: str) -> str:
        """Create a prompt for validating responses.
        
        Args:
            topic: The doctrinal topic
            response: The response to validate
            
        Returns:
            Formatted prompt string
        """
        topic_info = self.TOPICS[topic]
        prompt = f"""
        Please validate the following response against SDA teachings on {topic}:
        
        Response: {response}
        
        Key Biblical References:
        {', '.join(topic_info['key_verses'])}
        
        Key Principles:
        {', '.join(topic_info['principles'])}
        
        Please analyze for:
        1. Doctrinal accuracy
        2. Biblical alignment
        3. Spirit of Prophecy consistency
        4. Potential misunderstandings
        
        Return results as:
        - is_valid (boolean)
        - confidence (0-1)
        - concerns (list)
        - corrections (list)
        """
        return prompt
    
    def _check_with_ai(self, prompt: str) -> Dict[str, any]:
        """Send prompt to OpenAI for validation.
        
        Args:
            prompt: The validation prompt
            
        Returns:
            Dictionary containing AI validation results
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a doctrinal validation assistant for the Seventh-day Adventist Church."},
                    {"role": "user", "content": prompt}
                ]
            )
            return self._parse_ai_response(response.choices[0].message['content'])
        except Exception as e:
            return {
                'is_valid': False,
                'confidence': 0,
                'concerns': [f"Validation error: {str(e)}"],
                'corrections': []
            }
    
    def _parse_ai_response(self, response: str) -> Dict[str, any]:
        """Parse the AI response into structured validation results.
        
        Args:
            response: Raw AI response string
            
        Returns:
            Structured validation results
        """
        # Simple parsing for now - could be made more sophisticated
        is_valid = 'valid' in response.lower() and 'not valid' not in response.lower()
        confidence = 0.7  # Default confidence - could be extracted from response
        concerns = []
        corrections = []
        
        return {
            'is_valid': is_valid,
            'confidence': confidence,
            'concerns': concerns,
            'corrections': corrections
        }
