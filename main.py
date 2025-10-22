from core.orchestrator import load_params
from core.normalizer import normalize_jobs
from core.schema import Job, CommonQuery
from adapters import get_params_remotive,fetch_remotive,get_params_agentur, fetch_agentur, get_params_arbeitnow, fetch_arbeitnow,  get_params_jobicy, fetch_jobicy

from datetime import datetime
import pandas as pd
import os


IT_SYNONYMS = [
    "IT", "Informatik", "Software", "Softwareentwicklung", "Tech", "Technology",
    "Software & IT", "Computer Science", "Entwicklung", "Developer", "Engineering"
]

def main():


    common_params = CommonQuery(
        search=None,               
        category="IT",
        category_synonyms=IT_SYNONYMS,
        company=None,
        posted_since=None,
        work_mode=None,
        remote=None, 
        location=None,                         
        limit=25,
    ) 


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
 
    os.makedirs("exports", exist_ok=True)  # Herstellt file falls nötig

    out_file = f"exports/{datetime.now().strftime('%Y%m%d')}_Jobs_sammlung.xlsx"
    pd.DataFrame([j.model_dump() for j in all_normalized]).to_excel(out_file, index=False)
    print("Exportiert nach:", out_file)
##############################################################################################
if __name__ == "__main__":
    main()