import streamlit as st
import pandas as pd

st.set_page_config(page_title="Organic Reaction Reagent Table", layout="wide")

st.title("Organic Chemistry Reagent Table Generator")

st.write(
    "Enter reagents, molecular weights, densities, and equivalents. "
    "The table updates live when reaction scale, mass, volume, or yield values change."
)

st.sidebar.header("Reaction Scale")

limiting_mmol = st.sidebar.number_input(
    "Limiting reagent amount (mmol)",
    min_value=0.001,
    value=1.000,
    step=0.100,
    format="%.3f",
)

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

df["mmol"] = df["Equiv."] * limiting_mmol

df["Calculated Mass (mg)"] = df.apply(
    lambda row: row["mmol"] * row["MW (g/mol)"]
    if row["MW (g/mol)"] > 0
    else 0,
    axis=1,
)

df["Calculated Volume (mL)"] = df.apply(
    lambda row: row["Calculated Mass (mg)"] / 1000 / row["Density (g/mL)"]
    if row["Density (g/mL)"] > 0 and row["Calculated Mass (mg)"] > 0
    else 0,
    axis=1,
)

df["Mass from Entered Volume (mg)"] = df.apply(
    lambda row: row["Volume (mL)"] * row["Density (g/mL)"] * 1000
    if row["Density (g/mL)"] > 0 and row["Volume (mL)"] > 0
    else 0,
    axis=1,
)

df["mmol from Entered Mass"] = df.apply(
    lambda row: row["Mass (mg)"] / row["MW (g/mol)"]
    if row["MW (g/mol)"] > 0 and row["Mass (mg)"] > 0
    else 0,
    axis=1,
)

df["Equiv. from Entered Mass"] = df.apply(
    lambda row: row["mmol from Entered Mass"] / limiting_mmol
    if limiting_mmol > 0 and row["mmol from Entered Mass"] > 0
    else 0,
    axis=1,
)

st.subheader("Calculated Reaction Table")

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

st.subheader("Product Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    product_name = st.text_input("Product Name", value="Desired Product")

with col2:
    product_mw = st.number_input(
        "Product MW (g/mol)",
        min_value=0.0,
        value=250.0,
        step=1.0,
        format="%.3f",
    )

with col3:
    product_equiv = st.number_input(
        "Product Stoichiometry",
        min_value=0.01,
        value=1.0,
        step=0.1,
        format="%.2f",
        help="Usually 1.0 unless multiple products form per limiting reagent.",
    )

with col4:
    percent_yield = st.number_input(
        "% Yield",
        min_value=0.0,
        max_value=100.0,
        value=75.0,
        step=1.0,
        format="%.1f",
    )

theoretical_mmol = limiting_mmol * product_equiv
theoretical_mass_mg = theoretical_mmol * product_mw
expected_mass_mg = theoretical_mass_mg * (percent_yield / 100)

product_df = pd.DataFrame(
    {
        "Parameter": [
            "Product",
            "Theoretical mmol",
            "Theoretical Yield (mg)",
            "Theoretical Yield (g)",
            "Expected Yield (%)",
            "Expected Product (mg)",
            "Expected Product (g)",
        ],
        "Value": [
            product_name,
            f"{theoretical_mmol:.3f}",
            f"{theoretical_mass_mg:.2f}",
            f"{theoretical_mass_mg / 1000:.4f}",
            f"{percent_yield:.1f}",
            f"{expected_mass_mg:.2f}",
            f"{expected_mass_mg / 1000:.4f}",
        ],
    }
)

st.dataframe(product_df, use_container_width=True, hide_index=True)

st.metric("Expected Isolated Product", f"{expected_mass_mg:.2f} mg")

csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download reagent table as CSV",
    data=csv,
    file_name="organic_reaction_reagent_table.csv",
    mime="text/csv",
)
