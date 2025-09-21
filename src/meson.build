pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'varia'
moduledir_window = pkgdatadir / 'varia' / 'window'
moduledir_download = pkgdatadir / 'varia' / 'download'
moduledir_tray = pkgdatadir / 'varia' / 'tray'

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)
conf.set(
  'DESKTOP_FILE_LOCATION',
  get_option('prefix') / get_option('datadir') / 'applications' / 'io.github.giantpinkrobots.varia.desktop',
)

configure_file(
  input: 'varia-py.in',
  output: 'varia-py.py',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x',
)

configure_file(
  input: 'varia.in',
  output: 'varia',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x',
)

configure_file(
  input: 'autostart_util_linux.in',
  output: 'autostart_util_linux.py',
  configuration: conf,
  install: true,
  install_dir: moduledir,
  install_mode: 'rw-r--r--',
)

varia_sources = [
  'variamain.py',
  'initiate.py',
  'stringstorage.py',
  'autostart_util.py',
]

varia_sources_window = [
  'window/content.py',
  'window/sidebar.py',
  'window/preferences.py',
  'window/scheduler.py',
  'window/updater.py',
]

varia_sources_download = [
  'download/actionrow.py',
  'download/thread.py',
  'download/communicate.py',
  'download/listen.py',
  'download/scheduler.py',
  'download/videos.py',
  'download/details.py',
]

varia_sources_tray = [
  'tray/tray_linux.py',
  'tray/tray_windows.py',
  'tray/tray.png',
]

install_data(varia_sources, install_dir: moduledir)
install_data(varia_sources_window, install_dir: moduledir_window)
install_data(varia_sources_download, install_dir: moduledir_download)
install_data(varia_sources_tray, install_dir: moduledir_tray)
