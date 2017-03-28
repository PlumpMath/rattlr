import json
import os
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
    else:
        return {"type": "primitive",
                "value": val}


def wrap_bindings(bindings):
    return [{"name": n, **wrap_value(v)}
            for n, v in bindings.items()]


class Rattlr:
    assignment = re.compile("^\\s*([_a-zA-Z]\\w*)\\s*=\\s*(.+)$")
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
        return json.loads(json_data)

    def send(self, reply):
        reply_data = bytes(json.dumps(reply), "utf-8")
        self.out_pipe.write(struct.pack("i", len(reply_data)))
        self.out_pipe.write(reply_data)
        self.out_pipe.flush()

    def request(self, name):
        req = {"type": "request",
               "name": name}
        self.send(req)
        return self.receive()

    def eval_expr(self, e, imports, bindings, from_r):
        m = Rattlr.assignment.match(e)
        while True:
            lcls = {**self.persistent, **bindings, **from_r}
            try:
                if m:
                    name = m.group(1)
                    res = eval(m.group(2), lcls, imports)
                    if name[0] == '_':
                        self.persistent[name] = res
                    else:
                        bindings[name] = res
                    return None
                else:
                    return eval(e, lcls, imports)

            except NameError as err:
                n = Rattlr.undefined.match(err.args[0])
                if n:
                    name = n.group(1)
                    req = self.request(name)
                    if "missing" in req:
                        raise err
                    else:
                        from_r[name] = req["value"][0]
                else:
                    raise err

    def eval_sequence(self, data):
        imports = {i: __import__(i) for i in data['imports']}

        try:
            bindings = {}
            from_r = {}
            for e in data['exprs']:
                m = Rattlr.import_simple.match(e)
                if m:
                    self.persistent[m.group(1)] = __import__(m.group(1))
                    val = None
                    continue

                m = Rattlr.import_as.match(e)
                if m:
                    self.persistent[m.group(2)] = __import__(m.group(1))
                    val = None
                    continue

                val = self.eval_expr(e, imports, bindings, from_r)
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
