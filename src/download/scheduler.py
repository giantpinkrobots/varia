import datetime
from gi.repository import GLib

def schedule_downloads(self, previous_state):
    if self.appconf["schedule_enabled"] == 1:
        now_is_within_a_timespan = False

        for timespan in self.appconf['schedule']:
            weekday = timespan[0]

            timespan_time_start = datetime.time(timespan[1], timespan[2])
            timespan_time_end = datetime.time(timespan[3], timespan[4])

            if ( (weekday == datetime.datetime.now().weekday())
                and (datetime.datetime.now().time() >= timespan_time_start)
                and (datetime.datetime.now().time() < timespan_time_end) ):
                now_is_within_a_timespan = True

        if (self.appconf["schedule_mode"] == 'inclusive'):
            if now_is_within_a_timespan == True:
                self.scheduler_currently_downloading = True
            else:
                self.scheduler_currently_downloading = False
        else:
            if now_is_within_a_timespan == False:
                self.scheduler_currently_downloading = True
            else:
                self.scheduler_currently_downloading = False

    else:
        self.scheduler_currently_downloading = True

    if previous_state != self.scheduler_currently_downloading:
        if self.scheduler_currently_downloading == True:
            self.download_button.set_label(_("Download"))
            self.all_paused = True
            self.pause_all(self.header_pause_content)

        else:
            self.download_button.set_label(_("Schedule"))
            self.all_paused = False
            self.pause_all(self.header_pause_content)

    previous_state = self.scheduler_currently_downloading

    GLib.timeout_add(1000, schedule_downloads, self, previous_state)
