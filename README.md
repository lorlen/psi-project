# PSI Project

## Usage

### Prerequisites

* Python 3.10 (older versions may work, but they were not tested)
* Poetry (can be installed via `pip install poetry`)

### Run the program

To avoid problems, it's best to set Poetry to create virtualenvs in the project directory:

```
poetry config virtualenvs.in-project true
```

Then, switch to the project directory and install the project's dependencies with:

```
poetry install --no-dev
```

And finally, you can run it using:

```
poetry run
```

Alternatively, the project can be run without using Poetry, by running:

```
.venv/bin/python -m psi_project
```

or:

```
. .venv/bin/activate
python -m psi_project
```

The second example assumes a POSIX-compatible shell. If you are using a different shell, you should select an appropriate `activate.*` script.
