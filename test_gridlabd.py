import marimo

__generated_with = "0.1.39"
app = marimo.App()


@app.cell
def __(mo):
    refresh = mo.ui.refresh(options=["1s","2s","5s","10s"],default_interval="1s")
    refresh
    return refresh,


@app.cell
def __(os, threading, tmp):
    def gridlabd(*args):

        cmd = f"gridlabd {' '.join(args)}"
        os.system(f"echo '[Starting: {cmd}]' >>{tmp}")
        cmd += f" >>{tmp} 2>&1"
        code = os.system(cmd)
        os.system(f"echo '[Stopped: exit code {code}]' >>{tmp}")

    thread = threading.Thread(target = lambda:gridlabd("model.glm"))
    thread.start()
    thread.join()
    return gridlabd, thread


@app.cell
def __(mo, os):
    mo.hstack([mo.download(data=open(file,"rb"),filename=file,label=file) for file in sorted(os.listdir(".")) if os.path.splitext(file)[1] in [".csv",".json"]],justify='start')
        
    return


@app.cell
def __(mo, os):
    def fsize(file):
        size = os.stat(file).st_size
        unit = "B"
        for scale in ["kB","MB","GB","TB","PB","EB"]:
            if size < 1000:
                break
            size /= 1000
            unit = scale
        return f"{size:.3f} {unit}"
        
    listing = []
    for file in sorted(os.listdir(".")):
        if os.path.splitext(file)[1] in [".csv",".json"]:
            listing.append(mo.hstack([
                mo.hstack([
                    mo.ui.checkbox(),
                    mo.md(f"**{file}** ({fsize(file)})"),
                ],justify='start'),
                mo.download(data=open(file,"rb"),filename=file,label=""),
            ],justify='space-between'))
    mo.vstack(listing)
    return file, fsize, listing


@app.cell
def __(mo, refresh, tmp):
    refresh
    result = ""
    with open(tmp,"r") as fh:
        contents = fh.read()
        result = contents

    mo.md(f"""```\n{result}\n```""")
    return contents, fh, result


@app.cell
def __():
    import marimo as mo
    import sys, os, glob
    import subprocess
    import threading
    tmp = f"/tmp/gridlabd.{os.getpid()}"
    os.system(f"gridlabd --version 1>{tmp} 2>&1")
    None
    return glob, mo, os, subprocess, sys, threading, tmp


if __name__ == "__main__":
    app.run()
