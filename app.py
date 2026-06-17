#imports
import streamlit as st
import pandas as pd
import plotly.express as px

# page config
st.set_page_config(
    page_title="Purdue Football Recruiting Map",
    layout="wide",
    initial_sidebar_state="expanded"
)

# custom CSS for Purdue Customization
st.markdown(
    """
    <style>
    /* adjusts the active slider tracks, handles, and buttons to Purdue Gold */
    :root {
        --primary-color: #CFB991;
    }
    html, body, [data-testid="stAppViewContainer"] {
        --st-profile-primary: #CFB991;
    }
    div[data-testid="stMarkdownContainer"] + div [role="slider"] {
        background-color: #CFB991 !important;
        box-shadow: 0 0 0 2px #CFB991 !important;
    }
    div[data-baseweb="slider"] > div > div {
        background: linear-gradient(to right, #CFB991 0%, #CFB991 100%) !important;
    }

    div[data-testid="stAlert"] {
        background-color: #F6F1E5 !important; 
        border-left: 5px solid #8E6F3E !important; 
        color: #111111 !important;
    }

    div[data-testid="stAlert"] p {
        color: #111111 !important;
    }
    
    /* framed border around the interactive map */
    .map-container {
        border: 2px solid #CFB991 !important; 
        border-radius: 8px;
        padding: 10px;
        background-color: #FFFFFF;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# title block
st.markdown(
    """
    <h1 style='color: #8E6F3E; margin-bottom: 0px;'>Purdue Football Recruits by Hometown</h1>
    <p style='color: #8E6F3E; font-size: 1.1rem; margin-top: 5px; font-weight: 500;'>
        Explore historical pipelines and talent distribution since 1999.
    </p>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# data load
@st.cache_data
def load_data():
    df = pd.read_csv("purdue_recruits_geocoded.csv")
    # define positional groups
    position_map = {
        # defensive line
        "WDE": "DE",
        "SDE": "DE",
        # linebackers
        "ILB": "LB",
        "OLB": "LB",
        "LB": "LB",
        # offensive line
        "OT": "OT",
        "OG": "IOL",
        "OC": "IOL",
        "IOL": "IOL",
        # skill positions
        "RB": "RB",
        "APB": "RB",
        "FB": "RB",
        "WR": "WR",
        "TE": "TE",
        "DUAL": "QB",
        "PRO": "QB",
        "QB": "QB"
    }
    # map the positions into groups
    df["Position Group"] = df["Position"].map(position_map).fillna(df["Position"])
    # make sure rating/star column values are clean integers
    df["HS Stars"] = df["HS Stars"].fillna(0).astype(int)
    df["Class Year"] = df["Class Year"].astype(int)
    # create a smart label for star ratings based on the pre 2011 no ratings
    def get_rating_label(row):
        stars = row["HS Stars"]
        year = row["Class Year"]
        if stars > 0:
            return f"{stars} Stars"
        elif year < 2011:
            return "Pre-2011 (No Data)"
        else:
            return "Unrated"

    df["Rating Label"] = df.apply(get_rating_label, axis=1)
    # label recruiting classes by Coaching Era
    def get_coach_era(year):
        if year <= 2008:
            return "Joe Tiller (1997-2008)"
        elif 2009 <= year <= 2012:
            return "Danny Hope (2009-2012)"
        elif 2013 <= year <= 2016:
            return "Darrell Hazell (2013-2016)"
        elif 2017 <= year <= 2022:
            return "Jeff Brohm (2017-2022)"
        elif 2023 <= year <= 2024:
            return "Ryan Walters (2023-2024)"
        else:
            return "Barry Odom (2025-Present)"

    df["Coach Era"] = df["Class Year"].apply(get_coach_era)

    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "Could not find csv ")
    st.stop()

# sidebar filters

# purdue logo on sidebar
st.sidebar.image(
    "https://1000logos.net/wp-content/uploads/2024/05/Purdue-Boilermakers-Logo-1996.png",
    use_container_width=True
)
st.sidebar.markdown("---")

st.sidebar.header("Filters")

# Coaching Era Filter
st.sidebar.markdown("**Coaching Era**")
available_eras = [
    "All Coaches",
    "Joe Tiller (1997-2008)",
    "Danny Hope (2009-2012)",
    "Darrell Hazell (2013-2016)",
    "Jeff Brohm (2017-2022)",
    "Ryan Walters (2023-2024)",
    "Barry Odom (2025-Present)"
]
selected_era = st.sidebar.selectbox("Select Coach", options=available_eras, index=0, key="selected_era_key")

# subset to filter other filters
if selected_era != "All Coaches":
    df_era = df[df["Coach Era"] == selected_era]
else:
    df_era = df.copy()

# Year Slider
min_year = int(df_era["Class Year"].min())
max_year = int(df_era["Class Year"].max())
year_range = st.sidebar.slider(
    "Class Years",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
    key="year_range_key"
)

# Star Rating Dropdown Checkbox
st.sidebar.markdown("**Star Ratings**")

# update options based on coach era
available_labels = sorted(df_era["Rating Label"].unique(), key=lambda x: (not "Pre-2011" in x, not "Unrated" in x, x))

