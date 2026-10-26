# education-analysis

Analysis of English secondary school performance and catchments, using Department for Education data.

## Run

From `src/`:

```bash
python -m app
```

With no flags, both pipelines get their data and then plot it. `--performance` or `--places` selects a pipeline. `--get-data` or `--plot-data` selects a step. Leave a pair unset to run both of that pair.

```bash
python -m app --performance
python -m app --places
python -m app --performance --get-data
python -m app --places --plot-data
```

Each pipeline can also be run on its own:

```bash
python -m performance.run_performance
python -m places.run_places
```

Tables are saved under `data/` and charts under `charts/`.

## Layout

```
charts/                      saved charts
data/processed/              cleaned tables used for analysis
data/raw/                    downloaded source files
maps/                        saved maps
notebooks/                   exploratory analysis
src/app.py                   entrypoint for the pipelines
src/catchment/               catchment maps
src/config/                  schools, years, and dataset URLs
src/data_models/             shared configuration model
src/performance/             attainment and progress pipeline
src/places/                  applications and Year 7 roll pipeline
src/shared_funcitons.py      download, load, and logging helpers
tests/                       tests
environment.yml              conda environment
LICENSE                      MIT license
pyproject.toml               project metadata
README.md                    this file
```

Downloaded files and generated images stay out of git. The folders are kept with `.gitkeep` files.
