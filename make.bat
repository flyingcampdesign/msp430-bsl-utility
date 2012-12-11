@if %~1 == docs (
  asciidoc.py AUTHORS
  asciidoc.py CHANGES
  asciidoc.py INSTALL
  asciidoc.py LICENSE
  asciidoc.py README
  asciidoc.py RELEASE_NOTES
  pushd .
    cd docs
    asciidoc.py UserGuide
  popd
) else if %~1 == sdist (
  make clean
  python setup.py sdist
) else if %~1 == installer (
  make clean
  make docs
  python setup.py py2exe
  mkdir nsis
  makensis setup.nsi
) else if %~1 == clean (
  python setup.py clean
  del /Q /F *~
  del /Q /F .DS_Store
  del /Q /F *.html
  del /Q docs\*.html
  del MANIFEST
  RD /Q /S build
  RD /Q /S dist
  RD /Q /S msp430bslu.egg-info
  RD /Q /S nsis
) else (
  echo %~1 is not a supported make target!
  goto DONE
)

:DONE