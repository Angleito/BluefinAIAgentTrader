import logging
import random

logger = logging.getLogger(__name__)

class MockPerplexityClient:
    """Mock implementation of PerplexityClient"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        logger.info("Using MockPerplexityClient")
    
    def analyze_chart(self, image_path, prompt):
        logger.warning("[SIMULATION] Analyzing chart with mock client")
        
        # Simulate a random analysis
        actions = ["BUY", "SELL", "HOLD"]
        action = random.choice(actions)
        confidence = round(random.uniform(0.6, 0.95), 2)
        
        return {
            "analysis": "Mock analysis - This is a simulated response",
            "action": action,
            "confidence": confidence,
            "rationale": f"This is a mock rationale for simulation purposes. The recommendation is to {action} with {confidence*100}% confidence."
        }
    
    def query(self, prompt):
        logger.warning("[SIMULATION] Querying with mock client")
        return {
            "response": "Mock response - This is a simulated response to your query"
        } 