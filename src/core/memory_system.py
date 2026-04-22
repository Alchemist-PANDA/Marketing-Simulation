# src/core/memory_system.py
from typing import List, Dict, Any
from datetime import datetime

class MemoryEntry:
    def __init__(self, content: str, importance: float, timestamp: datetime):
        self.content = content
        self.importance = importance
        self.timestamp = timestamp
        self.last_accessed = timestamp

class MemorySystem:
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.short_term: List[MemoryEntry] = []
        self.long_term: List[MemoryEntry] = []

    def add_memory(self, content: str, importance: float):
        entry = MemoryEntry(content, importance, datetime.now())
        self.short_term.append(entry)

        # If too many short-term memories, "consolidate" some to long-term
        if len(self.short_term) > 10:
            self._consolidate()

    def _consolidate(self):
        # Move high-importance memories to long-term
        high_imp = [m for m in self.short_term if m.importance > 0.7]
        self.long_term.extend(high_imp)
        self.short_term = [m for m in self.short_term if m.importance <= 0.7]

    def retrieve(self, query: str, limit: int = 5) -> List[str]:
        """
        Simple retrieval - in production, this would use vector search.
        """
        all_memories = self.short_term + self.long_term
        # Just return the most recent ones for now
        sorted_memories = sorted(all_memories, key=lambda x: x.timestamp, reverse=True)
        return [m.content for m in sorted_memories[:limit]]
