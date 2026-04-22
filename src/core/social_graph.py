"""
Social Graph management for modeling network effects.
"""

from typing import Dict, Any, List, Set, Tuple
import networkx as nx

class SocialGraph:
    def __init__(self):
        self.graph = nx.Graph()
        self.nodes: Set[str] = set()

    def add_relationship(self, agent_a: str, agent_b: str, weight: float = 1.0):
        self.nodes.add(agent_a)
        self.nodes.add(agent_b)
        self.graph.add_edge(agent_a, agent_b, weight=weight)

    def get_neighbors(self, agent_id: str) -> List[str]:
        if agent_id not in self.graph:
            return []
        return list(self.graph.neighbors(agent_id))

    def __repr__(self):
        return f"SocialGraph(nodes={len(self.nodes)}, edges={self.graph.number_of_edges()})"
