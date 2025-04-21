
import streamlit as st
import requests
import pandas as pd

API_KEY = "8ae69ba4bb0bd40128737175cb9a0088"
SPORTS = ["americanfootball_nfl", "basketball_nba", "baseball_mlb"]
BOOKMAKERS = ["draftkings", "betmgm"]
REGIONS = "us"
MARKETS = ["h2h", "spreads", "totals", "player_props"]

@st.cache_data(ttl=60)
def fetch_odds(sport):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': REGIONS,
        'markets': ",".join(MARKETS),
        'bookmakers': ",".join(BOOKMAKERS)
    }
    res = requests.get(url, params=params)
    return res.json() if res.status_code == 200 else []

def organize_data(data):
    entries = []
    for game in data:
        sport_title = game.get("sport_title", "")
        commence_time = game.get("commence_time", "")
        for book in game['bookmakers']:
            book_name = book['title']
            for market in book['markets']:
                market_type = market['key']
                for outcome in market['outcomes']:
                    entries.append({
                        "Matchup": game['home_team'] + " vs " + game['away_team'],
                        "Team": outcome['name'],
                        "Odds": outcome['price'],
                        "Bookmaker": book_name,
                        "Market Type": market_type,
                        "Sport": sport_title,
                        "Time": commence_time
                    })
    return pd.DataFrame(entries)

st.set_page_config(page_title="Efficient Odds Dashboard", layout="wide")
st.title("Efficient Odds Dashboard")

selected_sport = st.selectbox("Select a Sport", options=SPORTS, format_func=lambda x: x.split("_")[-1].upper())
data = fetch_odds(selected_sport)
df = organize_data(data)

if not df.empty:
    market_filter = st.multiselect("Filter by Market Type", options=df["Market Type"].unique(), default=list(df["Market Type"].unique()))
    filtered_df = df[df["Market Type"].isin(market_filter)]
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.warning("No data available for this sport right now.")
