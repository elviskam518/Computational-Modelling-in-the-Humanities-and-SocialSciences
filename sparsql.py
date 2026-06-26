# pip install sparqlwrapper
# https://rdflib.github.io/sparqlwrapper/

import sys
from SPARQLWrapper import SPARQLWrapper, JSON

endpoint_url = "https://query.wikidata.org/sparql"

query = """SELECT
  ?laureate
  ?laureateName 
  ?prize
  ?prizeLabel
  (YEAR(?awardDate) AS ?awardYear)
  ?birthCountry
  ?birthCountryLabel
  ?inst
  ?instLabel
  ?instCountry
  ?instCountryLabel
  (IF(BOUND(?start), YEAR(?start), -1) AS ?startYear)
  (IF(BOUND(?end),   YEAR(?end),   -1) AS ?endYear)
WHERE {
  VALUES ?prize { 
    wd:Q44585  
    wd:Q38104 
    wd:Q80061  
    wd:Q37922  
    wd:Q35637 
    wd:Q47170
  }

  ?laureate wdt:P31 wd:Q5 ;
            p:P166 ?awardStatement .
  ?awardStatement ps:P166 ?prize ;
                  pq:P585 ?awardDate .

  FILTER(YEAR(?awardDate) >= 1900 && YEAR(?awardDate) <= 2024)

  ?laureate rdfs:label ?laureateName .
  FILTER(LANG(?laureateName) = "en")

  OPTIONAL { 
    ?laureate wdt:P19 ?birthPlace .
    ?birthPlace wdt:P17 ?birthCountry .
    ?birthCountry rdfs:label ?birthCountryLabel .
    FILTER(LANG(?birthCountryLabel) = "en")
  }

  ?laureate p:P108 ?affStmt .
  ?affStmt ps:P108 ?inst .
  OPTIONAL { ?affStmt pq:P580 ?start . }
  OPTIONAL { ?affStmt pq:P582 ?end   . }

  ?inst rdfs:label ?instLabel .
  FILTER(LANG(?instLabel) = "en")

  OPTIONAL {
    ?inst wdt:P17 ?instCountry .
    ?instCountry rdfs:label ?instCountryLabel .
    FILTER(LANG(?instCountryLabel) = "en")
  }
  FILTER(BOUND(?instCountryLabel))

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""


def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


results = get_results(endpoint_url, query)

for result in results["results"]["bindings"]:
    print(result)
