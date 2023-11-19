"""GridLAB-D runner

Asynchronous gridlabd runner.  Use this module to start and access a gridlabd
simulation asynchrnously.

Example:

    gld = 

"""
import os, sys
import threading
import requests
import time
import io
import subprocess, signal

class GridlabdHttpError(Exception):
    pass

DEBUG = True # enable debug output to stderr

def debug(msg):
    if DEBUG:
        print(f"DEBUG [gridlabd_runner]: {msg}",file=sys.stderr,flush=True)

class Gridlabd:

    # status flags
    READY = 0
    STARTING = 1
    RUNNING = 2
    ERROR = 3
    DONE = 4
    
    def __init__(self,
            *args, # primary commands to gridlabd
            binary = False, # use gridlabd binary if possible
            start = True, # start simulation immediately
            wait = False, # wait timeout for simulation to terminate 
            **kwargs, # global variable definitions
            ):
        """Setup a gridlabd simulation
        Arguments:
        - *args: command line options, see `gridlabd -h|--help|help` for details
        - binary (bool): use the gridlabd binary if possible (faster startup but no subcommands)
        - start (bool): start simulation immediately
        - wait (bool|int): wait for simulation to terminate
        - **kwargs: global variable definitions, see `gridlabd --globals` for details
        """
        debug(f"Gridlabd.__init__(self={self},*args={args},binary={binary},start={start},**kwargs={kwargs})")
        self.portnum = 6267
        self.command = ["gridlabd.bin" if binary and "GLD_BIN" in os.environ else "gridlabd"]
        for name,value in kwargs.items():
            self.command.extend(["-D", f"{name}={value}"])
        self.command.extend(["--server","-P",str(self.portnum),"-D","flush_output=TRUE"])
        self.command.extend(args)
        self.output = ""
        self.errors = ""
        self.threads = {}
        self.locks = {}
        self.globals = {}
        self.status = self.READY
        self.process = None
        self.refresh = None
        if start:
            self.start(wait=wait)
        debug(f"Gridlabd.__init__(self={self},*args={args},binary={binary},start={start},**kwargs={kwargs}) -->")

    # def __del__(self):
    #     try:
    #         os.killpg(os.getpgid(self.process.pid),signal.SIGTERM)
    #         self.process.wait()
    #     except:
    #         pass

    def start(self,wait=False):
        """Start the simulation process
        Arguments:
        - wait (bool|int): indicate whether/how long to wait before timeout
        """
        debug(f"Gridlabd._start(self={self})")

        self.locks["runner"] = threading.Event()

        async def _runner():
            self.status = self.STARTING
            self.process = await asyncio.create_subprocess_exec(*self.command,
                stdout = asyncio.subprocess.PIPE,
                stderr = asyncio.subprocess.PIPE,
                )
            self.status = self.RUNNING
            self.locks["runner"].set()  
            while self.process.returncode is None:
                buf = await self.process.stdout.read(1)
                if not buf:
                    break
                self.output += buf.decode()
            self.errors = await self.process.stderr.read().decode()
            self.result = subprocess.CompletedProgress(self.command,self.process.returncode,stdout=self.output,stderr=self.errors)
            self.process = None

        # def _reader(stream,output):
        #     debug(f"Gridlabd._reader(stream={stream},output={output}): starting reader")
        #     output.write(stream.read())
        #     stream.close()
        #     debug(f"Gridlabd._reader(stream={stream},output={output}): closing reader")
        
        # def _runner():
        #     debug(f"Gridlabd._runner(): command = [{self.get_command()}]")
        #     self.status = self.STARTING
        #     self.process = subprocess.Popen(self.command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=os.setsid)
        #     self.threads["stdout"] = threading.Thread(target=_reader,args=(self.process.stdout,self.output))
        #     self.threads["stderr"] = threading.Thread(target=_reader,args=(self.process.stderr,self.errors))
        #     self.threads["stdout"].start()
        #     self.threads["stderr"].start()
        #     self.status = self.RUNNING
        #     self.locks["runner"].set()
        #     debug(f"Gridlabd._runner() waiting for simulation to close pipes")
        #     self.threads["stdout"].join()
        #     debug(f"Gridlabd._runner() stdout closed --> output = {self.output}")
        #     self.threads["stderr"].join()
        #     debug(f"Gridlabd._runner() stderr closed --> errors = {self.errors}")
        #     debug(f"Gridlabd._runner() -->")

        def _monitor():
            debug(f"Gridlabd._monitor(): starting")
            self.locks["runner"].wait()
            while self.status < self.RUNNING or self.threads["runner"].is_alive():
                for name in self.globals:
                    try:
                        self.globals[name] = self.query(f"raw/{name}")
                    except:
                        e_type, e_value, e_trace = sys.exc_info()
                        debug(f"Gridlabd._monitor(): EXCEPTION {e_type.__name__} {e_value}")
                debug(f"Gridlabd._monitor(): sleeping")
                time.sleep(self.refresh)
                debug(f"Gridlabd._monitor(): waking up")
            debug(f"Gridlabd._monitor(): status = '{self.get_status()}'")
            debug(f"Gridlabd._monitor(): runner is_alive = {self.threads['runner'].is_alive()}")
            debug(f"Gridlabd._monitor(): waiting for pipes to close")
            debug(f"Gridlabd._monitor() -->")

        self.threads["runner"] = threading.Thread(target=_runner)
        self.threads["runner"].start()
        if wait:
            self.wait(timeout=wait if type(wait) is int else None)
        elif self.refresh:
            self.threads["monitor"] = threading.Thread(target=_monitor)
            self.threads["monitor"].start()
            debug(f"Gridlabd._start(self={self}): waiting for monitor")
            self.locks["runner"].wait()
            debug(f"Gridlabd._start(self={self}): monitor ok")
        debug(f"Gridlabd._start(self={self}) -->")
        if self.status == self.ERROR:
            raise GridlabdError(self.threads["runner"].returncode)

    def wait(self,timeout=None):
        """Wait for process to complete
        Arguments:
        - timeout (bool|int|None): specify whether/how long to wait
        """
        if "runner" in self.threads:
            self.threads["runner"].join(timeout)
            if self.process:
                debug(f"Gridlabd.wait() simulation exitcode = {self.process.returncode}")
                self.status = self.ERROR if self.process.returncode else self.DONE
            else:
                debug(f"Gridlabd.wait() simulation is running")
                self.status = self.RUNNING
        if "monitor" in self.threads:
            self.threads["monitor"].join(timeout)

    def get_status(self):
        """Get process status"""
        return ["READY","STARTING","RUNNING","ERROR","DONE"][self.status]

    def get_output(self,split=None):
        """Get process output so far"""
        result = self.output.read().decode()
        if split:
            return result.split(split)
        return result

    def get_errors(self,split=None):
        """Get process errors so far"""
        result = self.errors.read().decode()
        if split:
            return result.split(split)
        return result

    def get_exitcode(self):
        """Get process exit code"""
        return self.process.returncode if self.status > self.RUNNING else None

    def get_command(self):
        """Get command string"""
        return str(self.command)

    def query(self,query):
        """Query simulation
        Arguments:
        - query (str): query string
        """
        r = requests.get(f"http://localhost:{self.portnum}/{query}",
            headers = {"Connection": "close"})
        if r.status_code == 200:
            debug(f"Gridlabd.query(query='{query}'): -> {r.text}")
            return r.text
        debug(f"Gridlabd.query(query='{query}'): -> GridlabdHttpError({r.status_code})")
        raise GridlabdHttpError(r.status_code)

if __name__ == "__main__":

    import unittest

    class TestGridlabd(unittest.TestCase):

        def test_version(self):
            version = Gridlabd("--version")
            print("Exit #: ",gld.get_exitcode(),file=sys.stderr)
            print("Output:",gld.get_output(),file=sys.stderr)
            print("Errors:",gld.get_errors(),file=sys.stderr)

        def test_error(self):
            gld = Gridlabd("13.glm","clock.glm","recorders.glm",wait=True)
            print("Exit #: ",gld.get_exitcode(),file=sys.stderr)
            print("Output:",gld.get_output(),file=sys.stderr)
            print("Errors:",gld.get_errors(),file=sys.stderr)
            gld.wait()

        def test_success(self):
            gld = Gridlabd("8500.glm","clock.glm","recorders.glm",start=False)
            gld.refresh = 1
            gld.globals = {"progress":None,"clock":None}
            gld.start()
            while gld.get_exitcode() is None:
                print(gld.globals,file=sys.stderr,flush=True)
                time.sleep(1)

    unittest.main()