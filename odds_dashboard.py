import streamlit as st
import requests
import pandas as pd

API_KEY = "8ae69ba4bb0bd40128737175cb9a0088"
SPORT = "americanfootball_nfl"
BOOKMAKERS = ["draftkings", "betmgm"]
REGIONS = "us"
MARKETS = "moneyline"

# Add a list of popular teams for high-volume filtering (NFL + NBA + MLB)
POPULAR_TEAMS = [
    # NFL
    "Dallas Cowboys", "Kansas City Chiefs", "San Francisco 49ers",
    "Philadelphia Eagles", "Green Bay Packers", "New England Patriots",
    "Buffalo Bills", "Pittsburgh Steelers", "New York Giants", "Chicago Bears",
    # NBA
    "Boston Celtics", "Brooklyn Nets", "New York Knicks", "Philadelphia 76ers", "Toronto Raptors",
    "Chicago Bulls", "Cleveland Cavaliers", "Detroit Pistons", "Indiana Pacers", "Milwaukee Bucks",
    "Atlanta Hawks", "Charlotte Hornets", "Miami Heat", "Orlando Magic", "Washington Wizards",
    "Denver Nuggets", "Minnesota Timberwolves", "Oklahoma City Thunder", "Portland Trail Blazers", "Utah Jazz",
    "Golden State Warriors", "LA Clippers", "Los Angeles Lakers", "Phoenix Suns", "Sacramento Kings",
    "Dallas Mavericks", "Houston Rockets", "Memphis Grizzlies", "New Orleans Pelicans", "San Antonio Spurs",
    # MLB
    "New York Yankees", "Boston Red Sox", "Toronto Blue Jays", "Baltimore Orioles", "Tampa Bay Rays",
    "Chicago White Sox", "Cleveland Guardians", "Detroit Tigers", "Kansas City Royals", "Minnesota Twins",
    "Houston Astros", "Los Angeles Angels", "Oakland Athletics", "Seattle Mariners", "Texas Rangers",
    "Atlanta Braves", "Miami Marlins", "New York Mets", "Philadelphia Phillies", "Washington Nationals",
    "Chicago Cubs", "Cincinnati Reds", "Milwaukee Brewers", "Pittsburgh Pirates", "St. Louis Cardinals",
    "Arizona Diamondbacks", "Colorado Rockies", "Los Angeles Dodgers", "San Diego Padres", "San Francisco Giants"
]

@st.cache_data(ttl=60)
def fetch_odds():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'bookmakers': ",".join(BOOKMAKERS)
    }
    res = requests.get(url, params=params)
    return res.json() if res.status_code == 200 else []

def calculate_implied_prob(odds):
    return 1 / odds if odds > 0 else None

def find_best_lines(data):
    rows = []
    for game in data:
        line_dict = {}
        for book in game['bookmakers']:
            for market in book['markets']:
                for outcome in market['outcomes']:
                    key = (outcome['name'], book['title'].lower())
                    line_dict[key] = outcome['price']

        teams = list(set(k[0] for k in line_dict.keys()))
        if len(teams) == 2:
            team1, team2 = teams
            # Only include if either team is in the popular teams list
            if team1 not in POPULAR_TEAMS and team2 not in POPULAR_TEAMS:
                continue

            best_odds_team1 = max([line_dict.get((team1, b), float('-inf')) for b in BOOKMAKERS])
            best_odds_team2 = max([line_dict.get((team2, b), float('-inf')) for b in BOOKMAKERS])

            if best_odds_team1 > 0 and best_odds_team2 > 0:
                prob1 = calculate_implied_prob(best_odds_team1)
                prob2 = calculate_implied_prob(best_odds_team2)
                total_prob = prob1 + prob2
                efficiency = 1 / total_prob if total_prob > 0 else 0

                rows.append({
                    "Matchup": f"{team1} vs {team2}",
                    "Team A": team1,
                    "Odds A": best_odds_team1,
                    "Team B": team2,
                    "Odds B": best_odds_team2,
                    "Total Implied Probability": round(total_prob, 4),
                    "Efficiency Score (1 = zero vig)": round(efficiency, 4)
                })
    df = pd.DataFrame(rows)
    return df if not df.empty else pd.DataFrame(columns=["Matchup", "Team A", "Odds A", "Team B", "Odds B", "Total Implied Probability", "Efficiency Score (1 = zero vig)"])

# Streamlit UI
st.set_page_config(page_title="Efficient Betting Lines", layout="wide")
st.title("Efficient Odds Finder")
st.markdown("Find high-volume line pairs with minimal vig between DraftKings and BetMGM.")

data = fetch_odds()
df = find_best_lines(data)

st.markdown("---")
thresh_col, table_col = st.columns([1, 2])

with thresh_col:
    st.markdown("### Set Efficiency Threshold")
    threshold = st.slider("Max implied probability (e.g. 1.02 = 2% vig)", min_value=1.0, max_value=1.1, value=1.02, step=0.005)

with table_col:
    st.markdown("### Top Popular Game Opportunities")
    if not df.empty and "Total Implied Probability" in df.columns:
        filtered_df = df[df["Total Implied Probability"] <= threshold]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("No matchups found or data unavailable.")

st.markdown("---")

# Highlight best matches visually
if not df.empty and "Total Implied Probability" in df.columns:
    for _, row in df[df["Total Implied Probability"] <= threshold].iterrows():
        st.markdown(f"""
        #### {row['Matchup']}
        - {row['Team A']} @ **{row['Odds A']}**  
        - {row['Team B']} @ **{row['Odds B']}**  
        - Efficiency Score: `{row['Efficiency Score (1 = zero vig)']}`
        - Total Implied Probability: `{row['Total Implied Probability']}`
        """)

st.caption("Updates every 60 seconds. Data via The Odds API.")
