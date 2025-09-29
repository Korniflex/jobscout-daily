import requests
import pandas as pd
from pandas import json_normalize
from datetime import datetime


baseurl = 'https://www.arbeitnow.com/api/job-board-api'


def main_requests(baseurl):
    r = requests.get(baseurl, timeout=30)
    r.raise_for_status()
    return r.json()



def parse_json(response):
    return [
        {
            "title": job['title'],
            "company": job['company_name'],
            "location": job['location'],
            "url": job['url'],
            "created_at": job['created_at'],
        }
        for job in response.get('data', [])
    ]



all_jobs = []
for page in range(1,7):
    print('Seite', page)
    page_data = main_requests(baseurl)
    all_jobs.extend(parse_json(page_data))


    df = pd.DataFrame(all_jobs)
df



xlsx_filename = f"Arbeit_Now_1{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
df.to_excel('Arbeit_Now_1.xlsx', index=False)