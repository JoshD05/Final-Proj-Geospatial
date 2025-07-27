# Geospatial Analysis of Voter and Property Data

Final Project for Geospatial Concepts Course

## Project Overview
Analysis of voter registration data and property values for Pitt County and Beaufort County, North Carolina.

## Counties Analyzed
- **Pitt County** (County Code: 74)
- **Beaufort County**

## Data Sources
- **NC OneMap**: Addresses and Parcels datasets
- **NC State Board of Elections**: Voter registration data

## Project Structure
```
├── data/                    # Raw data files
├── scripts/                 # Python analysis scripts  
├── outputs/                # Results, maps, and GeoPackages
└── requirements.txt        # Python dependencies
```

## Spatial Reference System
EPSG:2264 – NAD83 / North Carolina (ftUS)

## Analysis Goals
1. Geocode voter addresses using address datasets
2. Spatial join voters to parcels
3. Analyze political affiliation vs property values
4. Conduct 5 additional spatial analyses
5. Create visualizations and maps
