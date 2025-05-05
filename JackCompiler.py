import sys
import os
from JackTokenizer import JackTokenizer
from SymbolTable import SymbolTable
from VMWriter import VMWriter
from VMCompilationEngine import VMCompilationEngine

def main(path):
    # Determine input .jack files and output .vm file
    if os.path.isdir(path):
        jack_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.jack')]
        out_path = os.path.join(path, os.path.basename(path) + '.vm')
    else:
        jack_files = [path]
        out_path = path.replace('.jack', '.vm')

    writer = VMWriter(out_path)
    # Bootstrap: call Sys.init
    writer.writeInit()
    for f in jack_files:
        tokenizer = JackTokenizer(f)
        class_name = os.path.splitext(os.path.basename(f))[0]
        symbol_table = SymbolTable()
        engine = VMCompilationEngine(tokenizer, symbol_table, writer, class_name)
        engine.compileClass()

    writer.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py <file.jack|directory>")
    else:
        main(sys.argv[1])