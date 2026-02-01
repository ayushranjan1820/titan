"""
Natural Language Processing service for query understanding.
Extracts structured filters from user queries using LLM.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

QUERY_PARSING_PROMPT_TEMPLATE = """You are a helpful shopping assistant that understands user queries and extracts structured information.

Given a user query about products, extract the following information:

1. **occasion**: What occasion/event is this for? (e.g., wedding, party, daily use, sports, office)
2. **gender**: Target gender (men, women, unisex, null if not specified)
3. **style**: Style preference (formal, casual, sporty, elegant, modern, classic, etc.)
4. **min_price**: Minimum price (number, null if not specified)
5. **max_price**: Maximum price (number, null if not specified)
6. **color**: Color preference (null if not specified)
7. **brand**: Brand preference (null if not specified)
8. **category**: Product category (watches, grocery, apparel, etc. - infer from context)
9. **additional_preferences**: List of other preferences, keywords, or requirements

Return ONLY a valid JSON object with these fields. Do not include any explanation.

Examples:

User query: "I need a formal men's watch for a wedding under 10000 rupees"
Output:
{{
  "occasion": "wedding",
  "gender": "men",
  "style": "formal",
  "min_price": null,
  "max_price": 10000,
  "color": null,
  "brand": null,
  "category": "watches",
  "additional_preferences": ["elegant", "special occasion"]
}}

User query: "casual women's watch for daily use, budget 5000-8000"
Output:
{{
  "occasion": "daily use",
  "gender": "women",
  "style": "casual",
  "min_price": 5000,
  "max_price": 8000,
  "color": null,
  "brand": null,
  "category": "watches",
  "additional_preferences": ["everyday", "comfortable"]
}}

User query: "sporty fitness tracker under 3000"
Output:
{{
  "occasion": "sports",
  "gender": null,
  "style": "sporty",
  "min_price": null,
  "max_price": 3000,
  "color": null,
  "brand": null,
  "category": "watches",
  "additional_preferences": ["fitness", "activity tracking"]
}}

Now extract information from this user query:
"{user_query}"

Return only the JSON object:
"""


RECOMMENDATION_EXPLANATION_PROMPT_TEMPLATE = """You are a helpful shopping assistant recommending products to a user.

Based on the user's query and the products we found, generate a helpful, natural explanation.

User Query: "{user_query}"

Filters Applied:
{filters_json}

Number of Products Found: {num_products}

Product Names:
{product_names}

Generate a brief (2-3 sentences) natural language explanation that:
1. Acknowledges the user's requirements
2. Explains why these products were selected
3. Highlights key features or benefits

Be conversational, helpful, and concise. Don't use marketing language.

