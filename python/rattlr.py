import cmd
import json
import os
import re
import struct
import sys


assignment = re.compile("\s*([_a-zA-Z]\w*)\s*=\s*(.+)")
undefined = re.compile("name '(.+)' is not defined")


def receive(in_pipe):
    size = struct.unpack('i', in_pipe.read(4))[0]
    if size == 0:
        return None
    json_data = in_pipe.read(size)[:-1]
    return json.loads(json_data)


def send(out_pipe, reply):
    reply_data = bytes(json.dumps(reply), "utf-8")
    out_pipe.write(struct.pack("i", len(reply_data)))
    out_pipe.write(reply_data)
    out_pipe.flush()


def request(in_pipe, out_pipe, name):
    req = {"type": "request",
           "name": name}
    send(out_pipe, req)
    return receive(in_pipe)


def eval_data(in_pipe, out_pipe, data):
    imports = dict()
    for i in data['imports']:
        imports[i] = __import__(i)

    try:
        bindings = dict()
        from_r = dict()
        val = None
        for e in data['exprs']:
            m = assignment.match(e)

            while True:
                lcls = {**persistent, **bindings, **from_r}
                try:
                    if m:
                        name = m.group(1)
                        res = eval(m.group(2), lcls, imports)
                        if name[0] == '_':
                            persistent[name] = res
                        else:
                            bindings[name] = res
                    else:
                        val = eval(e, lcls, imports)
                    break

                except NameError as err:
                    n = undefined.match(err.args[0])
                    if n:
                        name = n.group(1)
                        req = request(in_pipe, out_pipe, name)
                        if "missing" in req:
                            raise err
                        else:
                            from_r[name] = req["value"][0]
                    else:
                        raise err

    except Exception as exc:
        val = {"type": "exception",
               "type": type(exc).__name__,
               "args": exc.args}

    if val is None:
        reply = {"type": "null",
                 "bindings": bindings}
    else:
        reply = {"type": "primitive",
                 "bindings": bindings,
                 "result": val}
    return reply


def receive_eval_send(in_pipe, out_pipe):
    data = receive(in_pipe)
    if data is None:
        return False

    reply = eval_data(in_pipe, out_pipe, data)

    send(out_pipe, reply)
    return True


if __name__ == '__main__':
    pipe_dir = sys.argv[1]
    print("pipes dir: {}".format(pipe_dir))

    with open(os.path.join(pipe_dir, "rToPython"), "rb") as in_pipe:
        with open(os.path.join(pipe_dir, "pythonToR"), "wb") as out_pipe:
            print("ready")
            persistent = dict()
            while receive_eval_send(in_pipe, out_pipe):
                pass
    print("done")
