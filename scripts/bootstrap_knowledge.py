#!/usr/bin/env python3
"""
Knowledge Base Bootstrap Script
Loads initial documents into RAG on first run or manual invocation

Author: Project Synth
Version: 1.0
"""

import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.local_rag import SynthRAG


def load_file_to_rag(rag: SynthRAG, file_path: Path, source_name: str | None = None):
    """
    Load a single file into RAG
    
    Args:
        rag: SynthRAG instance
        file_path: Path to file
        source_name: Optional source name (defaults to filename)
    """
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        source = source_name or file_path.name
        
        # Add to RAG (will chunk if needed)
        success = rag.add_documents(
            texts=[content],
            sources=[source],
            metadatas=[{
                'file_path': str(file_path),
                'file_type': file_path.suffix,
                'bootstrap': True
            }]
        )
        
        if success > 0:
            print(f"   ✅ {file_path.name} ({len(content)} chars, {success} chunks)")
            return True
        else:
            print(f"   ❌ Failed to load {file_path.name}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error loading {file_path.name}: {e}")
        return False


def bootstrap_knowledge_base(force_reload: bool = False):
    """
    Bootstrap the knowledge base with initial documents
    
    Args:
        force_reload: If True, reload even if collection has documents
    """
    print("\n" + "="*70)
    print("📚 SYNTH KNOWLEDGE BASE BOOTSTRAP")
    print("="*70 + "\n")
    
    # Initialize RAG
    print("1️⃣  Initializing RAG system...")
    rag = SynthRAG()
    
    # Check if RAG is available
    stats = rag.get_stats()
    if stats['status'] != 'active':
        print(f"❌ RAG not available: {stats.get('error', 'Unknown error')}")
        print("\nMake sure:")
        print("  1. Qdrant is installed: pip install qdrant-client")
        print("  2. Ollama is running with qwen2.5:7b model")
        print("  3. SSH tunnel to Delta is active (if using remote Ollama)")
        return
    
    print(f"   ✅ RAG active: {stats['vector_count']} vectors")
    
    # Check if we should skip (already has data)
    if stats['vector_count'] > 0 and not force_reload:
        print(f"\n✅ Knowledge base already has {stats['vector_count']} vectors")
        print("   Use --force to reload")
        return
    
    if force_reload and stats['vector_count'] > 0:
        print(f"\n⚠️  Clearing existing {stats['vector_count']} vectors...")
        rag.clear_collection()
        print("   ✅ Collection cleared")
    
    # Find all documentation files
    print("\n2️⃣  Finding documentation files...")
    
    docs_to_load = []
    
    # Main documentation files
    doc_files = [
        'README.md',
        'PROJECT_README.md',
        'QUICK_START.md',
        'QUICK_REFERENCE.md',
        'DEVELOPMENT_ROADMAP.md',
        'SETUP_DOCUMENTATION.md',
        'PHASE1_COMPLETE.md',
        'PHASE2_BRAIN_AI.md',
        'PHASE3_HANDS.md',
        'PHASE4_INTEGRATION.md',
        'PHASE5_ADVANCED.md',
        'BRAIN_DOCUMENTATION.md',
    ]
    
    for doc_file in doc_files:
        file_path = project_root / doc_file
        if file_path.exists():
            docs_to_load.append(file_path)
    
    # Documentation folder
    docs_dir = project_root / 'docs'
    if docs_dir.exists():
        for doc_file in docs_dir.glob('*.md'):
            docs_to_load.append(doc_file)
    
    print(f"   Found {len(docs_to_load)} documentation files")
    
    # Load each document
    print("\n3️⃣  Loading documents into knowledge base...")
    
    loaded_count = 0
    for i, doc_path in enumerate(docs_to_load, 1):
        print(f"\n   [{i}/{len(docs_to_load)}] Loading {doc_path.name}...")
        if load_file_to_rag(rag, doc_path):
            loaded_count += 1
    
    # Final stats
    print("\n" + "="*70)
    print("📊 BOOTSTRAP COMPLETE")
    print("="*70)
    
    final_stats = rag.get_stats()
    print(f"\n✅ Loaded {loaded_count}/{len(docs_to_load)} documents")
    print(f"✅ Total vectors in collection: {final_stats['vector_count']}")
    print(f"✅ Embedding model: {final_stats['embedding_model']}")
    print(f"✅ Embedding dimensions: {final_stats['embedding_dim']}")
    
    print("\n💡 Knowledge base is ready!")
    print("   You can now ask questions about Project Synth")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Bootstrap Synth knowledge base')
    parser.add_argument('--force', action='store_true', 
                       help='Force reload even if collection has documents')
    
    args = parser.parse_args()
    
    try:
        bootstrap_knowledge_base(force_reload=args.force)
    except KeyboardInterrupt:
        print("\n\n⚠️  Bootstrap cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Bootstrap failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
