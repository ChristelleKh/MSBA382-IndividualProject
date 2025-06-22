import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Framingham CHD Risk Dashboard", page_icon="❤️", layout="wide")

st.title("❤️ Framingham Heart Study: CHD Risk Dashboard")

def check_password():
    def password_entered():
        if st.session_state["password"] == "CHD2025":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # cleanup
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Wrong password
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Correct password
        return True

if not check_password():
    st.stop()

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/ChristelleKh/MSBA382-IndividualProject/main/framingham_cleaned.csv"
    df = pd.read_csv(url)
    df['Smoking_Status'] = df['currentSmoker'].apply(lambda x: 'Current Smoker' if x == 1 else 'Non-Smoker')
    education_map = {1.0: 'Some High School', 2.0: 'High School/GED', 3.0: 'Some College', 4.0: 'College'}
    df['Education_Level'] = df['education'].map(education_map)

    return df


data = load_data()

# --- Main Layout with Fixed Filter Panel  ---
filters_col, plots_col = st.columns([1, 4])

with filters_col:
    st.subheader("Filter Data")

    gender_options = st.multiselect("Select Gender:", options=data['gender'].unique(), default=data['gender'].unique())
    age_min = int(data['age'].min())
    age_max = int(data['age'].max())
    age_range = st.slider("Select Age Range:", min_value=age_min, max_value=age_max, value=(age_min, age_max))

    risk_factor = st.selectbox("Select Risk Factor:", ["Smoking", "Body Weight", "Blood Pressure"], index=0)

filtered_data = data[
    (data['gender'].isin(gender_options)) &
    (data['age'].between(age_range[0], age_range[1]))
]

risk_data = filtered_data[filtered_data['TenYearCHD'] == 1]

# --- Chart Generation (with reduced height for better fit) ---
CHART_HEIGHT = 320

# --- Always shown ---

# Gender plot 
chd_rate_gender = filtered_data.groupby('gender')['TenYearCHD'].mean().reset_index()
chd_rate_gender['CHD_Risk_%'] = chd_rate_gender['TenYearCHD'] * 100
fig_sex = px.bar(chd_rate_gender, x='gender', y='CHD_Risk_%', title="CHD Risk Rate by Gender",
                 color='gender', color_discrete_map={'Male': '#800020', 'Female': '#A64A4A'})
fig_sex.update_layout(xaxis_showgrid=False, yaxis_showgrid=False, yaxis_title=None, xaxis_title=None, height=CHART_HEIGHT, showlegend=False, bargap=0.4)


# Age distribution plot 
fig_age = px.histogram(risk_data, x='age', marginal='box', title="Age Distribution of CHD Cases", color_discrete_sequence=['#800020'])
fig_age.update_layout(xaxis_showgrid=False, yaxis_showgrid=False, yaxis_title=None, height=CHART_HEIGHT)


# Education plot 
CUSTOM_RED_PALETTE = ['#800020', '#993333', '#A64A4A', '#BFBFBF']
chd_rate_edu = filtered_data.groupby('Education_Level')['TenYearCHD'].mean().reset_index()
chd_rate_edu['CHD_Risk_%'] = chd_rate_edu['TenYearCHD'] * 100
edu_order = ['Some High School', 'High School/GED', 'Some College', 'College']
# Create color map based on risk
sorted_by_risk = chd_rate_edu.sort_values('CHD_Risk_%', ascending=False)
color_map_edu = {cat: color for cat, color in zip(sorted_by_risk['Education_Level'], CUSTOM_RED_PALETTE)}
# Sort back for plotting
chd_rate_edu['Education_Level'] = pd.Categorical(chd_rate_edu['Education_Level'], categories=edu_order, ordered=True)
chd_rate_edu = chd_rate_edu.sort_values('Education_Level')
fig_edu = px.bar(chd_rate_edu, x='Education_Level', y='CHD_Risk_%', title='CHD Risk Rate by Education',
                 color='Education_Level', color_discrete_map=color_map_edu)
fig_edu.update_layout(xaxis_showgrid=False, yaxis_showgrid=False, yaxis_title=None, xaxis_title=None, showlegend=False, height=CHART_HEIGHT)


