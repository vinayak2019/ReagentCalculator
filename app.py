import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Organic Reagent Table", layout="wide")

st.title("Organic Chemistry Reagent Table")

st.write(
    "Edit the mass or volume of any reagent. "
    "That row becomes the reference, and the rest of the table updates automatically."
)

default_df = pd.DataFrame(
    {
        "Type": ["Reagent", "Reagent", "Solvent", "Product"],
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


def get_changed_cell():
    state = st.session_state.get("editor", {})
    edited_rows = state.get("edited_rows", {})

    if not edited_rows:
        return None, None

    last_row = list(edited_rows.keys())[-1]
    last_col = list(edited_rows[last_row].keys())[-1]

    return int(last_row), last_col


def calculate_from_reference(df, ref_row, changed_col=None):
    df = df.copy()

    ref = df.loc[ref_row]

    ref_type = ref["Type"]
    ref_mw = ref["MW (g/mol)"]
    ref_density = ref["Density (g/mL)"]
    ref_equiv = ref["Equiv."]
    ref_mass = ref["Mass (mg)"]
    ref_volume = ref["Volume (mL)"]

    # If user changed volume, calculate mass from volume and density
    if changed_col == "Volume (mL)" and ref_density > 0:
        ref_mass = ref_volume * ref_density * 1000
        df.loc[ref_row, "Mass (mg)"] = ref_mass

    # If user changed mass, calculate volume from mass and density
    if changed_col == "Mass (mg)" and ref_density > 0:
        df.loc[ref_row, "Volume (mL)"] = ref_mass / 1000 / ref_density

    # Calculate mmol of edited reference row
    if ref_type != "Solvent" and ref_mw > 0 and ref_mass > 0:
        ref_mmol = ref_mass / ref_mw
        df.loc[ref_row, "mmol"] = ref_mmol
    else:
        ref_mmol = 0

    # Convert edited row into the 1.0 equivalent reaction scale
    if ref_equiv > 0:
        base_mmol = ref_mmol / ref_equiv
    else:
        base_mmol = 0

    # Recalculate every other row
    for i, row in df.iterrows():
        row_type = row["Type"]
        mw = row["MW (g/mol)"]
        density = row["Density (g/mL)"]
        equiv = row["Equiv."]
        percent_yield = row["% Yield"]

        if i == ref_row:
            continue

        if row_type == "Solvent":
            df.loc[i, "mmol"] = 0
            df.loc[i, "Mass (mg)"] = 0
            continue

        mmol = base_mmol * equiv
        mass_mg = mmol * mw if mw > 0 else 0

        if row_type == "Product":
            if pd.notna(percent_yield):
                mass_mg = mass_mg * percent_yield / 100

            df.loc[i, "mmol"] = mmol
            df.loc[i, "Mass (mg)"] = mass_mg
            df.loc[i, "Volume (mL)"] = 0
            continue

        df.loc[i, "mmol"] = mmol
        df.loc[i, "Mass (mg)"] = mass_mg

        if density > 0:
            df.loc[i, "Volume (mL)"] = mass_mg / 1000 / density
        else:
            df.loc[i, "Volume (mL)"] = 0

    return df


edited_df = st.data_editor(
    st.session_state.table,
    key="editor",
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Type": st.column_config.SelectboxColumn(
            "Type",
            options=["Reagent", "Solvent", "Product", "Catalyst", "Other"],
        ),
        "Name": st.column_config.TextColumn("Name"),
        "MW (g/mol)": st.column_config.NumberColumn("MW (g/mol)", min_value=0.0, format="%.3f"),
        "Density (g/mL)": st.column_config.NumberColumn("Density (g/mL)", min_value=0.0, format="%.3f"),
        "Equiv.": st.column_config.NumberColumn("Equiv.", min_value=0.0, format="%.3f"),
        "% Yield": st.column_config.NumberColumn("% Yield", min_value=0.0, max_value=100.0, format="%.1f"),
        "Mass (mg)": st.column_config.NumberColumn("Mass (mg)", min_value=0.0, format="%.3f"),
        "Volume (mL)": st.column_config.NumberColumn("Volume (mL)", min_value=0.0, format="%.4f"),
        "mmol": st.column_config.NumberColumn("mmol", min_value=0.0, format="%.4f"),
    },
)

changed_row, changed_col = get_changed_cell()

if changed_row is not None:
    st.session_state.reference_row = changed_row

calculated_df = calculate_from_reference(
    edited_df,
    st.session_state.reference_row,
    changed_col,
)

if not calculated_df.round(6).equals(st.session_state.table.round(6)):
    st.session_state.table = calculated_df
    st.rerun()

st.info(
    "To scale the reaction, change the Mass or Volume of any non-solvent reagent. "
    "The app uses that row's equivalents to calculate the rest of the reaction table."
)

csv = st.session_state.table.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download table as CSV",
    csv,
    "organic_reaction_reagent_table.csv",
    "text/csv",
)
