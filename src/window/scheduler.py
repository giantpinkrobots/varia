import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from stringstorage import gettext as _

def add_timespan_clicked(button, self, timespans_box, day, start_h, start_m, end_h, end_m, switch_enabled):
    timespan_row = Adw.Bin()
    timespan_row.add_css_class('card')

    switch_enabled.set_sensitive(True)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    box.set_margin_start(10)
    box.set_margin_end(10)
    box.set_margin_top(10)
    box.set_margin_bottom(10)
    timespan_row.set_child(box)

    timespan_box_header = Gtk.Box()
    timespan_box_content = Gtk.Box()

    days_combobox = Gtk.ComboBoxText()
    all_days = [_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), _("Saturday"), _("Sunday")]

    for day_in_days in all_days:
        days_combobox.append_text(day_in_days)

    days_combobox.set_active(day)

    remove_button = Gtk.Button.new_from_icon_name("process-stop-symbolic")
    remove_button.set_valign(Gtk.Align.CENTER)
    remove_button.add_css_class("circular")
    remove_button.add_css_class("destructive-action")
    remove_button.connect("clicked", remove_timespan, self, timespans_box, timespan_row, len(self.timespans_list), switch_enabled)

    timespan_count_label = Gtk.Label()
    timespan_count_label.add_css_class("heading")
    timespan_box_header.append(timespan_count_label)
    timespan_box_header.append(Gtk.Box(hexpand=True))
    timespan_box_header.append(days_combobox)
    timespan_box_header.append(Gtk.Box(hexpand=True))
    timespan_box_header.append(remove_button)

    box.append(timespan_box_header)

    timespan_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    start_timespan_box = Gtk.Box(spacing=2, halign=Gtk.Align.END)
    end_timespan_box = Gtk.Box(spacing=2, halign=Gtk.Align.END)

    start_timespan_label = Gtk.Label(label=_("Start (h/m):"))
    start_timespan_spin_h = Gtk.SpinButton.new_with_range(0, 23, 1)
    start_timespan_spin_h.set_value(float(start_h))
    start_timespan_spin_m = Gtk.SpinButton.new_with_range(0, 59, 1)
    start_timespan_spin_m.set_value(float(start_m))
    end_timespan_label = Gtk.Label(label=_("End (h/m):"))
    end_timespan_spin_h = Gtk.SpinButton.new_with_range(0, 23, 1)
    end_timespan_spin_h.set_value(float(end_h))
    end_timespan_spin_m = Gtk.SpinButton.new_with_range(0, 59, 1)
    end_timespan_spin_m.set_value(float(end_m))

    start_timespan_box.append(start_timespan_label)
    start_timespan_box.append(start_timespan_spin_h)
    start_timespan_box.append(start_timespan_spin_m)
    end_timespan_box.append(end_timespan_label)
    end_timespan_box.append(end_timespan_spin_h)
    end_timespan_box.append(end_timespan_spin_m)

    timespan_separator = Gtk.Separator()

    timespan_box.append(start_timespan_box)
    timespan_box.append(timespan_separator)
    timespan_box.append(end_timespan_box)

    timespan_box_content.append(Gtk.Box(hexpand=True))
    timespan_box_content.append(timespan_box)
    timespan_box_content.append(Gtk.Box(hexpand=True))

    box.append(timespan_box_content)

    timespans_box.append(timespan_row)
    timespan_info = {'id': len(self.timespans_list), 'day': days_combobox, 'start_h': start_timespan_spin_h, 'start_m': start_timespan_spin_m, 'end_h': end_timespan_spin_h, 'end_m': end_timespan_spin_m, 'label': timespan_count_label}
    self.timespans_list.append(timespan_info)

    adjust_timespan_labels(self)

def remove_timespan(button, self, timespans_box, timespan_row, timespan_id, switch_enabled):
    timespan_row.unrealize()
    timespans_box.remove(timespan_row)
    self.timespans_list = [item for item in self.timespans_list if item.get('id') != timespan_id]
    if_there_are_any_timespans(self, switch_enabled)
    adjust_timespan_labels(self)

def change_schedule_mode(switch, state, self, mode, switch_mode_1, switch_mode_2):
    if (mode == 'inclusive'):
        if state:
            switch_mode_2.set_active(False)
        else:
            switch_mode_2.set_active(True)
    elif (mode == 'exclusive'):
        if state:
            switch_mode_1.set_active(False)
        else:
            switch_mode_1.set_active(True)

def save_schedule(preferencesDialog, self, preferencesWindow, switch_mode_1, switch_enabled):
    if switch_enabled.get_state():
        self.appconf["schedule_enabled"] = 1
        self.sidebar_scheduler_label.set_label(_("Scheduler enabled"))
    else:
        self.appconf["schedule_enabled"] = 0
        self.sidebar_scheduler_label.set_label("")

    if switch_mode_1.get_state():
        self.appconf["schedule_mode"] = 'inclusive'
    else:
        self.appconf["schedule_mode"] = 'exclusive'

    timespan_appconf = []

    for item in self.timespans_list:
        timespan_day = item['day'].get_active()
        timespan_start_h = item['start_h'].get_value_as_int()
        timespan_start_m = item['start_m'].get_value_as_int()
        timespan_end_h = item['end_h'].get_value_as_int()
        timespan_end_m = item['end_m'].get_value_as_int()

        timespan_appconf.append([timespan_day, timespan_start_h, timespan_start_m, timespan_end_h, timespan_end_m])

    self.appconf["schedule"] = timespan_appconf
    self.save_appconf()
    preferencesWindow.pop_subpage()

