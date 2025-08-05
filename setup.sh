#!/bin/bash

# Setup script for Basic AI Agent
echo "🚀 Setting up Basic AI Agent..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
# if [ ! -f .env ]; then
#     echo "📝 Creating .env file..."
#     cp .env.example .env
#     echo "⚠️  Please edit .env file and add your OPENAI_API_KEY"
# else
#     echo "✅ .env file already exists"
# fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OPENAI_API_KEY"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the agent:"
echo "   - Interactive mode: python agent.py"
echo "   - Web interface: streamlit run streamlit_app.py"
echo "   - Example usage: python example.py"
