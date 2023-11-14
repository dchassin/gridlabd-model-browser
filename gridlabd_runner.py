import os, sys
import threading
import requests
import time
import io
import subprocess

DEBUG = True

def debug(msg):
    print(f"DEBUG [gridlabd_runner]: {msg}",file=sys.stderr)
class Gridlabd:

    # status flags
    READY = 0
    STARTING = 1
    RUNNING = 2
    ERROR = 3
    DONE = 4
    
    def __init__(self,*args,binary=False,start=True,**kwargs):
        """Setup a gridlabd simulation
        Arguments:
        - binary (bool): use the gridlabd binary if possible (faster startup but no subcommands)
        - *args: command line options, see `gridlabd -h|--help|help` for details
        - **kwargs: global variable definitions, see `gridlabd --globals` for details
        """
        debug(f"Gridlabd.__init__(self={self},*args={args},binary={binary},start={start},**kwargs={kwargs})")
        self.command = ["gridlabd.bin" if binary and "GLD_BIN" in os.environ else "gridlabd"]
        for name,value in kwargs.items():
            self.command.extend(["-D", f"{name}={value}","--server","--server_portnum",self.portnum])
        self.command.extend(args)
        self.portnum = 6267
        self.output = io.BytesIO()
        self.errors = io.BytesIO()
        self.progress = 0.0
        self.threads = {}
        self.locks = {}
        self.status = self.READY
        self.result = None
        if start:
            self.start()
        debug(f"Gridlabd.__init__(self={self},*args={args},binary={binary},start={start},**kwargs={kwargs}) -->")

    def start(self):
        debug(f"Gridlabd._start(self={self})")
        self.locks["runner"] = threading.Event()
        self.locks["monitor"] = threading.Event()
        def _reader(stream,output):
            debug(f"Gridlabd._reader(stream={stream},output={output}): starting reader")
            output.write(stream.read())
            stream.close()
            debug(f"Gridlabd._reader(stream={stream},output={output}): closing reader")
        def _runner():
            debug(f"Gridlabd._runner(): starting")
            self.status = self.STARTING
            self.result = subprocess.Popen(self.command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.threads["stdout"] = threading.Thread(target=_reader,args=(self.result.stdout,self.output))
            self.threads["stderr"] = threading.Thread(target=_reader,args=(self.result.stderr,self.errors))
            self.threads["stdout"].start()
            self.threads["stderr"].start()
            self.status = self.ERROR if self.result.returncode else self.DONE
            self.locks["runner"].set()
            debug(f"Gridlabd._runner() -->")
        def _monitor():
            debug(f"Gridlabd._monitor(): starting")
            self.locks["monitor"].set()
            while self.status < self.RUNNING or self.threads["runner"].is_alive():
                time.sleep(1)
                r = requests.get(f"http://localhost:{self.portnum}/progress")
                if r.status_code == 200:
                    self.progress = float(r.text.decode())
                    debug(f"Gridlabd._monitor(): progress = {self.progress}")
                else:
                    debug(f"Gridlabd._monitor(): request --> r.status_code")
            self.threads["stdout"].join()
            self.threads["stderr"].join()
            debug(f"Gridlabd._monitor() -->")
        self.threads["monitor"] = threading.Thread(target=_monitor)
        self.threads["monitor"].start()
        self.threads["runner"] = threading.Thread(target=_runner)
        self.threads["runner"].start()
        debug(f"Gridlabd._start(self={self}): waiting for monitor")
        self.locks["runner"].wait()
        debug(f"Gridlabd._start(self={self}): moniter ok")
        self.status = self.RUNNING
        debug(f"Gridlabd._start(self={self}) -->")

    def get_status(self):
        return ["READY","STARTING","RUNNING","ERROR","DONE"][self.status]

    def get_output(self):
        return self.output.decode()

    def get_errors(self):
        return self.errors.decode()

    def get_exitcode(self):
        return self.result.returncode if self.status > self.RUNNING else None

if __name__ == "__main__":

    gld = Gridlabd("8500.glm","clock.glm","recorders.glm")
    while gld.status <= gld.RUNNING:
        print(f"Status = {gld.get_status()}, Progress = {gld.progress}",file=sys.stderr)
        time.sleep(1)
