pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'varia'
moduledir_window = pkgdatadir / 'varia' / 'window'
moduledir_download = pkgdatadir / 'varia' / 'download'

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'varia-py.in',
  output: 'varia-py.py',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

configure_file(
  input: 'varia.in',
  output: 'varia',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

varia_sources = [
  'variamain.py',
  'initiate.py',
]

varia_sources_window = [
  'window/content.py',
  'window/sidebar.py',
  'window/preferences.py',
  'window/scheduler.py',
  'window/tray.py'
]

varia_sources_download = [
  'download/actionrow.py',
  'download/thread.py',
  'download/communicate.py',
  'download/listen.py',
  'download/scheduler.py',
]

install_data(varia_sources, install_dir: moduledir)
install_data(varia_sources_window, install_dir: moduledir_window)
install_data(varia_sources_download, install_dir: moduledir_download)