# Smoking
chd_rate_smoke = filtered_data.groupby('Smoking_Status')['TenYearCHD'].mean().reset_index()
chd_rate_smoke['CHD_Risk_%'] = chd_rate_smoke['TenYearCHD'] * 100
fig_smoke = px.bar(chd_rate_smoke, x='Smoking_Status', y='CHD_Risk_%', title="CHD Risk by Smoking Status", color='Smoking_Status', color_discrete_map={'Current Smoker': '#800020', 'Non-Smoker': '#898989'})
fig_smoke.update_layout(xaxis_showgrid=False, yaxis_showgrid=False, yaxis_title=None, showlegend=False, xaxis_title=None, height=CHART_HEIGHT)

smokers_df = filtered_data[filtered_data['currentSmoker'] == 1].copy()
bins = [0, 9, 19, 70]
labels = ['Light (1-9)', 'Moderate (10-19)', 'Heavy (20+)']
smokers_df['Smoking_Intensity'] = pd.cut(smokers_df['cigsPerDay'], bins=bins, labels=labels, right=False)
chd_rate_intensity = smokers_df.groupby('Smoking_Intensity')['TenYearCHD'].mean().reset_index()
chd_rate_intensity['CHD_Risk_%'] = chd_rate_intensity['TenYearCHD'] * 100
fig_intensity = px.bar(chd_rate_intensity, x='Smoking_Intensity', y='CHD_Risk_%', title="CHD Risk by Smoking Intensity", color='Smoking_Intensity', color_discrete_sequence=['#BFBFBF', '#A64A4A', '#800020'])
fig_intensity.update_layout(xaxis_showgrid=False, yaxis_showgrid=False, yaxis_title=None, xaxis_title=None, showlegend=False, height=CHART_HEIGHT)

# Physical Health
fig_bmi = go.Figure()
fig_bmi.add_trace(go.Box(y=filtered_data[filtered_data['TenYearCHD'] == 0]['BMI'], name='No CHD', marker_color='#898989'))
fig_bmi.add_trace(go.Box(y=filtered_data[filtered_data['TenYearCHD'] == 1]['BMI'], name='CHD Risk', marker_color='#800020'))
fig_bmi.update_layout(title="BMI by CHD Status", xaxis_showgrid=False, yaxis_showgrid=False, yaxis_title=None, showlegend=False, height=CHART_HEIGHT)

fig_chol = go.Figure()
fig_chol.add_trace(go.Box(y=filtered_data[filtered_data['TenYearCHD'] == 0]['totChol'], name='No CHD', marker_color='#898989'))
fig_chol.add_trace(go.Box(y=filtered_data[filtered_data['TenYearCHD'] == 1]['totChol'], name='CHD Risk', marker_color='#800020'))
fig_chol.update_layout(title="Cholesterol by CHD Status", xaxis_showgrid=False, yaxis_showgrid=False, yaxis_title=None, showlegend=False, height=CHART_HEIGHT)

# BP
chd_rate_bp = filtered_data.groupby('BP_Category')['TenYearCHD'].mean().reset_index()
chd_rate_bp['CHD_Risk_%'] = chd_rate_bp['TenYearCHD'] * 100
bp_order = ['Normal', 'Elevated', 'Hypertension Stage 1', 'Hypertension Stage 2']
chd_rate_bp['BP_Category'] = pd.Categorical(chd_rate_bp['BP_Category'], categories=bp_order, ordered=True)
chd_rate_bp = chd_rate_bp.sort_values('BP_Category')
fig_bp = px.bar(chd_rate_bp, x='BP_Category', y='CHD_Risk_%', title="CHD Risk by Blood Pressure Category", color='BP_Category', color_discrete_sequence=['#BFBFBF', '#A64A4A', '#993333', '#800020'])
fig_bp.update_layout(xaxis_showgrid=False, yaxis_showgrid=False, yaxis_title=None, xaxis_title=None, showlegend=False, height=CHART_HEIGHT)


# Dashboard Layout
with plots_col:
    # Top row: always demographics
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        st.plotly_chart(fig_sex, use_container_width=True)
    with r1c2:
        st.plotly_chart(fig_age, use_container_width=True)
    with r1c3:
        st.plotly_chart(fig_edu, use_container_width=True)


    # Bottom row: only selected risk factor
    if risk_factor == "Smoking":
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.plotly_chart(fig_smoke, use_container_width=True)
        with r2c2:
            st.plotly_chart(fig_intensity, use_container_width=True)

    elif risk_factor == "Body Weight":
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.plotly_chart(fig_bmi, use_container_width=True)
        with r2c2:
            st.plotly_chart(fig_chol, use_container_width=True)

    elif risk_factor == "Blood Pressure":
        st.plotly_chart(fig_bp, use_container_width=True)



