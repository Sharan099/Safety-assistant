"""
Initialize Safety Copilot - Process documents and build vector store
"""
from app import SafetyCopilotApp
from config import DOCUMENTS_DIR
from pathlib import Path

def main():
    print("🛡️ Safety Copilot Initialization")
    print("=" * 50)
    
    # Check if documents exist
    pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"⚠️  No PDF files found in {DOCUMENTS_DIR}")
        print(f"   Please add PDF documents to: {DOCUMENTS_DIR}")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF file(s):")
    for pdf_file in pdf_files:
        print(f"   - {pdf_file.name}")
    
    print("\n🔄 Initializing Safety Copilot...")
    
    try:
        app = SafetyCopilotApp()
        app.initialize(force_rebuild=True)
        
        stats = app.get_stats()
        print("\n✅ Initialization Complete!")
        print(f"   Documents: {stats['num_documents']}")
        print(f"   Chunks: {stats['num_chunks']}")
        print(f"   Model: {stats['embedding_model']}")
        print("\n🚀 You can now run: streamlit run streamlit_app.py")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

