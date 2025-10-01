from adapters import API_bundesagentur as agentur
from adapters import API_remotive as remotive
from adapters import API_arbeitnow as arbeitnow

from API_bundesagentur import fetch_agentur, normalize_agentur, normalize_agentur_list, get_params_agentur
from .API_remotive import fetch_remotive, normalize_remotive, normalize_remotive_list, get_params_remotive
from .API_arbeitnow import fetch_arbeitnow, normalize_arbeitnow, normalize_arbeitnow_list, get_params_arbeitnow
