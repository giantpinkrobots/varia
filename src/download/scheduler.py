import datetime
from gi.repository import GLib
from stringstorage import gettext as _

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
            self.download_button_icon.set_from_icon_name("camera-video-symbolic")
            self.video_button_icon.set_from_icon_name("camera-video-symbolic")
            self.all_paused = True
            self.pause_all()

        else:
            self.download_button_icon.set_from_icon_name("alarm-symbolic")
            self.video_button_icon.set_from_icon_name("alarm-symbolic")
            self.all_paused = False
            self.pause_all()

    previous_state = self.scheduler_currently_downloading

    GLib.timeout_add(1000, schedule_downloads, self, previous_state)
