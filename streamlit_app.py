#!/usr/bin/env python3
"""
Streamlit Web Interface for Basic AI Agent
A web-based interface for the AI agent using Streamlit.
"""

import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Basic AI Agent",
    page_icon="🤖",
    layout="centered"
)

@st.cache_resource
def initialize_agent():
    """Initialize the AI agent with caching."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY not found in environment variables")
        st.stop()
    
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        openai_api_key=api_key
    )
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant. Answer questions clearly and concisely. "
                  "If you don't know something, say so honestly."),
        ("human", "{question}")
    ])
    
    return prompt_template | llm

def main():
    """Main Streamlit application."""
    
    # Title and description
    st.title("🤖 Basic AI Agent")
    st.markdown("Ask me any question and I'll do my best to help you!")
    
    # Initialize the agent
    try:
        chain = initialize_agent()
    except Exception as e:
        st.error(f"Failed to initialize AI agent: {str(e)}")
        return
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = chain.invoke({"question": prompt})
                    response_text = response.content
                    st.markdown(response_text)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Sidebar with information
    with st.sidebar:
        st.markdown("### About")
        st.markdown("This is a basic AI agent built with LangChain and Streamlit.")
        st.markdown("### Features")
        st.markdown("- Question answering")
        st.markdown("- Conversational interface")
        st.markdown("- Powered by OpenAI GPT models")
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    main()
