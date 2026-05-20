st.subheader("Product Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    product_name = st.text_input(
        "Product Name",
        value="Desired Product"
    )

with col2:
    product_mw = st.number_input(
        "Product MW (g/mol)",
        min_value=0.0,
        value=250.0,
        step=1.0,
        format="%.3f"
    )

with col3:
    product_equiv = st.number_input(
        "Product Stoichiometry",
        min_value=0.01,
        value=1.0,
        step=0.1,
        format="%.2f",
        help="Usually 1.0 unless multiple products form per limiting reagent."
    )

with col4:
    percent_yield = st.number_input(
        "% Yield",
        min_value=0.0,
        max_value=100.0,
        value=75.0,
        step=1.0,
        format="%.1f"
    )

# Theoretical calculations
theoretical_mmol = limiting_mmol * product_equiv

theoretical_mass_mg = theoretical_mmol * product_mw

expected_mass_mg = theoretical_mass_mg * (percent_yield / 100)

theoretical_mass_g = theoretical_mass_mg / 1000
expected_mass_g = expected_mass_mg / 1000

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
            f"{theoretical_mass_g:.4f}",
            f"{percent_yield:.1f}",
            f"{expected_mass_mg:.2f}",
            f"{expected_mass_g:.4f}",
        ],
    }
)

st.dataframe(
    product_df,
    use_container_width=True,
    hide_index=True
)

st.metric(
    "Expected Isolated Product",
    f"{expected_mass_mg:.2f} mg"
)
