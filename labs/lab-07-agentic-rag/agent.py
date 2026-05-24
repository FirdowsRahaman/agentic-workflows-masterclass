import os
import sys
import math
from typing import TypedDict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =====================================================================
# 1. State Definition
# =====================================================================

class Document(TypedDict):
    content: str
    source: str
    score: float

class RAGState(TypedDict):
    query: str
    query_expanded: str
    documents: list[Document]
    relevant_documents: list[Document]
    web_results: list[Document]
    answer: str
    status: str

# =====================================================================
# 2. Vector Store & Embedding Helper
# =====================================================================

# Hardcoded local document database (Knowledge Base)
LOCAL_DOCUMENTS = [
    {
        "content": "LangGraph is a library for building stateful, multi-actor applications with LLMs, built on top of LangChain. It natively supports cyclic workflows, conditional branching, and persistent memory.",
        "source": "LangGraph Official Docs"
    },
    {
        "content": "Model Context Protocol (MCP) is an open standard that enables developers to build secure, two-way connections between AI models and their data sources. It is designed to act like a USB port for AI models.",
        "source": "Anthropic MCP Specification"
    },
    {
        "content": "FastMCP is a high-level Python framework designed to build MCP servers quickly with minimal boilerplate. It handles server setup, registration of tools, and protocol parsing automatically.",
        "source": "FastMCP Python Guide"
    },
    {
        "content": "To configure a client for Model Context Protocol, you define server configurations in a json file containing command-line execution instructions and environment variables.",
        "source": "MCP Config Guide"
    }
]

# Simulated Web Search database
MOCK_WEB_SEARCH_DB = {
    "agentops observability": "AgentOps refers to observability, telemetry, and evaluation for AI agents. Key tools include Arize Phoenix and LangSmith, which track path tracing and execution costs.",
    "gemini model release": "Google recently released the Gemini 2.5 Flash and Pro model family. It supports extremely fast generation speeds, structured schema outputs, and native tool-calling capabilities."
}

class InMemoryVectorStore:
    def __init__(self):
        self.documents = LOCAL_DOCUMENTS
        self.embeddings = {}
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.initialized = False

    def initialize(self):
        """Pre-computes embeddings if live API key is present."""
        if not self.api_key:
            return
        
        try:
            from google import genai
            client = genai.Client()
            print("🔋 [Vector DB] Pre-computing embeddings for local knowledge base...")
            for i, doc in enumerate(self.documents):
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=doc["content"]
                )
                # Keep the float list
                self.embeddings[i] = response.embeddings[0].values
            self.initialized = True
            print("🟢 [Vector DB] Embeddings loaded successfully.")
        except Exception as e:
            print(f"⚠️ Failed to compute embeddings via API (falling back to mock mode): {e}")
            self.initialized = False

    def _cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def _keyword_similarity(self, query: str, doc_text: str) -> float:
        """Fallback keyword overlap score when no API key is available."""
        stopwords = {"what", "is", "and", "the", "a", "to", "in", "for", "with", "of", "an", "that", "it", "on", "are", "do", "you", "your", "this", "does", "what"}
        
        # Clean punctuation
        q_clean = "".join([c for c in query.lower() if c.isalnum() or c.isspace()])
        doc_clean = "".join([c for c in doc_text.lower() if c.isalnum() or c.isspace()])
        
        q_words = {w for w in q_clean.split() if w not in stopwords}
        doc_words = {w for w in doc_clean.split() if w not in stopwords}
        
        if not q_words:
            return 0.0
            
        # Match with simple stemming to avoid false substring matches (like 'top' matching 'agentops')
        def stem(word):
            for suffix in ["ing", "ely", "ment", "ed", "es", "s"]:
                if word.endswith(suffix) and len(word) > len(suffix) + 2:
                    return word[:-len(suffix)]
            return word

        q_stemmed = {stem(w) for w in q_words}
        doc_stemmed = {stem(w) for w in doc_words}
        
        overlap = len(q_stemmed.intersection(doc_stemmed))
        return overlap / len(q_words)

    def search(self, query: str, top_k: int = 2) -> list[Document]:
        results = []
        
        if self.initialized and self.api_key:
            try:
                from google import genai
                client = genai.Client()
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=query
                )
                query_embedding = response.embeddings[0].values
                
                for i, doc in enumerate(self.documents):
                    doc_emb = self.embeddings.get(i)
                    if doc_emb:
                        score = self._cosine_similarity(query_embedding, doc_emb)
                        results.append({
                            "content": doc["content"],
                            "source": doc["source"],
                            "score": score
                        })
            except Exception as e:
                print(f"⚠️ Search embedding call failed, falling back to keywords: {e}")
                self.initialized = False
        
        # Fallback keyword match
        if not self.initialized:
            for doc in self.documents:
                score = self._keyword_similarity(query, doc["content"])
                results.append({
                    "content": doc["content"],
                    "source": doc["source"],
                    "score": score
                })
                
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

