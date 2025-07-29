import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
from dataclasses import dataclass, asdict
import chromadb
from chromadb.config import Settings
from loguru import logger

from config.settings import ConfigManager

@dataclass
class MemoryEntry:
    """Represents a memory entry."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]]
    created_at: datetime
    last_accessed: datetime
    access_count: int

class MemoryEngine:
    """Manages Alfred's persistent memory system."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.persist_path = Path(config.get("memory.persist_path", "./data/memory"))
        self.persist_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self._init_chromadb()
        
        # Memory statistics
        self.stats = {
            "total_entries": 0,
            "queries_count": 0,
            "last_cleanup": datetime.now()
        }
        
        logger.info(f"Memory engine initialized with persist path: {self.persist_path}")
    
    def _init_chromadb(self):
        """Initialize ChromaDB vector store."""
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_path / "chromadb"),
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="alfred_memory",
                metadata={"description": "Alfred's persistent memory store"}
            )
            
            logger.info("ChromaDB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def store_interaction(self, prompt: str, response: str, metadata: Dict[str, Any] = None):
        """Store a prompt-response interaction in memory."""
        try:
            # Create memory ID
            memory_id = self._generate_memory_id(prompt, response)
            
            # Prepare content and metadata
            content = f"Prompt: {prompt}\nResponse: {response}"
            memory_metadata = {
                "type": "interaction",
                "prompt_length": len(prompt),
                "response_length": len(response),
                "created_at": datetime.now().isoformat(),
                "access_count": 0,
                **(metadata or {})
            }
            
            # Store in ChromaDB
            self.collection.add(
                documents=[content],
                metadatas=[memory_metadata],
                ids=[memory_id]
            )
            
            self.stats["total_entries"] += 1
            logger.debug(f"Stored memory: {memory_id}")
            
        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")
    
    def store_fact(self, fact: str, category: str = "general", metadata: Dict[str, Any] = None):
        """Store a factual piece of information."""
        try:
            memory_id = self._generate_memory_id(fact, category)
            
            fact_metadata = {
                "type": "fact",
                "category": category,
                "created_at": datetime.now().isoformat(),
                "access_count": 0,
                **(metadata or {})
            }
            
            self.collection.add(
                documents=[fact],
                metadatas=[fact_metadata],
                ids=[memory_id]
            )
            
            self.stats["total_entries"] += 1
            logger.debug(f"Stored fact: {memory_id}")
            
        except Exception as e:
            logger.error(f"Failed to store fact: {e}")
    
    def search(self, query: str, limit: int = 10, filter_metadata: Dict[str, Any] = None) -> List[str]:
        """Search memory for relevant entries."""
        try:
            # Perform vector search
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=filter_metadata
            )
            
            self.stats["queries_count"] += 1
            
            # Extract and return documents
            if results["documents"] and results["documents"][0]:
                documents = results["documents"][0]
                
                # Update access counts for retrieved memories
                if results["ids"] and results["ids"][0]:
                    self._update_access_counts(results["ids"][0])
                
                logger.debug(f"Memory search returned {len(documents)} results")
                return documents
            
            return []
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []
    
    def list_recent(self, limit: int = 10) -> List[str]:
        """List recent memory entries."""
        try:
            # Get recent entries (ChromaDB doesn't have direct time-based ordering,
            # so we'll get all and sort by metadata if possible)
            results = self.collection.get(
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            if results["documents"]:
                # Sort by creation time if available
                entries_with_time = []
                for i, doc in enumerate(results["documents"]):
                    metadata = results["metadatas"][i] if results["metadatas"] else {}
                    created_at = metadata.get("created_at", "")
                    entries_with_time.append((created_at, doc))
                
                # Sort by creation time (descending)
                entries_with_time.sort(key=lambda x: x[0], reverse=True)
                
                return [doc for _, doc in entries_with_time[:limit]]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to list recent memories: {e}")
            return []
    
    def clear(self):
        """Clear all memory."""
        try:
            self.client.delete_collection("alfred_memory")
            self.collection = self.client.create_collection(
                name="alfred_memory",
                metadata={"description": "Alfred's persistent memory store"}
            )
            self.stats["total_entries"] = 0
            logger.info("Memory cleared successfully")
            
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            # Get current collection count
            count = self.collection.count()
            self.stats["total_entries"] = count
            
            return {
                "total": count,
                "vectors": count,  # In ChromaDB, each entry has a vector
                "nodes": 0,       # Graph nodes would be implemented separately
                "queries": self.stats["queries_count"],
                "last_cleanup": self.stats["last_cleanup"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"total": 0, "vectors": 0, "nodes": 0}
    
    def is_healthy(self) -> str:
        """Check memory system health."""
        try:
            # Test basic operations
            self.collection.count()
            return "Healthy"
        except Exception as e:
            logger.error(f"Memory health check failed: {e}")
            return f"Unhealthy: {e}"
    
    def _generate_memory_id(self, *content_parts: str) -> str:
        """Generate a unique ID for memory entry."""
        content = "|".join(content_parts)
        return hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()
    
    def _update_access_counts(self, memory_ids: List[str]):
        """Update access counts for retrieved memories."""
        # Note: ChromaDB doesn't support atomic updates easily,
        # so this would require a more complex implementation
        # For now, we'll log the access
        logger.debug(f"Accessed memories: {len(memory_ids)}")
    
    def export_memory(self, output_path: str):
        """Export memory to file."""
        try:
            results = self.collection.get(include=["documents", "metadatas"])
            
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_entries": len(results["documents"]) if results["documents"] else 0,
                "entries": []
            }
            
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    metadata = results["metadatas"][i] if results["metadatas"] else {}
                    export_data["entries"].append({
                        "document": doc,
                        "metadata": metadata
                    })
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Memory exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export memory: {e}")
    
    def import_memory(self, input_path: str):
        """Import memory from file."""
        try:
            with open(input_path, 'r') as f:
                import_data = json.load(f)
            
            entries = import_data.get("entries", [])
            
            for entry in entries:
                doc = entry.get("document", "")
                metadata = entry.get("metadata", {})
                
                # Generate new ID for imported entry
                memory_id = self._generate_memory_id(doc)
                
                self.collection.add(
                    documents=[doc],
                    metadatas=[metadata],
                    ids=[memory_id]
                )
            
            logger.info(f"Imported {len(entries)} memory entries from {input_path}")
            
        except Exception as e:
            logger.error(f"Failed to import memory: {e}")