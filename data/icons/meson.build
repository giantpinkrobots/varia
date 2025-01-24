application_id = 'io.github.giantpinkrobots.varia'

scalable_dir = 'hicolor' / 'scalable' / 'apps'
install_data(
  scalable_dir / ('@0@.svg').format(application_id),
  install_dir: get_option('datadir') / 'icons' / scalable_dir
)

symbolic_dir = 'hicolor' / 'symbolic' / 'apps'
install_subdir(
  symbolic_dir,
  install_dir: get_option('datadir') / 'icons' / 'hicolor/symbolic'
)