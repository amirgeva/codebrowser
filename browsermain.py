from PySide import QtCore
from PySide import QtGui
import sys
import codebrowser

def main():
    app=QtGui.QApplication(sys.argv)
    codebrowser.gBrowser=codebrowser.CodeBrowser()
    codebrowser.gBrowser.tree.loadCodeTree()
    codebrowser.gBrowser.show()
    app.exec_()	


if __name__=='__main__':
    main()









