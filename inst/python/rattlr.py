import inspect
import io
import json
import numpy
import os
import pandas
import re
import struct
import sys


def wrap_value(val):
    if val is None:
        return {"type": "null"}
    elif isinstance(val, Exception):
        return {"type": "exception",
                "class": type(val).__name__,
                "args": val.args}
    elif isinstance(val, numpy.int64):
        return {"type": "primitive",
                "value": numpy.asscalar(val)}
    elif isinstance(val, range) or inspect.isgenerator(val):
        return {"type": "primitive",
                "value": list(val)}
    elif isinstance(val, numpy.ndarray):
        return {"type": "primitive",
                "value": val.tolist()}
    elif isinstance(val, pandas.DataFrame):
        return {"type": "dataframe",
                "csv": val.to_csv(index=False)}
    else:
        return {"type": "primitive",
                "value": val}


def wrap_bindings(bindings):
    return [{"name": n, **wrap_value(v)}
            for n, v in bindings.items()]


class Environment:
    def __init__(self, rattlr, imports, bindings, from_r):
        self.rattlr = rattlr
        self.bindings = bindings
        self.from_r = from_r
        self.imports = imports

    def make_locals(self):
        return {**self.from_r, **self.rattlr.persistent, **self.bindings}

    def _eval(self, expr):
        return eval(expr, self.make_locals(), self.imports)

    def _exec(self, expr):
        return exec(expr, self.make_locals(), self.imports)

    def run_lookup(self, thunk):
        while True:
            try:
                return thunk()
            except NameError as err:
                n = Rattlr.undefined.match(err.args[0])
                if n:
                    name = n.group(1)
                    req = self.rattlr.request(name)
                    if "missing" in req:
                        raise err
                    else:
                        self.from_r[name] = req["value"]
                else:
                    raise err

    def evaluate(self, expr):
        return self.run_lookup(lambda: self._eval(expr))

    def execute(self, expr):
        return self.run_lookup(lambda: self._exec(expr))


class Expression:
    def __init__(self, envir):
        self.envir = envir

    def evaluate(self):
        pass


class SimpleExpr(Expression):
    def __init__(self, expr, envir):
        Expression.__init__(self, envir)
        self.expr = expr

    def evaluate(self):
        return self.envir.evaluate(self.expr)


class Assignment(Expression):
    def __init__(self, name, expr, envir):
        Expression.__init__(self, envir)
        self.name = name
        self.expr = SimpleExpr(expr, envir)

    def evaluate(self):
        res = self.expr.evaluate()
        if self.name[0] == '_':
            self.envir.rattlr.persistent[self.name] = res
        else:
            self.envir.bindings[self.name] = res
        return None


class AssignItem(Expression):
    def __init__(self, name, item, expr, envir):
        Expression.__init__(self, envir)
        self.name = name
        self.item = item
        self.expr = expr

    def evaluate(self):
        Assignment(self.name, self.name, self.envir).evaluate()
        stmt = "{}[{}] = {}".format(self.name, self.item, self.expr)
        self.envir.execute(stmt)


class SimpleImport(Expression):
    def __init__(self, package, envir):
        Expression.__init__(self, envir)
        self.package = package

    def evaluate(self):
        self.envir.rattlr.persistent[self.package] = __import__(self.package)


class ImportAs(Expression):
    def __init__(self, name, package, envir):
        Expression.__init__(self, envir)
        self.name = name
        self.package = package

    def evaluate(self):
        self.envir.rattlr.persistent[self.name] = __import__(self.package)


class Rattlr:
    assignment = re.compile("^\\s*([_a-zA-Z]\\w*)\\s*=\\s*(.+)$")
    assign_item = re.compile("^\\s*([_a-zA-Z]\\w*)\\s*\[(.*)\]\\s*=\\s*(.+)$")
    undefined = re.compile("^name '(.+)' is not defined$")
    import_simple = re.compile("^\\s*import\\s+(\\S+)$")
    import_as = re.compile("^\\s*import\\s+(\\S+)\\s+as\\s+([_a-zA-Z]\\w*)$")

    def __init__(self, in_pipe, out_pipe):
        self.in_pipe = in_pipe
        self.out_pipe = out_pipe
        self.persistent = {}

    def receive(self):
        size = struct.unpack('i', self.in_pipe.read(4))[0]
        if size == 0:
            return None
        json_data = self.in_pipe.read(size)[:-1]
        data = json.loads(json_data)
        if "value" in data:
            if "dataframe" in data["type"]:
                str_in = io.StringIO(data["value"][0])
                data["value"] = pandas.read_csv(str_in)
            elif isinstance(data["value"], list):
                data["value"] = numpy.asarray(data["value"])

        return data

    def send(self, reply):
        try:
            reply_data = bytes(json.dumps(reply), "utf-8")
            self.out_pipe.write(struct.pack("i", len(reply_data)))
            self.out_pipe.write(reply_data)
            self.out_pipe.flush()
        except Exception as exc:
            self.send(wrap_value(exc))

    def request(self, name):
        req = {"type": "request",
               "name": name}
        self.send(req)
        return self.receive()

    def make_expr(self, e, imports, bindings, from_r):
        envir = Environment(self, imports, bindings, from_r)
        m = Rattlr.assignment.match(e)
        if m:
            return Assignment(m.group(1), m.group(2), envir)
        m = Rattlr.assign_item.match(e)
        if m:
            return AssignItem(m.group(1), m.group(2), m.group(3), envir)
        m = Rattlr.import_simple.match(e)
        if m:
            return SimpleImport(m.group(1), envir)
        m = Rattlr.import_as.match(e)
        if m:
            return ImportAs(m.group(2), m.group(1), envir)
        return SimpleExpr(e, envir)

    def eval_sequence(self, data):
        imports = {i: __import__(i) for i in data['imports']}
        try:
            bindings = {}
            from_r = {}
            val = None
            for e in data['exprs']:
                expr = self.make_expr(e, imports, bindings, from_r)
                val = expr.evaluate()
        except Exception as exc:
            val = exc

        return {**wrap_value(val), "bindings": wrap_bindings(bindings)}

    def receive_eval_send(self):
        data = self.receive()
        if data is None:
            return False

        reply = self.eval_sequence(data)

        self.send(reply)
        return True


def main(pipe_dir):
    with open(os.path.join(pipe_dir, "rToPython"), "rb") as in_pipe:
        with open(os.path.join(pipe_dir, "pythonToR"), "wb") as out_pipe:
            print("python started", file=sys.stderr)
            rattlr = Rattlr(in_pipe, out_pipe)
            while rattlr.receive_eval_send():
                pass
    print("python shutdown", file=sys.stderr)


if __name__ == '__main__':
    main(pipe_dir=sys.argv[1])
