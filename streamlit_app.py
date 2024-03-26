import streamlit as st
import pandas as pd
import base64
import time
from pytrends.request import TrendReq

# Función para validar proxies
def validate_proxy(proxy):
    try:
        # Realiza una solicitud a Google usando el proxy
        response = requests.get('https://www.google.com', proxies={'https': proxy})
        if response.status_code == 200:
            return True
    except:
        pass
    return False

# Función para obtener una lista de proxies válidos
def get_valid_proxies(proxy_sources):
    valid_proxies = []
    for source in proxy_sources:
        with requests.get(source) as response:
            for proxy in response.text.splitlines():
                if validate_proxy(proxy):
                    valid_proxies.append(proxy)
    return valid_proxies

# Lista de URLs de proxies
proxy_sources = [
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
"https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
"https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
"https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
"https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
"https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
"https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
"https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt",
"https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt",
"https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
"https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
"https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",
"https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt",
"https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
"https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
    # ... (resto de las URLs)
]

# Obtener lista de proxies válidos
proxies = get_valid_proxies(proxy_sources)

st.title("Google Trends For Top GSC Keywords")

st.markdown("""
**Instructions:**
1. Export the data from the [Performance Report](https://search.google.com/search-console/performance/search-analytics) (impressions, CTR, position) in Google Search Console. Then upload the `Queries.csv` file from the zip file.
2. The maximum number of queries to run is limited to 200 to avoid the application timing out or being blocked by Google.
""")

st.markdown("---")

sortby = st.selectbox('Sort keywords by', ('Clicks', 'Impressions', 'CTR', 'Position'))
cutoff = st.number_input('Number of queries', min_value=1, max_value=200, value=10)
pause = st.number_input('Pause between calls', min_value=1, max_value=60, value=10)
timeframe = st.selectbox('Timeframe', ('today 1-m', 'today 3-m', 'today 12-m'))
geo = st.selectbox('Geo', ('World', 'US', 'Mexico'))

if geo == 'World':
    geo = ''
elif geo == 'Mexico':
    geo = 'MX'

get_gsc_file = st.file_uploader("Upload GSC CSV file", type=['csv'])

def fetch_trends_with_retry(pytrends, kw_list, timeframe, geo, retries=3, backoff_factor=2):
  for attempt in range(retries):
    try:
      pytrends.build_payload(kw_list, cat=0, timeframe=timeframe, geo=geo, gprop='')
      return pytrends.interest_over_time()
    except Exception as e:
      st.error(f"Error fetching trends for {kw_list}: {e}. Attempt {attempt + 1} of {retries}.")
      time.sleep((backoff_factor ** attempt) * pause)
  raise Exception(f"Max retries reached for {kw_list}, unable to fetch trends.")

if get_gsc_file is not None:
  st.write("Data upload successful, processing... ")
   
  df = pd.read_csv(get_gsc_file, encoding='utf-8')
  df.sort_values(by=[sortby], ascending=False, inplace=True)
  df = df[:cutoff]
   
  d = {'Keyword': [], sortby: [], 'Trend': []}
  df3 = pd.DataFrame(data=d)
  keywords = []
  trends = []
  metric = df[sortby].tolist()
  up, down, flat, na = 0, 0, 0, 0

  progress_bar = st.progress(0)
  status_text = st.empty()
  total_keywords = len(df)
   
  for index, row in df.iterrows():
    keyword = row['Top queries']
    status_text.text(f"Processing keyword: {keyword}")
 
