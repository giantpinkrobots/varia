import os
win_reg_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

def get_autostart(): # Unused
    if os.name == 'nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, win_reg_key_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, "VariaAutostart")
                return True

        except:
            return False
    
    else:
        import autostart_util_linux
        return autostart_util_linux.get_autostart()

def set_autostart():
    if os.name == 'nt':
        import winreg
        import sys
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, win_reg_key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "VariaAutostart", 0, winreg.REG_SZ, f'"{sys.executable}"')
            return 0
        
        except Exception:
            return 1

    else:
        import autostart_util_linux
        try:
            autostart_util_linux.copy_autostart_file()
            return 0
        
        except Exception:
            return 1

def unset_autostart():
    if os.name == 'nt':
        import winreg
        import sys
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, win_reg_key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, "VariaAutostart")
        
        except:
            return 1

    else:
        import autostart_util_linux
        try:
            autostart_util_linux.delete_autostart_file()
            return 0
        
        except Exception:
            return 1