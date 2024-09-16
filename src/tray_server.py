import asyncio
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method
import subprocess

class TrayServer(ServiceInterface):
    def __init__(self, variaapp):
        super().__init__('io.github.giantpinkrobots.varia.tray')
        self.variaapp = variaapp

        if self.variaapp.appconf["default_mode"] == "background":
            self.visibility = False
        else:
            self.visibility = True
            self.variaapp.show()

    @method()
    async def toggle_window(self) -> 'b':
        if self.visibility:
            self.variaapp.hide()
            self.visibility = False
        else:
            self.variaapp.show()
            self.visibility = True

        return self.visibility

    @method()
    async def get_window_state(self) -> 'b':
        return self.visibility

    @method()
    async def exit_varia(self):
        self.variaapp.exitProgram(self.variaapp, self.variaapp, False)

class TrayServerRunner:
    def __init__(self, variaapp):
        self.variaapp = variaapp

    async def run(self):
        bus = await MessageBus().connect()
        tray_server = TrayServer(self.variaapp)
        bus.export('/TrayServer', tray_server)
        await bus.request_name('io.github.giantpinkrobots.varia.tray')

        self.variaapp.tray_process = subprocess.Popen([self.variaapp.trayexec, self.variaapp.localedir])

        while (self.variaapp.terminating != True):
            await asyncio.sleep(0.1)
            continue
