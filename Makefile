.PHONY: sdist docs clean

sdist: clean
	python setup.py sdist

docs:
	asciidoc AUTHORS
	asciidoc CHANGES
	asciidoc INSTALL
	asciidoc LICENSE
	asciidoc README
	asciidoc RELEASE_NOTES
	cd docs && asciidoc UserGuide

clean:
	rm -f *~
	rm -f .DS_Store
	rm -f *.html
	rm -rf docs/*.html
	rm -f MANIFEST
	rm -rf build
	rm -rf dist
	rm -rf msp430bslu.egg-info
	rm -rf nsis
