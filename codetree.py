from PySide import QtCore
from PySide import QtGui
from doxyparse import Reference, Member, Module, readAll
import sys

class CodeTree(QtGui.QDockWidget):
    def __init__(self,parent=None):
        super(CodeTree,self).__init__(parent)
        self.tree=QtGui.QTreeWidget()
        self.setWidget(self.tree)
        self.tree.itemDoubleClicked.connect(self.onDoubleClick)
        self.references={}
        self.modules={}
        
    def loadCodeTree(self):
        all=readAll()
        for module in all:
            if len(module.srcname)>0:
                item=QtGui.QTreeWidgetItem([module.srcname])
                from codebrowser import moduleDoubleClick
                item.onDoubleClick=moduleDoubleClick
                item.module=module
                self.modules[module.srcpath]=module
                self.tree.addTopLevelItem(item)
                self.addMembers(item,module)
        del all
    
    def getModule(self,path):
        return self.modules.get(path)
        
    def addMembers(self,item,module):
        for member in module.members:
            from codebrowser import addReference
            addReference(member.id,member)
            text=member.name+member.args
            memberItem=QtGui.QTreeWidgetItem([text])
            from codebrowser import memberDoubleClick
            memberItem.onDoubleClick=memberDoubleClick
            memberItem.member=member
            item.addChild(memberItem)
            
    def onDoubleClick(self,item, column):
        item.onDoubleClick(item)