Response:
"""


# ============================================================================
# LLM CLIENT (ABSTRACTED)
# ============================================================================

class LLMClient:
    """
    Abstract LLM client that can use different providers.
    Supports OpenAI, Google Gemini, or mock responses for testing.
    """
    
    def __init__(self):
        """Initialize LLM client based on available API keys."""
        self.provider = None
        self.client = None
        
        # Check for API keys
        openai_key = os.getenv("OPENAI_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY")

        
        if openai_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=openai_key)
                self.provider = "openai"
                logger.info("Using OpenAI as LLM provider")
            except ImportError:
                logger.warning("OpenAI library not installed. Install with: pip install openai")

        elif azure_openai_key:
            try:
                from openai import AzureOpenAI

                self.client = AzureOpenAI(
                    api_key=azure_openai_key,
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
                )

                self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
                self.provider = "azure_openai"

                logger.info("Using Azure OpenAI as LLM provider")

            except ImportError:
                logger.warning(
                    "Azure OpenAI library not installed. Install with: pip install openai"
                )
        
        elif google_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                self.client = genai.GenerativeModel('gemini-pro')
                self.provider = "google"
                logger.info("Using Google Gemini as LLM provider")
            except ImportError:
                logger.warning("Google GenAI library not installed. Install with: pip install google-generativeai")
        
        if not self.provider:
            logger.warning("No LLM API key found. Using mock responses.")
            logger.warning("Set OPENAI_API_KEY or GOOGLE_API_KEY environment variable for real LLM integration.")
            self.provider = "mock"
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if self.provider == "openai":
            return self._generate_openai(prompt, temperature, max_tokens)
        elif self.provider == "google":
            return self._generate_google(prompt, temperature, max_tokens)
        else:
            return self._generate_mock(prompt)
    
    def _generate_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # or gpt-4
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._generate_mock(prompt)
    
    def _generate_google(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate using Google Gemini API."""
        try:
            response = self.client.generate_content(
                prompt,
                generation_config={
                    'temperature': temperature,
                    'max_output_tokens': max_tokens
                }
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            return self._generate_mock(prompt)
    
    def _generate_mock(self, prompt: str) -> str:
        """Generate mock response for testing without API keys."""
        # Check if this is a query parsing request
        if "extract the following information" in prompt.lower():
            # Return a mock filter extraction
            return """{
                "occasion": "wedding",
                "gender": "men",
                "style": "formal",
                "min_price": null,
                "max_price": 10000,
                "color": null,
                "brand": null,
                "category": "watches",
                "additional_preferences": ["elegant", "special occasion"]
            }"""
        
        # Otherwise return a mock explanation
        return """Based on your requirements, I've selected these elegant timepieces that would be perfect for the occasion. 
These watches combine classic styling with quality craftsmanship, ensuring you look your best while staying within your budget. 
Each option offers excellent value and timeless appeal."""


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# ============================================================================
# QUERY PARSING FUNCTIONS
# ============================================================================

def parse_user_query_to_filters(user_query: str) -> Dict[str, Any]:
    """
    Parse natural language user query to structured filters.
    
    Args:
        user_query: Natural language query from user
        
    Returns:
        Dictionary with extracted filters and preferences
    """
    try:
        logger.info(f"Parsing query: {user_query}")
        
        # Build prompt
        prompt = QUERY_PARSING_PROMPT_TEMPLATE.format(user_query=user_query)
        
        # Get LLM response
        llm_client = get_llm_client()
        response = llm_client.generate(prompt, temperature=0.3, max_tokens=300)
        
        logger.debug(f"LLM response: {response}")
        
        # Parse JSON response
        # Clean response (remove markdown code blocks if present)
        response_clean = response.strip()
        if response_clean.startswith("```"):
            # Remove code block markers
            lines = response_clean.split('\n')
            response_clean = '\n'.join(lines[1:-1])
        
        filters = json.loads(response_clean)
        
        # Validate and clean
        filters = _validate_filters(filters)
        
        return filters
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response was: {response}")
        # Return basic fallback
        return _create_fallback_filters(user_query)
    
    except Exception as e:
        logger.error(f"Error parsing query: {e}")
        return _create_fallback_filters(user_query)


def _validate_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean extracted filters."""
    # Ensure required fields exist
    defaults = {
        "occasion": None,
        "gender": None,
        "style": None,
        "min_price": None,
        "max_price": None,
        "color": None,
        "brand": None,
        "category": "watches",  # Default category
        "additional_preferences": []
    }
    
    for key, default_value in defaults.items():
        if key not in filters:
            filters[key] = default_value
    
    return filters


def _create_fallback_filters(user_query: str) -> Dict[str, Any]:
    """Create fallback filters using simple keyword matching."""
    filters = {
        "occasion": None,
        "gender": None,
        "style": None,
        "min_price": None,
        "max_price": None,
        "color": None,
        "brand": None,
        "category": "watches",
        "additional_preferences": [],
        "search_query": user_query  # Use full query as search
    }
    
    query_lower = user_query.lower()
    
    # Simple keyword detection
    if "men" in query_lower or "male" in query_lower:
        filters["gender"] = "men"
    elif "women" in query_lower or "female" in query_lower or "ladies" in query_lower:
        filters["gender"] = "women"
    
    if "formal" in query_lower:
        filters["style"] = "formal"
    elif "casual" in query_lower:
        filters["style"] = "casual"
    elif "sport" in query_lower:
        filters["style"] = "sporty"
    
    # Extract price using regex
    import re
    price_matches = re.findall(r'under\s+(\d+)', query_lower)
    if price_matches:
        filters["max_price"] = int(price_matches[0])
    
    return filters


def generate_recommendation_explanation(
    user_query: str,
    filters: Dict[str, Any],
    products: list,
    num_total: int
) -> str:
    """
    Generate natural language explanation for recommendations.
    
    Args:
        user_query: Original user query
        filters: Extracted filters
        products: List of recommended products
        num_total: Total number of matching products
        
    Returns:
        Natural language explanation
    """
    try:
        # Prepare data for prompt
        filters_json = json.dumps(filters, indent=2)
        product_names = '\n'.join([f"- {p.name} (₹{p.price})" for p in products[:5]])
        
        prompt = RECOMMENDATION_EXPLANATION_PROMPT_TEMPLATE.format(
            user_query=user_query,
            filters_json=filters_json,
            num_products=num_total,
            product_names=product_names if product_names else "No products found"
        )
        
        # Get LLM response
        llm_client = get_llm_client()
        explanation = llm_client.generate(prompt, temperature=0.7, max_tokens=200)
        
        return explanation.strip()
    
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        # Fallback explanation
        return f"Found {num_total} products matching your requirements. Here are the top recommendations."
