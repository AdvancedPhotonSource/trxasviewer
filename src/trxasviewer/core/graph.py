# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import io
from collections import deque, defaultdict

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .fitting import _get_initial_state_indices, find_initial_states, create_initial_state_array  # noqa: F401


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

    if not unreachable_states:
        return True, None
    else:
        msg = f"States with no decay path to ground state: {', '.join(unreachable_states)}"
        return False, msg


def _compute_levels_and_edges(adjacent_matrix):
    """
    Derives state names, initial ("top") states, the forward edge map, and
    contiguous BFS depth levels (grouped by level) from an adjacency matrix.
    """
    num_states = len(adjacent_matrix)
    ground_index = num_states - 1
    state_names = [f"S{i + 1}" for i in range(ground_index)] + ["GS"]

    top_node_names = find_initial_states(adjacent_matrix)
    top_nodes = set(top_node_names)

    levels = defaultdict(lambda: None)
    queue = deque()
    for node in top_nodes:
        levels[node] = 0
        queue.append(node)

    edges = defaultdict(list)
    for to_idx, row in enumerate(adjacent_matrix):
        for from_idx, val in enumerate(row):
            if val == 1 and from_idx != to_idx:
                edges[state_names[from_idx]].append(state_names[to_idx])

    while queue:
        current = queue.popleft()
        current_level = levels[current]
        for neighbor in edges[current]:
            if levels[neighbor] is None or levels[neighbor] < current_level + 1:
                levels[neighbor] = current_level + 1
                queue.append(neighbor)

    for state in state_names:
        if state not in levels:
            levels[state] = max(levels.values() or [-1]) + 1

    unique_levels = sorted(set(levels.values()))
    level_map = {lvl: i for i, lvl in enumerate(unique_levels)}
    for k in levels:
        levels[k] = level_map[levels[k]]

    max_level = max(levels.values()) if levels else -1

    by_level = defaultdict(list)
    for state, lvl in levels.items():
        by_level[lvl].append(state)

    return top_nodes, edges, by_level, max_level


def _count_crossings(order, edges, max_level):
    """Counts edge-pair crossings between each pair of adjacent levels for a given node order."""
    total = 0
    for lvl in range(max_level):
        pos_top = {n: i for i, n in enumerate(order[lvl])}
        pos_bot = {n: i for i, n in enumerate(order[lvl + 1])}
        row_edges = [
            (pos_top[src], pos_bot[dst])
            for src in order[lvl]
            for dst in edges.get(src, [])
            if dst in pos_bot
        ]
        for i in range(len(row_edges)):
            for j in range(i + 1, len(row_edges)):
                (a0, a1), (b0, b1) = row_edges[i], row_edges[j]
                if (a0 - b0) * (a1 - b1) < 0:
                    total += 1
    return total


def _order_by_barycenter(by_level, edges, max_level, iterations=4):
    """
    Orders nodes within each depth level to reduce edge crossings between
    adjacent levels, using the Sugiyama-style barycenter heuristic: each
    node is repeatedly repositioned to the average rank of its neighbors
    in the level above/below, alternating sweep direction.
    """
    reverse_edges = defaultdict(list)
    for src, dsts in edges.items():
        for dst in dsts:
            reverse_edges[dst].append(src)

    order = {lvl: sorted(by_level[lvl]) for lvl in range(max_level + 1)}

    def rank_of(lvl):
        return {node: i for i, node in enumerate(order[lvl])}

    def barycenter_sort(lvl, neighbor_map, neighbor_ranks):
        current_rank = rank_of(lvl)

        def key(node):
            neighbor_pos = [neighbor_ranks[n] for n in neighbor_map.get(node, []) if n in neighbor_ranks]
            return sum(neighbor_pos) / len(neighbor_pos) if neighbor_pos else current_rank[node]

        order[lvl] = sorted(order[lvl], key=key)

    for _ in range(iterations):
        for lvl in range(1, max_level + 1):
            barycenter_sort(lvl, reverse_edges, rank_of(lvl - 1))
        for lvl in range(max_level - 1, -1, -1):
            barycenter_sort(lvl, edges, rank_of(lvl + 1))

    return order


