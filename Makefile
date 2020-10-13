EX_DIR=examples
SCR_DIR=renishawWiRE
EX_PYS:=$(wildcard $(EX_DIR)/ex*.py)
PKG_PYS:=$(wildcard $(SCR_DIR)/*.py)
DOWN_DONE=.downloaded
PIP_DONE=.piped

.PHONY: examples download $(EX_PYS) pip

pip: $(PIP_DONE)

$(PIP_DONE): setup.py $(PKG_PYS)
	pip install --upgrade ".[plot]"
	@touch $@

download: $(DOWN_DONE)

$(DOWN_DONE): $(EX_DIR)/spectra_files
	curl -LO https://github.com/alchem0x2A/py-wdf-reader/releases/download/binary/spectra_files.zip
	unzip -o spectra_files.zip -d examples/
	rm spectra_files.zip
	touch $@

examples: download pip $(EX_PYS)

$(EX_PYS):
	cd $(EX_DIR) &&\
	python $(shell basename $@)
