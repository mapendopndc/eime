import streamlit as st
import pandas as pd

# Load the data
if 'data' not in st.session_state:
    st.warning("Start with Summary Page")
    st.stop()

data = st.session_state['data']

# Get unique values for the dropdowns
storys = data["Story"].unique()
beam_ids = data["Beam"].unique()
uls_combo_ids = data["Load Combination"].unique()
ldf_combo_ids = data["kD Case"].unique()

if 'story' not in st.session_state:
    st.session_state['story'] = None
if 'beam' not in st.session_state:
    st.session_state['beam'] = None

# Dropdowns for filtering
selected_story = st.sidebar.selectbox("Select Story", options=list(storys), index=0 if st.session_state['story'] == None else storys.tolist().index(st.session_state['story']))
beam_ids = data[data["Story"] == selected_story]["Beam"].unique()
selected_beam_id = st.sidebar.selectbox("Select Beam", options=list(beam_ids), index=0 if  st.session_state['beam'] == None else beam_ids.tolist().index(st.session_state['beam']))
selected_uls_combo_id = st.sidebar.selectbox("Select Load Combination", options=list(uls_combo_ids))
selected_ldf_combo_id = st.sidebar.selectbox("Select Long-Duration Factor Combination", options=list(ldf_combo_ids))


# Apply filters
filtered_data = data.copy()
if selected_beam_id != "All":
    filtered_data = filtered_data[filtered_data["Beam"] == selected_beam_id]
if selected_uls_combo_id != "All":
    filtered_data = filtered_data[filtered_data["Load Combination"] == selected_uls_combo_id]
if selected_ldf_combo_id != "All":
    filtered_data = filtered_data[filtered_data["kD Case"] == selected_ldf_combo_id]
if selected_story != "All":
    filtered_data = filtered_data[filtered_data["Story"] == selected_story]

# Display filtered data
st.markdown("## Detailed Beam Report")
st.markdown("### Beam Data")
st.write(filtered_data)

UDL = filtered_data["UDL V2"][1:]
St1 = filtered_data["Station"][:-1]
St2 = filtered_data["Station"][1:]

weaved_UDL = [val for pair in zip(UDL, UDL) for val in pair]
weaved_St = [val for pair in zip(St1, St2) for val in pair]

import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=3,
    cols=1,
    subplot_titles=("Applied Load", "Shear Diagram", "Moment Diagram"),
    shared_xaxes=True
    )
for idx, row in filtered_data.iterrows():
    if (row["PL V2"] == 0): continue
    fig.add_annotation(
            x=row["Station"],
            y=0,
            xref="x",
            yref="y",
            text="Fy = " + str(round(row["PL V2"],1)) + "kN",
            showarrow=True,
            align="center",
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#636363",
            ax=0,
            ay=row["PL V2"],
            opacity=0.8
            )

fig.append_trace(go.Scatter(
    name="UDL",
    x=weaved_St,
    y=weaved_UDL,
    showlegend=False
), row=1, col=1)

fig.update_traces(fill='tozeroy', row=1, col=1)

fig.append_trace(go.Scatter(
    name="Shear",
    x=filtered_data["Station"],
    y=filtered_data["V2f"],
    showlegend=False
), row=2, col=1)

fig.update_traces(fill='tozeroy', row=2, col=1)

fig.append_trace(go.Scatter(
    name="Moment",
    x=filtered_data["Station"],
    y=filtered_data["M3f"],
    showlegend=False
), row=3, col=1)

fig.update_traces(fill='tozeroy', row=3, col=1)

fig.update_xaxes(title_text="Station (m)", row=2, col=1)
fig.update_yaxes(title_text="UDL (kN/m)", row=1, col=1)
fig.update_yaxes(title_text="V (kN)", row=2, col=1)
fig.update_yaxes(title_text="M (kNm)", row=3, col=1)

fig.update_layout(height=600, width=600, title_text="Beam Diagrams")

st.plotly_chart(fig)



st.markdown("### Glulam Beam Design")

st.markdown("#### Parameters")

formatted_stations = [f"{round(st, 2)} m" for st in filtered_data["Station"].to_list()]
selected_station = st.select_slider("Select Design Station",options=formatted_stations)
station_idx = formatted_stations.index(selected_station)

V_f = abs(filtered_data["V2f"].iloc[station_idx])
M_f = abs(filtered_data["M3f"].iloc[station_idx])
P_f = abs(filtered_data["Pf"].iloc[station_idx])

st.markdown("Factored Shear, $$V_f=$$ `" + str(V_f) + "`")
st.markdown("Factored Moment, $$M_f=$$ `" + str(M_f) + "`")
st.markdown("Factored Moment, $$P_f=$$ `" + str(P_f) + "`")

selected_beam_index = filtered_data.index[station_idx]

from libraries.TimberCalculator import *
beam_design:TimberBeamDesign = st.session_state['beam_design']

st.markdown("#### Bending Checks")

if 'moment3_check' not in st.session_state:
    st.session_state['moment3_check'] = True
#SA_Bending = st.expander("Strong-axis bending check " + ("✔️ `Pass`" if st.session_state['moment3_check'] else "❌ `Fail`"), expanded=False)

st.latex(beam_design.strongAxisPosBendingCheck.displayLatex(selected_beam_index).data)

if 'moment2_check' not in st.session_state:
    st.session_state['moment2_check'] = True
#WA_Bending = st.expander("Weak-axis bending check | " + ("✔️ `Pass`" if st.session_state['moment2_check'] else "❌ `Fail`"), expanded=False)


st.markdown("#### Shear Checks")

if 'shear_check' not in st.session_state:
    st.session_state['shear_check'] = True
#SA_Shear = st.expander("Strong-axis shear check | " + ("✔️ `Pass`" if st.session_state['shear_check'] else "❌ `Fail`"), expanded=False)

st.latex(beam_design.strongAxisShearCheck.displayLatex(selected_beam_index).data)


st.markdown("#### Compression Checks")

if 'comp_check' not in st.session_state:
    st.session_state['comp_check'] = True
#Comp_Checks = st.expander("Compression parallel-to-grain | " + ("✔️ `Pass`" if st.session_state['comp_check'] else "❌ `Fail`"), expanded=False)

st.latex(beam_design.parallelCompressionCheck.displayLatex(selected_beam_index).data)
