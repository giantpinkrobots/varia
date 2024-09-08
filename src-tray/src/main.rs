mod comm;

use std::{env, time::Duration};

use comm::DBusManager;
use dbus::blocking::Connection;
use gettextrs::gettext;
use ksni::{self, menu::StandardItem, MenuItem};

pub struct VariaTray<'a> {
    visible: bool,
    manager: DBusManager<'a>,
}

impl<'a> ksni::Tray for VariaTray<'a> {
    fn icon_name(&self) -> String {
        "io.github.giantpinkrobots.varia".into()
    }
    fn title(&self) -> String {
        gettext("Varia")
    }
    fn id(&self) -> String {
        env!("CARGO_PKG_NAME").into()
    }
    fn menu(&self) -> Vec<ksni::MenuItem<Self>> {
        vec![
            StandardItem {
                label: if self.visible {
                    gettext("Hide Varia")
                } else {
                    gettext("Show Varia")
                },
                activate: Box::new(|this: &mut Self| {
                    this.visible = this.manager.toggle_window().unwrap()
                }),
                ..Default::default()
            }
            .into(),
            MenuItem::Separator,
            StandardItem {
                label: gettextrs::gettext("Exit Varia"),
                activate: Box::new(|this: &mut Self| this.manager.exit_varia().unwrap()),
                ..Default::default()
            }
            .into(),
        ]
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let localedir = &args[1];

    gettextrs::bindtextdomain("varia", localedir)?;
    gettextrs::textdomain("varia")?;

    let session = Box::leak(Box::new(Connection::new_session()?));

    let proxy = session.with_proxy(
        "io.github.giantpinkrobots.varia.tray",
        "/TrayServer",
        Duration::from_millis(5000),
    );

    let manager = DBusManager { proxy };

    let tray = ksni::TrayService::new(VariaTray {
        visible: false,
        manager,
    });

    let handle = tray.handle();

    handle.update(|tray: &mut VariaTray| {
        let (window_state,): (bool,) = session
            .with_proxy(
                "io.github.giantpinkrobots.varia.tray",
                "/TrayServer",
                Duration::from_millis(5000),
            )
            .method_call(
                "io.github.giantpinkrobots.varia.tray",
                "get_window_state",
                (),
            )
            .unwrap();
        tray.visible = window_state;
    });

    tray.run()?;

    Ok(())
}
