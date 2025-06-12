import sys
from multiprocessing.connection import Client

from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import PropertyAccess
from dbus_next.service import ServiceInterface, dbus_property, method
from dbus_next.signature import Variant


class TrayService(ServiceInterface):
    def __init__(self, icon_name: str, custom_icon: bool = False):
        super().__init__('org.kde.StatusNotifierItem')

        self.icon_name = ''
        self.icon_data = []
        self.width = 0
        self.height = 0

        self.icon_data = []
        self.icon_name = icon_name

    @dbus_property(PropertyAccess.READ)
    def Category(self) -> 's':
        return 'ApplicationStatus'

    @dbus_property(PropertyAccess.READ)
    def Id(self) -> 's':
        return 'io.giantpinkrobots.varia'

    @dbus_property(PropertyAccess.READ)
    def Title(self) -> 's':
        return 'Varia'

    @dbus_property(PropertyAccess.READ)
    def Status(self) -> 's':
        return 'Active'

    @dbus_property(PropertyAccess.READ)
    def WindowId(self) -> 'u':
        return 0

    @dbus_property(PropertyAccess.READ)
    def IconName(self) -> 's':
        return self.icon_name

    @dbus_property(PropertyAccess.READ)
    def IconPixmap(self) -> 'a(iiay)':
        return [[self.width, self.height, bytes(self.icon_data)]]

    @dbus_property(PropertyAccess.READ)
    def Menu(self) -> 'o':
        return '/Menu'

    @dbus_property(PropertyAccess.READ)
    def ToolTip(self) -> '(sa(iiay)ss)':
        return ['', [], 'Varia', '']


class TrayMenu(ServiceInterface):
    def __init__(self, show_text: str, quit_text: str):
        super().__init__('com.canonical.dbusmenu')

        self.version = 3
        self.text_direction = 'ltr'
        self.status = 'normal'

        self.show_text = show_text
        self.quit_text = quit_text

        self.varia_conn = None

        self.menu = [
            0,  # Root menu ID
            {"children-display": Variant('s', "submenu")},
            [
                # Show Varia option
                Variant('(ia{sv}av)', [
                    2,
                    {"label": Variant('s', self.show_text)},
                    []
                ]),

                # Separator
                Variant('(ia{sv}av)', [
                    3,
                    {"enabled": Variant('b', True), "type": Variant('s', 'separator')},
                    []
                ]),

                # Quit option
                Variant('(ia{sv}av)', [
                    4,
                    {"label": Variant('s', self.quit_text)},
                    []
                ])
            ]
        ]

    @dbus_property(PropertyAccess.READ)
    def Status(self) -> 's':
        return self.status

    @dbus_property(PropertyAccess.READ)
    def TextDirection(self) -> 's':
        return self.text_direction

    @dbus_property(PropertyAccess.READ)
    def Version(self) -> 'u':
        return self.version

    @dbus_property(PropertyAccess.READ)
    def IconThemePath(self) -> 'as':
        return []

    @method()
    async def GetLayout(self, parentId: 'i', recursionDepth: 'i', propertyNames: 'as') -> 'u(ia{sv}av)':
       return [self.version, self.menu]

    @method()
    async def GetGroupProperties(self, ids: 'ai', propertyNames: 'as') -> 'a(ia{sv})':
        result = []
        for id in ids:
            if id == 0:  # Root menu
                props = {'children-display': Variant('s', 'submenu')}
                result.append([id, props])
            elif id == 2:  # Show menu item
                props = {'label': Variant('s', self.show_text)}
                result.append([id, props])
            elif id == 3:  # Separator
                props = {'type': Variant('s', 'separator'), 'enabled': Variant('b', True)}
                result.append([id, props])
            elif id == 4:  # Quit menu item
                props = {'label': Variant('s', self.quit_text)}
                result.append([id, props])
        return result

    @method()
    async def Event(self, id: 'i', eventId: 's', data: 'v', timestamp: 'u'):
        if self.varia_conn is None:
            try:
                # Connect to the main Varia process
                self.varia_conn = Client(('localhost', 6802), authkey=b'varia-tray-process')
            except ConnectionRefusedError:
                return

        if eventId == 'clicked':
            if id == 2:
                # Show the Varia window
                self.varia_conn.send('show')
            elif id == 4:
                # Quit Varia
                self.varia_conn.send('quit')

    @method()
    async def EventGroup(self, events: 'a(isvu)') -> 'ai':
        if self.varia_conn is None:
            try:
                # Connect to the main Varia process
                self.varia_conn = Client(('localhost', 6802), authkey=b'varia-tray-process')
            except ConnectionRefusedError:
                print(events[0][0])
                return [events[0][0]]

        for event in events:
            id, eventId, data, timestamp = event

            if eventId == 'clicked':
                if id == 2:
                    # Show the Varia window
                    self.varia_conn.send('show')
                elif id == 4:
                    # Quit Varia
                    self.varia_conn.send('quit')

        return []

    @method()
    async def AboutToShow(self, id: 'i') -> 'b':
        return False

    @method()
    async def AboutToShowGroup(self, ids: 'ai') -> 'aiai':
        return [[], []]


async def main():
    bus = await MessageBus().connect()

    status_introspection = await bus.introspect('org.kde.StatusNotifierWatcher', '/StatusNotifierWatcher')

    status_proxy = bus.get_proxy_object('org.kde.StatusNotifierWatcher', '/StatusNotifierWatcher', status_introspection)

    status_watcher = status_proxy.get_interface('org.kde.StatusNotifierWatcher')

    icon_name = 'io.github.giantpinkrobots.varia-symbolic'

    # Create the tray service and menu
    tray = TrayService(icon_name=icon_name)
    menu = TrayMenu(sys.argv[1], sys.argv[2])

    bus_name = 'io.github.giantpinkrobots.varia-tray'

    # Register the service and export interfaces
    await bus.request_name(bus_name)
    bus.export('/StatusNotifierItem', tray)
    bus.export('/Menu', menu)

    # Register with the status notifier watcher
    await status_watcher.call_register_status_notifier_item(bus_name)

    # Keep the process running
    await bus.wait_for_disconnect()

if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting Tray...")
