#!/usr/bin/env python
import os
import sys
import re
import xml.etree.ElementTree as ET

def scanXMLDirs(base):
    dirs=[]
    try:
        names=os.listdir(base)
        if 'xml' in names:
            dirs.append(os.path.join(base,'xml'))
        for name in names:
            dirs=dirs+scanXMLDirs(os.path.join(base,name))
    except OSError:
        pass
    return dirs

class Reference:
    def __init__(self,root):
        self.refid=root.get('refid')
        self.ident=root.text
        
    def save(self):
        root=ET.Element('reference')
        root.set('refid',self.refid)
        root.text=self.ident
        return root

class Member:
    def __init__(self,module,root):
        self.module=module
        if root.tag=="memberdef":
            self.loadFromXMLFile(root)
        elif root.tag=="member":
            self.load(root)
        elif root.tag=="codeline":
            print "Loading codeline"
        
    def assign(self,id,name,line):
        self.id=id
        self.name=name
        self.args=''
        self.filepath=self.module.srcpath
        self.line=line
        self.bodyend=line+1
        self.refs=[]
        
    def loadFromXMLFile(self,root):
        self.id=root.get('id')
        self.name=root.find('name').text
        self.args=root.find('argsstring')
        if not self.args is None:
            self.args=self.args.text
        if self.args is None:
            self.args=''
        loc=root.find('location')
        self.filepath=loc.get('file')
        self.line=int(loc.get('line'))
        try:
            self.bodyend=int(loc.get('bodyend'))
        except Exception:
            self.bodyend=self.line+1
        self.refs=[]
        allrefs=root.findall('references')
        self.readRefs(allrefs)
        
    def readRefs(self,refs):
        for ref in refs:
            self.refs.append(Reference(ref))
            
    def save(self):
        root=ET.Element('member')
        root.set('id',self.id)
        root.set('name',self.name)
        root.set('args',self.args)
        root.set('filepath',self.filepath)
        root.set('line',str(self.line))
        root.set('bodyend',str(self.bodyend))
        for ref in self.refs:
            root.append(ref.save())
        return root
        
    def load(self,root):
        self.refs=[]
        self.id=root.get('id')
        self.name=root.get('name')
        self.args=root.get('args')
        self.filepath=root.get('filepath')
        self.line=int(root.get('line'))
        self.bodyend=int(root.get('bodyend'))
        allrefs=root.findall('reference')
        for r in allrefs:
            self.refs.append(Reference(r))
            
        

class Module:
    def __init__(self,src):
        if type(src) is str:
            self.loadFromXMLFile(src)
        else:
            self.load(src)
            
    def loadFromXMLFile(self,filepath):
        print "Loading {}".format(filepath)
        self.srcpath=""
        self.srcname=""
        tree=ET.parse(filepath)
        root=tree.getroot()
        root=root.find('compounddef')
        if root is None:
            raise Exception('File has no compoundDef')
        self.id=root.get('id')
        self.members=[]
        try:
            allsec=root.findall('sectiondef')
            for sec in allsec:
                kind=sec.get('kind')
                if kind=='var' or kind=='func' or kind=='define':
                    self.readSection(sec)
        except Exception,e:
            print "Exception reading sections for module {}\n{}".format(filepath,e)
        listing=root.find('programlisting')
        if not listing is None:
            self.loadCodeLines(listing)
        self.srcpath=self.members[0].filepath
        self.srcname=(self.srcpath.split('/'))[-1]
        
    def loadCodeLines(self,listing):
        codelines=listing.findall('codeline')
        for cl in codelines:
            refid=cl.get('refid')
            if not refid is None:
                line=int(cl.get('lineno'))
                for r in cl.iter('ref'):
                    if r.get('refid')==refid:
                        m=Member(self,ET.Element('stub'))
                        m.assign(refid,r.text,line)
                        self.members.append(m)
                        

    def readSection(self,sec):
        all=sec.findall('memberdef')
        for member in all:
            self.members.append(Member(self,member))
            
    def sort(self):
        self.members.sort(key=lambda member: member.name)
            
    def save(self):
        root=ET.Element('module')
        root.set('id',self.id)
        root.set('srcpath',self.srcpath)
        root.set('srcname',self.srcname)
        for member in self.members:
            root.append(member.save())
        return root
        
    def load(self,root):
        self.id=root.get('id')
        self.srcpath=root.get('srcpath')
        self.srcname=root.get('srcname')
        self.members=[]
        members=root.findall('member')
        for m in members:
            self.members.append(Member(self,m))
        
def readXMLDirs(dirs):
    modules=[]
    for dir in dirs:
        files=os.listdir(dir)
        #files=files[0:25]
        for filename in files:
            if filename.endswith('.xml'):
                try:
                    filepath=os.path.join(dir,filename)
                    modules.append(Module(filepath))
                except Exception:
                    pass
    return modules
    
def save(modules):
    root=ET.Element('modules')
    for m in modules:
        root.append(m.save())
    return root
    
def load():
    try:
        root=ET.parse('cb.xml')
        print 'Loading from cb.xml'
        modules=[]
        allmods=root.findall('module')
        for m in allmods:
            modules.append(Module(m))
        return modules
    except IOError:
        return None

def sortAll(all):
    all.sort(key=lambda m: m.srcname)
    for m in all:
        m.sort()


def readAll():
    all=load()
    if all is None:
        dirs=scanXMLDirs('.')
        all=readXMLDirs(dirs)
        print 'Writing to cb.xml'
        ET.ElementTree(save(all)).write('cb.xml')
    sortAll(all)
    return all

def main():
    readAll()
    
if __name__=="__main__":
    main()
    