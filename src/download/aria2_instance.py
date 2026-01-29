import os
import subprocess
import json
import requests
import socket
import ctypes
import signal

class Aria2Instance:
    def __init__(self, appconf, aria2cexec):
        
        self.address = "http://localhost"
        self.port = "6801"
        self.appconf = appconf
        self.aria2cexec = aria2cexec
    
    def start_subprocess(self):
        aria2_config = [
            "--enable-rpc",
            "--rpc-listen-port=6801",
            "--rpc-allow-origin-all",
            "--follow-torrent=false",
            "--allow-overwrite=false",
            "--auto-file-renaming=true",
            "--min-split-size=1M",
            "--http-accept-gzip=true",
            "--disk-cache=128M",
            "--bt-enable-lpd=true",
            "--bt-hash-check-seed=true",
            "--enable-peer-exchange=true",
            "--enable-dht=true",
            "--enable-dht6=true",
            "--peer-agent=Transmission/3.00", # Some people block aria2's native user agent id because it
                                            # doesn't do any seeding by default. Thus here we change it
            "--peer-id-prefix=-TR3000-",      # to mimic Transmission instead.
            "--split=32",
            "--max-connection-per-server=16",
            "--bt-max-peers=250",
            "--bt-request-peer-speed-limit=5M",
            "--bt-tracker-connect-timeout=10",
            "--bt-tracker-interval=30",
            "--bt-save-metadata=true"]
    
        if os.name != 'nt' and os.uname().sysname != 'Darwin': # Running Linux
            libc = ctypes.CDLL("libc.so.6", use_errno=True)

            PR_SET_PDEATHSIG = 1
            SIGTERM = signal.SIGTERM

            def setup():
                res = libc.prctl(PR_SET_PDEATHSIG, SIGTERM)
                if res != 0:
                    err = ctypes.get_errno()
                    raise OSError(err, "prctl(PR_SET_PDEATHSIG) failed")
        
        else:
            def setup(): # On other operating systems
                pass

        if (self.appconf['remote'] == '0'):
            if (os.name == 'nt'):
                import win32job
                import win32process
                import win32api

                CREATE_NEW_PROCESS_GROUP = 0x00000200
                self.aria2c_subprocess = subprocess.Popen([self.aria2cexec] + aria2_config, creationflags=CREATE_NEW_PROCESS_GROUP, shell=True)
                self.aria2c_job = win32job.CreateJobObject(None, "")

                info = win32job.QueryInformationJobObject(self.aria2c_job, win32job.JobObjectExtendedLimitInformation)
                info["BasicLimitInformation"]["LimitFlags"] |= (win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)

                win32job.SetInformationJobObject(self.aria2c_job, win32job.JobObjectExtendedLimitInformation, info)
                win32job.AssignProcessToJobObject(self.aria2c_job, self.aria2c_subprocess._handle)

            else:
                if hasattr(os, 'posix_fallocate'):
                    aria2_config.append("--file-allocation=falloc") # Set fallocate on Linux for better performance
                    print("fallocate enabled.")
                    self.aria2c_subprocess = subprocess.Popen([self.aria2cexec] + aria2_config, preexec_fn=setup, start_new_session=True)

                else:
                    self.aria2c_subprocess = subprocess.Popen([self.aria2cexec] + aria2_config, preexec_fn=setup, start_new_session=True)
    
    def send_rpc_request(self, method):
        try:
            token = "token:" + self.appconf['remote_secret']
            json_request = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": method,
                "params":[token]
            }
            
            request = requests.post(f"{self.address}:{self.port}/jsonrpc", headers={'Content-Type': 'application/json'}, data=json.dumps(json_request))
            request.raise_for_status()
            return "result" in request.json()
        
        except:
            return -1
        
    def check_port_is_taken(self):
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            connection.bind((self.address, int(self.port)))
            in_use = False
        except:
            in_use = True
        finally:
            connection.close()

        return in_use
    
    def set_address_and_port(self, address, port):
        self.address = address
        self.port = port
