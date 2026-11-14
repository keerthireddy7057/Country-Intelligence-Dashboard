# Country Intelligence Dashboard

An interactive dashboard for exploring country-level demographic, economic, social, geographic, and electricity indicators. The application combines a FastAPI backend, SQLite data store, and responsive purple-themed HTML dashboard.

## Features

- Country profiles with ISO2 codes and UN M49 regions
- Side-by-side country comparison
- Indicator rankings and numeric filters
- Regional summary statistics
- Searchable country selectors
- Analytical findings and saved EDA charts
- 2024 electricity demand-versus-generation comparison, including the largest demand gaps
- JSON API with interactive Swagger documentation

## Quick start (Windows PowerShell)

1. Extract this ZIP.
2. Open PowerShell in the extracted `Country_Intelligence_Dashboard_Submission` folder.
3. Run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

4. Open the dashboard at <http://127.0.0.1:8000/dashboard>.
5. Open the API documentation at <http://127.0.0.1:8000/docs>.

To stop the local server, return to PowerShell and press `Ctrl+C`.

## API endpoints

- `GET /countries` — list or search countries
- `GET /countries/{country_name}` — retrieve a country profile
- `GET /countries/compare?country1=India&country2=China` — compare two countries
- `GET /rankings/population?limit=10` — rank by population
- `GET /rankings/gdp-per-capita?limit=10` — rank by GDP per capita
- `GET /regions/{region}/summary` — summarize a region
- `GET /insights/electricity-demand-exceeds-generation?limit=10` — return countries whose 2024 electricity demand exceeds generation

## Project structure

```text
Country_Intelligence_Dashboard_Submission/
├── app.py
├── index.html
├── requirements.txt
├── data/
│   ├── countries.db
│   ├── countries.csv
│   ├── countries_analysis.csv
│   ├── ember_electricity_2024.csv
│   ├── ember_generation_yearly_global.csv
│   ├── country_codes_iso.csv
│   └── source_workbooks/
├── docs/
│   ├── country_factbook_eda.ipynb
│   ├── data_dictionary.csv
│   ├── insight_report.md
│   └── charts/
└── README.md
```

`data/countries.csv` is the cleaned 100-country dataset used by the application. `data/countries_analysis.csv` is included as the input used by the EDA notebook. The SQLite database and 2024 Ember comparison file are required by the app.

## Data sources and interpretation

- The original country indicators were assembled from CIA World Factbook data. The provided source file did not include an estimate year for each field, so the data dictionary records those years as not recorded rather than inferring them.
- Region labels follow the UN M49 region classification.
- The ISO alpha-2 to alpha-3 country-code crosswalk is adapted from [datasets/country-codes](https://github.com/datasets/country-codes), released under the Open Data Commons Public Domain Dedication and License (PDDL).
- Electricity generation, demand, and net imports come from [Ember Yearly Electricity Data](https://ember-energy.org/data/yearly-electricity-data/), licensed under CC BY 4.0. The comparison uses 2024 records matched by ISO country code for 99 of the 100 dashboard countries; Ukraine has no matching 2024 record.
- Electricity values are in terawatt-hours (TWh). One TWh equals one billion kilowatt-hours. Demand above generation indicates net electricity imports in this comparison. This insight concerns electricity only, not total energy use across all fuels.
- The Factbook indicator values may reflect different estimate years. Avoid treating them as a synchronized, same-year panel.
- Missing source values remain missing; they should not be interpreted as zero.

See `docs/data_dictionary.csv` for column definitions, units, sources, and year notes. See `docs/insight_report.md` for the EDA findings and caveats.

## EDA notebook

The included notebook was prepared in Google Colab. To run it there, upload `data/countries_analysis.csv` into the Colab session before running the first cell. The notebook is supporting analysis; the dashboard runs from the packaged SQLite database and electricity comparison CSV.