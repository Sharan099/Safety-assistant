"""
Initialize Safety Copilot - Process documents and build vector store
Standalone script - NO Streamlit dependencies
"""
from vector_store_loader import load_or_build_vector_store
from core_app import SafetyCopilotCore
from config import DATA_DIR, DOCUMENTS_DIR
from pathlib import Path

def main():
    print("🛡️ Safety Copilot Initialization")
    print("=" * 50)
    
    # Check if documents exist
    pdf_files_professional = list(DATA_DIR.rglob("*.pdf")) if DATA_DIR.exists() else []
    pdf_files_legacy = list(DOCUMENTS_DIR.glob("*.pdf")) if DOCUMENTS_DIR.exists() else []
    all_pdfs = pdf_files_professional + pdf_files_legacy
    
    if not all_pdfs:
        print(f"⚠️  No PDF files found")
        print(f"   Please add PDF documents to:")
        print(f"   - {DATA_DIR} (professional structure)")
        print(f"   - {DOCUMENTS_DIR} (legacy)")
        return
    
    print(f"📄 Found {len(all_pdfs)} PDF file(s):")
    for pdf_file in all_pdfs[:10]:  # Show first 10
        print(f"   - {pdf_file.name}")
    if len(all_pdfs) > 10:
        print(f"   ... and {len(all_pdfs) - 10} more")
    
    print("\n🔄 Initializing Safety Copilot...")
    
    try:
        # Load or build vector store
        vector_store = SafetyVectorStore.load_or_build_store(force_rebuild=True)
        
        # Create core app
        core = SafetyCopilotCore()
        core.set_vector_store(vector_store)
        
        stats = core.get_stats()
        print("\n✅ Initialization Complete!")
        print(f"   Documents: {stats['num_documents']}")
        print(f"   Chunks: {stats['num_chunks']}")
        print(f"   Model: {stats['embedding_model']}")
        print("\n🚀 You can now run: streamlit run ui.py")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

