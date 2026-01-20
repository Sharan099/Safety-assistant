"""
Synthesis Agent - Synthesizes data across multiple documents, 
interprets technical tables, and compares conflicting standards
"""
from typing import List, Dict, Optional, Tuple
import re
from config import LLM_PROVIDER, LLM_MODEL, ANTHROPIC_API_KEY, OPENAI_API_KEY

# Initialize LLM client
claude_client = None
openai_client = None

if LLM_PROVIDER == "anthropic":
    if ANTHROPIC_API_KEY:
        try:
            from anthropic import Anthropic
            claude_client = Anthropic(api_key=ANTHROPIC_API_KEY)
            print("✅ Anthropic Claude client initialized for synthesis")
        except Exception as e:
            print(f"⚠️  Failed to initialize Anthropic: {e}")
    else:
        print("⚠️  ANTHROPIC_API_KEY not set for synthesis! Please add it to your .env file.")

if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"⚠️  Failed to initialize OpenAI: {e}")

class TableExtractor:
    """Extract and interpret technical tables from text"""
    
    @staticmethod
    def detect_table(text: str) -> bool:
        """Detect if text contains a table"""
        # Patterns that suggest tables
        table_indicators = [
            r'\|\s*[^\|]+\s*\|',  # Markdown table
            r'\s{3,}[^\s]+\s{3,}',  # Space-separated columns
            r'\t+[^\t]+',  # Tab-separated
            r'^\s*\d+\.\d+\s+[A-Z]',  # Numbered rows
            r'ASIL\s+[A-D]',  # ASIL table
            r'HIC\s+\d+',  # HIC values
        ]
        
        for pattern in table_indicators:
            if re.search(pattern, text, re.MULTILINE):
                return True
        return False
    
    @staticmethod
    def extract_table_data(text: str) -> Optional[Dict]:
        """Extract structured table data from text"""
        lines = text.split('\n')
        table_data = {
            "has_table": False,
            "rows": [],
            "headers": [],
            "type": None
        }
        
        # Try to find markdown table
        markdown_table = False
        for i, line in enumerate(lines):
            if '|' in line and i < len(lines) - 1:
                markdown_table = True
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if i == 0:
                    table_data["headers"] = cells
                else:
                    if cells and not all(c in ['---', ':', '-'] for c in cells):
                        table_data["rows"].append(cells)
        
        if markdown_table and table_data["rows"]:
            table_data["has_table"] = True
            table_data["type"] = "markdown"
            return table_data
        
        # Try to find space/tab separated table
        potential_table = []
        for line in lines:
            # Check for multiple spaces or tabs (suggesting columns)
            if re.search(r'\s{3,}|\t+', line):
                parts = re.split(r'\s{3,}|\t+', line.strip())
                if len(parts) >= 2:
                    potential_table.append(parts)
        
        if len(potential_table) >= 2:
            table_data["has_table"] = True
            table_data["headers"] = potential_table[0] if potential_table else []
            table_data["rows"] = potential_table[1:]
            table_data["type"] = "space_separated"
            return table_data
        
        return None

class StandardComparator:
    """Compare standards and regulations across documents"""
    
    @staticmethod
    def extract_standard_info(chunks: List[Tuple]) -> List[Dict]:
        """Extract standard/regulation information from chunks"""
        standards = []
        
        for chunk, similarity in chunks:
            info = {
                "document": chunk.document_name,
                "origin": chunk.origin,
                "method": chunk.method,
                "domain": chunk.domain,
                "strictness": chunk.strictness,
                "year": chunk.year,
                "text": chunk.text,
                "page": chunk.page_number,
                "section": chunk.section_number,
                "similarity": similarity
            }
            standards.append(info)
        
        return standards
    
    @staticmethod
    def detect_conflicts(standards: List[Dict]) -> List[Dict]:
        """Detect potential conflicts between standards"""
        conflicts = []
        
        # Group by domain/method
        grouped = {}
        for std in standards:
            key = f"{std.get('domain', 'Unknown')}_{std.get('method', 'Unknown')}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(std)
        
        # Check for conflicting requirements
        for key, group in grouped.items():
            if len(group) > 1:
                # Multiple sources for same standard - potential conflict
                origins = set(std.get('origin') for std in group)
                strictness_levels = set(std.get('strictness') for std in group)
                
                if len(origins) > 1 or len(strictness_levels) > 1:
                    conflicts.append({
                        "standard": key,
                        "sources": group,
                        "conflict_type": "multiple_interpretations"
                    })
        
        return conflicts

