import sys
import ast, inspect

def long_command(f):
    def _long(*args, **kargs):
        return f(*args, **kargs)
    return _long

def short_command(f):
    def _short(*args, **kargs):
        return f(*args, **kargs)
    return _short

def get_commands(name, deco):
    module = sys.modules[name]
    source = inspect.getsource(module)
    tree = ast.parse(source)

    ret = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            decorators = node.decorator_list

            for name in decorators:
                if name.id == deco.__name__:
                    ret[node.name] = getattr(module, node.name)
                    break
    return ret
