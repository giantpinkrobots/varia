import os
import sys
import subprocess
import threading
import ctypes
import signal
from multiprocessing.connection import Listener
from stringstorage import gettext as _

def start_tray_process(self, variaapp):
    if self.tray_process == None: # If tray process is not already running
        if os.name == 'nt' or (os.uname().sysname == 'Darwin'):

            if os.path.exists(os.path.join(os.getcwd(), 'tray', 'varia-tray.exe')): # Built with PyInstaller (Windows)
                tray_subprocess_input = [os.path.join(os.getcwd(), 'tray', 'varia-tray.exe'), _("Show"), _("Quit")]

            elif os.path.exists(os.path.join(os.getcwd(), 'tray', 'varia-tray')): # Built with PyInstaller (Mac)
                tray_subprocess_input = [os.path.join(os.getcwd(), 'tray', 'varia-tray'), _("Show"), _("Quit")]

            else: # Running standalone
                tray_subprocess_input = [sys.executable, os.path.join(os.path.dirname(__file__), 'tray_win_mac.py'), _("Show"), _("Quit")]

        else:
            tray_subprocess_input = [sys.executable, os.path.join(os.path.dirname(__file__), 'tray_linux_appindicator.py'), _("Show"), _("Quit")]

        def tray_process_connection():
            address = ('localhost', 6802)
            tray_listener = Listener(address, authkey=b'varia-tray-process')
            tray_conn = tray_listener.accept()

            while True:
                if self.tray_connection_thread_stop:
                    break

                try:
                    message = tray_conn.recv()
                    print("Tray icon pressed function: ", message)

                    if message == "show":
                        self.unminimize()
                        self.set_visible(True)
                        if os.uname().sysname != 'Darwin':
                            self.present()
                        
                        if self.appconf["tray_always_visible"] != "true":
                            self.tray_process.kill()
                            self.tray_process = None
                            break

                    elif message == "quit":
                        self.exitProgram(self, variaapp, False)
                        break

                except:
                    pass
            
            tray_listener.close()

        self.tray_connection_thread_stop = False
        self.tray_process = None

        if os.name == 'nt': # Windows
            import win32job
            import win32process
            import win32api

            CREATE_NEW_PROCESS_GROUP = 0x00000200
            self.tray_process = subprocess.Popen(tray_subprocess_input, creationflags=CREATE_NEW_PROCESS_GROUP)
            self.tray_job = win32job.CreateJobObject(None, "")

            info = win32job.QueryInformationJobObject(self.tray_job, win32job.JobObjectExtendedLimitInformation)
            info["BasicLimitInformation"]["LimitFlags"] |= (win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)

            win32job.SetInformationJobObject(self.tray_job, win32job.JobObjectExtendedLimitInformation, info)
            win32job.AssignProcessToJobObject(self.tray_job, self.tray_process._handle)

        elif os.uname().sysname != 'Darwin': # Linux
            libc = ctypes.CDLL("libc.so.6", use_errno=True)

            PR_SET_PDEATHSIG = 1
            SIGTERM = signal.SIGTERM

            def setup():
                res = libc.prctl(PR_SET_PDEATHSIG, SIGTERM)
                if res != 0:
                    err = ctypes.get_errno()
                    raise OSError(err, "prctl(PR_SET_PDEATHSIG) failed")

        else:
            def setup(): # Mac
                pass

        if self.tray_process == None:
            self.tray_process = subprocess.Popen(tray_subprocess_input, preexec_fn=setup, start_new_session=True)

        global tray_process_global
        tray_process_global = self.tray_process

        tray_process_connection_thread = threading.Thread(target=tray_process_connection, daemon=True)
        tray_process_connection_thread.start()
