"""
Quiz 5. Joseph Michael Blouin - 1290002, Feb 8th 2013

Graph module for undirected graphs.
"""

import random

try:
    import display
except:
    print("Warning: failed to load display module.  Graph drawing will not work.")
    
class Digraph:
    """
    Directed graph.  The vertices must be immutable.

    To create an empty graph:
    >>> G = Digraph()
    >>> (G.num_vertices(), G.num_edges())
    (0, 0)

    To create a circular graph with 3 vertices:
    >>> G = Digraph([(1, 2), (2, 3), (3, 1)])
    >>> (G.num_vertices(), G.num_edges())
    (3, 3)
    """

    def __init__(self, edges = None):
        self._tosets = {}
        self._fromsets = {}

        if edges:
            for e in edges: self.add_edge(e)

    def __repr__(self):
        return "Digraph({}, {})".format(self.vertices(), self.edges())

    def add_vertex(self, v):
        """
        Adds a vertex to the graph.  It starts with no edges.
        
        >>> G = Digraph()
        >>> G.add_vertex(1)
        >>> G.vertices() == {1}
        True
        """
        if v not in self._tosets:
            self._tosets[v] = set()
            self._fromsets[v] = set()

    def add_edge(self, e):
        """
        Adds an edge to graph.  If vertices in the edge do not exist, it adds them.
        
        >>> G = Digraph()
        >>> G.add_vertex(1)
        >>> G.add_vertex(2)
        >>> G.add_edge((1, 2))
        >>> G.add_edge((2, 1))
        >>> G.add_edge((3, 4))
        >>> G.add_edge((1, 2))
        >>> G.num_edges()
        3
        >>> G.num_vertices()
        4
        """
        # Adds the vertices (in case they don't already exist)
        for v in e:
            self.add_vertex(v)

        # Add the edge
        self._tosets[e[0]].add(e[1])
        self._fromsets[e[1]].add(e[0])

    def edges(self):
        """
        Returns the set of edges in the graph as ordered tuples.
        """
        return { (v, w) for v in self._tosets for w in self._tosets[v] }

    def vertices(self):
        """
        Returns the set of vertices in the graph.
        """
        return set(self._tosets.keys())

    def draw(self, filename, attr = {}):
        """
        Draws the graph into a dot file.
        """
        display.write_dot_desc((self.vertices(), self.edges()), filename, attr)

    def num_edges(self):
        m = 0
        for v in self._tosets:
            m += len(self._tosets[v])
        return m

    def num_vertices(self):
        """
        Returns the number of vertices in the graph.
        """
        return len(self._tosets)

    def adj_to(self, v):
        """
        Returns the set of vertices that contain an edge from v.

        >>> G = Digraph()
        >>> for v in [1, 2, 3]: G.add_vertex(v)
        >>> G.add_edge((1, 3))
        >>> G.add_edge((1, 2))
        >>> G.adj_to(3) == set()
        True
        >>> G.adj_to(1) == { 2, 3 }
        True
        """
        return self._tosets[v]

    def adj_from(self, v):
        """
        Returns the set of vertices that contain an edge to v.

        >>> G = Digraph()
        >>> G.add_edge((1, 3))
        >>> G.add_edge((2, 3))
        >>> G.adj_from(1) == set()
        True
        >>> G.adj_from(3) == { 1, 2 }
        True
        """
        return self._fromsets[v]

    def is_path(self, path):
        """
        Returns True if the list of vertices in the argument path are a
        valid path in the graph.  Returns False otherwise.

        Base Test Case
        >>> G = Digraph([(1, 2), (2, 3), (2, 4), (1, 5), (2, 5), (4, 5), (5, 2)])
        >>> G.is_path([1, 5, 2, 4, 5])
        True
        >>> G.is_path([1, 5, 4, 2])
        False

        Test a path containing multiples of the same edge
        >>> G.is_path([5, 2, 5, 2])
        False

        Test a path that could be incorrectly perceived as having multiples of the same edge
        IE test distinguishment between (x, y) and (y, x)
        >>> G.is_path([5, 2, 5])
        True

        Test Invalid first step
        >>> G.is_path([4, 2, 5, 2])
        False

        Test Invalid last step
        >>> G.is_path([1, 2, 3, 5])
        False

        Test bad vertex
        >>> G.is_path([10, 2, 4, 5])
        False
        >>> G.is_path([2, 4, 5, 10])
        False
        >>> G.is_path([2, 4, 10, 5])
        False

        Test empty path
        >>> G.is_path([])
        False

        """
        if not len(path): return False

        # Get the set of edges in this graph (important that this be a copy)
        edges = [v for v in self.edges()]

        # Make sure the path can actually be commuted
        for i in range(1, len(path)):
            # If the edge exists in the edges list, then it has not appeared before
            # and an edge exists betweeen the vertices
            if (path[i - 1], path[i]) in edges:
                # This edge is valid. Remove it from the set of edges so it cannot appear again
                edges.remove((path[i - 1], path[i]))
            else:
                # This edge is invalid either because no edge exists between these vertices or
                # it has already been traversed
                return False

        return True

