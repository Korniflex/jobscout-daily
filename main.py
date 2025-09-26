
import os
import json
from datetime import datetime

# imports der verschiedene API's und Struktur 
from adapters.API_remotive import get_params as params_remotive, fetch_remotive, normalize_remotive, normalize_remotive_list
from adapters.API_budenagentur import get_params as params_agentur, fetch_agentur, normalize_agentur, normalize_agentur_list


    # Hier kommen unsere User_inputs

search = input("Suchbegriff (z. B. Data Analyst): ")
category = input("Kategorie (leer lassen falls keine): ")

company = input("Firmenname (leer lassen falls keine): ")

limit = int(input("Limit Anzahl Ergebnisse (z. B. 10): ") or 10)


common_params = {
        "search": search,
        "category": category,
        "company": company,
        "limit": limit
}



raw_agentur = fetch_agentur(params_agentur(common_params))
jobs_agentur = normalize_agentur(raw_agentur)

raw_remotive = fetch_remotive(params_remotive(common_params))
jobs_remotive = normalize_remotive(raw_remotive)




jobs_all = jobs_agentur + jobs_remotive 
print(f"Total jobs: {len(jobs_all)}")

"""if __main__=  ... durch suchen und implentieren"""