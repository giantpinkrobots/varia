project('varia',
          version: 'v2025.10.14',
    meson_version: '>= 0.61.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'varia'

i18n = import('i18n')
gnome = import('gnome')



subdir('data')
subdir('src')
subdir('po')

install_subdir('dependencies_information', install_dir: moduledir)

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