def random_graph(n, m):
    """
    Make a random Digraph with n vertices and m edges.

    >>> G = random_graph(10, 5)
    >>> G.num_edges()
    5
    >>> G.num_vertices()
    10
    >>> G = random_graph(1, 1)
    Traceback (most recent call last):
    ...
    ValueError: For 1 vertices, you wanted 1 edges, but can only have a maximum of 0
    """
    G = Digraph()
    for v in range(n):
        G.add_vertex(v)

    max_num_edges = n * (n-1)
    if m > max_num_edges:
        raise ValueError("For {} vertices, you wanted {} edges, but can only have a maximum of {}".format(n, m, max_num_edges))

    while G.num_edges() < m:
        G.add_edge(random.sample(range(n), 2))

    return G

def spanning_tree(G, start):  
    """ 
    Runs depth-first-search on G from vertex start to create a spanning tree.
    """
    visited = set()
    todo = [ (start, None) ]

    T = Digraph()
    
    while todo:
        (cur, e) = todo.pop()

        if cur in visited: continue

        visited.add(cur)
        if e: T.add_edge(e)

        for n in G.adj_to(cur):
            if n not in visited:
                todo.append((n, (cur, n)))
                
    return T

def shortest_path(G, source, dest):
    """
    Returns the shortest path from vertex source to vertex dest or None if there is no such path.

    Essentially Dijkstra's Algorithm.

    Note: Although it would require only a couple simple modifications to the code I decided
            to return null if source == dest although it could be desired to find the shortest path
            that leads back to the source without returning a path of zero length if such a path is possible.

    >>> G = Digraph([(1, 2), (2, 3), (3, 4), (4, 5), (1, 6), (3, 6), (6, 7)])
    >>> path = shortest_path(G, 1, 7)
    >>> path
    [1, 6, 7]
    >>> G.is_path(path)
    True

    Test a source vertex not in the graph
    >>> shortest_path(G, 10, 1) is None
    True

    Test a destination vertex not in the graph
    >>> shortest_path(G, 1, 10) is None
    True

    Test a path that is not possible
    >>> shortest_path(G, 4, 6) is None
    True

    Test the reverse of a possible path
    >>> shortest_path(G, 7, 1) is None
    True

    Test a path where source == dest
    >>> shortest_path(G, 1, 1) is None
    True

    Test on a graph with zero/one/two vertices
    >>> G2 = Digraph()
    >>> shortest_path(G2, 1, 2) is None
    True
    >>> G2.add_vertex(1)
    >>> shortest_path(G2, 1, 2) is None
    True
    >>> G2.add_edge([1,2])
    >>> shortest_path(G2, 1, 2)
    [1, 2]
    >>> shortest_path(G2, 2, 1) is None
    True

    """

    # Check that source exists within G and that source != dest
    if source not in G.vertices() or source == dest: return

    # Get the spanning tree from this node
    tree = spanning_tree(G, source)

    # Make sure that the dest is in the sources' spanning tree
    if dest not in tree.vertices(): return

    # Begin searching the spanning tree
    queue = [ source ]

    # List of previous nodes
    previous = {}

    while queue:
        currentElement = queue.pop()

        # Are we there yet?!
        if dest == currentElement:
            # Walk backwards in history until we get to the source node
            path = [ dest ]
            while path[-1] != source:
                # Use path.append for speed and reverse later
                path.append( previous[ path[-1] ] )

            # The path is now backwards, reverse and return
            path.reverse()
            return path

        # Find the children of this element
        # and append to the queue with history
        for child in [child for child in tree.edges() if child[0] == currentElement]: 
            previous[child[1]] = currentElement
            queue.append(child[1])

def compress(walk):
    """
    Remove cycles from a walk to create a path.
    
    >>> compress([1, 2, 3, 4])
    [1, 2, 3, 4]
    >>> compress([1, 3, 0, 1, 6, 4, 8, 6, 2])
    [1, 6, 2]
    """
    
    lasttime = {}

    for (i,v) in enumerate(walk):
        lasttime[v] = i

    rv = []
    i = 0
    while (i < len(walk)):
        rv.append(walk[i])
        i = lasttime[walk[i]]+1

    return rv
    
            

if __name__ == "__main__":
    import doctest
    doctest.testmod()
