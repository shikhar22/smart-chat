#!/usr/bin/env python3
"""
Basic AI Agent using LangChain
A simple AI agent that can answer basic questions using OpenAI's GPT models.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

# Load environment variables
load_dotenv()

class BasicAIAgent:
    """A basic AI agent using LangChain for question answering."""
    
    def __init__(self, model_name="gpt-3.5-turbo", temperature=0.7):
        """
        Initialize the AI agent.
        
        Args:
            model_name (str): The OpenAI model to use
            temperature (float): Controls randomness in responses (0.0 to 1.0)
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Initialize the ChatOpenAI model
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=self.api_key
        )
        
        # Create a prompt template for consistent responses
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant. Answer questions clearly and concisely. "
                      "If you don't know something, say so honestly."),
            ("human", "{question}")
        ])
        
        # Create a chain for processing questions
        self.chain = self.prompt_template | self.llm
    
    def ask_question(self, question: str) -> str:
        """
        Ask the AI agent a question and get a response.
        
        Args:
            question (str): The question to ask
            
        Returns:
            str: The AI's response
        """
        try:
            response = self.chain.invoke({"question": question})
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat_loop(self):
        """Start an interactive chat session with the AI agent."""
        print("🤖 Basic AI Agent")
        print("=" * 50)
        print("Ask me any question! Type 'quit', 'exit', or 'bye' to end the conversation.")
        print()
        
        while True:
            try:
                question = input("You: ").strip()
                
                if question.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("🤖 Goodbye! Have a great day!")
                    break
                
                if not question:
                    print("🤖 Please ask me a question!")
                    continue
                
                print("🤖 Thinking...")
                response = self.ask_question(question)
                print(f"🤖 Agent: {response}")
                print()
                
            except KeyboardInterrupt:
                print("\n🤖 Goodbye! Have a great day!")
                break
            except Exception as e:
                print(f"🤖 Error: {str(e)}")

def main():
    """Main function to run the AI agent."""
    try:
        # Create the AI agent
        agent = BasicAIAgent()
        
        # Start the chat loop
        agent.chat_loop()
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please make sure you have set your OPENAI_API_KEY in the .env file")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    main()
