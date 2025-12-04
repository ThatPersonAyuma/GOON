import json
from ds.treenode import TreeNode

def load_my_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
def dict_to_tree(data, parent=None):
    node = TreeNode(
        name=data["name"],
        is_folder=data["is_folder"],
        content=data.get("content", ""),
        parent=parent
    )

    for child_data in data.get("children", []):
        child = dict_to_tree(child_data, parent=node)
        node.add_child(child)

    return node

def load_tree_from_my(path):
    data = load_my_file(path)
    return dict_to_tree(data)

    
def tree_to_dict(node):
    return {
        "name": node.name,
        "is_folder": node.is_folder,
        "content": node.content,
        "children": [tree_to_dict(c) for c in node.children]
    }
def save_my_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
def save_tree_to_my(path, root_node):
    data = tree_to_dict(root_node)
    save_my_file(path, data)
    
    
# root = load_tree_from_my("test.goon")
# print(root.content)
# new_note = TreeNode("New Note", is_folder=False, content="Hello world")
# root.add_child(new_note)
# save_tree_to_my("coba.goon", root)
