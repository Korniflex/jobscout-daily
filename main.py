# Bibliotheken importieren
from adapters import arbeitnow, bundesagentur, remotive
import os
import json
from datetime import datetime

# API's importieren
from adapters.API_arbeitnow import get_params as params_arbeitnow, fetch_arbeitnow, normalize_arbeitnow, normalize_arbeitnow_list
from adapters.API_bundesagentur import get_params as params_agentur, fetch_agentur, normalize_agentur, normalize_agentur_list
from adapters.API_remotive import get_params as params_remotive, fetch_remotive, normalize_remotive, normalize_remotive_list

# User Inputs
def main():

    search = input("Suchbegriff (z. B. Data Analyst): ")
    category = input("Kategorie (leer lassen falls keine): ")
    company = input("Firmenname (leer lassen falls keine): ")
    try:
        limit = int(input("Limit Anzahl Ergebnisse (z. B. 10): ") or 10)
        limit=10
    except ValueError:
        limit = 10


    common_params = {
            "search": search,
            "category": category,
            "company": company,
            "limit": limit
    }

    params_for_arbeitnow = params_arbeitnow(**common_params)
    raw_arbeitnow = fetch_arbeitnow(params_for_agentur)
    jobs_arbeitnow = normalize_arbeitnow_list(raw_agentur)

    params_for_agentur= params_agentur(**common_params)
    raw_agentur = fetch_agentur(params_for_agentur)
    jobs_agentur = normalize_agentur_list(raw_agentur)

    params_for_remotive = params_remotive(**common_params)
    raw_remotive = fetch_remotive(params_for_remotive)
    jobs_remotive = normalize_remotive_list(raw_remotive)



    jobs_all = jobs_arbeitnow + jobs_agentur + jobs_remotive
    print(f"Total jobs: {len(jobs_all)}")

    for job in jobs_all[:10]:
        print(f"{job['source']:<20} | {job['title']:<50} | {job['company']:<30} | {job['location']}")

if __name__ == "__main__":
    main()
