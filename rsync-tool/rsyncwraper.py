import os
import re
import time
import Queue
import shlex, subprocess
from threading import Thread

subprocess_kwargs = {} 
if subprocess.mswindows: 
    su = subprocess.STARTUPINFO() 
    su.dwFlags |= subprocess.STARTF_USESHOWWINDOW 
    su.wShowWindow = subprocess.SW_HIDE 
    subprocess_kwargs['startupinfo'] = su

class PasswordInvalidException(Exception):
    pass

class RSyncThread(Thread):
    PASSWORD_INVALID = 0x00000001
    TYPE_PROGRESS = 0x00000002
    def __init__(self, sself, cmdstr, env, *args, **kwargs):
        Thread.__init__(self)
        self.sself = sself
        self.cmdstr = cmdstr
        self.cmdobj = None
        self.env = env

        self.returncode = -1
        self.stderr = None
        self.shell = False
        self.command = shlex.split(self.cmdstr)
        self.timeout = 3
        self.running = False

    def prepare(self):
        self.cmdobj = subprocess.Popen(self.command, stdin=None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=self.shell, executable=None, env=self.env,
            **subprocess_kwargs)
        return self.cmdobj

    def run(self):
        self.prepare()
        self.running = True
        buffer0 = ''
        def dealwithbuffer(buf, buffer0):
            buffer0 += buf

            pos = buffer0.find('\n')
            if pos == -1:
                return buffer0

            end = pos +1
            line = buffer0[:end]
            buffer0 = buffer0[end:]
            # print '+' * 30
            # print line
            # print '+' * 30
            # Deal with line

            ret = re.match(r'\s+([\d,]+)\s+(\d+)%\s+([\d\.]+\w+/s).*', line)
            if ret:
                size, percent, speed = ret.groups()
                size = ''.join(size.split(','))
                # 80857 2 487.42kB/s
                # 2777858 100 4.11MB/s
                # print size, percent, speed
                self.sself.OnProgress(size, percent, speed)

            return dealwithbuffer('', buffer0)

        while self.cmdobj.poll() is None:
            # NOTICE: Windows not support select on file number, but it support socket file number which provided by WinSock lib.
            # infds, outfds, errfds = select.select([self.cmdobj.stdout, ], [], [], 300)  
            # if self.cmdobj.stdout in infds:
            try:
                stdout0 = os.read(self.cmdobj.stdout.fileno(), 4096)
                buffer0 = dealwithbuffer(stdout0, buffer0)
            except OSError:
                pass
            time.sleep(0.3)
        # Deal with remain buffer
        buffer0 = dealwithbuffer(self.cmdobj.stdout.read(), buffer0)
        
        self.returncode = self.cmdobj.returncode
        out, self.stderr = self.cmdobj.communicate()
        self.cmdobj.wait()
        self.sself.OnFinished(self.returncode, self.stderr)
        #print('progress exit with %s %s' % (self.returncode, self.stderr))

    def kill(self):
        if self.cmdobj:
            self.cmdobj.kill()

class RSyncMonitor(Thread):
    def __init__(self, init_class=RSyncThread, timeout = 20):
        Thread.__init__(self)
        self.init_class = init_class
        self.watch_dog = False
        self.timeout = timeout
        self.rsync_progress_args = []
        self.rsync_progress_kwargs = {}
        self.fjp = None
        self.returncode = -999
        self.returnmsg = None

    def run(self):
        self.fjp = self.init_class(self, *self.rsync_progress_args, **self.rsync_progress_kwargs)

        try:
            self.fjp.start()
            begin = time.time()
            while self.fjp.is_alive():
                if not self.watch_dog and time.time()-begin > self.timeout:
                    self.fjp.kill()
                    break
                    
                time.sleep(0.3)
            self.fjp.join()
        except PasswordInvalidException, e:
            self.OnPasswordInvalid()

    def runcmd(self, *args, **kwargs):
        self.queue = Queue.Queue() # Use PulseProgress to get result from monitor

        self.rsync_progress_args = args
        self.rsync_progress_kwargs = kwargs
        self.start()

    def PulseProgress(self):
        if self.queue:
            try:
                typ, data = self.queue.get(block=False)
                self.queue.task_done()
                if typ & RSyncThread.TYPE_PROGRESS:
                    return data
            except Queue.Empty as e:
                return None
        return None

    # virtual
    def OnProgress(self, size, percent, speed):
        # feed the dog (one time valid)
        self.watch_dog = True
        if self.queue:
            self.queue.put((RSyncThread.TYPE_PROGRESS, (size, percent, speed)))

    def OnFinished(self, returncode, msg):
        self.returncode = returncode
        self.returnmsg = msg
        if self.returncode != 0:
            self.OnError(returncode, msg)

    # virtual
    def OnError(self, errcode, msg):
        pass

    # virtual
    def OnPasswordInvalid(self):
        pass

    def terminate(self):
        # wait cmd run
        if self.fjp.cmdobj.poll() is not None:
            # cmdobj run completely
            return
        else:
            if subprocess.mswindows: cmd = 'taskkill /F /PID %s' % self.fjp.cmdobj.pid
            else: cmd = 'kill -9 %s' % self.fjp.cmdobj.pid
            os.system(cmd)

if __name__ == '__main__':
    class RSync(RSyncMonitor):
        def OnProgress(self, size, percent, speed):
            RSyncMonitor.OnProgress(self, size, percent, speed)
            #print('OnProgress %s %s %s' % (size, percent, speed))

        def OnError(self, errcode, msg):
            print('%s %s' % (errcode, msg))

        def OnPasswordInvalid(self):
            print('OnPasswordInvalid')


    env = os.environ
    env['RSYNC_PASSWORD'] = '111111'
    rmonitor = RSync()
    rmonitor.runcmd(r'rsync.exe -avz --info=progress2 --delete rsync://rsync@tick0.hackos.org/other other', env)
    while rmonitor.is_alive():
        ret = rmonitor.PulseProgress()
        if ret: print(ret)

    rmonitor.terminate()
    rmonitor.join()
