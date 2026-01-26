import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import preprocessor
import libraries.TimberTables as TimberTables
from libraries.eime import status_desc, EngineeringCheck

st.set_page_config(
    page_title="Timber Designer"
)

def load_data(file_path):
    data = pd.read_excel(file_path, header=1)
    return preprocessor.process_etabsdata(data)

species = st.sidebar.selectbox("Species", TimberTables.SpecifiedStrengthTable.keys())
grade = st.sidebar.selectbox("Grade", TimberTables.SpecifiedStrengthTable[species].keys())

if 'data_check' not in st.session_state:
    st.session_state['data_check'] = False

with st.sidebar.form(key="DesignInputs", border=False):

    service_condition = st.selectbox("Service Condition", TimberTables.ServiceConditionFactorTable.keys())
    eff_length_factor = st.selectbox("Restraints", TimberTables.EffectiveLengthFactorTable.keys())
    d = st.number_input("Depth", value=810)
    b = st.number_input("Width", value=240)
    submitted_inputs = st.form_submit_button('Check Design', disabled=(not st.session_state['data_check']) )

if not st.session_state['data_check']:
    st.info('Upload your results and enter your inputs to begin.', icon="↙️")
    uploaded_file = st.file_uploader("Upload ETBAS excel export.")
    if uploaded_file is not None:
         with st.spinner('Processing ETABS data...'):
            st.session_state['data'] = None
            st.session_state['data'] = load_data(uploaded_file)
         st.session_state['data_check'] = True
         st.rerun()
    st.stop()

data = st.session_state['data']

######### START LOGIC
from libraries.TimberCalculator import *
profile = RectangularProfile(b,d)
material = TimberMaterial(grade,species)
section = TimberSection(profile, material)
loading = TimberLoads()
loading.M3,loading.PL_M3,loading.PS_M3 = data["M3f"], data["PL - M3"], data["PS - M3"]
loading.V2,loading.PL_V2,loading.PS_V2 = data["V2f"], data["PL - V2"], data["PS - V2"]
loading.P,loading.PL_P,loading.PS_P = data["Pf"], data["PL - P"], data["PS - P"]
parameters = TimberDesignParameters(data["Beam Id"], data["Length"], eff_length_factor, service_condition, data["Lu"], data["Wf"], data["Sum G"])
beam_design = TimberBeamDesign(section, loading, parameters)
beam_design.checkAll()
######### END LOGIC

st.session_state['beam_design'] = beam_design

# Post Processing
table = pd.pivot_table(beam_design.utilization, values=["uM3", "uV2", "uP"], index="beam_id", aggfunc="max")

# Body Begins
st.header("Design Results")

# Success message
total_cols = len(beam_design.strongAxisPosBendingCheck.results.columns) + len(beam_design.strongAxisShearCheck.results.columns) + len(beam_design.parallelCompressionCheck.results.columns)
num_eqs = len(data.index) * total_cols
num_elems = len(table.index)
success_msg = f"**Success!** `{num_eqs}` code equations ran across `{num_elems}` different structural elements."
st.success(success_msg, icon="✅")

# Pass rate - progress bar
logs = beam_design.status_log.loc[:, beam_design.status_log.columns != 'beam_id']
worst_status = logs.max(1)
status_labels = [status_desc[status] for status in sorted(worst_status.unique())]
status_counts = worst_status.value_counts().sort_index()
status_summary = {"Pass":0, "Warning":0, "Fail":0, "Error": 0}
status_summary.update(dict(zip(status_labels, status_counts)))
passing_elements = status_summary["Pass"] + status_summary["Warning"] 
failing_elements = status_summary["Fail"]
pass_rate = passing_elements / (passing_elements + failing_elements)
rate_msg = "Pass Rate: `"+ str(round(pass_rate*100,2)) +"%`"
my_bar = st.progress(round(pass_rate,2), text=rate_msg)

# Status breakdown - pie chart
pie_chart = go.Figure(data=[go.Pie(labels=status_labels, values=status_counts, hole=.3)])

