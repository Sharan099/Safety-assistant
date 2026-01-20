#!/bin/bash
# Setup script for Safety Copilot deployment

echo "🚀 Setting up Safety Copilot..."

# Create necessary directories
mkdir -p data/unece_regulations
mkdir -p data/nhtsa_guidelines
mkdir -p data/functional_safety_concepts
mkdir -p data/validation_testing
mkdir -p data/passive_safety/regulations
mkdir -p data/passive_safety/ncap_protocols
mkdir -p data/passive_safety/fundamentals_training
mkdir -p vector_store
mkdir -p logs
mkdir -p .streamlit

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Initialize vector store (if documents exist)
if [ -d "data" ] && [ "$(ls -A data)" ]; then
    echo "🔄 Initializing vector store..."
    python initialize.py
fi

echo "✅ Setup complete!"

