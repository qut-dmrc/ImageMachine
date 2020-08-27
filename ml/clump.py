import scipy.spatial.distance
import scipy.cluster.hierarchy


def descend_cluster(cluster_node, tree_node, metadata):
    for cluster_child in [cluster_node.left, cluster_node.right]:
        if cluster_child:
            new_node = {
                'name': cluster_child.id,
                'distance': cluster_child.dist,
                'children': [],
                'metadata': {}
            }

            # If a leaf node
            if cluster_child.id < len(metadata):
                new_node['metadata'] = metadata[cluster_child.id]

            tree_node['children'].append(new_node)
            descend_cluster(cluster_child, new_node, metadata)


def clump(predictions, metadata, method='average', metric='euclidean'):
    pairwise_distances = scipy.spatial.distance.pdist(predictions, metric)
    clusters = scipy.cluster.hierarchy.linkage(pairwise_distances, method, metric)

    root_node = scipy.cluster.hierarchy.to_tree(clusters)

    tree = {
        'name': 'root',
        'distance': 0,
        'children': [],
        'metadata': {}
    }

    descend_cluster(root_node, tree, metadata)
    return tree
