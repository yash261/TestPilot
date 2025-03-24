import hashlib
import logging
import matplotlib.pyplot as plt
import networkx as nx

class SimpleTokenCounter:
    def token_count(self, text):
        return len(text.split())

class SimpleIO:
    def read_text(self, fname):
        try:
            with open(fname, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            logging.warning(f"Could not read {fname} as UTF-8. Skipping this file.")
            return ""

    def tool_error(self, message):
        logging.error(f"Error: {message}")

    def tool_output(self, message):
        print(message)

# Assuming nx_graph is your MultiDiGraph
def visualize_graph(graph):
    pos = nx.spring_layout(graph)  # positions for all nodes
    plt.figure(figsize=(12, 8))

    # Draw nodes
    nx.draw_networkx_nodes(graph, pos, node_size=700)

    # Draw edges
    nx.draw_networkx_edges(graph, pos, width=1.0, alpha=0.5)

    # Draw labels
    nx.draw_networkx_labels(graph, pos, font_size=12)

    plt.title("Visualization of MultiDiGraph")
    plt.axis('off')  # Turn off the axis
    plt.show()

def generate_node_id(path: str):

    # Create a SHA-1 hash of the combined string
    hash_object = hashlib.md5()
    hash_object.update(path.encode("utf-8"))

    # Get the hexadecimal representation of the hash
    node_id = hash_object.hexdigest()

    return node_id
