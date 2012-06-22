import subprocess
import sys
from pprint import pprint

class ffprobe:
    show_format=True
    show_streams=True
    ffprobe="/usr/bin/ffprobe"
    streams=[]
    format={}
    def __init__(self):
        self.streams=[]
        self.format={}
        command=[self.ffprobe]
        if self.show_format:
            command.append("-show_format")
        if self.show_streams:
            command.append("-show_streams")

        command.append("-")

        self.ffprobe_process=subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    def need_data(self):
        if self.ffprobe_process.returncode==None:
            return True
        else:
            return False

    def append_data(self,data):
        self.ffprobe_process.poll()
        try:
            return self.ffprobe_process.stdin.write(data)
        except IOError:
            self.parse_output()
            return False

    def parse_output(self):
        self.raw_output=self.ffprobe_process.stdout.read()
        lines=self.raw_output.strip().split("\n")
        in_stream=False
        in_format=False
        for line in lines:
            if in_stream==False and in_format==False and line=="[STREAM]":
                stream={}
                in_stream=True
                continue
            if in_stream==True and in_format==False and line=="[/STREAM]":
                self.streams.append(stream)
                in_stream=False
                continue
            if in_stream==False and in_format==False and line=="[FORMAT]":
                in_format=True
                continue
            if in_stream==False and in_format==True and line=="[/FORMAT]":
                in_format=True
                continue
            parts=line.split("=",2)
            if len(parts)==2:
                key=parts[0]
                value=parts[1]
                if in_stream==True:
                    stream[key]=value
                    continue
                if in_format==True:
                    self.format[key]=value
                    continue
    def pprint(self):
        streams_string_list=[]
        for stream in self.streams:
            if stream['codec_type']=="audio":
                streams_string_list.append(
                    "%s channel %s" % (
                        stream['channels'],
                        stream['codec_long_name']
                    ))
            elif stream['codec_type']=="video":
                streams_string_list.append(
                    "%sx%s %s" % (
                        stream['width'],
                        stream['height'],
                        stream['codec_long_name']
                    ))
            elif stream['codec_type']=="data":
                continue
            else:
                print "unknown codec type: %s" % stream['codec_type']
                pprint(stream)
        return "%s [ %s ]" % (
            self.format['format_long_name'],
            ", ".join(streams_string_list)
            )
            

if __name__ == "__main__":
    prober=ffprobe()
    file=open("test.ts","r")
    while prober.need_data():
        sys.stdout.write(".")
        sys.stdout.flush()
        data=file.read(2048)
        prober.append_data(data)
    print
    pprint(prober.streams)
    pprint(prober.format)
