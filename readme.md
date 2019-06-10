# skedulord

## project structure 

```
│
├── data/               <- The original, immutable data dump. 
├── notebooks/          <- Jupyter notebooks. Naming convention is a short `-` delimited 
│                          description, a number (for ordering), and the creator's initials,
│                          e.g. `initial-data-exploration-01-hg`.
├── tests/              <- Unit tests.
├── skedulord/      <- Python module with source code of this project.
├── Makefile            <- Makefile with commands like `make environment`
└── README.md           <- The top-level README for developers using this project.
```

## installation 

Install `skedulord` in the virtual environment via:

```bash
$ pip install --editable .
```
