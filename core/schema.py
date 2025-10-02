# wenn ich es richti gverstanden haben, müssen wir eine Klasse Job erstellen. 
# Es verhindert, Errors zu bekommen, wenn felder leer sind. 
# Es ist eine stabielere Variante als unsere get_params
# wird für unsere selbstgebaute API sehr nützlich

from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class Job(BaseModel):
    
    source : str
    id: str
    
    title: str
    job_type :  Optional[str] = None
    remote :  Optional[str] = None
    tags :  Optional[str] = None

    company :  Optional[str] = None
    description :  Optional[str] = None
    location : Optional[str] = None
    
    posted_at :  Optional[str] = None
    fetched_at : datetime
    url : HttpUrl

class CommonQuery(BaseModel):
    search: Optional[str] = None
    category: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    posted_since: Optional[str] = None
    mode: Optional[str] = None
    limit: int = 50
    page: int = 1

    

