#!/usr/bin/env python3
"""
RAG (Retrieval Augmented Generation) Agent using LangChain
A RAG agent that can answer company-specific questions using vector search.
"""

import os
import json
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import TextLoader, PyPDFLoader
import docx2txt

# Load environment variables
load_dotenv()

class CompanyRAGAgent:
    """A RAG agent that can answer questions about specific companies."""
    
    def __init__(self, model_name="gpt-3.5-turbo", temperature=0.7):
        """
        Initialize the RAG agent.
        
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
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Dictionary to store company vector stores
        self.company_stores = {}
        
        # Create companies directory if it doesn't exist
        self.companies_dir = Path("companies")
        self.companies_dir.mkdir(exist_ok=True)
        
        # Create vector stores directory
        self.vectordb_dir = Path("vectordb")
        self.vectordb_dir.mkdir(exist_ok=True)
        
        # RAG prompt template
        self.rag_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant that answers questions about companies based on the provided context.

Context: {context}

Question: {input}

Instructions:
- Answer the question based ONLY on the provided context
- If the information is not in the context, say "I don't have information about that in the company documents"
- Be specific and cite relevant details from the context
- If asked about company policies, provide the exact policy details mentioned
- If asked about what the company does, describe their business activities and services

Answer:""")
    
    def load_company_documents(self, company_name: str, documents_path: Optional[str] = None) -> List[Document]:
        """
        Load documents for a specific company.
        
        Args:
            company_name (str): Name of the company
            documents_path (str, optional): Path to company documents directory
            
        Returns:
            List[Document]: List of loaded documents
        """
        if documents_path is None:
            documents_path = self.companies_dir / company_name
        else:
            documents_path = Path(documents_path)
        
        if not documents_path.exists():
            return []
        
        documents = []
        
        # Load all supported file types
        for file_path in documents_path.rglob("*"):
            if file_path.is_file():
                try:
                    if file_path.suffix.lower() == '.txt':
                        loader = TextLoader(str(file_path))
                        docs = loader.load()
                        documents.extend(docs)
                    
                    elif file_path.suffix.lower() == '.pdf':
                        loader = PyPDFLoader(str(file_path))
                        docs = loader.load()
                        documents.extend(docs)
                    
                    elif file_path.suffix.lower() in ['.docx', '.doc']:
                        text = docx2txt.process(str(file_path))
                        doc = Document(
                            page_content=text,
                            metadata={"source": str(file_path)}
                        )
                        documents.append(doc)
                    
                    elif file_path.suffix.lower() == '.json':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Convert JSON to text
                            text = json.dumps(data, indent=2)
                            doc = Document(
                                page_content=text,
                                metadata={"source": str(file_path)}
                            )
                            documents.append(doc)
                
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    continue
        
        # Add metadata about the company to all documents
        for doc in documents:
            doc.metadata["company"] = company_name
        
        return documents
    
    def create_company_vectorstore(self, company_name: str, documents_path: Optional[str] = None, force_recreate: bool = False):
        """
        Create or load a vector store for a specific company.
        
        Args:
            company_name (str): Name of the company
            documents_path (str, optional): Path to company documents
            force_recreate (bool): Whether to force recreation of the vector store
        """
        vectordb_path = self.vectordb_dir / company_name
        
        # Check if vector store already exists and we're not forcing recreation
        if not force_recreate and vectordb_path.exists() and company_name in self.company_stores:
            return
        
        # Load company documents
        documents = self.load_company_documents(company_name, documents_path)
        
        if not documents:
            raise ValueError(f"No documents found for company: {company_name}")
        
        # Split documents into chunks
        splits = self.text_splitter.split_documents(documents)
        
        # Create vector store
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=str(vectordb_path)
        )
        
        # Store the vector store
        self.company_stores[company_name] = vectorstore
        
        print(f"Created vector store for {company_name} with {len(splits)} document chunks")
    
    def get_company_vectorstore(self, company_name: str) -> Optional[Chroma]:
        """
        Get the vector store for a specific company.
        
        Args:
            company_name (str): Name of the company
            
        Returns:
            Optional[Chroma]: The vector store if it exists
        """
        if company_name in self.company_stores:
            return self.company_stores[company_name]
        
        # Try to load existing vector store
        vectordb_path = self.vectordb_dir / company_name
        if vectordb_path.exists():
            try:
                vectorstore = Chroma(
                    persist_directory=str(vectordb_path),
                    embedding_function=self.embeddings
                )
                self.company_stores[company_name] = vectorstore
                return vectorstore
            except Exception as e:
                print(f"Error loading vector store for {company_name}: {e}")
                return None
        
        return None
    
    def ask_company_question(self, question: str, company_name: str) -> str:
        """
        Ask a question about a specific company using RAG.
        
        Args:
            question (str): The question to ask
            company_name (str): The company to ask about
            
        Returns:
            str: The AI's response based on company documents
        """
        try:
            # Get the vector store for the company
            vectorstore = self.get_company_vectorstore(company_name)
            
            if vectorstore is None:
                return f"No knowledge base found for company: {company_name}. Please make sure company documents are loaded."
            
            # Create retriever
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            )
            
            # Create document chain
            document_chain = create_stuff_documents_chain(self.llm, self.rag_prompt)
            
            # Create retrieval chain
            retrieval_chain = create_retrieval_chain(retriever, document_chain)
            
            # Get response
            response = retrieval_chain.invoke({"input": question})
            
            return response["answer"]
            
        except Exception as e:
            return f"Error processing question: {str(e)}"
    
    def list_available_companies(self) -> List[str]:
        """
        List all companies that have document directories.
        
        Returns:
            List[str]: List of company names
        """
        companies = []
        
        # Check companies directory
        if self.companies_dir.exists():
            for item in self.companies_dir.iterdir():
                if item.is_dir():
                    companies.append(item.name)
        
        # Check vector store directory for additional companies
        if self.vectordb_dir.exists():
            for item in self.vectordb_dir.iterdir():
                if item.is_dir() and item.name not in companies:
                    companies.append(item.name)
        
        return sorted(companies)
    
    def add_company_document(self, company_name: str, content: str, filename: str):
        """
        Add a document for a specific company.
        
        Args:
            company_name (str): Name of the company
            content (str): Content of the document
            filename (str): Name of the file
        """
        company_dir = self.companies_dir / company_name
        company_dir.mkdir(exist_ok=True)
        
        file_path = company_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Added document {filename} for company {company_name}")
        
        # Recreate vector store to include new document
        self.create_company_vectorstore(company_name, force_recreate=True)

