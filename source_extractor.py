"""
Source Extractor - Extracts only sources actually cited in LLM answers
"""
import re
from typing import List, Dict, Set

def extract_cited_sources(answer: str, all_sources: List[Dict]) -> List[Dict]:
    """
    Extract only sources that were actually cited/mentioned in the answer
    """
    if not answer or not all_sources:
        return []
    
    answer_lower = answer.lower()
    cited_sources = []
    seen_docs = set()
    
    for source in all_sources:
        doc_name = source.get("document_name", "")
        page_num = source.get("page_number")
        section = source.get("section_number", "")
        
        # Check if document name is mentioned in answer
        doc_mentioned = False
        if doc_name:
            # Try full name
            if doc_name.lower() in answer_lower:
                doc_mentioned = True
            # Try stem (filename without extension)
            doc_stem = doc_name.replace(".pdf", "").replace(".PDF", "")
            if doc_stem.lower() in answer_lower:
                doc_mentioned = True
            # Try partial matches for long names
            doc_words = doc_stem.split()
            if len(doc_words) > 0:
                # Check if key words from doc name appear
                key_words = [w for w in doc_words if len(w) > 3]
                if any(word.lower() in answer_lower for word in key_words[:3]):
                    doc_mentioned = True
        
        # Check if page number is mentioned
        page_mentioned = False
        if page_num:
            # Look for "page X", "p. X", "pg X", etc.
            page_patterns = [
                rf"page\s+{page_num}\b",
                rf"p\.\s*{page_num}\b",
                rf"pg\.?\s*{page_num}\b",
                rf"p\s+{page_num}\b",
            ]
            if any(re.search(pattern, answer_lower) for pattern in page_patterns):
                page_mentioned = True
        
        # Check if section is mentioned
        section_mentioned = False
        if section:
            section_patterns = [
                rf"section\s+{re.escape(section)}\b",
                rf"sec\.?\s+{re.escape(section)}\b",
            ]
            if any(re.search(pattern, answer_lower) for pattern in section_patterns):
                section_mentioned = True
        
        # Include source if document or page is mentioned
        # Also include if it's a high-similarity source (likely used)
        similarity = source.get("similarity_score", 0.0)
        if doc_mentioned or page_mentioned or section_mentioned or similarity >= 0.6:
            # Avoid duplicates
            source_key = (doc_name, page_num)
            if source_key not in seen_docs:
                cited_sources.append(source)
                seen_docs.add(source_key)
    
    # If no sources were explicitly cited, return top 3 by similarity
    if not cited_sources and all_sources:
        sorted_sources = sorted(all_sources, key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        cited_sources = sorted_sources[:3]
    
    return cited_sources

def extract_source_references(answer: str) -> Set[tuple]:
    """
    Extract (document, page) tuples mentioned in the answer
    """
    references = set()
    
    # Pattern: "Document: X, Page: Y" or "X, Page Y" or "X (Page Y)"
    patterns = [
        r"document[:\s]+([^,]+?)[,\s]+page[:\s]+(\d+)",
        r"([^,]+?)[,\s]+page[:\s]+(\d+)",
        r"([^(]+?)\s*\([^)]*page[:\s]*(\d+)",
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, answer, re.IGNORECASE)
        for match in matches:
            doc = match.group(1).strip()
            page = match.group(2).strip()
            if doc and page.isdigit():
                references.add((doc.lower(), int(page)))
    
    return references