# Instantiate vector store global
vector_store = InMemoryVectorStore()

# =====================================================================
# 3. Agent RAG Nodes
# =====================================================================

def retrieve_node(state: RAGState) -> dict:
    """Queries vector database to fetch relevant text chunks."""
    print(f"\n🔍 [Node: retrieve] Fetching local documents for query: '{state['query']}'")
    docs = vector_store.search(state["query"])
    for d in docs:
        print(f"   - Match Found (Score: {d['score']:.4f}): '{d['content'][:60]}...' [{d['source']}]")
    return {"documents": docs}

def grade_documents_node(state: RAGState) -> dict:
    """Evaluates retrieved chunks and filters out irrelevant ones."""
    print("\n🛡️ [Node: grade_documents] Checking document relevance...")
    relevant_docs = []
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ℹ️ Grader running in Mock Mode...")
        # Simulating relevance grading based on keyword overlap
        for doc in state["documents"]:
            # If search score is high, mark relevant
            if doc["score"] >= 0.3:
                print(f"   🟢 ACCEPTED: '{doc['content'][:50]}...'")
                relevant_docs.append(doc)
            else:
                print(f"   🔴 REJECTED (Irrelevant): '{doc['content'][:50]}...'")
        return {"relevant_documents": relevant_docs}

    try:
        from google import genai
        client = genai.Client()
        
        for doc in state["documents"]:
            prompt = f"""Evaluate whether the following document chunk contains information relevant to answering this user query.
            
Query: {state['query']}
Document: {doc['content']}

Respond with exactly one word: 'YES' if the document is relevant, or 'NO' if it is not.
Answer:"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            verdict = response.text.strip().upper()
            if "YES" in verdict:
                print(f"   🟢 ACCEPTED: '{doc['content'][:50]}...'")
                relevant_docs.append(doc)
            else:
                print(f"   🔴 REJECTED: '{doc['content'][:50]}...'")
                
        return {"relevant_documents": relevant_docs}
    except Exception as e:
        print(f"⚠️ LLM Grading failed, falling back to scores: {e}")
        # Fallback to local heuristic
        for doc in state["documents"]:
            if doc["score"] > 0.15:
                relevant_docs.append(doc)
        return {"relevant_documents": relevant_docs}

def query_expansion_node(state: RAGState) -> dict:
    """Expands query and queries external web mock index."""
    print("\n🔄 [Node: query_expansion] Local data insufficient. Expanding search and querying Web Search API...")
    
    query = state["query"]
    expanded_query = query
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            client = genai.Client()
            prompt = f"""Rewrite the following user query to optimize it for a web search engine. Expand abbreviations and focus on core technical concepts.
