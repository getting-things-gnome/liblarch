BIG_NUMBER = 2000
STAIRS = 200

from liblarch import Tree
from liblarch.tree import TreeNode
from liblarch_gtk import TreeView
import time, gtk

#This is a dummy treenode that only have one properties: a color
class DummyNode(TreeNode):
    def __init__(self,tid):
        TreeNode.__init__(self, tid)
        self.colors = []
        
        
tree = Tree()
view = tree.get_viewtree()
view = tree.get_viewtree(refresh = False)
nodes_id = []
################now testing the GTK treeview ##################
#The columns description:
desc = {}
col = {}
col['title'] = "Node name"
render_text = gtk.CellRendererText()
col['renderer'] = ['markup',render_text]
def get_node_name(node):
    return node.get_id()
col['value'] = [str,get_node_name]
desc['titles'] = col
treeview = TreeView(view,desc)



start = time.time()
previous_id = None
for index in xrange(BIG_NUMBER):
    nid = "stress" + str(index)
    node = DummyNode(nid)
    nodes_id.append(node.get_id())
    tree.add_node(node)
    previous_id = nid
end = time.time()
print "\nADDING %d NODES: %f" % (BIG_NUMBER, end - start)

start = time.time()
for node_id in nodes_id:
    tree.refresh_node(node_id)
end = time.time()
print "\nUPDATING %d NODES: %f" % (BIG_NUMBER, end - start)


start = time.time()
for node_id in nodes_id:
    tree.del_node(node_id)
end = time.time()
print "\nDELETING %d NODES: %f" % (BIG_NUMBER, end - start)

start = time.time()
previous_id = None
for index in xrange(STAIRS):
    nid = "stress" + str(index)
    node = DummyNode(nid)
    nodes_id.append(node.get_id())
    tree.add_node(node,parent_id=previous_id)
    previous_id = nid
end = time.time()
print "\nADDING %d NODES in stairs: %f" % (STAIRS, end - start)

start = time.time()
for node_id in nodes_id:
    tree.refresh_node(node_id)
end = time.time()
print "\nUPDATING %d NODES in stairs: %f" % (STAIRS, end - start)
