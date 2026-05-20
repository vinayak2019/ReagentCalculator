import streamlit as st
import pandas as pd

st.set_page_config(page_title="Organic Reaction Reagent Table", layout="wide")

st.title("Organic Chemistry Reagent Table Generator")

st.write(
    "Enter reagents, molecular weights, densities, and equivalents. "
    "The table updates live when mass, volume, equivalents, or scale are changed."
)

st.sidebar.header("Reaction Scale")

limiting_mmol = st.sidebar.number_input(
    "Limiting reagent amount (mmol)",
    min_value=0.001,
    value=1.000,
    step=0.100,
    format="%.3f"
)

st.sidebar.write("All reagent amounts are calculated relative to this scale.")

default_data = pd.DataFrame(
    {
        "Reagent": ["Limiting reagent", "Reagent 2", "Solvent"],
        "MW (g/mol)": [150.0, 100.0, 0.0],
        "Density (g/mL)": [0.0, 1.05, 0.0],
        "Equiv.": [1.0, 1.2, 0.0],
        "Mass (mg)": [150.0, 120.0, 0.0],
        "Volume (mL)": [0.0, 0.114, 5.0],
        "Role": ["Limiting reagent", "Reagent", "Solvent"],
    }
)

st.subheader("Editable Reagent Table")

edited = st.data_editor(
    default_data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Reagent": st.column_config.TextColumn("Reagent"),
        "MW (g/mol)": st.column_config.NumberColumn("MW (g/mol)", min_value=0.0, format="%.3f"),
        "Density (g/mL)": st.column_config.NumberColumn("Density (g/mL)", min_value=0.0, format="%.3f"),
        "Equiv.": st.column_config.NumberColumn("Equiv.", min_value=0.0, format="%.3f"),
        "Mass (mg)": st.column_config.NumberColumn("Mass (mg)", min_value=0.0, format="%.3f"),
        "Volume (mL)": st.column_config.NumberColumn("Volume (mL)", min_value=0.0, format="%.4f"),
        "Role": st.column_config.SelectboxColumn(
            "Role",
            options=["Limiting reagent", "Reagent", "Catalyst", "Solvent", "Workup", "Other"],
        ),
    },
)

df = edited.copy()

# Calculations
df["mmol"] = df["Equiv."] * limiting_mmol

df["Calculated Mass (mg)"] = df.apply(
    lambda row: row["mmol"] * row["MW (g/mol)"] if row["MW (g/mol)"] > 0 else 0,
    axis=1
)

df["Calculated Volume (mL)"] = df.apply(
    lambda row: row["Calculated Mass (mg)"] / 1000 / row["Density (g/mL)"]
    if row["Density (g/mL)"] > 0 and row["Calculated Mass (mg)"] > 0
    else 0,
    axis=1
)

df["Mass from Entered Volume (mg)"] = df.apply(
    lambda row: row["Volume (mL)"] * row["Density (g/mL)"] * 1000
    if row["Density (g/mL)"] > 0 and row["Volume (mL)"] > 0
    else 0,
    axis=1
)

df["mmol from Entered Mass"] = df.apply(
    lambda row: row["Mass (mg)"] / row["MW (g/mol)"]
    if row["MW (g/mol)"] > 0 and row["Mass (mg)"] > 0
    else 0,
    axis=1
)

df["Equiv. from Entered Mass"] = df.apply(
    lambda row: row["mmol from Entered Mass"] / limiting_mmol
    if limiting_mmol > 0 and row["mmol from Entered Mass"] > 0
    else 0,
    axis=1
)

display_cols = [
    "Reagent",
    "Role",
    "MW (g/mol)",
    "Density (g/mL)",
    "Equiv.",
    "mmol",
    "Calculated Mass (mg)",
    "Calculated Volume (mL)",
    "Mass (mg)",
    "Volume (mL)",
    "Equiv. from Entered Mass",
]

st.subheader("Calculated Reaction Table")
st.dataframe(
    df[display_cols],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Reaction Summary")

summary = df[df["Role"] != "Solvent"].copy()

st.write(f"**Limiting scale:** {limiting_mmol:.3f} mmol")

st.dataframe(
    summary[
        [
            "Reagent",
            "Equiv.",
            "mmol",
            "Calculated Mass (mg)",
            "Calculated Volume (mL)",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download reagent table as CSV",
    data=csv,
    file_name="organic_reaction_reagent_table.csv",
    mime="text/csv",
)