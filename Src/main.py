import re
import ast

class LaverParser:
    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.arrays = {}
        self.current_function_name = None
        self.patterns = {
            r'p: "(.+)"': lambda match: ast.Expr(ast.Call(func=ast.Name(id='print', ctx=ast.Load()),
                                                          args=[ast.Str(s=match.group(1))],
                                                          keywords=[])),
            r'var ([^ ]+) = "(.+)"': lambda match: self.handle_variable_definition(match.group(1), match.group(2)),
            r'array ([^:]+): \[(.+)\]': lambda match: self.handle_array_definition(match.group(1), match.group(2)),
            r'i: &([^ ]+)': lambda match: self.handle_variable_reference(match.group(1)),
            r'if: &([^ ]+) == "(.+)" {': lambda match: ast.If(test=ast.Compare(left=self.handle_variable_reference(match.group(1)),
                                                                                   ops=[ast.Eq()],
                                                                                   comparators=[ast.Str(s=match.group(2))]),
                                                                 body=[],
                                                                 orelse=[]),
            r'else {': lambda match: ast.If(test=None, body=[], orelse=[]),
            r'elseif': lambda match: ast.Pass(),  # ignore 'elseif' keyword
            r'for: {([^;]+);([^;]+);([^}]+)} {': lambda match: ast.For(target=ast.Name(id='_', ctx=ast.Store()),
                                                                         iter=ast.Call(func=ast.Name(id='range', ctx=ast.Load()),
                                                                                       args=[ast.Num(n=int(match.group(1))),
                                                                                             ast.Num(n=int(match.group(2))),
                                                                                             ast.Num(n=int(match.group(3)))],
                                                                                       keywords=[]),
                                                                         body=[],
                                                                         orelse=[]),
            r'newfunc: ([^:]+) {': lambda match: self.handle_function_start(match.group(1)),
            r'endfunc': lambda match: self.handle_function_end(),
            r'func: ([^:]+) {': lambda match: self.handle_function_call(match.group(1), []),
            r'end': lambda match: ast.Pass(),
            r'([^ ]+) = (.+)': lambda match: ast.Assign(targets=[ast.Name(id=match.group(1), ctx=ast.Store())],
                                                        value=self.handle_expression(match.group(2))),
            r'([^ ]+)\(\)': lambda match: ast.Call(func=ast.Name(id=match.group(1), ctx=ast.Load()),
                                                   args=[],
                                                   keywords=[]),
            r'([^ ]+)\(([^)]+)\)': lambda match: ast.Call(func=ast.Name(id=match.group(1), ctx=ast.Load()),
                                                           args=[self.handle_expression(arg.strip()) for arg in match.group(2).split(',')],
                                                           keywords=[]),
            r'import ([^ ]+)': lambda match: ast.Import(names=[ast.alias(name=match.group(1), asname=None)]),
        }

    def handle_variable_definition(self, var_name, value):
        self.variables[var_name] = value
        return ast.Assign(targets=[ast.Name(id=var_name, ctx=ast.Store())],
                          value=ast.Str(s=value))
    
    def handle_variable_reference(self, var_name):
        return ast.Name(id=var_name, ctx=ast.Load())
    
    def handle_expression(self, expression):
        if expression.isdigit():
            return ast.Num(n=int(expression))
        elif expression in self.variables:
            return ast.Str(s=self.variables[expression])
        elif expression in self.arrays:
            return self.arrays[expression]
        else:
            return ast.Name(id=expression, ctx=ast.Load())

    def handle_array_definition(self, array_name, values):
        values = [self.handle_expression(value.strip()) for value in values.split(',')]
        self.arrays[array_name] = ast.List(elts=values, ctx=ast.Load())
        return ast.Assign(targets=[ast.Name(id=array_name, ctx=ast.Store())],
                          value=self.arrays[array_name])
    
    def parse_block(self, code_block):
        statements = []
        for line in code_block.split('\n'):
            line = line.strip()
            if line:
                statements.append(self.parse_line(line))
        return statements
    
    def parse_line(self, line):
        for pattern, handler in self.patterns.items():
            match = re.match(pattern, line)
            if match:
                return handler(match)
        raise SyntaxError(f"Invalid syntax: {line}")

    def handle_function_start(self, func_name):
        self.current_function_name = func_name
        self.functions[func_name] = []
        return ast.FunctionDef(name=func_name,
                               args=ast.arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
                               body=self.functions[func_name],
                               decorator_list=[])
    
    def handle_function_end(self):
        self.current_function_name = None
        return ast.Pass()

    def handle_function_call(self, func_name, args):
        if func_name not in self.functions:
            raise NameError(f"Function '{func_name}' is not defined.")
        return ast.Expr(ast.Call(func=ast.Name(id=func_name, ctx=ast.Load()),
                                 args=[self.handle_expression(arg.strip()) for arg in args.split(',')],
                                 keywords=[]))

def compile_laver_file(file_path):
    with open(file_path, 'r') as f:
        laver_code = f.read()
    parser = LaverParser()
    parsed_code = parser.parse_block(laver_code)
    python_ast = ast.parse('')
    python_ast.body = parsed_code
    compiled_code = compile(python_ast, file_path, 'exec')
    return compiled_code

# 사용자로부터 .laver 파일 경로 입력 받기
laver_file_path = input("Enter the path to the .laver file: ")

# .laver 파일 컴파일 및 실행
compiled_code = compile_laver_file(laver_file_path)
exec(compiled_code)
