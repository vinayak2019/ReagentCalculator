import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Organic Reaction Reagent Table", layout="wide")

st.title("Organic Chemistry Reagent Table Generator")

st.write(
    "Enter the amount of one reagent you plan to use. "
    "Mark that reagent as the scale-setting reagent. "
    "All other reagents and the expected product mass will update automatically."
)

# -----------------------------
# Default table
# -----------------------------
default_df = pd.DataFrame(
    {
        "Use as Scale": [True, False, False, False],
        "Type": ["Reagent", "Reagent", "Solvent", "Product"],
        "Name": ["Starting material", "Reagent 2", "Solvent", "Product"],
        "MW (g/mol)": [150.0, 100.0, 0.0, 250.0],
        "Density (g/mL)": [0.0, 1.05, 0.0, 0.0],
        "Equiv.": [1.0, 1.2, 0.0, 1.0],
        "% Yield": [np.nan, np.nan, np.nan, 75.0],
        "Mass (mg)": [120.0, 0.0, 0.0, 0.0],
        "Volume (mL)": [0.0, 0.0, 5.0, 0.0],
        "mmol": [0.0, 0.0, 0.0, 0.0],
    }
)

if "reagent_table" not in st.session_state:
    st.session_state.reagent_table = default_df.copy()


# -----------------------------
# Calculation function
# -----------------------------
def calculate_table(df):
    df = df.copy()

    # Ensure only one row is used as scale
    scale_rows = df.index[df["Use as Scale"] == True].tolist()

    if len(scale_rows) == 0:
        df.loc[0, "Use as Scale"] = True
        scale_index = 0
    else:
        scale_index = scale_rows[0]
        df["Use as Scale"] = False
        df.loc[scale_index, "Use as Scale"] = True

    scale_row = df.loc[scale_index]

    scale_mw = scale_row["MW (g/mol)"]
    scale_mass_mg = scale_row["Mass (mg)"]
    scale_equiv = scale_row["Equiv."]

    if scale_mw > 0 and scale_mass_mg > 0 and scale_equiv > 0:
        scale_mmol = (scale_mass_mg / scale_mw) / scale_equiv
    else:
        scale_mmol = 0

    for i, row in df.iterrows():
        mw = row["MW (g/mol)"]
        density = row["Density (g/mL)"]
        equiv = row["Equiv."]
        row_type = row["Type"]
        percent_yield = row["% Yield"]

        # Solvents are not calculated by equivalents
        if row_type == "Solvent":
            df.loc[i, "mmol"] = 0
            continue

        # Product calculation
        if row_type == "Product":
            product_mmol = scale_mmol * equiv
            theoretical_mass_mg = product_mmol * mw

            if pd.notna(percent_yield):
                expected_mass_mg = theoretical_mass_mg * percent_yield / 100
            else:
                expected_mass_mg = theoretical_mass_mg

            df.loc[i, "mmol"] = product_mmol
            df.loc[i, "Mass (mg)"] = expected_mass_mg
            df.loc[i, "Volume (mL)"] = 0
            continue

        # Reagent calculation
        reagent_mmol = scale_mmol * equiv
        reagent_mass_mg = reagent_mmol * mw if mw > 0 else 0

        df.loc[i, "mmol"] = reagent_mmol

        # Do not overwrite the manually entered scale reagent mass
        if i != scale_index:
            df.loc[i, "Mass (mg)"] = reagent_mass_mg

        if density > 0:
            df.loc[i, "Volume (mL)"] = reagent_mass_mg / 1000 / density
        else:
            df.loc[i, "Volume (mL)"] = 0

    return df


# -----------------------------
# Editable table
# -----------------------------
edited_df = st.data_editor(
    st.session_state.reagent_table,
    num_rows="dynamic",
    use_container_width=True,
    key="editor",
    column_config={
        "Use as Scale": st.column_config.CheckboxColumn(
            "Use as Scale",
            help="Check the reagent whose entered mass determines the reaction scale.",
        ),
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
    disabled=["mmol"],
)

calculated_df = calculate_table(edited_df)

if not calculated_df.round(6).equals(st.session_state.reagent_table.round(6)):
    st.session_state.reagent_table = calculated_df
    st.rerun()


# -----------------------------
# Notes
# -----------------------------
st.info(
    "Use the checkbox to choose the reagent that sets the reaction scale. "
    "Enter the mass you want to use for that reagent. "
    "The app calculates all other reagent masses and volumes from equivalents. "
    "For the product row, enter the product MW, product stoichiometry, and expected % yield."
)

csv = st.session_state.reagent_table.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download table as CSV",
    data=csv,
    file_name="organic_reaction_reagent_table.csv",
    mime="text/csv",
)
