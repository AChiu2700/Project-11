class CompilationEngine:
    def __init__(self, tokenizer, output_file):
        self.tokenizer = tokenizer
        self.output = open(output_file, 'w')
        self.indent_level = 0
        self.tokenizer.advance()

    def _write_indent(self):
        self.output.write('  ' * self.indent_level)

    def write_start(self, tag):
        self._write_indent()
        self.output.write(f"<{tag}>\n")
        self.indent_level += 1

    def write_end(self, tag):
        self.indent_level -= 1
        self._write_indent()
        self.output.write(f"</{tag}>\n")

    def write_token(self, tag, value):
        self._write_indent()
        self.output.write(f"<{tag}> {value} </{tag}>\n")

    def writeTokenAndAdvance(self):
        token = self.tokenizer.token()
        ttype = self.tokenizer.tokenType()
        # Map JackTokenizer types to XML tags
        tag_map = {
            'KEYWORD': 'keyword',
            'SYMBOL': 'symbol',
            'IDENTIFIER': 'identifier',
            'INT_CONST': 'integerConstant',
            'STRING_CONST': 'stringConstant'
        }
        tag = tag_map[ttype]
        value = token
        if token == '<': value = '&lt;'
        elif token == '>': value = '&gt;'
        elif token == '&': value = '&amp;'
        elif tag == 'stringConstant': value = token.strip('"')
        self.write_token(tag, value)
        self.tokenizer.advance()

    def compileClass(self):
        self.write_start('class')
        # 'class' className '{'
        for _ in range(3):
            self.writeTokenAndAdvance()
        # classVarDec*
        while self.tokenizer.token() in ('static', 'field'):
            self.compileClassVarDec()
        # subroutineDec*
        while self.tokenizer.token() in ('constructor', 'function', 'method'):
            self.compileSubroutine()
        # '}' class end
        self.writeTokenAndAdvance()
        self.write_end('class')
        self.output.close()

    def compileClassVarDec(self):
        self.write_start('classVarDec')
        # ('static'|'field') type varName (',' varName)* ';'
        for _ in range(3):
            self.writeTokenAndAdvance()
        while self.tokenizer.token() == ',':
            self.writeTokenAndAdvance()
            self.writeTokenAndAdvance()
        self.writeTokenAndAdvance()
        self.write_end('classVarDec')

    def compileSubroutine(self):
        self.write_start('subroutineDec')
        # ('constructor'|'function'|'method') returnType subroutineName
        for _ in range(3):
            self.writeTokenAndAdvance()
        # '('
        self.writeTokenAndAdvance()
        self.compileParameterList()
        # ')'
        self.writeTokenAndAdvance()
        # subroutine body
        self.write_start('subroutineBody')
        # '{'
        self.writeTokenAndAdvance()
        # varDec*
        while self.tokenizer.token() == 'var':
            self.compileVarDec()
        # statements
        self.compileStatements()
        # '}'
        self.writeTokenAndAdvance()
        self.write_end('subroutineBody')
        self.write_end('subroutineDec')

    def compileParameterList(self):
        self.write_start('parameterList')
        if self.tokenizer.token() != ')':
            # type varName (',' type varName)*
            self.writeTokenAndAdvance()
            self.writeTokenAndAdvance()
            while self.tokenizer.token() == ',':
                self.writeTokenAndAdvance()
                self.writeTokenAndAdvance()
                self.writeTokenAndAdvance()
        self.write_end('parameterList')

    def compileVarDec(self):
        self.write_start('varDec')
        # 'var' type varName (',' varName)* ';'
        for _ in range(3):
            self.writeTokenAndAdvance()
        while self.tokenizer.token() == ',':
            self.writeTokenAndAdvance()
            self.writeTokenAndAdvance()
        self.writeTokenAndAdvance()
        self.write_end('varDec')

    def compileStatements(self):
        self.write_start('statements')
        while self.tokenizer.token() in ('let', 'if', 'while', 'do', 'return'):
            stmt = self.tokenizer.token()
            getattr(self, f'compile{stmt.capitalize()}')()
        self.write_end('statements')

    def compileLet(self):
        self.write_start('letStatement')
        # 'let' varName ('[' expression ']')? '=' expression ';'
        self.writeTokenAndAdvance()  # let
        self.writeTokenAndAdvance()  # varName
        if self.tokenizer.token() == '[':
            self.writeTokenAndAdvance()
            self.compileExpression()
            self.writeTokenAndAdvance()
        self.writeTokenAndAdvance()  # '='
        self.compileExpression()
        self.writeTokenAndAdvance()  # ';'
        self.write_end('letStatement')

    def compileIf(self):
        self.write_start('ifStatement')
        # 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        self.writeTokenAndAdvance()  # if
        self.writeTokenAndAdvance()  # '('
        self.compileExpression()
        self.writeTokenAndAdvance()  # ')'
        self.writeTokenAndAdvance()  # '{'
        self.compileStatements()
        self.writeTokenAndAdvance()  # '}'
        if self.tokenizer.token() == 'else':
            self.writeTokenAndAdvance()  # else
            self.writeTokenAndAdvance()  # '{'
            self.compileStatements()
            self.writeTokenAndAdvance()  # '}'
        self.write_end('ifStatement')

    def compileWhile(self):
        self.write_start('whileStatement')
        # 'while' '(' expression ')' '{' statements '}'
        self.writeTokenAndAdvance()
        self.writeTokenAndAdvance()
        self.compileExpression()
        self.writeTokenAndAdvance()
        self.writeTokenAndAdvance()
        self.compileStatements()
        self.writeTokenAndAdvance()
        self.write_end('whileStatement')

    def compileDo(self):
        self.write_start('doStatement')
        # 'do' subroutineCall ';'
        self.writeTokenAndAdvance()
        self.compileSubroutineCall()
        self.writeTokenAndAdvance()
        self.write_end('doStatement')

    def compileReturn(self):
        self.write_start('returnStatement')
        # 'return' expression? ';'
        self.writeTokenAndAdvance()
        if self.tokenizer.token() != ';':
            self.compileExpression()
        self.writeTokenAndAdvance()
        self.write_end('returnStatement')

    def compileExpression(self):
        self.write_start('expression')
        self.compileTerm()
        while self.tokenizer.token() in ['+', '-', '*', '/', '&', '|', '<', '>', '=']:
            self.writeTokenAndAdvance()
            self.compileTerm()
        self.write_end('expression')

    def compileTerm(self):
        self.write_start('term')
        tokenType = self.tokenizer.tokenType()
        token = self.tokenizer.token()
        # integer constant
        if tokenType == 'INT_CONST':
            self.writeTokenAndAdvance()
        # string constant
        elif tokenType == 'STRING_CONST':
            self.writeTokenAndAdvance()
        # keyword constant
        elif token in ('true', 'false', 'null', 'this'):
            self.writeTokenAndAdvance()
        # '(' expression ')'
        elif token == '(':  
            self.writeTokenAndAdvance()
            self.compileExpression()
            self.writeTokenAndAdvance()
        # unary op term
        elif token in ('-', '~'):
            self.writeTokenAndAdvance()
            self.compileTerm()
        # varName '[' expression ']'
        elif self.tokenizer.tokens[self.tokenizer.current_index+1] == '[':
            self.writeTokenAndAdvance()  # varName
            self.writeTokenAndAdvance()  # '['
            self.compileExpression()
            self.writeTokenAndAdvance()  # ']'
        # subroutine call
        elif self.tokenizer.tokens[self.tokenizer.current_index+1] in ('.', '('):
            self.compileSubroutineCall()
        # varName
        else:
            self.writeTokenAndAdvance()
        self.write_end('term')

    def compileExpressionList(self):
        self.write_start('expressionList')
        if self.tokenizer.token() != ')':
            self.compileExpression()
            while self.tokenizer.token() == ',':
                self.writeTokenAndAdvance()
                self.compileExpression()
        self.write_end('expressionList')

    def compileSubroutineCall(self):
        # subroutineName or className.subroutineName
        self.writeTokenAndAdvance()  # identifier
        if self.tokenizer.token() == '.':
            self.writeTokenAndAdvance()
            self.writeTokenAndAdvance()
        # '('
        self.writeTokenAndAdvance()
        self.compileExpressionList()
        # ')'
        self.writeTokenAndAdvance()
