import scipy.spatial.distance
import scipy.cluster.hierarchy
from neo4j import GraphDatabase

# MATCH (n {name:"root"}) -[r:HAS_CHILD*1..4 {model:'vgg16'}]- (a) RETURN n,a to filter path
def create_cluster_node(tx, name, distance, metadata, isLeaf):
    if isLeaf:
        query = ("CREATE (n:LEAF {name: $name, distance: $distance, metadata:$metadata}) RETURN ID(n)")
        metadata = metadata['_mediaPath'][0]
    else:
        query = ("CREATE (n:Node {name: $name, distance: $distance, metadata:$metadata}) RETURN ID(n)")
        metadata = None
    result = tx.run(query, name = name, distance = distance, metadata = metadata)
    _id = result.single()[0]
    return _id

def find_cluster_node(tx, name):
    query = ("MATCH (n {name:$name}) RETURN ID(n)")
    result = tx.run(query, name=name)
    node = []
    for record in result:
        node.append(record[0])
    return node

def add_child(tx, parent_id, child_id, model):
    # create_cluster_node
    query = (
        "MATCH (parent:Node) WHERE ID(parent)=$parentID "
        "MATCH (child) WHERE ID(child)=$childID "
        "CREATE (parent)-[:HAS_CHILD {model:$model}]->(child)"
        )
    tx.run(query, parentID = parent_id, childID = child_id, model = model)

def descend_cluster(cluster_node, tree_node, metadata, driver, model):
    # with driver.session() as session:
    #     isLeaf = type(tree_node['name']) is int and tree_node['name'] < len(metadata)
    #     node = session.read_transaction(find_cluster_node, tree_node['name'])
    #     if len(node) > 0:
    #         _id = node[0]
    #     else: 
    #         _id = session.write_transaction(create_cluster_node, tree_node['name'], tree_node['distance'], tree_node['metadata'], isLeaf)
    _id = 0
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
            child_id = descend_cluster(cluster_child, new_node, metadata, driver, model)
            # with driver.session() as session:
            #     session.write_transaction(add_child, _id, child_id, model)
    return _id


def clump(predictions, metadata, model, method='average', metric='euclidean'):
    pairwise_distances = scipy.spatial.distance.pdist(predictions, metric)
    # print(type(pairwise_distances))
    clusters = scipy.cluster.hierarchy.linkage(pairwise_distances, method, metric)

    root_node = scipy.cluster.hierarchy.to_tree(clusters)

    tree = {
        'name': 'root',
        'distance': 0,
        'children': [],
        'metadata': {}
    }
    # Neo4j Driver
    # driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "abc123"))
    driver = None
    descend_cluster(root_node, tree, metadata, driver, model)
    # driver.close()
    return tree
