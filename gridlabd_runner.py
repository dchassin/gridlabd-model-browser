import os, sys
import subprocess
import time
import shutil

class GridlabdException(Exception):
    pass

_exitcode = {
    -1 : "FAILED",
     0 : "SUCCESS",
     1 : "ARGERR",
     2 : "ENVERR",
     3 : "TSTERR",
     4 : "USRERR",
     5 : "RUNERR",
     6 : "INIERR",
     7 : "PRCERR",
     8 : "SVRKLL",
     9 : "IOERR",
    10 : "LDERR",
    11 : "TMERR",
   127 : "SHFAILED",
   128 : "SIGNAL",
 128+1 : "SIGHUP",
 128+2 : "SIGINT",
 128+9 : "SIGKILL",
128+15 : "SIGTERM",
   255 : "EXCEPTION",
}

def gridlabd(*args,split=None,**kwargs):
    gld = Gridlabd(*args,**kwargs)
    return gld.result.stdout if not split else gld.result.stdout.strip().split(split if type(split) is str else "\n")

class Gridlabd:

    def __init__(self,*args,
            binary = False,
            start = True,
            wait = True,
            timeout = None,
            **kwargs,
            ):
        cmd = shutil.which("gridlabd.bin")
        cmd = cmd if cmd else shutil.which("gridlabd")
        if not cmd:
            raise GridlabdException("gridlabd not found")
        self.command = [cmd]
        for name,value in kwargs.items():
            self.command.extend(["-D",f"{name}={value}"])
        self.command.extend(args)
        self.process = None
        self.result = None
        if not start:
            raise NotImplementedError("Gridlabd.start")
        elif not wait:
            raise NotImplementedError("Gridlabd.wait")
        else:
            self.run(timeout=timeout)

    def run(self,timeout=None):
        try:
            self.result = subprocess.run(self.command, 
                capture_output = True, 
                text = True,
                timeout = timeout,
                )
        except subprocess.TimeoutExpired:
            raise
        except:
            raise
        if self.result.returncode != 0:
            raise GridlabdException(f"gridlabd.{_exitcode[self.result.returncode]} -- {self.result.stderr}" 
                if self.result.returncode in _exitcode 
                else f"gridlabd.EXITCODE {self.result.returncode}") 

    def is_started(self):
        return not self.process is None

    def is_completed(self):
        return not self.result is None

    def start(self,wait=True):
        if self.is_completed():
            raise GridlabdException("already completed")
        if self.is_started():
            raise GridlabdException("already started")

    def wait(self,timeout=None):
        if self.is_completed():
            raise GridlabdException("already completed")

if __name__ == '__main__':

    import unittest

    class TestGridlabd(unittest.TestCase):

        def test_run(self):
            self.assertTrue(gridlabd("--version").startswith("HiPAS GridLAB-D"))

    # gld = Gridlabd("--version",binary=True)
    # proc = gld.start(wait=False)
    # while not gld.is_completed():
    #     print("STDOUT",proc.stdout,file=sys.stdout,flush=True)
    #     print("STDERR",proc.stderr,file=sys.stderr,flush=True)
    #     print("RCODE ",proc.returncode,file=sys.stderr,flush=True)
    #     time.sleep(1)

    # run = Gridlabd("8500.glm","clock.glm","recorders.glm")
    # run.start(wait=False)
    # while not run.result:
    #     print("STDOUT",run.output,file=sys.stdout,flush=True)
    #     print("STDERR",run.errors,file=sys.stderr,flush=True)
    #     time.sleep(1)
    # run.wait()

    unittest.main()