def synthesis_agent(
    question: str,
    retrieved_chunks: List[Tuple],
    conversation_history: List[Dict] = None
) -> Dict:
    """
    Synthesize information across multiple documents, interpret tables, 
    and compare conflicting standards
    """
    if not retrieved_chunks:
        return {
            "synthesis": f"I couldn't find relevant information in the available safety documents for your question: '{question}'. The documents I have access to don't appear to contain this information. Please try rephrasing your question or check if the specific document you're looking for is available in the library.",
            "tables": [],
            "comparisons": [],
            "conflicts": [],
            "num_sources": 0
        }
    
    # Extract all relevant chunks
    all_chunks = [chunk for chunk, _ in retrieved_chunks]
    
    # 1. Extract and interpret tables
    tables = []
    for chunk in all_chunks:
        if TableExtractor.detect_table(chunk.text):
            table_data = TableExtractor.extract_table_data(chunk.text)
            if table_data and table_data.get("has_table"):
                tables.append({
                    "document": chunk.document_name,
                    "page": chunk.page_number,
                    "section": chunk.section_number,
                    "table_data": table_data,
                    "context": chunk.text[:500]  # Context around table
                })
    
    # 2. Extract standard information
    standards = StandardComparator.extract_standard_info(retrieved_chunks)
    
    # 3. Detect conflicts
    conflicts = StandardComparator.detect_conflicts(standards)
    
    # 4. Build synthesis prompt
    context_parts = []
    for chunk, similarity in retrieved_chunks:
        source_info = f"[{chunk.document_name}"
        if chunk.origin:
            source_info += f", {chunk.origin}"
        if chunk.method:
            source_info += f", {chunk.method}"
        source_info += f", Page {chunk.page_number}"
        if chunk.section_number:
            source_info += f", Section {chunk.section_number}"
        source_info += "]"
        
        context_parts.append(f"{source_info}\n{chunk.text}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # Add table information if found
    table_context = ""
    if tables:
        table_context = "\n\n**Technical Tables Found:**\n"
        for i, table in enumerate(tables, 1):
            table_context += f"\nTable {i} from {table['document']} (Page {table['page']}):\n"
            if table['table_data'].get('headers'):
                table_context += f"Headers: {', '.join(table['table_data']['headers'])}\n"
            if table['table_data'].get('rows'):
                table_context += f"Rows: {len(table['table_data']['rows'])} data rows\n"
    
    # Add conflict information
    conflict_context = ""
    if conflicts:
        conflict_context = "\n\n**Potential Standard Conflicts Detected:**\n"
        for conflict in conflicts:
            conflict_context += f"\n- {conflict['standard']}: Multiple sources with different interpretations\n"
    
    # Conversation history context
    history_context = ""
    if conversation_history:
        recent_questions = [msg.get("content", "") for msg in conversation_history[-5:] if msg.get("role") == "user"]
        if recent_questions:
            history_context = f"\n\n**Recent Conversation Context:**\n" + "\n".join(f"- {q}" for q in recent_questions)
    
    synthesis_prompt = f"""You are a helpful AI Safety Assistant. Your role is to provide clear, easy-to-understand answers by synthesizing information from multiple safety documents.

**User Question:** {question}
{history_context}

**Relevant Information from Multiple Documents:**
{context}
{table_context}
{conflict_context}

**THE THREE R's - CRITICAL REQUIREMENTS:**

**1. RETRIEVAL (Did you find the right information?):**
- Only use information that is CLEARLY present in the provided context above
- Synthesize information from multiple sources when available
- If the context doesn't contain the answer, you MUST say so explicitly
- Do NOT use information from your training data - only from the context provided
- Verify that the context actually answers the question before responding

**2. REASONING (Why did you give that answer?):**
- Explain WHERE you found the information (e.g., "The test procedures show..." or "Comparing the standards reveals...")
- If citing specific values from tables, explain what the table represents
- If comparing standards, explain the differences clearly
- Be clear about what part of the documents supports your answer
- Use natural language, not technical citations

**3. REFUSAL (Admit when data is missing):**
- If the context doesn't contain the answer, say so clearly
- Example: "I found information about UNECE R94 and Euro NCAP, but I don't see details about [specific thing] in the available documents"
- NEVER make up numbers, values, or requirements
- If information is incomplete or unclear, state this explicitly
- It's better to say "I cannot find this information across the available documents" than to guess

**ADDITIONAL INSTRUCTIONS:**
1. Synthesize information from all provided sources to give a comprehensive answer
2. Skip any garbled or unclear text - only use clear, readable information
3. Write in SIMPLE, CLEAR language that anyone can understand
4. Be CONCISE and to the point - avoid unnecessary technical jargon
5. DO NOT mention document names, page numbers, or file paths in your answer text
6. If comparing standards, explain differences simply with reasoning
7. If interpreting tables, explain key values in plain language with context

**OUTPUT FORMAT:**
Provide a simple, human-friendly answer that:
- Synthesizes information from multiple sources if available
- Explains where/how you found the information (reasoning)
- Admits when information is missing (refusal)

**Example Good Answer (with all 3 R's):**
"The maximum allowable HIC value for a 50th percentile male dummy is 1000 according to UNECE R94. This is specified in the performance criteria section which defines injury thresholds. However, Euro NCAP uses a different threshold of 700 for their assessment. The difference comes from UNECE being a regulatory minimum while Euro NCAP sets higher performance targets for star ratings."

**Example Good Refusal:**
"I found information about UNECE R94 and Euro NCAP protocols in the available documents, but I don't see specific details about the IIHS 2025 protocol. The documents I have access to cover European regulations and protocols, but not the IIHS 2025 standard."

**CRITICAL:**
- If the context contains garbled or unreadable text, skip it completely
- Only use clear, readable sentences
- If you cannot form a coherent answer from the context, say so clearly
- Do NOT repeat garbled text, repeated characters, or unreadable content
- Format your answer in clean, readable sentences

**Answer:**"""
    
    # Generate synthesis using LLM
    synthesis_result = ""
    llm_error = None
    
    # Try Anthropic Claude first
    if claude_client:
        claude_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229"
        ]
        
        print(f"🔍 Attempting synthesis with Anthropic Claude...")
        
        for model_name in claude_models:
            try:
                print(f"🔄 Trying synthesis model: {model_name}")
                response = claude_client.messages.create(
                    model=model_name,
                    max_tokens=3000,  # More tokens for synthesis
                    temperature=0.3,
                    messages=[{"role": "user", "content": synthesis_prompt}]
                )
                # Extract synthesis result with validation
                if response.content and len(response.content) > 0:
                    synthesis_result = response.content[0].text.strip()
                    if synthesis_result:
                        print(f"✅ Synthesis generated using {model_name} (length: {len(synthesis_result)} chars)")
                        break
                    else:
                        print(f"⚠️  Empty synthesis from {model_name}, trying next...")
                        continue
                else:
                    print(f"⚠️  No content in synthesis response from {model_name}, trying next...")
                    continue
            except Exception as e:
                error_msg = str(e)
                llm_error = error_msg
                if "404" in error_msg or "not_found" in error_msg.lower():
                    print(f"⚠️  Model {model_name} not found (404), trying next...")
                    continue
                elif "401" in error_msg or "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                    print(f"❌ Authentication error with {model_name}: {error_msg}")
                    break
                elif "429" in error_msg or "rate_limit" in error_msg.lower():
                    print(f"⚠️  Rate limit error with {model_name}: {error_msg}")
                    break
                else:
                    print(f"⚠️  Claude error with {model_name}: {error_msg}")
                    continue
    else:
        print(f"⚠️  Claude client not initialized for synthesis. LLM_PROVIDER={LLM_PROVIDER}, ANTHROPIC_API_KEY={'set' if ANTHROPIC_API_KEY else 'NOT SET'}")
        llm_error = "Claude client not initialized. Check ANTHROPIC_API_KEY in .env file."
    
    # Fallback to OpenAI
    if not synthesis_result and openai_client:
        openai_models = ["gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4"]
        for model_name in openai_models:
            try:
                response = openai_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": synthesis_prompt}],
                    max_tokens=3000,
                    temperature=0.3
                )
                synthesis_result = response.choices[0].message.content.strip()
                print(f"✅ Synthesis generated using {model_name}")
                break
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "not_found" in error_msg.lower():
                    continue
                else:
                    print(f"⚠️  OpenAI error: {e}")
                    break
    
    # Fallback if no LLM
    if not synthesis_result:
        # Simple synthesis with heavily cleaned text
        import re
        synthesis_result = f"I found relevant information in the available documents. Here's what I can tell you:\n\n"
        
        # Get the best chunk (highest similarity)
        if retrieved_chunks:
            best_chunk, best_sim = retrieved_chunks[0]
            # Aggressive text cleaning
            clean_text = best_chunk.text
            
            # Remove excessive special characters and garbled patterns
            clean_text = re.sub(r'[^\w\s\-.,;:()\[\]{}%°±×÷≤≥≠≈∞∑∏∫√αβγδεθλμπστφω]', ' ', clean_text)
            # Fix merged words
            clean_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_text)
            # Remove excessive spaces
            clean_text = re.sub(r'\s+', ' ', clean_text)
            # Remove garbled patterns (repeated characters, weird spacing)
            clean_text = re.sub(r'([a-zA-Z])\1{2,}', r'\1', clean_text)  # Remove repeated letters
            clean_text = re.sub(r'([^\w\s])\1{2,}', ' ', clean_text)  # Remove repeated special chars
            # Remove lines with too many special characters (likely garbled)
            lines = clean_text.split('\n')
            clean_lines = []
            for line in lines:
                # Check if line is mostly readable (at least 70% alphanumeric)
                if line.strip():
                    alnum_ratio = sum(1 for c in line if c.isalnum() or c.isspace()) / len(line) if line else 0
                    if alnum_ratio >= 0.7:
                        clean_lines.append(line.strip())
            clean_text = ' '.join(clean_lines)
            
            # Extract meaningful sentences (at least 15 characters, mostly readable)
            sentences = re.split(r'[.!?]\s+', clean_text)
            meaningful_sentences = []
            for s in sentences:
                s = s.strip()
                if len(s) >= 15:
                    # Check readability (at least 60% alphanumeric)
                    alnum_ratio = sum(1 for c in s if c.isalnum() or c.isspace()) / len(s) if s else 0
                    # Check for too many single-letter words (garbled pattern)
                    words_in_s = s.split()
                    single_letter_words = sum(1 for w in words_in_s if len(w) == 1 and w.isalpha())
                    if len(words_in_s) > 0 and single_letter_words / len(words_in_s) <= 0.2:  # Max 20% single letters
                        if alnum_ratio >= 0.6:
                            meaningful_sentences.append(s)
            
            if meaningful_sentences:
                # Take first 3-5 meaningful sentences
                synthesis_result += ' '.join(meaningful_sentences[:5])
            else:
                # If no clean sentences, provide a refusal message
                synthesis_result += "I found information in the documents, but it appears to be unclear or garbled. Please try rephrasing your question or check if the documents contain clear information about this topic."
        
        synthesis_result += "\n\nNote: This is extracted directly from the documents. For a more complete answer, please ensure the LLM service is available."
    
    # Clean synthesis result - remove source citations and garbled text
    import re
    
    # Remove common citation patterns
    synthesis_result = re.sub(r'\[Document[^\]]+\]', '', synthesis_result)
    synthesis_result = re.sub(r'\(Document[^\)]+\)', '', synthesis_result)
    synthesis_result = re.sub(r'Page \d+', '', synthesis_result)
    synthesis_result = re.sub(r'Section [^\s]+', '', synthesis_result)
    synthesis_result = re.sub(r'\([^\)]*Origin[^\)]*\)', '', synthesis_result)
    synthesis_result = re.sub(r'\([^\)]*Method[^\)]*\)', '', synthesis_result)
    
    # Aggressive garbled text removal
    synthesis_result = re.sub(r'([a-zA-Z])\1{2,}', r'\1', synthesis_result)  # Remove repeated letters
    synthesis_result = re.sub(r'([^\w\s])\1{2,}', ' ', synthesis_result)  # Remove repeated special chars
    synthesis_result = re.sub(r'_{3,}', ' ', synthesis_result)  # Remove multiple underscores
    synthesis_result = re.sub(r'__+', ' ', synthesis_result)  # Remove double+ underscores
    synthesis_result = re.sub(r'\s+_\s+', ' ', synthesis_result)  # Remove standalone underscores
    synthesis_result = re.sub(r'_\d+', ' ', synthesis_result)  # Remove underscore followed by number
    
    # Fix merged words
    synthesis_result = re.sub(r'([a-z])([A-Z])', r'\1 \2', synthesis_result)
    
    # Remove garbled patterns like "Ove In ra ju ll ry" (single letters separated by spaces)
    words = synthesis_result.split()
    clean_words = []
    for word in words:
        # Skip words that are mostly single letters (likely garbled)
        if len(word) == 1 and word.isalpha():
            continue
        # Skip words with too many special chars
        if word and sum(1 for c in word if not c.isalnum()) > len(word) * 0.5:
            continue
        clean_words.append(word)
    synthesis_result = ' '.join(clean_words)
    
    # Clean up text
    synthesis_result = re.sub(r'[^\w\s\-.,;:()\[\]{}%°±×÷≤≥≠≈∞∑∏∫√αβγδεθλμπστφω]', ' ', synthesis_result)
    synthesis_result = re.sub(r'\s+', ' ', synthesis_result)
    
    # Remove sentences that are mostly garbled (less than 60% alphanumeric)
    sentences = re.split(r'[.!?]\s+', synthesis_result)
    clean_sentences = []
    for sentence in sentences:
        if sentence.strip() and len(sentence.strip()) >= 10:
            alnum_ratio = sum(1 for c in sentence if c.isalnum() or c.isspace()) / len(sentence) if sentence else 0
            # Check for too many single-letter "words" (garbled pattern)
            words_in_sentence = sentence.split()
            single_letter_words = sum(1 for w in words_in_sentence if len(w) == 1 and w.isalpha())
            if len(words_in_sentence) > 0 and single_letter_words / len(words_in_sentence) > 0.3:
                continue  # Skip sentences with >30% single-letter words
            if alnum_ratio >= 0.6:  # At least 60% readable
                clean_sentences.append(sentence.strip())
    
    if clean_sentences:
        synthesis_result = '. '.join(clean_sentences) + '.'
    else:
        # If no clean sentences, try to extract meaningful phrases
        words = synthesis_result.split()
        phrases = []
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            if sum(1 for c in phrase if c.isalnum()) / len(phrase) >= 0.6:
                phrases.append(phrase)
        if phrases:
            synthesis_result = '. '.join(phrases[:3]) + '.'
        else:
            synthesis_result = "I found some information in the documents, but it appears to be unclear or garbled. Please try rephrasing your question or check if the documents contain clear information about this topic."
    
    # Final cleanup
    synthesis_result = re.sub(r'\s+', ' ', synthesis_result)
    synthesis_result = synthesis_result.strip()
    
    return {
        "synthesis": synthesis_result,
        "tables": tables,
        "comparisons": standards,
        "conflicts": conflicts,
        "num_sources": len(all_chunks)
    }

