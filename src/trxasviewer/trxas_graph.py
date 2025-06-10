import sys
from collections import deque, defaultdict
from graphviz import Digraph


def _get_initial_state_indices(adj_matrix):
    """
    Helper function to find the indices of all initial states.

    An initial state is one with no incoming transitions from other states.

    Parameters:
    - adj_matrix: 2D list representing adjacency (1 at [i][j] means j → i)

    Returns:
    - A list of integer indices for the initial states.
    """
    num_states = len(adj_matrix)
    initial_indices = []
    for i in range(num_states):
        # Sum the values in the row `i` to count incoming edges from other states.
        # We exclude the diagonal element `adj_matrix[i][i]`, which represents a self-loop.
        num_parents = sum(adj_matrix[i][j] for j in range(num_states) if i != j)

        if num_parents == 0:
            initial_indices.append(i)
    return initial_indices


def find_initial_states(adj_matrix):
    """
    Finds all states with no incoming transitions (parents).

    Parameters:
    - adj_matrix: 2D list representing adjacency (1 at [i][j] means j → i)

    Returns:
    - A list of names for the initial states (e.g., ['S1', 'S4']).
    """
    num_states = len(adj_matrix)
    if num_states == 0:
        return []

    state_names = [f"S{i + 1}" for i in range(num_states)]

    # Use the helper function to get the indices of initial states
    initial_indices = _get_initial_state_indices(adj_matrix)

    # Map indices to state names
    return [state_names[i] for i in initial_indices]


def create_initial_state_array(adj_matrix):
    """
    Creates an array indicating the initial states of a system.

    This function identifies states with no incoming transitions from other states
    and represents them with a 1 in an output array. All other states are
    represented with a 0.

    Parameters:
    - adj_matrix: A 2D list (square matrix) where adj_matrix[i][j] = 1
                  signifies a transition from state j to state i.

    Returns:
    - A list of integers (e.g., [1, 0, 0, 1]) where a 1 at index `i`
      indicates that state `i` is an initial state.
    """
    num_states = len(adj_matrix)
    if num_states == 0:
        return []

    initial_array = [0] * num_states

    # Use the helper function to get the indices of initial states
    initial_indices = _get_initial_state_indices(adj_matrix)

    # Set the value to 1 for each initial state index
    for i in initial_indices:
        initial_array[i] = 1

    return initial_array


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
                stack.extend(graph.get(node, []))
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
    Visualize decay graph with automated labeling.
    - Initial states are colored green and labeled with c0_i.
    - Ground state is colored blue.
    - Transient states are colored red.
    - Edges are labeled with decay time t_ij inside a purple box.

    Parameters:
    - adjacent_matrix: 2D list defining transitions (1 at [i][j] means j → i)
    - filename: output image name (without extension)
    """
    try:
        verify_decay_paths(adjacent_matrix)
    except ValueError as e:
        print(f"Error: {e}")
        return

    dot = Digraph(format="png")
    dot.attr(rankdir="TB", size="6,4!", dpi="150", ratio="fill")

    num_states = len(adjacent_matrix)
    ground_index = num_states - 1
    state_names = [f"S{i + 1}" for i in range(ground_index)] + ["GS"]

    # Use our new function to find the parentless ("top") nodes
    top_node_names = find_initial_states(adjacent_matrix)
    top_nodes = set(top_node_names)

    # Compute depth levels using a simple propagation (BFS-like)
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

    # Add any nodes missed by BFS (e.g., disconnected components) and assign a default level
    for state in state_names:
        if state not in levels:
            levels[state] = max(levels.values() or [-1]) + 1

    # Normalize levels to be contiguous
    unique_levels = sorted(set(levels.values()))
    level_map = {lvl: i for i, lvl in enumerate(unique_levels)}
    for k in levels:
        levels[k] = level_map[levels[k]]

    max_level = max(levels.values()) if levels else -1

    # Create invisible nodes and edges for level alignment.
    for lvl in range(max_level + 1):
        dot.node(f"level_{lvl}", label="", shape="point", width="0")

    if max_level > 0:
        for lvl in range(max_level):
            dot.edge(f"level_{lvl}", f"level_{lvl+1}", style="invis")

    # Group nodes by level for horizontal alignment
    for lvl in range(max_level + 1):
        with dot.subgraph() as s:
            s.attr(rank="same")
            s.node(f"level_{lvl}")
            for state, slvl in levels.items():
                if slvl == lvl:
                    node_label = state
                    # If the state is an initial state, color it green and add c0 label
                    if state in top_nodes:
                        state_index = state.replace("S", "")
                        node_label = f"{state}\nc0_{state_index}"
                        s.node(
                            state,
                            label=node_label,
                            shape="rectangle",
                            style="filled",
                            fillcolor="lightgreen",
                        )
                    # If the state is the ground state, color it blue
                    elif state == "GS":
                        s.node(
                            state,
                            label=node_label,
                            shape="rectangle",
                            style="filled",
                            fillcolor="lightblue",
                        )
                    # Otherwise, it's a transient state, so color it red
                    else:
                        s.node(
                            state,
                            label=node_label,
                            shape="rectangle",
                            style="filled",
                            fillcolor="lightcoral",
                        )

    # Draw actual transitions with automated, boxed labels
    for from_node, to_nodes in edges.items():
        for to_node in to_nodes:
            from_index = from_node.replace("S", "")
            to_index = to_node.replace("S", "").replace("G", "0")
            text_label = f"t_{from_index}{to_index}"

            # Use HTML-like labels to create a colored box
            html_label = f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0"><TR><TD BGCOLOR="plum">{text_label}</TD></TR></TABLE>>'
            dot.edge(from_node, to_node, label=html_label)

    # Render the graph to bytes or file
    if output == "bytes":
        return dot.pipe(format="png")
    elif output == "file":
        dot.render(filename, view=True, cleanup=True)
        return filename + ".png"


if __name__ == "__main__":
    # Example matrix: S1 is an initial state.
    # S1 -> S2, S1 -> S3, S1 -> S4
    # S2 -> GS, S3 -> GS, S4 -> GS
    adjacent_matrix = [
        [1.0, 0.0, 0.0, 0.0, 0.0],  # S1 has no parents
        [1.0, 1.0, 0.0, 0.0, 0.0],  # S2 has parent S1
        [1.0, 0.0, 1.0, 0.0, 0.0],  # S3 has parent S1
        [1.0, 0.0, 0.0, 1.0, 0.0],  # S4 has parent S1
        [0.0, 1.0, 1.0, 1.0, 0.0],  # GS has parents S2, S3, S4
    ]

    # --- Find the initial states ---
    initials = find_initial_states(adjacent_matrix)
    print(f"The initial states are: {initials}")

    # --- Generate the graph visualization ---
    output_file_top_nodes = draw_decay_graph_with_top_nodes(
        adjacent_matrix, filename="decay_graph_demo", output="file"
    )
    print(f"Graph saved to: {output_file_top_nodes}")

    import numpy as np

    nz_idx = np.nonzero(adjacent_matrix)
    print(nz_idx)
