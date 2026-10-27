# highschool-performance

Analysis of English secondary school performance, applications and catchments, using Department for Education data.

Written to inform parent's choices in applying for year 7 places. 

## Configuration

Configurations, such as which schools and years, to analyse are set in the JSON files under `src\config`. 

   - To change general settigns, edit `src/settings.json`
   - To add school addresses for geolocation, edit `src/school_addresses.json`
   - To add school catchment distances, typically available from authority websites, edit `src\catchment_distances.json`


## Run

To run the full pipeline, from `src/` run:

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

Raw and processed data are saved under `data/` and charts under `charts/`. Stored data will be used where it is available. To reprocess data, for example after a config change, delete the relevant files in `/data/processed/`. To re-download raw data from source, delete bothe processed data files in `data/processed/` and `data/raw/`. 

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

## Charts

Here are some indicative charts for a selection of schools in Haringey, London. 


### Attainment 8 (2024) against KS2 prior attainment (2019)

![Attainment 8 (2024) against KS2 prior attainment (2019)](charts/a8_ks2_scatter.png)


### Progress 8 (2024) against KS2 prior attainment (2019)

![Progress 8 (2024) against KS2 prior attainment (2019)](charts/p8_ks2_scatter.png)


### Progress 8 (2024) against KS2 prior attainment (2019)

Key: P8[CI Upper, CI Lower, N]
CI: Confidence Interval at 95% level. 

![Progress 8 (2024) against KS2 prior attainment (2019)](charts/p8_ks2_band_table.png)

### Prior Attainment Profile (KS2) for 2024 GCSE Cohort (2019 Intake)

![Prior Attainment Profile (KS2) for 2024 GCSE Cohort (2019 Intake)](charts/ks2_band_distribution.png)


### Progress 8 by KS2 prior attainment, 2022/23 and 2023/24

![Progress 8 by KS2 prior attainment, 2022/23 and 2023/24](charts/p8_by_prior_attainment.png)


### Attainment 8 by prior attainment group

![Attainment 8 by prior attainment group](charts/a8_band_distribution.png)


### Progress 8 by sex, 2022/23 and 2023/24

![Progress 8 by sex, 2022/23 and 2023/24](charts/p8_by_sex.png)


### All schools catchment distances, 2026 admissions

![All schools catchment distances, 2026 admissions](charts/all_schools_catchments_2026.png)


### Greig catchment distances by admissions year

![Greig catchment distances by admissions year](charts/Greig_catchments.png)



