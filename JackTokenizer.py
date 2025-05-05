import re

class JackTokenizer:
    def __init__(self, input_file):
        with open(input_file, 'r') as f:
            self.data = f.read()

        self.tokens = self.tokenize()
        # print(f"DEBUG: Total tokens = {len(self.tokens)}")
        self.current_index = -1
        self.current_token = None


    def tokenize(self):
        # Remove all comments (single-line, multi-line, doc)
        code = re.sub(r'//.*', '', self.data)
        code = re.sub(r'/\*\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

        symbols = '{}()[].,;+-*/&|<>=~'
        tokens = []
        i = 0
        while i < len(code):
            c = code[i]

            if c.isspace():
                i += 1
                continue
            elif c in symbols:
                tokens.append(c)
                i += 1
            elif c == '"':
                j = i + 1
                while code[j] != '"':
                    j += 1
                tokens.append(code[i:j+1])
                i = j + 1
            elif c.isdigit():
                j = i
                while j < len(code) and code[j].isdigit():
                    j += 1
                tokens.append(code[i:j])
                i = j
            elif c.isalpha() or c == '_':
                j = i
                while j < len(code) and (code[j].isalnum() or code[j] == '_'):
                    j += 1
                tokens.append(code[i:j])
                i = j
            else:
                i += 1  # Skip unknown chars (shouldn't happen)

        return tokens


    def hasMoreTokens(self):
        return self.current_index < len(self.tokens) - 1

    def advance(self):
        if self.hasMoreTokens():
            self.current_index += 1
            self.current_token = self.tokens[self.current_index]
        else:
            self.current_token = None

    def tokenType(self):
        token = self.current_token
        if token is None:
            raise ValueError("No current token. Did you forget to call advance()?")

        keywords = {"class", "constructor", "function", "method", "field", "static", "var",
                    "int", "char", "boolean", "void", "true", "false", "null", "this",
                    "let", "do", "if", "else", "while", "return"}
        symbols = "{}()[].,;+-*/&|<>=~"

        if token in keywords:
            return "KEYWORD"
        elif token in symbols:
            return "SYMBOL"
        elif token.isdigit():
            return "INT_CONST"
        elif token.startswith('"'):
            return "STRING_CONST"
        else:
            return "IDENTIFIER"

    def token(self):
        return self.current_token
