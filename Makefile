VENV_DIR := venv

# venv layout differs between Windows and Unix-like systems
ifeq ($(OS),Windows_NT)
	PYTHON_BIN := python
	VENV_PYTHON := $(VENV_DIR)/Scripts/python.exe
else
	PYTHON_BIN := python3
	VENV_PYTHON := $(VENV_DIR)/bin/python
endif

.PHONY: setup pipeline dashboard

# installs all necessary dependencies (creates a virtual environment and
# installs everything listed in requirements.txt into it)
# note: pip is invoked via 'python -m pip' rather than calling pip.exe
# directly -- on Windows, pip.exe can't overwrite itself mid-upgrade
setup:
	$(PYTHON_BIN) -m venv $(VENV_DIR)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt

# runs the full data pipeline end-to-end, no manual steps required
pipeline:
	$(VENV_PYTHON) load_data.py

# starts the local dashboard server
dashboard:
	$(VENV_PYTHON) app.py