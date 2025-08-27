import streamlit as st
import pandas as pd
import os


st.set_page_config(page_title="Burracchiadi 2025", layout="wide")


# --- File paths ---
PARTICIPANTS_FILE = "participants.csv"
RESULTS_FILE = "results.csv"


# --- Load & Save CSV Helpers ---
def load_csv(file, cols):
if os.path.exists(file):
return pd.read_csv(file)
return pd.DataFrame(columns=cols)


def save_csv(df, file):
df.to_csv(file, index=False)


# --- RP Calculation ---
def calculate_rp(score_a, score_b):
diff = abs(score_a - score_b)
if diff <= 99:
return (500, 500) if score_a > score_b else (500, 500)
elif 100 <= diff <= 299:
return (600, 400) if score_a > score_b else (400, 600)
elif 300 <= diff <= 499:
return (700, 300) if score_a > score_b else (300, 700)
elif 500 <= diff <= 699:
return (750, 250) if score_a > score_b else (250, 750)
elif 700 <= diff <= 999:
return (800, 200) if score_a > score_b else (200, 800)
else: # diff >= 1000
return (900, 100) if score_a > score_b else (100, 900)


# --- Ranking Calculation ---
def update_ranking(results_df):
ranking = {}
for _, result in results_df.iterrows():
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
df.index = df.index + 1 # Start ranking from 1
return df


# --- Load Data ---
participants_df = load_csv(PARTICIPANTS_FILE, ["Participant"])
results_df = load_csv(RESULTS_FILE, ["a1", "a2", "b1", "b2", "score_a", "score_b"])


# --- Title ---
st.title("🏆 Burracchiadi 2025")


# --- Sidebar Navigation ---
menu = st.sidebar.radio("Navigation", ["Ranking", "Manage Participants", "Add / Update Results"], index=0)


# --- Manage Participants ---
if menu == "Manage Participants":
st.header("👥 Manage Participants")


edited_participants = st.data_editor(participants_df, num_rows="dynamic", key="participants_editor")


if not edited_participants.equals(participants_df):
save_csv(edited_participants, PARTICIPANTS_FILE)
participants_df = edited_participants
st.dataframe(ranking_df.style.apply(highlight_rows, axis=1))