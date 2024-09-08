import dbus
import dbus.mainloop.glib
import dbus.service

from gi.repository import GLib

class TrayServer(dbus.service.Object):
    def __init__(self, path, variaapp) -> None:
        self.variaapp = variaapp

        if self.variaapp.appconf["default_mode"] == "background":
            self.visibility = False
        else:
            self.visibility = True
            self.variaapp.show()

        dbus.service.Object.__init__(self, dbus.SessionBus(), path)

    @dbus.service.method(dbus_interface='io.github.giantpinkrobots.varia.tray', in_signature='', out_signature='b')
    def toggle_window(self):
        if self.visibility:
            self.variaapp.hide()
            self.visibility = False
        else:
            self.variaapp.show()
            self.visibility = True

        return dbus.Boolean(self.visibility)

    @dbus.service.method(dbus_interface='io.github.giantpinkrobots.varia.tray', in_signature='', out_signature='b')
    def get_window_state(self):
        return dbus.Boolean(self.visibility)

    @dbus.service.method(dbus_interface='io.github.giantpinkrobots.varia.tray', in_signature='', out_signature='')
    def exit_varia(self):
        self.variaapp.exitProgram(self.variaapp, self.variaapp, False)

class TrayServerRunner:
    def __init__(self, variaapp) -> None:
        self.variaapp = variaapp
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self.session_bus = dbus.SessionBus()
        self.bus_name = dbus.service.BusName("io.github.giantpinkrobots.varia.tray", self.session_bus)
        self.tray_server = TrayServer(path='/TrayServer', variaapp=self.variaapp)

    def run(self):
        self.loop = GLib.MainLoop()
        self.loop.run()

    def exit(self):
        self.loop.quit()
