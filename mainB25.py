import streamlit as st
import pandas as pd
import os


st.set_page_config(page_title="Burracchiadi 2025", layout="wide")


# --- File paths ---
PARTICIPANTS_FILE = "participants.csv"
RESULTS_FILE = "results.csv"


# --- Load participants ---
def load_participants():
if os.path.exists(PARTICIPANTS_FILE):
return pd.read_csv(PARTICIPANTS_FILE)["Participant"].tolist()
return []


def save_participants(participants):
pd.DataFrame(participants, columns=["Participant"]).to_csv(PARTICIPANTS_FILE, index=False)


# --- Load results ---
def load_results():
if os.path.exists(RESULTS_FILE):
df = pd.read_csv(RESULTS_FILE)
return df.to_dict("records")
return []


def save_results(results):
pd.DataFrame(results).to_csv(RESULTS_FILE, index=False)


# --- RP Calculation ---
def calculate_rp(score_a, score_b):
diff = abs(score_a - score_b)
if diff <= 100:
return (600, 400) if score_a > score_b else (400, 600)
elif diff <= 300:
return (700, 300) if score_a > score_b else (300, 700)
else:
return (800, 200) if score_a > score_b else (200, 800)


# --- Ranking Calculation ---
def update_ranking(results):
ranking = {}
for result in results:
team_a = [result["a1"], result["a2"]]
team_b = [result["b1"], result["b2"]]
score_a, score_b = result["score_a"], result["score_b"]
rp_a, rp_b = calculate_rp(score_a, score_b)


for p in team_a:
if p not in ranking:
ranking[p] = {"total_rp": 0, "matches": 0}
ranking[p]["total_rp"] += rp_a
ranking[p]["matches"] += 1


for p in team_b:
if p not in ranking:
ranking[p] = {"total_rp": 0, "matches": 0}
ranking[p]["total_rp"] += rp_b
ranking[p]["matches"] += 1


ranking_data = []
for participant, stats in ranking.items():
avg_rp = stats["total_rp"] / stats["matches"] if stats["matches"] > 0 else 0
ranking_data.append([participant, stats["total_rp"], stats["matches"], round(avg_rp, 2)])


df = pd.DataFrame(ranking_data, columns=["Participant", "Total RP", "Matches Played", "Average RP"])
df = df.sort_values(by=["Average RP", "Matches Played"], ascending=[False, False]).reset_index(drop=True)
return df


# --- Initialize data ---
participants = load_participants()
results = load_results()


# --- Title ---
st.dataframe(ranking_df.style.apply(highlight_rows, axis=1))