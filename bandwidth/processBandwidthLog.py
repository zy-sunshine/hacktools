import sys
import re
from time import sleep
from acom.utils.cmdwrapper import runcmd
from acom.utils.sysutil import dtUtil

class ProcessMonitor(object):
    # can not long time running nethogs, because it will consume 99%cpu and a
    # lot of memory.
    # #log out every 5 minute, count 15, so 15minutes close once
    CMD_NETHOGS = "nethogs -t -s -v0 -c1"
    TEST_OUTPUT = '''
Refreshing:
/usr/bin/python3/15280/1000     0.332723        0.334064
python3/2666/1000       0.17875 1.05981
sshd: netsec@pts/5,pts/6/7994/1000      0.0834789       0.00876045
185.201.226.166:8090-114.84.173.42:47054/0/0    0.0381594       0.0420656
python3/14048/1001      0.0018549       0.0048275
185.201.226.166:48840-41.250.122.248:30777/0/0  0.000154495     0.000185013
185.201.226.166:42696-42.190.205.178:64904/0/0  0.000154495     0.000185013
    '''

    def __init__(self):
        self.interval = 60

    def writeStdout(self, line):
        self.parseLine(line)

    def writeStderr(self, line):
        self.parseLine(line)

    def testParse(self):
        for line in self.TEST_OUTPUT.split('\n'):
            line = line.strip()
            self.writeStdout(line)

    def work(self):
        while True:
            runcmd(self.CMD_NETHOGS, trycnt=0, printout=False, callback=self)
            sleep(self.interval)

    def parseLine(self, line):
        if self.isLineStartswithIp(line): return
        info = self.tryParseProcess(line)
        if not info: return
        try:
            with open('/proc/%s/cmdline' % info['pid'], 'rt') as fp:
                info['cmdline'] = fp.read()
        except OSError:
            info['cmdline'] = info['other']
        if info['sent'] < 0.01: return  # omit 0.01MB
        if info['received'] < 0.01: return  # omit 0.01MB
        info['dt'] = dtUtil.now().strftime('%Y-%m-%d %H:%M:%S')
        sys.stdout.write('[%(dt)s] %(pid)s\t%(sent).02f\t%(received).02f\t%(cmdline)s\n' % info)
        sys.stdout.flush()

    IP_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    def isLineStartswithIp(self, line):
        '''
        1.1.1.1:1-1.1.
        255.255.255.0
                  ^
        '''
        match = self.IP_PATTERN.search(line)
        if match:
            return True

    PROCESS_PATTERN = re.compile(r'(.*)/(\d+?)/(\d+?)\W+([0-9\.]+?)\W+([0-9\.]+?)$')
    def tryParseProcess(self, line):
        match = self.PROCESS_PATTERN.search(line)
        if not match: return None
        m = match.groups()
        return {
            'line': line,
            'other': m[0],
            'pid': int(m[1]),
            'uid': int(m[2]),
            'sent': float(m[3]),
            'received': float(m[4]),
        }

if __name__ == '__main__':
    monitor = ProcessMonitor()
    #monitor.testParse()
    monitor.work()
