"""
world_map.py — Das mentale Raummodell (Schicht 3, Woche 3)

Topologische Karte als Graph: Knoten = Orte, Kanten = Fahrwege.
Nutzt networkx für kürzeste Wege (Dijkstra/BFS).

Als Java-Leute: das ist ein klassischer gewichteter Graph.
"""
import networkx as nx


class WorldMap:
    def __init__(self):
        self.g = nx.Graph()

    def add_place(self, name, objects=None):
        """Einen markanten Ort als Knoten speichern."""
        self.g.add_node(name, objects=objects or [])

    def connect(self, place_a, place_b, distance_cm):
        """Zwei Orte mit Fahr-Kosten verbinden."""
        self.g.add_edge(place_a, place_b, weight=distance_cm)

    def shortest_path(self, start, goal):
        """Kürzester Weg als Liste von Orten (oder None)."""
        try:
            return nx.shortest_path(self.g, start, goal, weight="weight")
        except nx.NetworkXNoPath:
            return None

    def find_place_with_object(self, label):
        """Ersten Ort finden, an dem ein bestimmtes Objekt gesehen wurde."""
        for name, data in self.g.nodes(data=True):
            if label in data.get("objects", []):
                return name
        return None