with st.spinner("Rendering scatter plot ..."):

    scatter_data = table.reset_index()
    scatter_data["Plot Seq"] = scatter_data.index

    # Y values for the area chart (all y values set to 1)
    y_area = [1] * len(scatter_data["Plot Seq"])

    # Create the figure
    util_scatter_fig = go.Figure()

    util_scatter_fig.add_trace(go.Scatter(x=scatter_data["Plot Seq"], y=scatter_data["uM3"], mode='markers', name='M3'))
    util_scatter_fig.add_trace(go.Scatter(x=scatter_data["Plot Seq"], y=scatter_data["uV2"], mode='markers', name='V2'))
    util_scatter_fig.add_trace(go.Scatter(x=scatter_data["Plot Seq"], y=scatter_data["uP"], mode='markers', name='P'))
    #fig2.add_trace(go.Scatter(x=scatter_data["Plot Seq"], y=scatter_data["uW2"], mode='markers', name='W2', customdata=scatter_data[["Beam", "Story"]], hovertemplate="<b>Story:</b> %{customdata[1]}<br><b>Beam:</b> %{customdata[0]}<br>"))
    #fig2.add_trace(go.Scatter(x=scatter_data["Plot Seq"], y=scatter_data["uV2"], mode='markers', name='V2', customdata=scatter_data[["Beam", "Story"]], hovertemplate="<b>Story:</b> %{customdata[1]}<br><b>Beam:</b> %{customdata[0]}<br>"))
    #fig2.add_trace(go.Scatter(x=scatter_data["Plot Seq"], y=scatter_data["uP"], mode='markers', name='P', customdata=scatter_data[["Beam", "Story"]], hovertemplate="<b>Story:</b> %{customdata[1]}<br><b>Beam:</b> %{customdata[0]}<br>"))
    
    # Area chart with filled area
    util_scatter_fig.add_trace(go.Scatter(x=scatter_data["Plot Seq"], y=y_area, fill='tozeroy', mode='none', name='Pass', fillcolor='rgba(39, 245, 101, 0.3)'))

    # Update layout
    util_scatter_fig.update_layout(
        xaxis=dict(
            title="Beams",
            showticklabels=False  # Hide x-axis tick labels
        ),
        yaxis=dict(
            title="Utilization",
            range = [0,2]
            ),
        title="Utilization of beams by design check"
    )

    st.plotly_chart(util_scatter_fig)

st.write("###### Utilization Table")

def utilization_color(val):
    color = '#ffd6de' if val > 1 else '#daf5dd'
    return 'background-color: %s' % color

with st.spinner("Rendering utilization table ..."):
    colored_table = table.style.map(utilization_color, subset=["uM3", "uV2", "uP"])
    st.dataframe(colored_table)

st.write("###### Output Summary")
st.plotly_chart(pie_chart)

st.write("###### Error Log")
error_counts = logs.apply(pd.Series.value_counts)
error_labels = pd.Series(error_counts.index).apply(lambda x: status_desc[x])
error_counts = error_counts.reset_index(drop=True)
error_counts.insert(0, "Status", error_labels)

st.dataframe(error_counts)
st.write("Legend")
cc_ids = list(beam_design.checklist.keys())
cc_desc = [check.message for check in beam_design.checklist.values()]
check_codes = pd.DataFrame({"Code": cc_ids, "Description":cc_desc})
st.write(check_codes)

inspection_index:int = st.number_input("Inspect Section", min_value=0, step=1, format="%d")

st.markdown('**Bending**')
st.latex(beam_design.strongAxisPosBendingCheck.displayLatex(inspection_index).data)
st.markdown('**Shear**')
st.latex(beam_design.strongAxisShearCheck.displayLatex(inspection_index).data)
st.markdown('**Compression**')
st.latex(beam_design.parallelCompressionCheck.displayLatex(inspection_index).data)

st.write("###### Full Data Table")
st.dataframe(data)