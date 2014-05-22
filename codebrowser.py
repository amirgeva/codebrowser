from PySide import QtCore
from PySide import QtGui
import sys
from codeedit import CodeEditor
from browsestack import BrowseStack
from codetree import CodeTree

gBrowser=None

def backspacePressed():
    gBrowser.backspacePressed()

class CodeBrowser(QtGui.QMainWindow):
    def __init__(self,parent=None):
        super(CodeBrowser,self).__init__(parent)
        self.path=''
        self.edit=CodeEditor()
        self.edit.setFont(QtGui.QFont('monospace',14))
        self.setCentralWidget(self.edit)
        self.stack=BrowseStack()
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self.stack)
        self.refs={}
        self.tree=CodeTree()
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.tree)
        self.backShortCut=QtGui.QShortcut(self)
        self.backShortCut.setKey(QtGui.QKeySequence(QtCore.Qt.Key_Backspace))
        self.backShortCut.activated.connect(backspacePressed)
        self.backShortCut.setEnabled(True)

    def loadModule(self,module):
        memberColor=QtGui.QColor(0,64,192)
        refColor=QtGui.QColor(0,192,128)
        unboundColor=QtGui.QColor(192,64,64)
        path=module.srcpath
        if path!=self.path:
            self.path=path
            self.edit.setText(path,open(path,'r').read())
            for member in module.members:
                self.edit.code.addHighlight(member.name,member.line,memberColor,member.id)
                for ref in member.refs:
                    if ref.refid in self.refs:
                        refMember=self.refs.get(ref.refid)
                        self.edit.code.addRefHighlights(refMember.name,member.line,member.bodyend,refColor,ref.refid)
                    else:
                        self.edit.code.addRefHighlights(ref.ident,member.line,member.bodyend,unboundColor,None)
        
    def gotoMember(self,member):
        self.loadModule(member.module)
        line=member.line
        self.edit.code.setCurrentLine(self.path,line)
        
    def gotoRef(self,refid,curLine):
        if refid in self.refs:
            self.stack.addItem("{}:{}".format(self.path,curLine))
            refMember=self.refs.get(refid)
            self.gotoMember(refMember)
            
    def backspacePressed(self):
        top=self.stack.top()
        c=top.split(':')
        path=c[0]
        line=int(c[1])
        module=self.tree.getModule(path)
        if not module is None:
            self.loadModule(module)
            self.edit.code.setCurrentLine(path,line)
        self.stack.pop()
        

def moduleDoubleClick(item):
    gBrowser.loadModule(item.module)

def memberDoubleClick(item):
    gBrowser.gotoMember(item.member)

def addReference(refid,member):
    gBrowser.refs[refid]=member
