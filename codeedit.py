from PySide import QtCore
from PySide import QtGui
import re

identifier = re.compile(r"([^\d\W]\w*)")

class CodeView(QtGui.QWidget):
    """ A custom widget that shows code, breakpoints and current position """
    
    def __init__(self,scrollArea,parent=None):
        super(CodeView,self).__init__(parent)
        self.scrollArea=scrollArea
        self.updateScrolling=False
        self.tipVisible=False
        self.spacing=0
        self.currentLine=-1
        self.boundingRect=QtCore.QRect(0,0,200,200)
        self.setMinimumSize(QtCore.QSize(200,200))
        self.drawLineNumbers=True
        self.lineNumMargin=0
        self.setFont(QtGui.QFont('monospace',18))
        self.setMouseTracking(True)
        self.wordUnderCursor=''
        self.hoverCount=1000
        self.timer=QtCore.QTimer(self)
        self.timer.timeout.connect(self.onTimer)
        self.timer.start(100)
        self.hoverPos=QtCore.QPoint(0,0)
        self.highlights={}
        self.text=None
        self.path=''
        self.fm=None
        
    def setFont(self,font):
        """ Set the font used to draw text """
        self.font=font
        self.fontMetrics=QtGui.QFontMetrics(self.font)
        self.repaint()
        
    def closingApp(self):
        """ Called by application before closing its main window """
        self.timer.stop()
        
    def load(self,path):
        self.setText(path,open(path,'r').read())        
        
    def setText(self,path,text):
        """ Sets the source code text for the current file

        text can be either a \n delimited string, or a list of line strings        
        
        """
        self.path=path
        self.highlights={}
        self.currentLine=-1
        self.boundingRect=QtCore.QRect(0,0,1,1)
        if type(text) is str:
            self.text=text.split('\n')
        elif type(text) is list:
            self.text=text
        else:
            raise Exception('Invalid argument to CodeView.setText')

    def addHighlight(self,name,line,color,refid):
        if not line in self.highlights:
            self.highlights[line]={}
        hdict=self.highlights.get(line)
        hdict[name]=(color,refid)
        
    def addRefHighlights(self,name,startLine,endLine,color,refid):
        nameParts=re.findall(identifier,name)
        name=nameParts[-1]
        print "Adding ref '{}' between lines {},{}".format(name,startLine,endLine)
        for line in xrange(startLine,endLine):
            text=self.text[line-1]
            parts=re.split(identifier,text)
            for part in parts:
                if part==name:
                    self.addHighlight(part,line,color,refid)

    def setCurrentLine(self,path,line):
        """ Set the index (1 based) of the active line

        This is called every time the current line changes.  If the currently
        viewed file is not the active source, the current line is not updated        
        
        """
        if self.path==path:
            self.currentLine=line
            self.updateScrolling=True
            self.repaint()

    def isIdentChar(self,s):
        """ A predicate of valid characters in C/C++ identifiers """
        return s.isalpha() or s=='_' or s.isdigit()

    def extractWord(self,line,index):
        """ Given a line string and column position, extract identifier 

        Returns an empty string if an identifier cannot be found in
        the specified location.
        
        """
        if not self.isIdentChar(line[index]):
            return ""
        start=index
        while start>0:
            start-=1
            if not self.isIdentChar(line[start]):
                start+=1
                break
        stop=index
        while stop<len(line):
            stop+=1
            if stop==len(line):
                break
            if not self.isIdentChar(line[stop]):
                break
        word=line[start:stop]
        if word[0].isdigit():
            return ""
        return word
        
    def getMouseLine(self,event):
        """ Convert mouse event y pixel position to a line number (0 based) """
        y=event.y()
        return y/self.spacing
        
    def mousePressEvent(self,event):
        """ Checks for left click and follow references """
        if event.button()==QtCore.Qt.MouseButton.LeftButton:
            line=self.getMouseLine(event)+1
            if len(self.wordUnderCursor)>0:
                hdict=self.highlights.get(line)
                if self.wordUnderCursor in hdict:
                    refid=(hdict.get(self.wordUnderCursor))[1]
                    if not refid is None:
                        import codebrowser
                        codebrowser.gBrowser.gotoRef(refid,line)
        super(CodeView,self).mousePressEvent(event)

    def mouseMoveEvent(self,event):
        """ Track mouse movements to identify hover events """
        if self.spacing>0:
            if self.tipVisible:
                # Clear old tool tip
                QtGui.QToolTip.showText(self.hoverPos,"")
                self.tipVisible=False
            if event.button()==QtCore.Qt.NoButton and event.type()==QtCore.QEvent.MouseMove:
                # Simple move.  Reset the counter to wait for hover
                self.hoverCount=0
                self.hoverPos=event.pos()
                
                
            # Find column by checking text width incrementally until
            # it is over the x position (without the margin)                
            x=(event.x()-self.lineNumMargin)
            lineIndex=self.getMouseLine(event)
            self.wordUnderCursor=''
            if lineIndex<len(self.text) and lineIndex>=0:
                line=self.text[lineIndex]
                n=len(line)
                for i in xrange(1,n):
                    w=self.fontMetrics.width(line[0:i])
                    if w>x:
                        # column position found.  Extract identifier
                        if line[i-1]!=' ':
                            self.wordUnderCursor=self.extractWord(line,i-1)
                        break
        super(CodeView,self).mouseMoveEvent(event)

    def getCurrentWord(self):
        """ Returns the current word calculated during mouse move """
        return self.wordUnderCursor
            
    def drawHighlights(self,qp,x,y,line,highlights):
        parts=re.split(identifier,line)
        black=QtGui.QColor(0,0,0)
        fm=qp.fontMetrics()
        w=fm.boundingRect('a').width()
        for part in parts:
            if part in highlights:
                color=(highlights.get(part))[0]
                qp.setPen(color)
            else:
                qp.setPen(black)
            qp.drawText(x,y,part)
            x+=len(part)*w
            
    def paintEvent(self,event):
        qp=QtGui.QPainter()
        qp.begin(self)
        if not self.text is None:
            self.draw(qp,event.rect())
        qp.end()
        
    def draw(self,qp,drawRect):
        """ Draw the source code text, breakpoints and current line mark """
        qp.setFont(self.font)
        fm=qp.fontMetrics()
        self.fm=fm
        ascent=fm.ascent()
        descent=fm.descent()
        self.spacing=fm.lineSpacing()
        # Find the range of visible lines, to find out whether the active
        # line is not visible (and then center it)
        scrollPosition=self.scrollArea.verticalScrollBar().value()
        firstVisibleLine=(scrollPosition+self.spacing/2) / self.spacing
        windowHeight=self.scrollArea.height()
        visibleLines=windowHeight / self.spacing - 1
        lastVisibleLine=firstVisibleLine+visibleLines-1
        y=self.spacing
        margin=8 * fm.maxWidth()
        self.lineNumMargin=0
        if self.drawLineNumbers:
            self.lineNumMargin=8*fm.maxWidth()
            margin+=self.lineNumMargin
        maxWidth=self.boundingRect.width()
        boundingHeight=len(self.text)*self.spacing
        linenum=1
        # Get the current file breakpoints.  Default to empty
        for line in self.text:
            lineRect=fm.boundingRect(line)
            if lineRect.width() > maxWidth:
                maxWidth=lineRect.width()
            x=0
            # Draw line numbers
            if self.drawLineNumbers:
                s=str(linenum)
                s=' '*(6-len(s))+s
                qp.drawText(0,y,s)
                x+=self.lineNumMargin
            qp.setPen(QtGui.QColor(0,0,0))
            # Draw the actual line text
            if linenum in self.highlights:
                self.drawHighlights(qp,x,y,line,self.highlights.get(linenum))
            else:
                qp.drawText(x,y,line)
            qp.setPen(QtGui.QColor(0,0,0))
            y+=self.spacing
            linenum+=1
        rc=False
        if boundingHeight>self.boundingRect.height() or maxWidth>self.boundingRect.width():
            self.boundingRect=QtCore.QRect(0,0,maxWidth,boundingHeight)
            self.resize(QtCore.QSize(maxWidth+margin,boundingHeight))
            rc=True
        # Center around active line, if it is out of the visible range
        if self.updateScrolling:
            self.updateScrolling=False
            if self.currentLine<firstVisibleLine or self.currentLine>lastVisibleLine:
                newFirst=self.currentLine-visibleLines/2
                if newFirst<0:
                    newFirst=0
                self.scrollArea.verticalScrollBar().setValue(newFirst*self.spacing)
        return rc
        
    def leaveEvent(self,event):
        """ Mouse left view, reset the hover counter to infinity """
        self.hoverCount=100
        super(CodeView,self).leaveEvent(event)

    def mouseDoubleClickEvent(self,event):
        """ Double click toggles breakpoint in the line """
        if not self.text is None and type(self.text) is list:
            y=event.y()
            lineIndex=y/self.spacing
            if lineIndex>=0 and lineIndex<len(self.text) and len(self.path)>0:
                self.toggleBreakpoint(lineIndex)
        super(CodeView,self).mouseDoubleClickEvent(event)
        
    def onTimer(self):
        """ Hover detection timer.  Called every 100ms """
        if self.hoverCount<10:
            self.hoverCount+=1
            if self.hoverCount==5:
                self.generateTooltip()
            
    def generateTooltip(self):
        """ Hover above a variable.  Generate an evaluation tooltip """
        if len(self.wordUnderCursor)>0:
                tip = '{}'.format('value')
                pos=self.mapToGlobal(self.hoverPos)
                QtGui.QToolTip.showText(pos,tip)
                self.tipVisible=True

        
class CodeEditor(QtGui.QScrollArea):
    """ Wrapper above the CodeView, to provide scrolling """
    
    def __init__(self,parent=None):
        super(CodeEditor,self).__init__(parent)
        self.setMinimumSize(QtCore.QSize(800,600))
        self.code=CodeView(self)
        self.setWidget(self.code)

    def closingApp(self):
        """ Called by the application before closing the main window """
        self.code.closingApp()
        
    def setText(self,path,text):
        self.code.setText(path,text)
        self.code.repaint()


if __name__=='__main__':
    """ Small unit test """
    import sys
    app=QtGui.QApplication(sys.argv)
    w=QtGui.QMainWindow()
    e=CodeEditor()
    e.setText('codeedit.py',open('codeedit.py','r').read())
    w.setCentralWidget(e)
    w.show()
    app.exec_()
