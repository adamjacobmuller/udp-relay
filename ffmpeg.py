import subprocess
import sys
import fcntl
import os
from pprint import pprint

class ffmpeg:
    ffmpeg="/usr/bin/ffmpeg"
    input="-"
    output=""
    frames=1
    d_stderr=""
    d_stdout=""
    debug=True
    def __init__(self):
        self.input="-"
        self.output=[]
        self.frames=1

    def start(self):
        command=[self.ffmpeg]
        
        command.append("-i")
        command.append(self.input)
        
        if self.frames:
            command.append("-frames")
            command.append(str(self.frames))
        
        for ci in self.output:
            command.append(ci)
        
        self.ffmpeg_process=subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)


        stdout_fd = self.ffmpeg_process.stdout.fileno()
        stdout_fl = fcntl.fcntl(stdout_fd,fcntl.F_GETFL)
        fcntl.fcntl(stdout_fd,fcntl.F_SETFL,stdout_fl|os.O_NONBLOCK)
        
        stderr_fd = self.ffmpeg_process.stderr.fileno()
        stderr_fl = fcntl.fcntl(stderr_fd,fcntl.F_GETFL)
        fcntl.fcntl(stderr_fd,fcntl.F_SETFL,stderr_fl|os.O_NONBLOCK)

    def need_data(self):
        if self.ffmpeg_process.returncode==None:
            return True
        else:
            return False

    def finish(self):
        self.ffmpeg_process.stdin.close()
        while self.ffmpeg_process.returncode==None:
            self.ffmpeg_process.poll()
            try:
                l_stdout=self.ffmpeg_process.stdout.readline().decode().strip()
                if self.debug==True and len(l_stdout)>0:
                    print("STDOUT: %s" % l_stdout)
            except IOError: pass
        
            try:
                l_stderr=self.ffmpeg_process.stderr.readline().decode().strip()
                if self.debug==True and len(l_stderr)>0:
                    print("STDERR: %s" % l_stderr)
            except IOError: pass
        got_log=True
        while got_log==True:
            got_log=False
            try:
                l_stdout=self.ffmpeg_process.stdout.readline().decode().strip()
                if self.debug==True and len(l_stdout)>0:
                    print("STDOUT: %s" % l_stdout)
                    got_log=True
            except IOError: pass
        
            try:
                l_stderr=self.ffmpeg_process.stderr.readline().decode().strip()
                if self.debug==True and len(l_stderr)>0:
                    print("STDERR: %s" % l_stderr)
                    got_log=True
            except IOError: pass
            


    def append_data(self,data):
        try:
            l_stdout=self.ffmpeg_process.stdout.readline().decode().strip()
            if self.debug==True and len(l_stdout)>0:
                print("STDOUT: %s" % l_stdout)
        except IOError: pass
    
        try:
            l_stderr_r=self.ffmpeg_process.stderr.readline()
            l_stderr=l_stderr_r.decode(errors='replace').strip()
            if self.debug==True and len(l_stderr)>0:
                print("STDERR: %s" % l_stderr)
        except IOError: pass
        except UnicodeDecodeError:
            print("unable to decode %s" % (l_stderr_r))


        self.ffmpeg_process.poll()
        try:
            return self.ffmpeg_process.stdin.write(data)
        except IOError:
            return False


if __name__ == "__main__":
    import sys
    import shlex
    prober=ffmpeg()
    prober.output=sys.argv[1:]
    prober.start()
    file=open("test.ts","rb")
    while prober.need_data():
        data=file.read(2048)
        if len(data)==0:
            prober.finish()
            break
        prober.append_data(data)
    print
