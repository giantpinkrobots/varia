pub struct DBusManager<'a> {
    pub proxy: dbus::blocking::Proxy<'a, &'a dbus::blocking::Connection>,
}

impl<'a> DBusManager<'a> {
    pub fn toggle_window(&self) -> Result<bool, Box<dyn std::error::Error>> {
        let (new_state,): (bool,) =
            self.proxy
                .method_call("io.github.giantpinkrobots.varia.tray", "toggle_window", ())?;

        Ok(new_state)
    }

    pub fn exit_varia(&self) -> Result<(), Box<dyn std::error::Error>> {
        self.proxy
            .method_call("io.github.giantpinkrobots.varia.tray", "exit_varia", ())?;

        std::process::exit(0);
    }
}
