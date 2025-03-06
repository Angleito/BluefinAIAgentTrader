"""
Perplexity API Client for the Trading Agent.

This module provides a client for the Perplexity API, allowing the trading agent to
leverage AI-powered insights for market analysis and trading decisions.
"""
import os
import time
import logging
import requests
from typing import Dict, Any, Optional, List, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/perplexity_api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("perplexity_client")

class PerplexityClient:
    """Client for the Perplexity API to analyze charts and market data."""
    
    BASE_URL = "https://api.perplexity.ai"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Perplexity API client.
        
        Args:
            api_key: The API key for Perplexity. If not provided, it will be read from
                     the PERPLEXITY_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            logger.warning("Perplexity API key is not set. Many features will be unavailable.")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
        # For rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
    
    def _rate_limit(self):
        """Enforce rate limiting for API requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle the API response, checking for errors.
        
        Args:
            response: The API response.
            
        Returns:
            The parsed JSON response.
            
        Raises:
            Exception: If the API returns an error.
        """
        if response.status_code != 200:
            error_msg = f"Perplexity API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        try:
            return response.json()
        except ValueError:
            error_msg = f"Invalid JSON response: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def analyze_chart(self, chart_image_path: str, prompt: str) -> Dict[str, Any]:
        """
        Analyze a chart image using Perplexity's vision capabilities.
        
        Args:
            chart_image_path: Path to the chart image file.
            prompt: The prompt to guide the analysis.
            
        Returns:
            The analysis result from Perplexity.
        """
        if not self.api_key:
            logger.error("Perplexity API key is not set. Cannot analyze chart.")
            return {"error": "API key not configured"}
        
        try:
            # Check if the image file exists
            if not os.path.exists(chart_image_path):
                logger.error(f"Chart image file not found: {chart_image_path}")
                return {"error": f"Image file not found: {chart_image_path}"}
            
            # Prepare the multipart form data
            self._rate_limit()
            
            # For Perplexity's vision API
            endpoint = f"{self.BASE_URL}/chat/completions"
            
            with open(chart_image_path, "rb") as image_file:
                # Convert image to base64 for API compatibility
                import base64
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                
                payload = {
                    "model": "llama-3-sonar-small-32k-vision",  # Use appropriate model for vision capabilities
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url", 
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{encoded_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 4000
                }
                
                response = self.session.post(endpoint, json=payload)
                result = self._handle_response(response)
                
                logger.info(f"Chart analysis completed for {chart_image_path}")
                return result
                
        except Exception as e:
            logger.error(f"Error analyzing chart: {e}")
            return {"error": str(e)}
    
    def query(self, prompt: str, model: str = "llama-3-sonar-small-32k") -> Dict[str, Any]:
        """
        Query the Perplexity API with a text prompt.
        
        Args:
            prompt: The text prompt to send.
            model: The model to use for the query.
            
        Returns:
            The query result from Perplexity.
        """
        if not self.api_key:
            logger.error("Perplexity API key is not set. Cannot query API.")
            return {"error": "API key not configured"}
        
        try:
            self._rate_limit()
            
            endpoint = f"{self.BASE_URL}/chat/completions"
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 4000
            }
            
            response = self.session.post(endpoint, json=payload)
            result = self._handle_response(response)
            
            logger.info(f"Query completed: {prompt[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error querying Perplexity API: {e}")
            return {"error": str(e)}
    
    def extract_trading_recommendation(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a structured trading recommendation from an analysis result.
        
        Args:
            analysis_result: The raw analysis result from Perplexity.
            
        Returns:
            A structured trading recommendation with action, confidence, and rationale.
        """
        if "error" in analysis_result:
            return {"action": "HOLD", "confidence": 0.0, "rationale": f"Error: {analysis_result['error']}"}
        
        try:
            # Extract the content from the response
            content = analysis_result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not content:
                return {"action": "HOLD", "confidence": 0.0, "rationale": "No content in response"}
            
            # Use a follow-up query to extract structured data
            extraction_prompt = f"""
            Based on this market analysis, extract a clear trading recommendation:
            
            {content}
            
            Please format your response as JSON with these fields:
            - action: Either "BUY", "SELL", or "HOLD"
            - confidence: A decimal between 0.0 and 1.0 indicating confidence
            - rationale: A brief explanation for the recommendation
            - timeframe: The suggested timeframe for this trade (short-term, medium-term, long-term)
            - risk_level: Estimated risk level (low, medium, high)
            
            Return ONLY the JSON object, nothing else.
            """
            
            extraction_result = self.query(extraction_prompt)
            extracted_content = extraction_result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Parse the JSON response
            import json
            try:
                # Clean up the response to handle potential formatting issues
                # Remove markdown code blocks if present
                if "```json" in extracted_content:
                    extracted_content = extracted_content.split("```json")[1].split("```")[0].strip()
                elif "```" in extracted_content:
                    extracted_content = extracted_content.split("```")[1].split("```")[0].strip()
                
                recommendation = json.loads(extracted_content)
                
                # Validate and sanitize the recommendation
                valid_actions = ["BUY", "SELL", "HOLD"]
                if recommendation.get("action", "").upper() not in valid_actions:
                    recommendation["action"] = "HOLD"
                else:
                    recommendation["action"] = recommendation["action"].upper()
                
                # Ensure confidence is a float between 0 and 1
                try:
                    confidence = float(recommendation.get("confidence", 0.0))
                    recommendation["confidence"] = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError):
                    recommendation["confidence"] = 0.0
                
                # Ensure required fields exist
                if "rationale" not in recommendation:
                    recommendation["rationale"] = "No rationale provided"
                
                return recommendation
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse recommendation JSON: {extracted_content}")
                # Attempt a more basic extraction if JSON parsing fails
                action = "HOLD"
                confidence = 0.5
                rationale = "Could not parse structured recommendation"
                
                if "buy" in extracted_content.lower():
                    action = "BUY"
                    confidence = 0.6
                elif "sell" in extracted_content.lower():
                    action = "SELL"
                    confidence = 0.6
                
                return {
                    "action": action,
                    "confidence": confidence,
                    "rationale": rationale,
                    "timeframe": "medium-term",
                    "risk_level": "medium"
                }
                
        except Exception as e:
            logger.error(f"Error extracting trading recommendation: {e}")
            return {"action": "HOLD", "confidence": 0.0, "rationale": f"Error: {str(e)}"}

# Singleton instance for application-wide use
_instance = None

def get_perplexity_client() -> PerplexityClient:
    """
    Get the singleton instance of the PerplexityClient.
    
    Returns:
        The PerplexityClient instance.
    """
    global _instance
    if _instance is None:
        _instance = PerplexityClient()
    return _instance 