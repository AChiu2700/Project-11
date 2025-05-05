from VMWriter import VMWriter
from SymbolTable import SymbolTable

class VMCompilationEngine:
    # Map Jack kinds to VM segments
    segment_map = {
        'static': 'static',
        'field':  'this',
        'arg':    'argument',
        'var':    'local'
    }

    def __init__(self, tokenizer, symbol_table: SymbolTable, writer: VMWriter, class_name: str):
        self.tokenizer = tokenizer
        self.table = symbol_table
        self.writer = writer
        self.className = class_name
        self.labelCnt = 0
        # advance to first token
        self.tokenizer.advance()

    def _newLabel(self, base: str) -> str:
        lbl = f"{base}{self.labelCnt}"
        self.labelCnt += 1
        return lbl

    def compileClass(self):
        # skip 'class' className '{'
        self.tokenizer.advance()
        self.tokenizer.advance()
        self.tokenizer.advance()
        # compile class var declarations
        while self.tokenizer.token() in ('static', 'field'):
            self.compileClassVarDec()
        # compile each subroutine
        while self.tokenizer.token() in ('constructor', 'function', 'method'):
            self.compileSubroutine()
        # skip '}'
        self.tokenizer.advance()

    def compileClassVarDec(self):
        kind = self.tokenizer.token()
        self.tokenizer.advance()
        type_ = self.tokenizer.token(); self.tokenizer.advance()
        name = self.tokenizer.token()
        self.table.define(name, type_, kind)
        self.tokenizer.advance()
        while self.tokenizer.token() == ',':
            self.tokenizer.advance()
            name = self.tokenizer.token()
            self.table.define(name, type_, kind)
            self.tokenizer.advance()
        self.tokenizer.advance()  # ';'

    def compileSubroutine(self):
        subType = self.tokenizer.token()  # constructor|function|method
        self.tokenizer.advance()
        self.tokenizer.advance()          # return type
        name = self.tokenizer.token(); self.tokenizer.advance()

        # start subroutine scope
        self.table.startSubroutine()

        # parameter list
        self.tokenizer.advance()          # '('
        nArgs = self.compileParameterList()
        self.tokenizer.advance()          # ')'

        # subroutine body
        self.tokenizer.advance()          # '{'
        while self.tokenizer.token() == 'var':
            self.compileVarDec()
        nLocals = self.table.varCount('var')

        # function declaration
        funcName = f"{self.className}.{name}"
        self.writer.writeFunction(funcName, nLocals)

        # constructor: allocate fields and set this
        if subType == 'constructor':
            nFields = self.table.varCount('field')
            self.writer.writePush('constant', nFields)
            self.writer.writeCall('Memory.alloc', 1)
            self.writer.writePop('pointer', 0)

        # method: bind this to argument 0
        elif subType == 'method':
            self.writer.writePush('argument', 0)
            self.writer.writePop('pointer', 0)

        # compile statements
        self.compileStatements()
        # skip '}'
        self.tokenizer.advance()

    def compileParameterList(self) -> int:
        cnt = 0
        if self.tokenizer.token() != ')':
            type_ = self.tokenizer.token(); self.tokenizer.advance()
            name = self.tokenizer.token()
            self.table.define(name, type_, 'arg')
            self.tokenizer.advance(); cnt += 1
            while self.tokenizer.token() == ',':
                self.tokenizer.advance()
                type_ = self.tokenizer.token(); self.tokenizer.advance()
                name = self.tokenizer.token()
                self.table.define(name, type_, 'arg')
                self.tokenizer.advance(); cnt += 1
        return cnt

    def compileVarDec(self):
        self.tokenizer.advance()          # 'var'
        type_ = self.tokenizer.token(); self.tokenizer.advance()
        name = self.tokenizer.token()
        self.table.define(name, type_, 'var')
        self.tokenizer.advance()
        while self.tokenizer.token() == ',':
            self.tokenizer.advance()
            name = self.tokenizer.token()
            self.table.define(name, type_, 'var')
            self.tokenizer.advance()
        self.tokenizer.advance()          # ';'

    def compileStatements(self):
        while self.tokenizer.token() in ('let', 'if', 'while', 'do', 'return'):
            cmd = self.tokenizer.token()
            getattr(self, f"compile{cmd.capitalize()}")()

    def compileDo(self):
        self.tokenizer.advance()          # 'do'
        self.compileSubroutineCall()
        self.writer.writePop('temp', 0)
        self.tokenizer.advance()          # ';'

    def compileLet(self):
        self.tokenizer.advance()          # 'let'
        varName = self.tokenizer.token(); self.tokenizer.advance()
        isArray = False
        if self.tokenizer.token() == '[':
            isArray = True
            self.tokenizer.advance()
            self.compileExpression()
            self.tokenizer.advance()      # ']'
            seg = self.segment_map[self.table.kindOf(varName)]
            idx = self.table.indexOf(varName)
            self.writer.writePush(seg, idx)
            self.writer.writeArithmetic('add')
        self.tokenizer.advance()          # '='
        self.compileExpression()
        self.tokenizer.advance()          # ';'
        if isArray:
            self.writer.writePop('temp', 0)
            self.writer.writePop('pointer', 1)
            self.writer.writePush('temp', 0)
            self.writer.writePop('that', 0)
        else:
            seg = self.segment_map[self.table.kindOf(varName)]
            idx = self.table.indexOf(varName)
            self.writer.writePop(seg, idx)

    def compileWhile(self):
        start = self._newLabel('WHILE_EXP')
        end = self._newLabel('WHILE_END')
        self.writer.writeLabel(start)
        self.tokenizer.advance(); self.tokenizer.advance()
        self.compileExpression()
        self.tokenizer.advance()
        self.writer.writeArithmetic('not')
        self.writer.writeIf(end)
        self.tokenizer.advance()
        self.compileStatements()
        self.tokenizer.advance()
        self.writer.writeGoto(start)
        self.writer.writeLabel(end)

    def compileReturn(self):
        self.tokenizer.advance()          # 'return'
        if self.tokenizer.token() != ';':
            self.compileExpression()
        else:
            self.writer.writePush('constant', 0)
        self.writer.writeReturn()
        self.tokenizer.advance()          # ';'

    def compileIf(self):
        self.tokenizer.advance(); self.tokenizer.advance()
        self.compileExpression()
        self.tokenizer.advance()

        false_lbl = self._newLabel('IF_FALSE')
        end_lbl = self._newLabel('IF_END')

        self.writer.writeArithmetic('not')
        self.writer.writeIf(false_lbl)

        self.tokenizer.advance(); self.compileStatements(); self.tokenizer.advance()
        self.writer.writeGoto(end_lbl)

        self.writer.writeLabel(false_lbl)
        if self.tokenizer.token() == 'else':
            self.tokenizer.advance(); self.tokenizer.advance()
            self.compileStatements()
            self.tokenizer.advance()

        self.writer.writeLabel(end_lbl)

    def compileExpression(self):
        self.compileTerm()
        while self.tokenizer.token() in ('+', '-', '*', '/', '&', '|', '<', '>', '='):
            op = self.tokenizer.token(); self.tokenizer.advance()
            self.compileTerm()
            mapping = {
                '+': 'add', '-': 'sub',
                '*': 'call Math.multiply 2', '/': 'call Math.divide 2',
                '&': 'and', '|': 'or',
                '<': 'lt', '>': 'gt', '=': 'eq'
            }
            self.writer.writeArithmetic(mapping[op])

    def compileTerm(self):
        ttype = self.tokenizer.tokenType()
        token = self.tokenizer.token()
        if ttype == 'INT_CONST':
            self.writer.writePush('constant', int(token))
            self.tokenizer.advance()
        elif ttype == 'STRING_CONST':
            s = token.strip('"')
            self.writer.writePush('constant', len(s))
            self.writer.writeCall('String.new', 1)
            for ch in s:
                self.writer.writePush('constant', ord(ch))
                self.writer.writeCall('String.appendChar', 2)
            self.tokenizer.advance()
        elif token in ('true', 'false', 'null', 'this'):
            if token == 'true':
                self.writer.writePush('constant', 0)
                self.writer.writeArithmetic('not')
            elif token in ('false', 'null'):
                self.writer.writePush('constant', 0)
            else:
                self.writer.writePush('pointer', 0)
            self.tokenizer.advance()
        elif token == '(':
            self.tokenizer.advance(); self.compileExpression(); self.tokenizer.advance()
        elif token in ('-', '~'):
            op = token; self.tokenizer.advance(); self.compileTerm();
            self.writer.writeArithmetic('neg' if op == '-' else 'not')
        else:
            nxt = self.tokenizer.tokens[self.tokenizer.current_index + 1]
            if nxt == '[':
                var = token; self.tokenizer.advance(); self.tokenizer.advance()
                self.compileExpression(); self.tokenizer.advance()
                seg = self.segment_map[self.table.kindOf(var)]
                idx = self.table.indexOf(var)
                self.writer.writePush(seg, idx); self.writer.writeArithmetic('add')
                self.writer.writePop('pointer', 1); self.writer.writePush('that', 0)
            elif nxt in ('.', '('):
                self.compileSubroutineCall()
            else:
                seg = self.segment_map[self.table.kindOf(token)]
                idx = self.table.indexOf(token)
                self.writer.writePush(seg, idx); self.tokenizer.advance()

    def compileExpressionList(self) -> int:
        cnt = 0
        if self.tokenizer.token() != ')':
            self.compileExpression(); cnt += 1
            while self.tokenizer.token() == ',':
                self.tokenizer.advance(); self.compileExpression(); cnt += 1
        return cnt

    def compileSubroutineCall(self):
        name = self.tokenizer.token(); self.tokenizer.advance()
        nArgs = 0
        if self.tokenizer.token() == '.':
            self.tokenizer.advance()
            sub = self.tokenizer.token()
            if self.table.kindOf(name):
                seg = self.segment_map[self.table.kindOf(name)]
                idx = self.table.indexOf(name)
                self.writer.writePush(seg, idx)
                name = f"{self.table.typeOf(name)}.{sub}"
                nArgs += 1
            else:
                name = f"{name}.{sub}"
            self.tokenizer.advance()
        else:
            # method on this
            self.writer.writePush('pointer', 0)
            name = f"{self.className}.{name}"
            nArgs += 1
        self.tokenizer.advance()  # '('
        n = self.compileExpressionList()
        self.tokenizer.advance()  # ')'
        self.writer.writeCall(name, nArgs + n)
