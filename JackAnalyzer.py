import sys
import os
from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine

def main(input_path):
    if input_path.endswith(".jack"):
        jack_files = [input_path]
    else:
        jack_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith(".jack")]

    for file in jack_files:
        print(f"Processing: {file}")

        # Generate Token XML
        tokenizer = JackTokenizer(file)
        token_output = file.replace(".jack", "T.xml")
        with open(token_output, 'w') as out:
            out.write("<tokens>\n")

            # --- Correct XML Tag Mapping ---
            tag_map = {
                "KEYWORD": "keyword",
                "SYMBOL": "symbol",
                "IDENTIFIER": "identifier",
                "INT_CONST": "integerConstant",
                "STRING_CONST": "stringConstant"
            }

            while tokenizer.hasMoreTokens():
                tokenizer.advance()
                token = tokenizer.token()
                token_type = tokenizer.tokenType()

                xml_tag = tag_map[token_type]

                clean_token = token
                if token == '<':
                    clean_token = '&lt;'
                elif token == '>':
                    clean_token = '&gt;'
                elif token == '&':
                    clean_token = '&amp;'
                elif xml_tag == "stringConstant":
                    clean_token = token.strip('"')

                # Indented output for tokenizer XML
                out.write(f"  <{xml_tag}> {clean_token} </{xml_tag}>\n")

            out.write("</tokens>\n")

        # Generate Parse Tree XML
        tokenizer = JackTokenizer(file)  # Reset tokenizer
        parse_output = file.replace(".jack", ".xml")
        compiler = CompilationEngine(tokenizer, parse_output)
        compiler.compileClass()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python JackAnalyzer.py <input_file_or_directory>")
    else:
        main(sys.argv[1])