def if_there_are_any_timespans(self, switch_enabled):
    if self.timespans_list == []:
        switch_enabled.set_sensitive(False)
        switch_enabled.set_active(False)
        self.appconf["schedule_enabled"] = 0
        self.sidebar_scheduler_label.set_label("")
        self.save_appconf()

def adjust_timespan_labels(self):
    i = 1
    for timespan in self.timespans_list:
        timespan['label'].set_label(str(i) + " / " + str(len(self.timespans_list)))
        i += 1

def show_scheduler_dialog(self, preferencesWindow, variaapp, show_preferences, variaVersion):
    schedulerDialog = Adw.NavigationPage(title=_("Scheduler"))

    self.timespans_list = []

    root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    main_box.set_margin_start(15)
    main_box.set_margin_end(15)
    main_box.set_margin_top(15)
    main_box.set_margin_bottom(15)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_child(root_box)

    schedulerDialog_headerbar = Adw.HeaderBar()
    schedulerDialog_headerbar.set_show_end_title_buttons(False)
    schedulerDialog_headerbar.add_css_class('flat')
    
    root_box.append(schedulerDialog_headerbar)
    root_box.append(main_box)
    schedulerDialog.set_child(scrolled_window)

    modes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

    box_enabled = Gtk.Box()

    label_enabled = Gtk.Label(label=_("Enabled"))

    expanding_box_enabled = Gtk.Box()
    Gtk.Widget.set_hexpand(expanding_box_enabled, True)

    switch_enabled = Gtk.Switch()
    switch_enabled.set_active(self.appconf["schedule_enabled"])

    box_enabled.append(label_enabled)
    box_enabled.append(expanding_box_enabled)
    box_enabled.append(switch_enabled)

    box_mode_1 = Gtk.Box()
    label_mode_1 = Gtk.Label(label=_("Start downloading in these times"))
    expanding_box_mode_1 = Gtk.Box()
    Gtk.Widget.set_hexpand(expanding_box_mode_1, True)
    switch_mode_1 = Gtk.Switch()
    if self.appconf["schedule_mode"] == 'inclusive':
        switch_mode_1.set_active(True)
    box_mode_1.append(label_mode_1)
    box_mode_1.append(expanding_box_mode_1)
    box_mode_1.append(switch_mode_1)

    box_mode_2 = Gtk.Box()
    label_mode_2 = Gtk.Label(label=_("Stop downloading in these times"))
    expanding_box_mode_2 = Gtk.Box()
    Gtk.Widget.set_hexpand(expanding_box_mode_2, True)
    switch_mode_2 = Gtk.Switch()
    if self.appconf["schedule_mode"] == 'exclusive':
        switch_mode_2.set_active(True)
    box_mode_2.append(label_mode_2)
    box_mode_2.append(expanding_box_mode_2)
    box_mode_2.append(switch_mode_2)

    switch_mode_1.connect("state-set", change_schedule_mode, self, 'inclusive', switch_mode_1, switch_mode_2)
    switch_mode_2.connect("state-set", change_schedule_mode, self, 'exclusive', switch_mode_1, switch_mode_2)

    modes_box.append(box_enabled)
    separator_1 = Gtk.Separator()
    modes_box.append(separator_1)
    modes_box.append(box_mode_1)
    modes_box.append(box_mode_2)

    main_box.append(modes_box)

    separator_2 = Gtk.Separator()
    main_box.append(separator_2)

    timespans_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    
    add_timespan_button = Gtk.Button(label=_("Add Timespan"))
    add_timespan_button.set_halign(Gtk.Align.CENTER)
    add_timespan_button.add_css_class("pill")
    add_timespan_button.add_css_class("suggested-action")
    add_timespan_button.connect("clicked", add_timespan_clicked, self, timespans_box, 0, 0, 0, 0, 0, switch_enabled)

    main_box.append(add_timespan_button)

    main_box.append(timespans_box)

    save_button = Gtk.Button(tooltip_text=_("Save"), label=_("Save"))
    save_button.connect("clicked", save_schedule, self, preferencesWindow, switch_mode_1, switch_enabled)
    save_button.add_css_class("suggested-action")
    schedulerDialog_headerbar.pack_end(save_button)

    # Build timespans from appconf:
    for item in self.appconf["schedule"]:
        add_timespan_clicked('no', self, timespans_box, item[0], item[1], item[2], item[3], item[4], switch_enabled)

    if_there_are_any_timespans(self, switch_enabled)

    preferencesWindow.push_subpage(schedulerDialog)
    #schedulerDialog.present(self)
