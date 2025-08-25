import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from stringstorage import gettext as _
import json
import threading
import os
import subprocess
import time

update_download_progress = 0

def windows_updater(bannerButton, app, variaapp, parentWindow, variaVersion, mode):
    if mode == 1:
        if parentWindow is not None:
            parentWindow.close()

        # Show checking for updates dialog
        checking_dialog = Adw.AlertDialog()
        checking_dialog_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
        checking_dialog.set_child(checking_dialog_box)
        checking_dialog_box.set_margin_top(30)
        checking_dialog_box.set_margin_bottom(30)
        checking_dialog_box.set_margin_start(60)
        checking_dialog_box.set_margin_end(60)
        checking_dialog_spinner = Adw.Spinner()
        checking_dialog_spinner.set_size_request(30, 30)
        checking_dialog_box.append(checking_dialog_spinner)
        checking_dialog_label = Gtk.Label(label=_("Checking for updates..."))
        checking_dialog_label.add_css_class("title-1")
        checking_dialog_box.append(checking_dialog_label)
        checking_dialog.set_can_close(False)
        checking_dialog.present(app)

    else:
        checking_dialog = None
        
    if os.path.exists(os.path.join(app.appdir, 'updater-all-releases.txt')):
        os.remove(os.path.join(app.appdir, 'updater-all-releases.txt'))
    
    thread = threading.Thread(target=lambda: start_update_check(variaVersion, app, variaapp, checking_dialog, mode), daemon=True)
    thread.start()

def start_update_check(variaVersion, app, variaapp, checking_dialog, mode):
    print(os.path.join(app.appdir, 'updater-all-releases.txt'))
    process = subprocess.Popen(
        [os.path.join(os.getcwd(), app.aria2cexec), '--quiet=true', '--console-log-level=warn', '--download-result=hide',
         '--out=updater-all-releases.txt', 'https://api.github.com/repos/giantpinkrobots/varia/releases'],
        text=True, shell=True, cwd = app.appdir
    )
    
    process.wait()
    
    if os.path.exists(os.path.join(app.appdir, 'updater-all-releases.txt')):
        all_releases = open(os.path.join(app.appdir, 'updater-all-releases.txt')).read()

        while True:
            try:
                os.remove(os.path.join(app.appdir, 'updater-all-releases.txt'))
                break

            except:
                time.sleep(0.5)
                pass

    else:
        latest_name_for_windows = "failed"
    
    i = 0
    while True:
        try:
            contents = json.loads(all_releases)[i]
        except:
            print("Couldn't check for updates.")
            latest_name_for_windows = "failed"
            break

        latest_name_for_windows = contents["name"]
        latest_windows_binary_url = 'https://github.com/giantpinkrobots/varia/releases/download/' + latest_name_for_windows + '/varia-windows-setup-amd64.exe'
        
        if latest_windows_binary_url in all_releases:
            break
        else:
            i += 1
            if i > len(json.loads(all_releases)):
                print("Couldn't check for updates.")
                latest_name_for_windows = "failed"
                break

    if checking_dialog != None:
        checking_dialog.set_can_close(True)
        checking_dialog.close()

    if latest_name_for_windows != variaVersion and latest_name_for_windows != "failed":
        if mode == 1:
            GLib.idle_add(show_update_question_dialog, update_pressed, latest_windows_binary_url, latest_name_for_windows, app, variaapp)
        else:
            GLib.idle_add(show_update_available_banner, windows_updater, app, variaapp, variaVersion)
            
def show_update_question_dialog(update_pressed, latest_windows_binary_url, latest_name_for_windows, app, variaapp):
    update_question_dialog = Adw.AlertDialog()
    update_question_dialog.set_body(_("A new version of Varia is available. Do you want to update?"))
    update_question_dialog.add_response("yes",  _("Yes"))
    update_question_dialog.add_response("no",  _("No"))
    update_question_dialog.set_response_appearance("yes", Adw.ResponseAppearance.SUGGESTED)
    update_question_dialog.connect("response", update_pressed, latest_windows_binary_url, latest_name_for_windows, app, variaapp)
    update_question_dialog.set_close_response("no")
    update_question_dialog.present(app)

def show_update_available_banner(windows_updater, app, variaapp, variaVersion):
    app.update_available_banner = Adw.Banner(title=_("Update available"))
    app.update_available_banner.set_button_label(_("Update"))
    app.update_available_banner.connect("button-clicked", windows_updater, app, variaapp, None, variaVersion, 1)
    app.update_available_banner.set_revealed(True)
    app.content_box.insert_child_after(app.update_available_banner, app.content_box.get_first_child())

def update_pressed(dialog, response_id, latest_windows_binary_url, latest_name_for_windows, app, variaapp):
    dialog.set_can_close(True)
    dialog.close()
    dialog = None
    
    if response_id == "no":
        print("Don't update")
    else:
        print("Begin update")

        update_downloading_dialog = Adw.AlertDialog()
        update_downloading_dialog_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
        update_downloading_dialog.set_child(update_downloading_dialog_box)
        update_downloading_dialog_box.set_margin_top(30)
        update_downloading_dialog_box.set_margin_bottom(30)
        update_downloading_dialog_box.set_margin_start(60)
        update_downloading_dialog_box.set_margin_end(60)

        update_downloading_dialog_spinner = Adw.Spinner()
        update_downloading_dialog_spinner.set_size_request(30, 30)
        update_downloading_dialog_box.append(update_downloading_dialog_spinner)

        update_downloading_dialog_label = Gtk.Label(label=_("Downloading update..."))
        update_downloading_dialog_label.add_css_class("title-1")
        update_downloading_dialog_box.append(update_downloading_dialog_label)

        update_downloading_dialog_progress_bar = Gtk.ProgressBar()
        update_downloading_dialog_box.append(update_downloading_dialog_progress_bar)

        update_downloading_dialog.set_can_close(False)
        update_downloading_dialog.present(app)
        
        def download_update():
            global update_download_progress
            process = subprocess.Popen(
                [app.aria2cexec, '--dir=' + app.appconf['download_directory'], '--out=variaUpdate-' + latest_name_for_windows + '.exe', '--quiet=false', '--summary-interval=1', latest_windows_binary_url],
                shell=True, text=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            
            while(True):
                if process.poll() != None:
                    break
                
                i = 0
                latest_output = ""
                
                try:
                    for line in iter(process.stdout.readline, b''):
                        latest_output = latest_output + line
                        i += 1
                        if i == 2:
                            break
                        
                    if ('(' in latest_output) and ('%' in latest_output):
                        open_parenthesis_location = latest_output.find('(') + 1
                        percent_location = latest_output.find('%')
                        current_percentage = int(latest_output[open_parenthesis_location: percent_location]) / 100
                        GLib.idle_add(update_downloading_dialog_progress_bar.set_fraction, current_percentage)
                except:
                    pass
            
            update_downloading_dialog.set_can_close(True)
            update_downloading_dialog.close()
            
            if process.returncode == 0:
                update_downloading_dialog_progress_bar.set_fraction(100)
                app.update_executable = os.path.join(app.appconf['download_directory'], "variaUpdate-" + latest_name_for_windows + ".exe")
                app.exitProgram(variaapp, variaapp, background=False)
            else:
                dialog = Adw.AlertDialog()
                dialog.set_body(_("Download failed."))
                dialog.add_response("ok",  _("OK"))
                dialog.set_close_response("ok")
                dialog.present(app)

        thread = threading.Thread(target=download_update, daemon=True)
        thread.start()