def render_decay_graph(ax, adjacent_matrix):
    """
    Draw the decay graph onto an existing matplotlib Axes, with automated labeling.
    - Initial states are colored green and labeled with c0_i.
    - Ground state is colored blue.
    - Transient states are colored red.
    - Edges are labeled with decay time t_ij inside a purple box.

    Parameters:
    - ax: matplotlib Axes to draw onto (cleared and configured by this function)
    - adjacent_matrix: 2D list defining transitions (1 at [i][j] means j → i)

    Returns:
    - (True, None) on success, or (False, error_message) if the matrix is invalid.
    """
    flag, msg = verify_decay_paths(adjacent_matrix)
    if not flag:
        return False, msg

    top_nodes, edges, by_level, max_level = _compute_levels_and_edges(adjacent_matrix)
    order = _order_by_barycenter(by_level, edges, max_level)

    pos = {}
    max_row_width = max(len(order[lvl]) for lvl in range(max_level + 1))
    for lvl in range(max_level + 1):
        row = order[lvl]
        n = len(row)
        for i, state in enumerate(row):
            pos[state] = (i - (n - 1) / 2.0, -lvl)

    def color_for(state):
        if state in top_nodes:
            return "lightgreen"
        elif state == "GS":
            return "lightblue"
        return "lightcoral"

    ax.clear()
    box_w, box_h = 0.6, 0.35

    # Draw actual transitions with automated, boxed labels
    for from_node, to_nodes in edges.items():
        for to_node in to_nodes:
            x0, y0 = pos[from_node]
            x1, y1 = pos[to_node]
            ax.add_patch(FancyArrowPatch(
                (x0, y0 - box_h / 2), (x1, y1 + box_h / 2),
                arrowstyle="-|>", mutation_scale=12, color="black", zorder=1,
            ))

            from_index = from_node.replace("S", "")
            to_index = to_node.replace("S", "").replace("G", "0")
            text_label = f"t_{from_index}{to_index}"
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ax.text(
                mx, my, text_label, fontsize=8, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="plum", ec="none"), zorder=3,
            )

    for state, (x, y) in pos.items():
        ax.add_patch(FancyBboxPatch(
            (x - box_w / 2, y - box_h / 2), box_w, box_h,
            boxstyle="square,pad=0.0", fc=color_for(state), ec="black", zorder=2,
        ))
        ax.text(x, y, state, fontsize=10, ha="center", va="center", zorder=4)

    ax.set_xlim(-max_row_width / 2 - 0.5, max_row_width / 2 + 0.5)
    ax.set_ylim(-max_level - 1, 1)
    ax.axis("off")
    return True, None


def draw_decay_graph_with_top_nodes(
    adjacent_matrix, filename="decay_with_top_nodes", output="bytes"
):
    """
    Visualize decay graph with automated labeling, rendering to a standalone
    figure and returning PNG bytes or a saved file path. See render_decay_graph
    for the drawing logic and adjacent_matrix format.
    """
    flag, msg = verify_decay_paths(adjacent_matrix)
    if not flag:
        return False, msg

    _, _, by_level, max_level = _compute_levels_and_edges(adjacent_matrix)
    max_row_width = max(len(by_level[lvl]) for lvl in range(max_level + 1))

    fig, ax = plt.subplots(figsize=(max(6, max_row_width * 1.3), 4), dpi=600)
    render_decay_graph(ax, adjacent_matrix)

    fig.tight_layout()

    # Render the graph to bytes or file
    if output == "bytes":
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        return True, buf.getvalue()
    elif output == "file":
        out_path = filename + ".png"
        fig.savefig(out_path)
        plt.close(fig)
        return True, out_path


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
    flag, output_file_top_nodes = draw_decay_graph_with_top_nodes(
        adjacent_matrix, filename="decay_graph_demo", output="file"
    )
    print(f"Graph saved to: {output_file_top_nodes}")

    import numpy as np

    nz_idx = np.nonzero(adjacent_matrix)
    print(nz_idx)
