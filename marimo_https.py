import os, sys
import json
import random

token_bits=32
token = "0" # hex(random.randint(0,1e32))[2:]
print("Access token is",token)

from flask import Flask, request

app = Flask(__name__)

with open(sys.argv[0].replace("py","json"),"r") as fh:
    notebooks = json.load(fh)

@app.route("/")
def api_root():
    items = "&nbsp;".join([f"""<input type=button value="{name}" onclick="req=new XMLHttpRequest();req.open('GET','/edit/{name}?token={token}');req.send();"/>""" for name in notebooks])
    return f"""<h1>Notebooks</h1>{items}"""

@app.route(f"/<command>/<notebook>")
def api_command_notebook(command,notebook):

    if command not in ["run","edit"]:
        return "Bad request",400
    elif request.args.get("token") != token:
        return "Unauthorized",401
    elif command in ["run"] and not os.path.exists(f"{notebook}.py"):
        return "Not found",404
    elif notebook not in notebooks:
        return "Not acceptable",406
    elif os.system(f"marimo {command} {notebook}.py &") != 0:
        return "Forbidden",403
    else:
        return "OK",200

if __name__ == "__main__":
    app.run()#ssl_context='adhoc')
