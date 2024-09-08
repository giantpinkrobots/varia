pkgdatadir = get_option('prefix') / get_option('datadir') / 'varia'
moduledir = pkgdatadir / 'varia' / 'tray'

buildtype = get_option('buildtype')

bindir = join_paths(join_paths('target', buildtype, 'varia-tray'))

message('Building tray program...')
if buildtype == 'debug'
  cargo = [find_program('cargo'), 'build']
elif buildtype == 'release'
  cargo = [find_program('cargo'), 'build', '--release']
endif

build = run_command(cargo, check: true)
install_data(bindir, install_dir: moduledir)
