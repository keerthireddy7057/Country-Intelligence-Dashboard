from pathlib import Path
import sqlite3

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

DATA_DIR = Path(__file__).with_name("data")
DB_FILE = DATA_DIR / "countries.db"

connection = sqlite3.connect(DB_FILE)
countries = pd.read_sql_query("SELECT * FROM countries", connection)
connection.close()

# Ember's 2024 electricity data uses TWh. Numerically, 1 TWh equals 1 billion kWh.
EMBER_FILE = DATA_DIR / "ember_electricity_2024.csv"
if EMBER_FILE.exists():
    ember = pd.read_csv(EMBER_FILE, keep_default_na=False)
    countries = countries.merge(ember, on="iso2", how="left")
    for column in [
        "ember_generation_twh",
        "ember_demand_twh",
        "ember_net_imports_twh",
        "ember_year",
    ]:
        countries[column] = pd.to_numeric(countries[column], errors="coerce")

app = FastAPI(title="Country Intelligence API", version="1.0.0")


def clean_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def clean_records(frame):
    return [
        {key: clean_value(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


@app.get("/")
def home():
    return {
        "message": "Country Intelligence API",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "countries": len(countries),
    }


@app.get("/countries")
def list_countries(
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=300),
):
    result = countries
    if search:
        result = result[
            result["country"].str.contains(search, case=False, na=False)
        ]
    return clean_records(result.head(limit))


@app.get("/search")
def search_by_indicator(
    indicator: str,
    min_value: float | None = Query(default=None, alias="min"),
    max_value: float | None = Query(default=None, alias="max"),
    limit: int = Query(default=100, ge=1, le=300),
):
    if indicator not in countries.columns or indicator in ["country", "iso2"]:
        raise HTTPException(
            status_code=400,
            detail="Use a numeric indicator column name",
        )

    result = countries.copy()
    result[indicator] = pd.to_numeric(result[indicator], errors="coerce")
    result = result.dropna(subset=[indicator])

    if min_value is not None:
        result = result[result[indicator] >= min_value]
    if max_value is not None:
        result = result[result[indicator] <= max_value]

    return clean_records(result.head(limit))


# Keep this before /countries/{country_name}.
@app.get("/countries/compare")
def compare_countries(country1: str, country2: str):
    names = [country1.casefold(), country2.casefold()]
    result = countries[
        countries["country"].str.casefold().isin(names)
    ]

    if len(result) != 2:
        raise HTTPException(
            status_code=404,
            detail="Check both country names; one or both were not found.",
        )

    return clean_records(result)


@app.get("/countries/{country_name}")
def get_country(country_name: str):
    result = countries[
        countries["country"].str.casefold() == country_name.casefold()
    ]

    if result.empty:
        raise HTTPException(status_code=404, detail="Country not found")

    return clean_records(result.head(1))[0]


@app.get("/rankings/population")
def population_ranking(
    limit: int = Query(default=10, ge=1, le=100),
):
    result = countries.copy()
    result["population"] = pd.to_numeric(
        result["population"], errors="coerce"
    )
    result = result.nlargest(limit, "population")
    return clean_records(result)


@app.get("/rankings/gdp-per-capita")
def gdp_ranking(
    limit: int = Query(default=10, ge=1, le=100),
):
    result = countries.copy()
    result["gdp_per_capita_usd"] = pd.to_numeric(
        result["gdp_per_capita_usd"], errors="coerce"
    )
    result = result.nlargest(limit, "gdp_per_capita_usd")
    return clean_records(result)


@app.get("/insights/electricity-demand-exceeds-generation")
def electricity_demand_exceeds_generation(
    limit: int = Query(default=100, ge=1, le=300),
):
    required = ["ember_demand_twh", "ember_generation_twh"]
    if not all(column in countries.columns for column in required):
        raise HTTPException(
            status_code=503,
            detail="The Ember 2024 electricity comparison file is unavailable.",
        )

    result = countries.copy()
    result["ember_demand_twh"] = pd.to_numeric(
        result["ember_demand_twh"], errors="coerce"
    )
    result["ember_generation_twh"] = pd.to_numeric(
        result["ember_generation_twh"], errors="coerce"
    )
    result = result.dropna(subset=required)
    result = result[
        result["ember_demand_twh"] > result["ember_generation_twh"]
    ].copy()
    result["demand_generation_gap_twh"] = (
        result["ember_demand_twh"] - result["ember_generation_twh"]
    )
    result = result.nlargest(limit, "demand_generation_gap_twh")
    return clean_records(result)


@app.get("/regions/{region}/summary")
def region_summary(region: str):
    if "region" not in countries.columns:
        raise HTTPException(status_code=400, detail="Region data is unavailable")

    result = countries[
        countries["region"].fillna("").str.casefold() == region.casefold()
    ]

    if result.empty:
        raise HTTPException(status_code=404, detail="Region not found")

    numeric_columns = [
        column for column in result.columns
        if column not in ["country", "iso2", "region"]
    ]

    averages = (
        result[numeric_columns]
        .apply(pd.to_numeric, errors="coerce")
        .mean()
        .to_dict()
    )

    return {
        "region": result["region"].iloc[0],
        "country_count": len(result),
        "countries": result["country"].tolist(),
        "average_indicators": {
            key: clean_value(value) for key, value in averages.items()
        },
    }
@app.get("/dashboard")
def dashboard():
    return FileResponse(Path(__file__).with_name("index.html"))
