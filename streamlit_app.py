import streamlit as st
import pandas as pd
import base64
import time
from pytrends.request import TrendReq

st.title("Google Trends For Top GSC Keywords")

st.markdown("""
**Instructions:**
1. Export the data from the [Performance Report](https://search.google.com/search-console/performance/search-analytics) (impressions, CTR, position) in Google Search Console. Then upload the `Queries.csv` file from the zip file.
2. The maximum number of queries to run is limited to 200 to avoid the application timing out or being blocked by Google.
""")

st.markdown("---")

sortby = st.selectbox('Sort keywords by', ('Clicks', 'Impressions', 'CTR', 'Position'))
cutoff = st.number_input('Number of queries', min_value=1, max_value=200, value=10)
pause = st.number_input('Pause between calls', min_value=1, max_value=60, value=10)  # Ajustado para permitir pausas más largas
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
            print(f"Error fetching trends for {kw_list}: {e}. Attempt {attempt + 1} of {retries}.")
            time.sleep((backoff_factor ** attempt) * pause)
    raise Exception(f"Max retries reached for {kw_list}, unable to fetch trends.")

if get_gsc_file is not None:
    st.write("Data upload successful, processing... 😎")
    
    df = pd.read_csv(get_gsc_file, encoding='utf-8')
    df.sort_values(by=[sortby], ascending=False, inplace=True)
    df = df[:cutoff]
    
    d = {'Keyword': [], sortby: [], 'Trend': []}
    df3 = pd.DataFrame(data=d)
    keywords = []
    trends = []
    metric = df[sortby].tolist()
    up, down, flat, na = 0, 0, 0, 0

    for index, row in df.iterrows():
        keyword = row['Top queries']
        print(f"Processing keyword: {keyword}")  # Añadido para depuración
        pytrends = TrendReq(hl='es-MX', tz=-480)  # Ajustado para español de México y zona horaria del Pacífico
        kw_list = [keyword]
        try:
            df2 = fetch_trends_with_retry(pytrends, kw_list, timeframe, geo)
            trend1 = int((df2[keyword][-5] + df2[keyword][-4] + df2[keyword][-3])/3)
            trend2 = int((df2[keyword][-4] + df2[keyword][-3] + df2[keyword][-2])/3)
            trend3 = int((df2[keyword][-3] + df2[keyword][-2] + df2[keyword][-1])/3)

            if trend3 > trend2 and trend2 > trend1:
                trends.append('UP')
                up += 1
            elif trend3 < trend2 and trend2 < trend1:
                trends.append('DOWN')
                down += 1
            else:
                trends.append('FLAT')
                flat += 1
        except Exception as e:
            print(f"Unable to fetch trends for {keyword}: {e}")
            trends.append('N/A')
            na += 1
        time.sleep(pause)

    df3['Keyword'] = keywords
    df3['Trend'] = trends
    df3[sortby] = metric

    def colortable(val):
        color = 'white'
        if val == 'DOWN':
            color = "lightcoral"
        elif val == 'UP':
            color = "lightgreen"
        elif val == 'FLAT':
            color = "lightblue"
        return f'background-color: {color}'

    df3 = df3.style.applymap(colortable)

    def get_csv_download_link(df, title):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{title}.csv">Download CSV file</a>'
        return href

    total = up + down + flat + na
    st.write(f"Up: {up} | {round((up/total)*100, 0)}%")
    st.write(f"Down: {down} | {round((down/total)*100, 0)}%")
    st.write(f"Flat: {flat} | {round((flat/total)*100, 0)}%")
    st.write(f"N/A: {na} | {round((na/total)*100, 0)}%")

    st.markdown(get_csv_download_link(df3.data, "gsc-keyword-trends"), unsafe_allow_html=True)
    st.dataframe(df3.data)

st.write('Author: [Your Name](https://www.linkedin.com/in/yourprofile/)')
