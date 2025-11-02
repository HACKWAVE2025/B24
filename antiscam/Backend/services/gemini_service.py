import os
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        """Initialize Gemini service with API key from environment variables"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model = None
        
        # Only try to import and configure Gemini if API key is present
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                # Initialize the model
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("Gemini service initialized successfully")
            except ImportError:
                logger.warning("Google Generative AI library not installed. Gemini features will be disabled.")
                self.model = None
            except Exception as e:
                logger.error(f"Failed to initialize Gemini service: {e}")
                self.model = None
        else:
            logger.warning("GEMINI_API_KEY not found in environment variables. Gemini features will be disabled.")
    
    def is_enabled(self) -> bool:
        """Check if Gemini service is properly configured and enabled"""
        return self.model is not None and self.api_key is not None
    
    def generate_fraud_explanation(self, transaction_data: Dict[str, Any], agent_results: List[Dict[str, Any]], overall_risk: float) -> str:
        """
        Generate a human-readable explanation of why a transaction was flagged as potentially fraudulent.
        
        Args:
            transaction_data: The original transaction data
            agent_results: Results from all AI agents
            overall_risk: The overall risk score
            
        Returns:
            str: A human-readable explanation of the fraud indicators
        """
        if not self.is_enabled():
            return "Gemini AI service is not configured. Set GEMINI_API_KEY in environment variables to enable AI explanations."
        
        try:
            # Import genai here to avoid issues when library is not installed
            import google.generativeai as genai
            
            # Create a detailed prompt for Gemini
            prompt = self._create_analysis_prompt(transaction_data, agent_results, overall_risk)
            
            # Generate the explanation
            if self.model:
                response = self.model.generate_content(prompt)
                
                if response and response.text:
                    return response.text.strip()
                else:
                    return "Unable to generate explanation at this time."
            else:
                return "Gemini AI service is not properly initialized."
                
        except Exception as e:
            logger.error(f"Error generating fraud explanation: {e}")
            return "Sorry, unable to generate explanation at this time."
    
    def _create_analysis_prompt(self, transaction_data: Dict[str, Any], agent_results: List[Dict[str, Any]], overall_risk: float) -> str:
        """Create a detailed prompt for the Gemini AI analysis"""
        prompt = f"""
        You are a financial security expert analyzing potential fraud indicators in UPI transactions. 
        Based on the transaction details and AI agent analysis below, provide a clear, concise explanation 
        of why this transaction was flagged as potentially fraudulent.

        TRANSACTION DETAILS:
        - UPI ID: {transaction_data.get('receiver', 'N/A')}
        - Amount: ₹{transaction_data.get('amount', 'N/A')}
        - Message/Reason: {transaction_data.get('reason', 'N/A') or transaction_data.get('message', 'N/A')}
        - Time: {transaction_data.get('time', 'N/A')}

        AGENT ANALYSIS RESULTS:
        """
        
        for agent in agent_results:
            prompt += f"""
        {agent.get('name', 'Unknown Agent')} (Risk Score: {agent.get('riskScore', 'N/A')}):
        - Message: {agent.get('message', 'N/A')}
        - Evidence: {', '.join(agent.get('evidence', [])) if agent.get('evidence') else 'N/A'}
            """
        
        prompt += f"""
        OVERALL RISK ASSESSMENT: {overall_risk}%

        Please provide 2-3 key reasons why this transaction was flagged, using simple language that a 
        non-technical user can understand. Focus on the most significant red flags and explain why 
        they might indicate fraud. Keep the explanation concise (under 200 words) and actionable.

        Format your response as a clear explanation without any markdown or special formatting.
        """
        
        return prompt

# Global instance of the service
gemini_service = GeminiService()