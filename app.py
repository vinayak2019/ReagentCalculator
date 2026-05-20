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

    # Find limiting reagent row
    limiting_rows = df.index[df["Type"] == "Limiting Reagent"].tolist()

    if limiting_rows:
        limiting_row = limiting_rows[0]
    else:
        limiting_row = ref_row

    # First update reference row if volume or mass changed
    ref = df.loc[ref_row]
    ref_density = ref["Density (g/mL)"]
    ref_mass = ref["Mass (mg)"]
    ref_volume = ref["Volume (mL)"]

    if changed_col == "Volume (mL)" and ref_density > 0:
        ref_mass = ref_volume * ref_density * 1000
        df.loc[ref_row, "Mass (mg)"] = ref_mass

    if changed_col == "Mass (mg)" and ref_density > 0:
        df.loc[ref_row, "Volume (mL)"] = ref_mass / 1000 / ref_density

    # Use edited row to determine reaction scale
    ref = df.loc[ref_row]
    ref_mw = ref["MW (g/mol)"]
    ref_equiv = ref["Equiv."]
    ref_mass = ref["Mass (mg)"]

    if ref_mw > 0 and ref_mass > 0 and ref_equiv > 0:
        base_mmol = (ref_mass / ref_mw) / ref_equiv
    else:
        base_mmol = 0

    # Recalculate table
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

        mmol = base_mmol * equiv
        mass_mg = mmol * mw if mw > 0 else 0

        if i == ref_row:
            if mw > 0 and df.loc[i, "Mass (mg)"] > 0:
                df.loc[i, "mmol"] = df.loc[i, "Mass (mg)"] / mw
            continue

        if row_type == "Product":
            # Product amount is calculated from limiting reagent
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
            options=["Limiting Reagent", "Reagent", "Solvent", "Product", "Catalyst", "Other"],
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