def main():
    """Main function for testing the RAG agent."""
    try:
        agent = CompanyRAGAgent()
        
        # Example: Create sample company data
        sample_companies = {
            "TechCorp": """
            TechCorp is a leading technology company specializing in artificial intelligence and machine learning solutions.
            
            What we do:
            - Develop AI-powered software solutions for businesses
            - Provide machine learning consulting services
            - Create custom automation tools for enterprises
            
            Company Policies:
            - Remote work policy: Employees can work remotely up to 3 days per week
            - Vacation policy: 25 days of paid vacation per year
            - Training policy: Each employee gets $2000 annual budget for professional development
            - Code of conduct: All employees must maintain confidentiality and act with integrity
            
            Founded: 2020
            Headquarters: San Francisco, CA
            Employee count: 150
            """,
            
            "GreenEnergy": """
            GreenEnergy Solutions is a renewable energy company focused on sustainable power generation.
            
            What we do:
            - Design and install solar panel systems
            - Develop wind energy projects
            - Provide energy storage solutions
            - Offer energy efficiency consulting
            
            Company Policies:
            - Environmental policy: Carbon neutral operations by 2025
            - Work from home policy: Flexible remote work arrangements available
            - Benefits policy: Comprehensive health, dental, and vision coverage
            - Safety policy: All field workers must complete monthly safety training
            
            Founded: 2015
            Headquarters: Austin, TX
            Employee count: 300
            """
        }
        
        # Add sample documents
        for company, content in sample_companies.items():
            agent.add_company_document(company, content, "company_overview.txt")
        
        print("Available companies:", agent.list_available_companies())
        
        # Interactive testing
        while True:
            company = input("\nEnter company name (or 'quit' to exit): ").strip()
            if company.lower() in ['quit', 'exit']:
                break
            
            question = input("Enter your question: ").strip()
            if not question:
                continue
            
            answer = agent.ask_company_question(question, company)
            print(f"\nAnswer: {answer}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
