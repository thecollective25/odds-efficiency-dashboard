
import streamlit as st
import requests
import pandas as pd

API_KEY = "8ae69ba4bb0bd40128737175cb9a0088"
SPORTS = ["basketball_nba", "baseball_mlb"]
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

def calculate_implied_prob(odds):
    return 1 / odds if odds > 0 else None

def organize_data(data):
    entries = []
    for game in data:
        sport_title = game.get("sport_title", "")
        commence_time = game.get("commence_time", "")
        matchup = game['home_team'] + " vs " + game['away_team']
        for book in game['bookmakers']:
            book_name = book['title']
            for market in book['markets']:
                market_type = market['key']
                for outcome in market['outcomes']:
                    odds = outcome['price']
                    implied_prob = calculate_implied_prob(odds)
                    entries.append({
                        "Matchup": matchup,
                        "Team": outcome['name'],
                        "Odds": odds,
                        "Implied Probability": round(implied_prob, 4) if implied_prob else None,
                        "Bookmaker": book_name,
                        "Market Type": market_type,
                        "Sport": sport_title,
                        "Time": commence_time
                    })
    df = pd.DataFrame(entries)
    return df.sort_values(by=["Bookmaker", "Implied Probability"])

st.set_page_config(page_title="Efficient Odds Dashboard", layout="wide")
st.title("Efficient Odds Dashboard")

all_data = []
for sport in SPORTS:
    data = fetch_odds(sport)
    df = organize_data(data)
    all_data.append(df)

full_df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

if not full_df.empty:
    st.markdown("### All NBA & MLB Odds (Sorted by Bookmaker and Vig)")
    market_filter = st.multiselect("Filter by Market Type", options=full_df["Market Type"].unique(), default=list(full_df["Market Type"].unique()))
    bookmaker_filter = st.multiselect("Filter by Bookmaker", options=full_df["Bookmaker"].unique(), default=list(full_df["Bookmaker"].unique()))
    filtered_df = full_df[(full_df["Market Type"].isin(market_filter)) & (full_df["Bookmaker"].isin(bookmaker_filter))]
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.warning("No data available for NBA or MLB right now.")
