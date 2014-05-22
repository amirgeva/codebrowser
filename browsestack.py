from PySide import QtCore
from PySide import QtGui
import sys


class BrowseStack(QtGui.QDockWidget):
    def __init__(self,parent=None):
        super(BrowseStack,self).__init__(parent)
        self.stacklist=QtGui.QListView()
        self.items=[]
        self.setWidget(self.stacklist)
        
    def updateItems(self):
        m=self.stacklist.model()
        model=QtGui.QStringListModel()
        model.setStringList(self.items)
        self.stacklist.setModel(model)
        del m
        
    def addItem(self,item):
        self.items.append(item)
        self.updateItems()
        
    def top(self):
        if len(self.items)==0:
            return ''
        return self.items[-1]
    
    def pop(self):
        if len(self.items)>0:
            del self.items[-1]
            self.updateItems()
    