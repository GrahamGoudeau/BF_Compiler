import sys
import os
import subprocess
import re

operators = ['+', '-', '<', '>', '[', ']', '.', ',', '\n', '\t', ' ']
comment = '#'

OUT_FILE_NAME = ""

ARR_SIZE = 30000

C_SIG = False

# return the open file, or exit if problem with file
#def setup():
def print_usage():
    print("Usage:\tcompile.py [input_file.bf] [desired output name] [-flags]")
    print("Flags:\t-rs=# [set mem tape size; default {0}]".format(ARR_SIZE))
    print("\t-c [preserve c code output]")
    sys.exit()

def set_options():
    global OUT_FILE_NAME
    global ARR_SIZE
    global C_SIG
    if len(sys.argv) < 3: 
        print_usage()
    if sum(map(num_bf_files, sys.argv)) != 1:
        print_usage()

    # set mem tape size and c preservation flag
    for arg in sys.argv:
        if arg == "-c":
            C_SIG = True
        size_regex = re.search(r'-rs=([0-9]+)', arg)
        try:
            # the integer is in re.group(1)
            ARR_SIZE = int(size_regex.group(1))
        except AttributeError:
            continue 

# find .bf file, and try to open it
def get_source_file():
    for arg in sys.argv:
        if arg.split(".")[-1] == 'bf':
            try:
                file = open(arg, 'r')
            except IOError:
                print("Problem with file: {0}".format(arg))
                sys.exit()
            
            return file

# find out file name; only argument without a '.' or '='
def get_out_file_name():
    global OUT_FILE_NAME
    for arg in sys.argv:
        if arg != sys.argv[0] and not ('.' in arg) and not ('=' in arg):
            if arg != '-c':
                OUT_FILE_NAME = arg

# return 1 on .bf file, 0 otherwise
def num_bf_files(option):
    if option.split(".")[-1] == 'bf': return 1
    else: return 0 

def main():
    global OUT_FILE_NAME
    global ARR_SIZE

    # read flags, reset array size if necessary
    set_options()

    # set the out file name
    get_out_file_name()

    # open source file, exiting if error with file
    file = get_source_file()

    # delete comments
    pre_proc = preprocess(file.read()) 

    # print error messages for syntax errors and exit if errors
    syntax_report(pre_proc)

    # check brackets matched; exit if unmatched
    check_brackets(pre_proc)

    # compile
    compile(pre_proc)

    file.close()

def preprocess(code):
    # remove comments and rest of line until \n
    for i in range(len(code)):
        if i < len(code) and code[i] == comment:
            # splice out comment character and rest of the line
            code = code[:i] + code[(i + 1):]
            while i < len(code) and code[i] != '\n':
                code = code[:i] + code[(i + 1):]

    return code


def syntax_report(code):
    if (syntax_valid(code)):
        return

    # search for syntax errors, report when found
    line_num = 1
    col = 1
    for i in range(len(code)):
        # increment line number and column
        if code[i] == '\n': 
            line_num += 1
            col = 1
            continue
        
        if code[i] not in operators:
            print("Syntax error at line " + str(line_num) + 
                    " col " + str(col) + ": " + code[i])
        col += 1

    sys.exit()

def check_brackets(code):
    stack = []

    line_num = 1
    col = 1
    for i in range(len(code)):
        # reset error report line/col numbers on newline
        if code[i] == '\n':
            line_num += 1
            col = 1
            continue

        if code[i] == '[':
            stack.append(code[i])
        elif code[i] == ']' and len(stack) != 0: 
            stack.pop()
        elif code[i] == ']' and len(stack) == 0: 
            print("Mismatched brackets at " + str(line_num) +
                    " col " + str(col))
            sys.exit()

        col += 1

    if len(stack) != 0:
        print("Too many open brackets")
        sys.exit()

def syntax_valid(code):
    return all(map(lambda c: c in operators, code)) 

def compile(code):
    global ARR_SIZE 
    c_file_name = OUT_FILE_NAME + '.c'
    out_file = open(c_file_name, 'w')

    write_header(out_file)

    generate_code(code, out_file)

    out_file.write("\treturn EXIT_SUCCESS;")
    out_file.write("}")
    out_file.close()

    # compile c code
    gcc_compile(out_file, c_file_name)

    # remove leftover c file
    if not C_SIG:
        os.remove(c_file_name)

def gcc_compile(out_file, c_file_name):
    cmd = ["gcc", "-O0", "-g", c_file_name, "-o", OUT_FILE_NAME]
    p = subprocess.Popen(cmd)
    p.wait()

def generate_code(code, out_file):
    num_indent = 1
    for c in code:
        for _ in range(num_indent):
            if c != ' ' and c != '\n' and c != '\t':
                out_file.write("\t")
        if c == '+':
            out_file.write("mem_tape[tape_head]++;\n")
        elif c == '-':
            out_file.write("mem_tape[tape_head]--;\n")
        elif c == '>':
            out_file.write("tape_head++;\n")
        elif c == '<':
            out_file.write("tape_head--;\n")
        elif c == '.':
            out_file.write("fprintf(stdout, \"%c\", mem_tape[tape_head]);\n")
        elif c == '[':
            out_file.write("while (mem_tape[tape_head] != 0) {\n")
            num_indent += 1
        elif c == ']':
            num_indent -= 1
            out_file.write("}\n")
        elif c == ',':
            out_file.write("mem_tape[tape_head] = getchar();\n")

def write_header(out_file):
    out_file.write("#include <stdlib.h>\n")
    out_file.write("#include <stdio.h>\n")
    out_file.write("#include <stdint.h>\n")
    out_file.write("\n\nint main(int argc, char **argv)\n{\n")
    out_file.write("\n\tchar mem_tape[{0}];\n".format(ARR_SIZE))
    out_file.write("\tsize_t tape_head = 0;\n")
    out_file.write("\tint i;\n")
    out_file.write("\tfor (i = 0; i < {0}; i++) \
mem_tape[i] = 0;\n".format(ARR_SIZE))

    
if __name__ == "__main__":
    main()
