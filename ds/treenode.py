class TreeNode:
    def __init__(self, name, is_folder=True, content="", parent=None):
        self.name = name
        self.is_folder = is_folder
        self.content = content
        self.parent = parent
        self.children = []
        self.tree_id = None
    
    def add_child(self, child):
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)
    
    def get_path(self):
        path = []
        node = self
        while node:
            path.insert(0, node.name)
            node = node.parent
        return "/".join(path)
