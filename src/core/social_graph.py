# src/core/social_graph.py
from typing import Dict, Any, List, Set, Tuple
import networkx as nx

class SocialGraph:
    def __init__(self):
        self.graph = nx.Graph()
        self.nodes: Set[str] = set()

    def add_relationship(
        self,
        agent_a: str,
        agent_b: str,
        weight: float = 1.0,
        relationship_type: str = "friend"
    ):
        """
        Create a connection between two agents.
        """
        self.nodes.add(agent_a)
        self.nodes.add(agent_b)
        self.graph.add_edge(
            agent_a,
            agent_b,
            weight=weight,
            rel_type=relationship_type
        )

    def get_neighbors(self, agent_id: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Find friends/connections of a given agent.
        """
        if agent_id not in self.nodes:
            return []

        neighbors = []
        for neighbor in self.graph.neighbors(agent_id):
            edge_data = self.graph.get_edge_data(agent_id, neighbor)
            neighbors.append((neighbor, edge_data))
        return neighbors

    def get_reach(self, agent_id: str, depth: int = 2) -> int:
        """
        Calculate how many agents an agent can reach within N hops.
        """
        if agent_id not in self.nodes:
            return 0

        # Simple BFS reachability
        reachable_nodes = nx.single_source_shortest_path_length(
            self.graph,
            agent_id,
            cutoff=depth
        )
        return len(reachable_nodes) - 1  # subtract the agent themselves

    def __repr__(self):
        return f"SocialGraph(nodes={len(self.nodes)}, edges={self.graph.number_of_edges()})"
