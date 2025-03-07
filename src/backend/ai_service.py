import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError(
                "OpenAI API key not found. Please add your API key to the .env file:\n"
                "1. Create a .env file in the project root if it doesn't exist\n"
                "2. Add the line: OPENAI_API_KEY=your_api_key_here\n"
                "3. Replace 'your_api_key_here' with your actual OpenAI API key"
            )
        
        try:
            self.client = OpenAI(api_key=api_key)
            # Test the API connection
            self.client.models.list()
            logger.info("Successfully initialized OpenAI API")
            
            # Set the default model
            self.model = "gpt-3.5-turbo"
            logger.info(f"Using model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI API: {str(e)}")
            raise ValueError(
                f"Failed to initialize OpenAI API. Please check if your API key is valid: {str(e)}"
            )

        self.error_prompt_template = """
        Analyze this Python code error and provide a detailed explanation and solution:
        
        Code Context:
        {code}
        
        Error:
        {error}
        
        Please provide:
        1. A clear explanation of what's causing the error
        2. A specific solution to fix it
        3. Best practices to avoid this issue in the future
        """

        self.performance_prompt_template = """
        Analyze this Python code for performance optimization:
        
        {code}
        
        Current Issues:
        {issues}
        
        Please provide:
        1. Specific optimization suggestions
        2. Example of optimized code
        3. Explanation of why the optimization helps
        """

    async def get_suggestions(self, code: str, errors: List[Dict]) -> List[Dict]:
        suggestions = []
        
        for error in errors:
            prompt = self.error_prompt_template.format(
                code=code,
                error=f"{error['type']}: {error['message']} at line {error['line']}"
            )
            
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert Python developer helping to debug code."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                suggestion = response.choices[0].message.content
                suggestions.append({
                    "error_type": error["type"],
                    "line": error["line"],
                    "suggestion": suggestion
                })
            except Exception as e:
                logger.error(f"Failed to get suggestion: {str(e)}")
                suggestions.append({
                    "error_type": error["type"],
                    "line": error["line"],
                    "suggestion": f"Failed to get AI suggestion: {str(e)}"
                })
                
        return suggestions

    async def get_chat_response(self, message: str, code_context: str) -> str:
        try:
            prompt = f"""
            User Question: {message}
            
            Code Context:
            {code_context}
            
            Please provide a helpful response that:
            1. Addresses the specific question
            2. Explains any relevant concepts
            3. Provides practical solutions if applicable
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Python developer helping users debug their code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to get chat response: {str(e)}")
            return f"Failed to get AI response: {str(e)}"

    async def optimize_code(self, code: str, performance_issues: List[Dict]) -> Dict:
        try:
            issues_text = "\n".join([
                f"- {issue['type']}: {issue['message']} at line {issue['line']}"
                for issue in performance_issues
            ])
            
            prompt = self.performance_prompt_template.format(
                code=code,
                issues=issues_text
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Python developer focusing on code optimization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return {
                "optimized_code": response.choices[0].message.content,
                "success": True
            }
        except Exception as e:
            logger.error(f"Failed to optimize code: {str(e)}")
            return {
                "error": f"Failed to optimize code: {str(e)}",
                "success": False
            } 