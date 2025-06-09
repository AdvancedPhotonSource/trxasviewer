from graphviz import Digraph


def verify_decay_paths(adj_matrix):
    """
    Verifies that all excited states (excluding the ground state) have a path to the ground state.

    Parameters:
    - adj_matrix: 2D list representing adjacency (1 at [i][j] means j → i)

    Returns:
    - True if valid, raises ValueError if any excited state cannot reach ground state.
    """
    num_states = len(adj_matrix)
    ground_index = num_states - 1
    state_names = [f"S{i + 1}" for i in range(ground_index)] + ["GS"]

    # Build graph: edge j → i if adj[i][j] == 1
    graph = {i: [] for i in range(num_states)}
    for to_idx, row in enumerate(adj_matrix):
        for from_idx, val in enumerate(row):
            if val == 1 and from_idx != to_idx:
                graph[from_idx].append(to_idx)

    # DFS to see if each excited state can reach ground
    def can_reach_ground(start):
        visited = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node == ground_index:
                return True
            if node not in visited:
                visited.add(node)
                stack.extend(graph[node])
        return False

    # Check all excited states
    unreachable_states = []
    for i in range(ground_index):  # skip ground state
        if not can_reach_ground(i):
            unreachable_states.append(state_names[i])

    if unreachable_states:
        raise ValueError(
            f"States with no decay path to ground state: {', '.join(unreachable_states)}"
        )

    return True


def draw_decay_graph_with_top_nodes(
    adjacent_matrix, filename="decay_with_top_nodes", output="bytes"
):
    """
    Visualize decay graph where:
    - S0 and all nodes with no parents are forced to the top level.
    - Remaining nodes are placed based on energy-like depth from top.

    Parameters:
    - adjacent_matrix: 2D list defining transitions (1 at [i][j] means j → i)
    - filename: output image name (without extension)
    """
    if not verify_decay_paths(adjacent_matrix):
        print("not valid adjacent matrix")
        return

    dot = Digraph(format="png")
    dot.attr(rankdir="TB", size="6,4!", dpi="150", ratio="fill")

    num_states = len(adjacent_matrix)
    ground_index = num_states - 1
    state_names = [f"S{i + 1}" for i in range(ground_index)] + ["GS"]

    # Identify parentless nodes (no incoming edges)
    incoming = [0] * num_states
    for to_idx, row in enumerate(adjacent_matrix):
        for from_idx, value in enumerate(row):
            if value == 1 and from_idx != to_idx:
                incoming[to_idx] += 1

    top_nodes = {state_names[0]}  # always include S0
    for idx, val in enumerate(incoming):
        if val == 0:
            top_nodes.add(state_names[idx])

    # Compute depth levels using a simple propagation (BFS-like)
    from collections import deque, defaultdict

    levels = defaultdict(lambda: None)
    queue = deque()

    for node in top_nodes:
        levels[node] = 0
        queue.append(node)

    # Build graph edges for lookup
    edges = defaultdict(list)
    for to_idx, row in enumerate(adjacent_matrix):
        for from_idx, val in enumerate(row):
            if val == 1 and from_idx != to_idx:
                from_node = state_names[from_idx]
                to_node = state_names[to_idx]
                edges[from_node].append(to_node)

    # BFS to assign depth levels
    while queue:
        current = queue.popleft()
        current_level = levels[current]
        for neighbor in edges[current]:
            if levels[neighbor] is None or levels[neighbor] < current_level + 1:
                levels[neighbor] = current_level + 1
                queue.append(neighbor)

    # Normalize levels
    unique_levels = sorted(set(levels.values()))
    level_map = {lvl: i for i, lvl in enumerate(unique_levels)}
    for k in levels:
        levels[k] = level_map[levels[k]]

    max_level = max(levels.values())

    # Create dummy level nodes for alignment
    for lvl in range(max_level + 1):
        dot.node(f"level_{lvl}", label="", shape="point", width="0")

    # Add real nodes and invisible aligners
    for state, lvl in levels.items():
        dot.node(state, shape="rectangle")
        dot.edge(f"level_{lvl}", state, style="invis")

    # Group nodes by level
    for lvl in range(max_level + 1):
        with dot.subgraph() as s:
            s.attr(rank="same")
            s.node(f"level_{lvl}")
            for state, slvl in levels.items():
                if slvl == lvl:
                    s.node(state)

    # Draw actual transitions
    for to_idx, row in enumerate(adjacent_matrix):
        for from_idx, value in enumerate(row):
            if value == 1 and from_idx != to_idx:
                from_state = state_names[from_idx]
                to_state = state_names[to_idx]
                dot.edge(from_state, to_state)

    # Render the graph to bytes or file
    if output == "bytes":
        return dot.pipe(format="png")
    elif output == "file":
        dot.render(filename, view=False)
        return filename + ".png"


def generate_graph_bytes(adj_matrix):
    """
    Generate Graphviz PNG image bytes from adjacency matrix.
    """
    return draw_decay_graph_with_top_nodes(adj_matrix)


if __name__ == "__main__":
    adjacent_matrix = [
        [1, 0, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [1, 1, 1, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 1, 1, 0],
    ]

    adjacent_matrix = [
        [1, 0, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [1, 1, 1, 0, 0],
        [0, 1, 0, 1, 0],
        [1, 0, 1, 1, 0],
    ]

    # adjacent_matrix = [
    #     [1, 0, 0, 0, 0],
    #     [0, 1, 0, 0, 0],
    #     [0, 0, 1, 0, 0],
    #     [0, 0, 0, 1, 0],
    #     [1, 1, 1, 1, 0],
    # ]
    adjacent_matrix = [
        [1.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 1.0, 1.0, 0.0],
    ]

    # Generate new layout with top nodes enforced
    # Generate new layout with top nodes enforced
    output_file_top_nodes = draw_decay_graph_with_top_nodes(
        adjacent_matrix, output="file"
    )