if "star_version" not in st.session_state:
    st.session_state["star_version"] = 0

for label in available_labels:
    if f"star_state_{label}" not in st.session_state:
        st.session_state[f"star_state_{label}"] = True

star_popover = st.sidebar.popover("Select Star Ratings", use_container_width=True)
col1, col2 = star_popover.columns(2)

# render the buttons and adjust for screen
if col1.button("Select All", key=f"all_btn_{selected_era.split()[0]}", use_container_width=True):
    for label in available_labels:
        st.session_state[f"star_state_{label}"] = True
    st.session_state["star_version"] += 1
    st.rerun()

if col2.button("Clear All", key=f"clear_btn_{selected_era.split()[0]}", use_container_width=True):
    for label in available_labels:
        st.session_state[f"star_state_{label}"] = False
    st.session_state["star_version"] += 1
    st.rerun()

# display checkboxes
selected_rating_labels = []
for label in available_labels:
    state_key = f"star_state_{label}"

    # generate a unique key containing the version number
    v_key = f"chk_{selected_era.split()[0]}_v{st.session_state['star_version']}_{label}"

    is_checked = star_popover.checkbox(
        label,
        value=st.session_state[state_key],
        key=v_key
    )

    # save manual user click selections back into memory
    st.session_state[state_key] = is_checked
    if is_checked:
        selected_rating_labels.append(label)

# Position Group Dropdown Checkbox
st.sidebar.markdown("**Position Groups**")

# update options based on coach era
available_groups = sorted(df_era["Position Group"].dropna().unique())

if "pos_version" not in st.session_state:
    st.session_state["pos_version"] = 0

for group in available_groups:
    if f"pos_state_{group}" not in st.session_state:
        st.session_state[f"pos_state_{group}"] = True

# open the popover container
pos_popover = st.sidebar.popover("Select Position Groups", use_container_width=True)
col1_pos, col2_pos = pos_popover.columns(2)

# render the buttons and adjust for screen
if col1_pos.button("Select All", key=f"all_pos_btn_{selected_era.split()[0]}", use_container_width=True):
    for group in available_groups:
        st.session_state[f"pos_state_{group}"] = True
    st.session_state["pos_version"] += 1
    st.rerun()

if col2_pos.button("Clear All", key=f"clear_pos_btn_{selected_era.split()[0]}", use_container_width=True):
    for group in available_groups:
        st.session_state[f"pos_state_{group}"] = False
    st.session_state["pos_version"] += 1
    st.rerun()

# display checkboxes inside a fixed-height scrollable container
selected_position_groups = []
with pos_popover.container(height=200, border=False):
    for group in available_groups:
        state_key = f"pos_state_{group}"
        v_key_pos = f"chk_pos_{selected_era.split()[0]}_v{st.session_state['pos_version']}_{group}"

        is_checked = st.checkbox(
            group,
            value=st.session_state[state_key],
            key=v_key_pos
        )
        st.session_state[state_key] = is_checked
        if is_checked:
            selected_position_groups.append(group)

# Master Reset Filters Button
st.sidebar.markdown("---")

# define the callback function
def reset_all_filters_callback():
    # reset the core widgets via their session state keys
    st.session_state["selected_era_key"] = "All Coaches"
    st.session_state["year_range_key"] = (int(df["Class Year"].min()), int(df["Class Year"].max()))

    # clear out all custom Star Rating states
    for label in sorted(df["Rating Label"].unique()):
        st.session_state[f"star_state_{label}"] = True
    st.session_state["star_version"] += 1

    # clear out all custom Position Group states
    for group in sorted(df["Position Group"].dropna().unique()):
        st.session_state[f"pos_state_{group}"] = True
    st.session_state["pos_version"] += 1

# Bind the callback to the button click event
st.sidebar.button("🔄 Reset All Filters", on_click=reset_all_filters_callback, use_container_width=True)

# apply filters to DF

# create the base filter conditions
era_condition = df["Coach Era"] == selected_era if selected_era != "All Coaches" else pd.Series(True, index=df.index)

# apply the remaining active filters onto the era-scoped data subset
filtered_df = df_era[
    (df_era["Class Year"] >= year_range[0]) &
    (df_era["Class Year"] <= year_range[1]) &
    (df_era["Rating Label"].isin(selected_rating_labels)) &
    (df_era["Position Group"].isin(selected_position_groups))
]

# group by hometown to get dynamic counts per city for the map pins
city_counts = filtered_df.groupby(["Hometown City", "Hometown State", "lat", "lon"]).size().reset_index(name="Count")

# build the map

# find the all-time maximum city count across the UNFILTERED dataset
global_city_max = int(df.groupby(["Hometown City", "Hometown State"]).size().max())

# append a temporary reference anchor row to the active dataframe.
anchor_row = pd.DataFrame([{
    "Hometown City": "ANCHOR", "Hometown State": "ANCHOR",
    "lat": 0.0, "lon": 0.0, "Count": global_city_max
}])

if not city_counts.empty:
    map_df = pd.concat([city_counts, anchor_row], ignore_index=True)
