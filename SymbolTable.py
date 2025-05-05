class SymbolTable:
    def __init__(self):
        self.class_scope = {}
        self.subroutine_scope = {}
        self.counters = {'static':0,'field':0,'arg':0,'var':0}
    def startSubroutine(self):
        self.subroutine_scope.clear()
        self.counters['arg']=0
        self.counters['var']=0
    def define(self,name, type_, kind):
        idx=self.counters[kind]
        entry={'type':type_,'kind':kind,'index':idx}
        if kind in ('static','field'):
            self.class_scope[name]=entry
        else:
            self.subroutine_scope[name]=entry
        self.counters[kind]+=1
    def varCount(self,kind): return self.counters[kind]
    def kindOf(self,name):
        if name in self.subroutine_scope: return self.subroutine_scope[name]['kind']
        if name in self.class_scope: return self.class_scope[name]['kind']
        return None
    def typeOf(self,name):
        if name in self.subroutine_scope: return self.subroutine_scope[name]['type']
        if name in self.class_scope: return self.class_scope[name]['type']
        return None
    def indexOf(self,name):
        if name in self.subroutine_scope: return self.subroutine_scope[name]['index']
        if name in self.class_scope: return self.class_scope[name]['index']
        return None
