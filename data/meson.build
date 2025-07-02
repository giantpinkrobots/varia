desktop_file = i18n.merge_file(
        input: 'io.github.giantpinkrobots.varia.desktop.in',
       output: 'io.github.giantpinkrobots.varia.desktop',
         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: get_option('datadir') / 'applications'
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

appstream_file = i18n.merge_file(
        input: 'io.github.giantpinkrobots.varia.metainfo.xml.in',
       output: 'io.github.giantpinkrobots.varia.metainfo.xml',
       po_dir: '../po',
      install: true,
  install_dir: get_option('datadir') / 'metainfo'
)

appstreamcli = find_program('appstreamcli', required: false, disabler: true)
test('Validate appstream file', appstreamcli,
     args: ['validate', '--no-net', '--explain', appstream_file])

install_data('io.github.giantpinkrobots.varia.gschema.xml',
  install_dir: get_option('datadir') / 'glib-2.0' / 'schemas'
)

install_data('io.github.giantpinkrobots.varia.mime.xml',
    install_dir: join_paths(get_option('datadir'), 'mime', 'packages')
)

install_data('io.github.giantpinkrobots.varia.mime.svg',
  install_dir: join_paths(get_option('datadir'), 'icons', 'hicolor', 'scalable', 'mimetypes')
)

install_data('io.github.giantpinkrobots.varia.service',
  install_dir: join_paths(get_option('datadir'), 'dbus-1', 'services')
)


compile_schemas = find_program('glib-compile-schemas', required: false, disabler: true)
test('Validate schema file',
     compile_schemas,
     args: ['--strict', '--dry-run', meson.current_source_dir()])

subdir('icons')
