"""
Quick test script to verify Safety Copilot setup
"""
import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    try:
        import streamlit
        print("✅ Streamlit")
    except ImportError as e:
        print(f"❌ Streamlit: {e}")
        return False
    
    try:
        from config import DATA_DIR, DOCUMENTS_DIR
        print("✅ Config")
    except ImportError as e:
        print(f"❌ Config: {e}")
        return False
    
    try:
        from document_processor import DocumentProcessor
        print("✅ Document Processor")
    except ImportError as e:
        print(f"❌ Document Processor: {e}")
        return False
    
    try:
        from vector_store import SafetyVectorStore
        print("✅ Vector Store")
    except ImportError as e:
        print(f"❌ Vector Store: {e}")
        return False
    
    try:
        from safety_copilot import create_safety_copilot_workflow
        print("✅ Safety Copilot")
    except ImportError as e:
        print(f"❌ Safety Copilot: {e}")
        return False
    
    try:
        from pdf_linker import find_pdf_path
        print("✅ PDF Linker")
    except ImportError as e:
        print(f"❌ PDF Linker: {e}")
        return False
    
    return True

def test_directories():
    """Test if required directories exist"""
    print("\n📁 Testing directories...")
    from config import DATA_DIR, DOCUMENTS_DIR, VECTOR_STORE_DIR
    
    dirs = {
        "Data Directory": DATA_DIR,
        "Documents Directory": DOCUMENTS_DIR,
        "Vector Store Directory": VECTOR_STORE_DIR
    }
    
    all_exist = True
    for name, path in dirs.items():
        if path.exists():
            print(f"✅ {name}: {path}")
        else:
            print(f"⚠️  {name}: {path} (will be created)")
            all_exist = False
    
    return all_exist

def test_pdfs():
    """Test if PDF files are found"""
    print("\n📄 Testing PDF files...")
    from config import DATA_DIR, DOCUMENTS_DIR
    
    pdfs_found = False
    
    # Check professional structure
    if DATA_DIR.exists():
        pdf_files = list(DATA_DIR.rglob("*.pdf"))
        if pdf_files:
            print(f"✅ Found {len(pdf_files)} PDF(s) in data/ structure:")
            for pdf in pdf_files[:5]:  # Show first 5
                print(f"   - {pdf.relative_to(DATA_DIR)}")
            pdfs_found = True
    
    # Check legacy directory
    if DOCUMENTS_DIR.exists():
        legacy_pdfs = list(DOCUMENTS_DIR.glob("*.pdf"))
        if legacy_pdfs:
            print(f"✅ Found {len(legacy_pdfs)} PDF(s) in documents/ folder:")
            for pdf in legacy_pdfs[:5]:
                print(f"   - {pdf.name}")
            pdfs_found = True
    
    if not pdfs_found:
        print("⚠️  No PDF files found. Add PDFs to:")
        print(f"   - {DATA_DIR}/")
        print(f"   - {DOCUMENTS_DIR}/")
    
    return pdfs_found

def test_env():
    """Test environment variables"""
    print("\n🔑 Testing environment...")
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    llm_provider = os.getenv("LLM_PROVIDER", "anthropic")
    print(f"   LLM Provider: {llm_provider}")
    
    if llm_provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key:
            print(f"✅ Anthropic API Key: {'*' * 20}...{api_key[-4:]}")
        else:
            print("⚠️  ANTHROPIC_API_KEY not set")
    elif llm_provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            print(f"✅ OpenAI API Key: {'*' * 20}...{api_key[-4:]}")
        else:
            print("⚠️  OPENAI_API_KEY not set")
    
    return bool(api_key)

def main():
    """Run all tests"""
    print("=" * 60)
    print("🛡️ Safety Copilot - Setup Verification")
    print("=" * 60)
    
    results = {
        "Imports": test_imports(),
        "Directories": test_directories(),
        "PDFs": test_pdfs(),
        "Environment": test_env()
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "⚠️  CHECK"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! Ready to run the app.")
        print("\n🚀 Run: streamlit run streamlit_app.py")
    else:
        print("⚠️  Some checks need attention. See above for details.")
        print("\n💡 Next steps:")
        if not results["Imports"]:
            print("   - Install dependencies: pip install -r requirements.txt")
        if not results["PDFs"]:
            print("   - Add PDF files to data/ or documents/ folder")
        if not results["Environment"]:
            print("   - Create .env file with API keys")
    print("=" * 60)

if __name__ == "__main__":
    main()

