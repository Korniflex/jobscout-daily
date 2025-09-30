# Bibliotheken importieren
from adapters import API_budenagentur, API_arbeitnow, API_remotive
import os
import json
from datetime import datetime
import pandas as pd

# API's importieren
from adapters.API_arbeitnow import get_params as params_arbeitnow, fetch_arbeitnow, normalize_arbeitnow, normalize_arbeitnow_list
from adapters.API_remotive import get_params as params_remotive, fetch_remotive, normalize_remotive, normalize_remotive_list
from adapters.API_budenagentur import get_params as params_agentur, fetch_agentur, normalize_agentur, normalize_agentur_list


# User Inputs
    # Einrichtung unserer Suchparametern:
def main():

    search = input("Suchbegriff (z. B. Data Analyst): ")
    category = input("Berufsfeld (leer lassen falls keine): ")
    company = input("Firmenname (leer lassen falls keine): ")
    location =input("Berufsort (leer lassen falls keine)")

    common_params = {
            "search": search,
            "category": category,
            "company": company,
            "location": location,
    }

# Einrichtung der Bundesagentur API
    params_for_agentur= params_agentur(**common_params)
    raw_agentur = fetch_agentur(params_for_agentur)
    jobs_agentur = normalize_agentur_list(raw_agentur)

# Einrichtung der Remotive API
    params_for_remotive = params_remotive(**common_params)
    raw_remotive = fetch_remotive(params_for_remotive)
    jobs_remotive = normalize_remotive_list(raw_remotive)

# Einrichtung der Arbeitnow API
    params_for_arbeitnow = params_arbeitnow(**common_params)
    raw_arbeitnow = fetch_arbeitnow(params_for_arbeitnow)
    jobs_arbeitnow= normalize_arbeitnow_list(raw_arbeitnow)

# Die Jeweiligen zukomnenden APIs hier einfügen.


#Concat der verschieden APIs
    jobs_all = jobs_agentur + jobs_remotive + jobs_arbeitnow
    print(f"Total jobs: {len(jobs_all)}")
    # Excel Export:
    out_file = f"jobs_{datetime.now().strftime('%Y%m%d_Jobs_sammlung')}.xlsx"
    pd.DataFrame(jobs_all).to_excel(out_file, index=False)
    print("Exportiert nach:", out_file)

#Anzeige der ersten 50 Jobs um den terminal nicht zu explodieren:
    for job in jobs_all[:50]:
        print(f"{job['source']:<50} | {job['title']:<50} | {job['company']:<50} | {job['location']}")

if __name__ == "__main__":
    main()

