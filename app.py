import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os

st.set_page_config(
    page_title="Organic Reagent Table",
    layout="wide",
    page_icon="🧪"
)

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #ffffff;
    }

    h1, h2, h3 {
        color: #1f4e79;
        font-family: Arial, sans-serif;
    }

    .main-title {
        font-size: 38px;
        font-weight: 700;
        color: #1f4e79;
        padding-top: 15px;
    }

    .subtitle {
        font-size: 17px;
        color: #444444;
        margin-bottom: 25px;
    }

    .section-card {
        background-color: #f7f9fc;
        padding: 18px;
        border-radius: 12px;
        border-left: 6px solid #1f4e79;
        margin-bottom: 20px;
    }

    .footer {
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #dddddd;
        color: #666666;
        font-size: 14px;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Header with logo
# -----------------------------
col_logo, col_title = st.columns([1, 6])

with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.markdown("🧪")

with col_title:
    st.markdown(
        """
        <div class="main-title">Organic Chemistry Reagent Table</div>
        <div class="subtitle">
        Bhat Research Group · Reaction Setup and Yield Calculator
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="section-card">
    Enter reagent name, molecular weight, density, equivalents, mass, or volume.
    Change the mass or volume of any reagent and the table updates automatically.
    Select <b>Limiting Reagent</b> in the Type column to calculate product yield.
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Default table
# -----------------------------
default_df = pd.DataFrame(
    {
        "Type": ["Limiting Reagent", "Reagent", "Solvent", "Product"],
        "Name": ["Starting material", "Reagent 2", "Solvent", "Product"],
        "MW (g/mol)": [150.0, 100.0, 0.0, 250.0],
        "Density (g/mL)": [0.0, 1.05, 0.0, 0.0],
        "Equiv.": [1.0, 1.2, 0.0, 1.0],
        "% Yield": [np.nan, np.nan, np.nan, 75.0],
        "Mass (mg)": [120.0, 96.0, 0.0, 150.0],
        "Volume (mL)": [0.0, 0.0914, 5.0, 0.0],
        "mmol": [0.800, 0.960, 0.0, 0.600],
    }
)

if "table" not in st.session_state:
    st.session_state.table = default_df.copy()

if "reference_row" not in st.session_state:
    st.session_state.reference_row = 0


# -----------------------------
# Detect edited cell
# -----------------------------
def get_changed_cell():
    state = st.session_state.get("editor", {})
    edited_rows = state.get("edited_rows", {})

    if not edited_rows:
        return None, None

    last_row = list(edited_rows.keys())[-1]
    last_col = list(edited_rows[last_row].keys())[-1]

    return int(last_row), last_col


# -----------------------------
# Calculation function
# -----------------------------
def calculate_table(df, ref_row, changed_col=None):
    df = df.copy()

    # Find limiting reagent
    limiting_rows = df.index[df["Type"] == "Limiting Reagent"].tolist()

    if limiting_rows:
        limiting_row = limiting_rows[0]
    else:
        limiting_row = ref_row

    # Update reference row from mass or volume
    ref = df.loc[ref_row]

    ref_density = ref["Density (g/mL)"]
    ref_mass = ref["Mass (mg)"]
    ref_volume = ref["Volume (mL)"]

    if changed_col == "Volume (mL)" and ref_density > 0:
        ref_mass = ref_volume * ref_density * 1000
        df.loc[ref_row, "Mass (mg)"] = ref_mass

    if changed_col == "Mass (mg)" and ref_density > 0:
        df.loc[ref_row, "Volume (mL)"] = ref_mass / 1000 / ref_density

    # Reaction scale is determined from edited reagent
    ref = df.loc[ref_row]
    ref_type = ref["Type"]
    ref_mw = ref["MW (g/mol)"]
    ref_equiv = ref["Equiv."]
    ref_mass = ref["Mass (mg)"]

    if ref_type != "Solvent" and ref_mw > 0 and ref_mass > 0 and ref_equiv > 0:
        base_mmol = (ref_mass / ref_mw) / ref_equiv
    else:
        base_mmol = 0

    # Recalculate all rows
    for i, row in df.iterrows():
        row_type = row["Type"]
        mw = row["MW (g/mol)"]
        density = row["Density (g/mL)"]
        equiv = row["Equiv."]
        percent_yield = row["% Yield"]

        if row_type == "Solvent":
            df.loc[i, "mmol"] = 0
            df.loc[i, "Mass (mg)"] = 0
            continue

        if row_type == "Product":
            lim = df.loc[limiting_row]

            lim_mw = lim["MW (g/mol)"]
            lim_mass = lim["Mass (mg)"]
            lim_equiv = lim["Equiv."]

            if lim_mw > 0 and lim_mass > 0 and lim_equiv > 0:
                limiting_base_mmol = (lim_mass / lim_mw) / lim_equiv
            else:
                limiting_base_mmol = base_mmol

            product_mmol = limiting_base_mmol * equiv
            theoretical_mass_mg = product_mmol * mw if mw > 0 else 0

            if pd.notna(percent_yield):
                expected_mass_mg = theoretical_mass_mg * percent_yield / 100
            else:
                expected_mass_mg = theoretical_mass_mg

            df.loc[i, "mmol"] = product_mmol
            df.loc[i, "Mass (mg)"] = expected_mass_mg
            df.loc[i, "Volume (mL)"] = 0
            continue

        mmol = base_mmol * equiv
        mass_mg = mmol * mw if mw > 0 else 0

        if i == ref_row:
            if mw > 0 and df.loc[i, "Mass (mg)"] > 0:
                df.loc[i, "mmol"] = df.loc[i, "Mass (mg)"] / mw
            continue

        df.loc[i, "mmol"] = mmol
        df.loc[i, "Mass (mg)"] = mass_mg

        if density > 0:
            df.loc[i, "Volume (mL)"] = mass_mg / 1000 / density
        else:
            df.loc[i, "Volume (mL)"] = 0

    return df


# -----------------------------
# Table
# -----------------------------
st.subheader("Reaction Table")

edited_df = st.data_editor(
    st.session_state.table,
    key="editor",
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Type": st.column_config.SelectboxColumn(
            "Type",
            options=[
                "Limiting Reagent",
                "Reagent",
                "Solvent",
                "Product",
                "Catalyst",
                "Other",
            ],
        ),
        "Name": st.column_config.TextColumn("Name"),
        "MW (g/mol)": st.column_config.NumberColumn(
            "MW (g/mol)",
            min_value=0.0,
            format="%.3f",
        ),
        "Density (g/mL)": st.column_config.NumberColumn(
            "Density (g/mL)",
            min_value=0.0,
            format="%.3f",
        ),
        "Equiv.": st.column_config.NumberColumn(
            "Equiv.",
            min_value=0.0,
            format="%.3f",
        ),
        "% Yield": st.column_config.NumberColumn(
            "% Yield",
            min_value=0.0,
            max_value=100.0,
            format="%.1f",
        ),
        "Mass (mg)": st.column_config.NumberColumn(
            "Mass (mg)",
            min_value=0.0,
            format="%.3f",
        ),
        "Volume (mL)": st.column_config.NumberColumn(
            "Volume (mL)",
            min_value=0.0,
            format="%.4f",
        ),
        "mmol": st.column_config.NumberColumn(
            "mmol",
            min_value=0.0,
            format="%.4f",
        ),
    },
)

changed_row, changed_col = get_changed_cell()

if changed_row is not None:
    st.session_state.reference_row = changed_row

calculated_df = calculate_table(
    edited_df,
    st.session_state.reference_row,
    changed_col,
)

if not calculated_df.round(6).equals(st.session_state.table.round(6)):
    st.session_state.table = calculated_df
    st.rerun()

# -----------------------------
# Instructions
# -----------------------------
st.info(
    "Change the mass or volume of any reagent to rescale the reaction. "
    "Use Type = Limiting Reagent for the reagent that determines theoretical yield. "
    "Use Type = Product for the product row and enter the expected % yield."
)

# -----------------------------
# Download
# -----------------------------
csv = st.session_state.table.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download table as CSV",
    data=csv,
    file_name="organic_reaction_reagent_table.csv",
    mime="text/csv",
)

st.markdown(
    """
    <div class="footer">
    Bhat Research Group · Columbia College · Organic Chemistry Resources
    </div>
    """,
    unsafe_allow_html=True,
)