else:
    # if no results match, pass just the anchor row so the map still renders
    map_df = anchor_row

# build the bubble map
fig_bubble = px.scatter_geo(
    map_df,
    lat="lat",
    lon="lon",
    size="Count",
    hover_name="Hometown City",
    hover_data={"Hometown State": True, "Count": True, "lat": False, "lon": False},
    scope="usa",
    size_max=25,
)

# style the bubbles and set a minimum size threshold for readability
fig_bubble.update_traces(
    marker=dict(
        color="#CFB991",
        line=dict(width=1.5, color="#111111"),
        opacity=0.85,
        sizemin=4
    )
)

# if the active filter results are completely empty, hide the anchor point bubble entirely
if city_counts.empty:
    fig_bubble.update_traces(visible=False)

# apply map aesthetic
fig_bubble.update_layout(
    geo=dict(
        showland=True,
        landcolor="#FDFDFD",
        subunitcolor="rgb(180, 180, 180)",
        countrycolor="rgb(100, 100, 100)",
        bgcolor="rgba(0,0,0,0)",
        lakecolor="rgb(255, 255, 255)",
        showlakes=True
    ),
    margin={"r": 0, "t": 10, "l": 0, "b": 0},
    height=650
)

# wrap the map inside a container border
with st.container(border=True):
    selected_point = st.plotly_chart(
        fig_bubble,
        use_container_width=True,
        on_select="rerun"
    )

# active filters banner

active_coach = selected_era if selected_era != "All Coaches" else "All Coaches"
active_years = f"{year_range[0]} - {year_range[1]}"

# handle Star Ratings string display
if len(selected_rating_labels) == len(available_labels):
    active_stars = "All Ratings"
elif len(selected_rating_labels) == 0:
    active_stars = "None Selected"
else:
    active_stars = ", ".join(selected_rating_labels)

# handle Position Groups string display
if len(selected_position_groups) == len(available_groups):
    active_positions = "All Positions"
elif len(selected_position_groups) == 0:
    active_positions = "None Selected"
else:
    active_positions = ", ".join(selected_position_groups)

# render a styled information box
st.info(
    f" **Active Filters:**  \n"
    f" **Coach/Era:** {active_coach}  \n"
    f" **Years:** {active_years}  \n"
    f" **Stars:** `{active_stars}`  \n"
    f" **Positions:** `{active_positions}`"
)

# insight tables

st.markdown("---")
col_table1, col_table2 = st.columns(2)

with col_table1:
    st.markdown("### Recruits by Star Rating")
    if not filtered_df.empty:
        stars_summary_df = (
            filtered_df["Rating Label"]
            .value_counts()
            .reset_index()
        )
        stars_summary_df.columns = ["Star Rating", "Total Recruits"]

        stars_summary_df = stars_summary_df.sort_values(
            by="Star Rating",
            ascending=False,
            key=lambda col: col.str.extract(r'(\d+)').fillna(0).astype(int)[0]
        )

        st.dataframe(stars_summary_df, use_container_width=True, hide_index=True)
    else:
        st.info("No rating data available for current filter selection.")

with col_table2:
    st.markdown("### Top Hometown States")
    if not filtered_df.empty:
        top_states_df = (
            filtered_df["Hometown State"]
            .value_counts()
            .reset_index()
        )
        top_states_df.columns = ["State", "Total Recruits"]
        st.dataframe(top_states_df.head(10), use_container_width=True, hide_index=True)
    else:
        st.info("No state data available for current filter selection.")

# click to reveal bubble table

st.markdown("---")
st.markdown("### Selected Bubble Player Information")

# check if the user has clicked on a specific city pin on the map
if (
        selected_point
        and "selection" in selected_point
        and "points" in selected_point["selection"]
        and len(selected_point["selection"]["points"]) > 0
):
    point_data = selected_point["selection"]["points"][0]
    clicked_city = point_data.get("hovertext", "ANCHOR")

    # guard against clicking the invisible reference calculation anchor row
    if clicked_city != "ANCHOR":
        matched_row = map_df[
            (map_df["lat"] == point_data["lat"]) &
            (map_df["lon"] == point_data["lon"])
            ]

        if not matched_row.empty:
            clicked_state = matched_row.iloc[0]["Hometown State"]

            # find all individual player rows matching this hub
            roster_df = filtered_df[
                (filtered_df["Hometown City"] == clicked_city) &
                (filtered_df["Hometown State"] == clicked_state)
                ].sort_values(by="Class Year", ascending=False)

            # display a grid panel of the players from that hometown
            st.success(
                f" Showing **{len(roster_df)}** recruits from **{clicked_city}, {clicked_state}**")

            clean_display_df = roster_df[[
                "Class Year", "Name", "Position Group", "Position",
                "HS Stars", "Rating Label", "High School", "Coach Era"
            ]]

            st.dataframe(
                clean_display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(
                "Click on any gold city bubble on the map above to view the player information from that hometown")
    else:
        st.info(
            "Click on any gold city bubble on the map above to view the player information from that hometown")
else:
    st.info("Click on any gold city bubble on the map above to view the player information from that hometown")