Original Query: {query}
Search Query:"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            expanded_query = response.text.strip()
            print(f"   [Query Expanded] '{query}' ──> '{expanded_query}'")
        except Exception as e:
            print(f"⚠️ Query expansion failed: {e}")
            
    # Run mock Web Search lookup
    print(f"🌐 [Web Search API] Executing query: '{expanded_query}'...")
    web_results = []
    
    q_low = expanded_query.lower()
    for key, value in MOCK_WEB_SEARCH_DB.items():
        # Check if key words are in query
        words = key.split()
        if any(w in q_low for w in words):
            web_results.append({
                "content": value,
                "source": "Web Search Index",
                "score": 1.0
            })
            print(f"   - Web Hit: '{value[:60]}...'")
            
    if not web_results:
        print("   - No web search results found.")
        
    return {"query_expanded": expanded_query, "web_results": web_results, "status": "requires_web_search"}

def generate_node(state: RAGState) -> dict:
    """Synthesizes all gathered information to generate a complete grounded response."""
    print("\n✍️ [Node: generate] Synthesizing final answer...")
    
    # Compile sources
    context_chunks = state["relevant_documents"] + state.get("web_results", [])
    context_text = "\n\n".join([f"Source: {c['source']}\nContent: {c['content']}" for c in context_chunks])
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ℹ️ Generator running in Mock Mode...")
        # Mock answers
        if state["status"] == "requires_web_search":
            ans = "Based on web telemetry reports, AgentOps deals with telemetry/observability. Key tools include Arize Phoenix and LangSmith."
        else:
            ans = "LangGraph is a stateful library built on LangChain for creating cyclic LLM workflow graphs with persistent state."
        return {"answer": ans}

    try:
        from google import genai
        client = genai.Client()
        prompt = f"""You are a helpful Technical Assistant. Answer the user query using ONLY the grounding context provided below.
        If the context does not contain enough information to answer, state that you cannot answer.

Query: {state['query']}

Grounding Context:
{context_text if context_text else "- No grounding context available."}

Answer:"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return {"answer": response.text.strip()}
    except Exception as e:
        return {"answer": f"Error generating grounded response: {str(e)}"}

# =====================================================================
# 4. Conditional Edges
# =====================================================================

def check_relevance_edge(state: RAGState) -> str:
    """Determines whether to proceed directly or trigger query expansion/web fallback."""
    # If no relevant local docs were found, route to expansion
    if not state["relevant_documents"]:
        print("🔗 [Edge: check_relevance] 0 relevant local documents ──> Route to 'query_expansion'")
        return "query_expansion"
    else:
        print(f"🔗 [Edge: check_relevance] {len(state['relevant_documents'])} relevant documents found ──> Route to 'generate'")
        return "generate"

# =====================================================================
# 5. Core Pipeline Runner
# =====================================================================

def run_corrective_rag(query: str):
    print("=" * 80)
    print(f"🚀 Initializing Corrective RAG (CRAG) Pipeline | Query: '{query}'")
    print("=" * 80)
    
    # Initialize state
    state: RAGState = {
        "query": query,
        "query_expanded": "",
        "documents": [],
        "relevant_documents": [],
        "web_results": [],
        "answer": "",
        "status": "success"
    }
    
    # Step 1: Retrieve
    retrieved = retrieve_node(state)
    state.update(retrieved)
    
    # Step 2: Grade
    graded = grade_documents_node(state)
    state.update(graded)
    
    # Step 3: Conditional Routing (evaluate edge)
    next_node = check_relevance_edge(state)
    
    if next_node == "query_expansion":
        # Step 4: Expand query and get web search results
        expanded = query_expansion_node(state)
        state.update(expanded)
    
    # Step 5: Generate
    final_output = generate_node(state)
    state.update(final_output)
    
    print("\n🎉 CRAG Execution Finished!")
    print("-" * 80)
    print(f"👉 Final Answer:\n{state['answer']}")
    print("-" * 80)
    print(f"Workflow Status: {state['status'].upper()}\n")

if __name__ == "__main__":
    # Pre-initialize Vector Store Embeddings
    vector_store.initialize()
    
    # Test Case 1: Queries answered fully by local database (LangGraph)
    run_corrective_rag("What is LangGraph and what does it support?")
    
    # Test Case 2: Query requiring web search fallback (AgentOps)
    run_corrective_rag("What is agentops and what observability tools are used?")
