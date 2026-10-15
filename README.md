# education-analysis

Analysis of English secondary school performance and catchments, using Department for Education data.

## Layout

```
data/raw/                  downloaded source files
data/processed/            cleaned tables used for analysis
notebooks/                 exploratory analysis
src/download_dfe.py        fetch DfE performance data
src/process_data.py        clean raw files into processed tables
src/plot_performance.py    performance charts
src/plot_catchments.py     catchment maps
outputs/charts/            saved charts
outputs/maps/              saved maps
tests/                     tests
```

Downloaded files and generated images stay out of git. The folders are kept with `.gitkeep` files.
