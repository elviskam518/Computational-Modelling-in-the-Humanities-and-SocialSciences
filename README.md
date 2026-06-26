- `datacleaning.py`  
  Reads the raw Wikidata export in `query1.csv`, cleans and standardises country names,
  and infers each laureate’s main research country based on employment timelines.

- `Temporal_trend_analysis.py`  
   Code for Temporal trend analysis model

- `SNA.py`  
   Code for Social Network Analysis model

- `sparsql.py`  
  Contains the SPARQL query used to download the original Nobel-related data
  from Wikidata (not needed to rerun the analysis if `query1.csv` is already present).

- `query1.csv`  
  Raw input dataset exported from Wikidata, including laureate names, award years,
  birth countries, institutions, and employment start/end years.