from core.orchestrator import load_params
from core.normalizer import normalize_jobs


from datetime import datetime
import pandas as pd
import os


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
    all_raws= load_params(common_params)
    all_normalized= normalize_jobs(all_raws)

    # Hier weiter: 
    # 
    # -> dedupe 
    # 
    # -> DB upsert 
    # 
    # -> print/return



########################################################################################
#Temporäres Excel File

    print(f"Gesamt normalisierte Jobs: {len(all_normalized)}")
    for j in all_normalized[:5]:
        print(j["title"], "-", j["company"],"-", j["url"])
    
    
    os.makedirs("exports", exist_ok=True)  # Herstellt file falls nötig

    out_file = f"exports/{datetime.now().strftime('%Y%m%d')}_Jobs_sammlung.xlsx"
    pd.DataFrame(all_normalized).to_excel(out_file, index=False)
    print("Exportiert nach:", out_file)
##############################################################################################
if __name__ == "__main__":
    main()