#!/bin/bash

# Semantic RAG Pipeline Setup Script

echo "🚀 Setting up Semantic RAG Pipeline..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check for environment variables
echo "🔑 Checking environment variables..."

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY environment variable is not set!"
    echo "   Please set it before running the API:"
    echo "   export OPENAI_API_KEY='your-api-key-here'"
    echo ""
fi

# Check if firebase config exists
if [ ! -d "firebase_config" ]; then
    echo "📁 Creating firebase_config directory..."
    mkdir -p firebase_config
fi

echo "🔥 Checking Firebase configuration..."
if [ ! -f "firebase_config/Kalco.json" ]; then
    echo "⚠️  Warning: No Firebase configuration files found in firebase_config/"
    echo "   Please add your Firebase service account keys:"
    echo "   - firebase_config/Kalco.json"
    echo "   - firebase_config/TechCorp.json"
    echo "   - firebase_config/FinanceFirst.json"
    echo "   - etc."
    echo ""
fi

echo "✅ Setup complete!"
echo ""
echo "🎯 To start the API server:"
echo "   source .venv/bin/activate"
echo "   python3 main.py"
echo ""
echo "📖 API Documentation will be available at:"
echo "   http://localhost:8000/docs"
echo ""
echo "🧪 To run tests:"
echo "   python3 test_rag_pipeline.py"
echo ""
echo "💡 To see example usage:"
echo "   python3 example_usage.py"
