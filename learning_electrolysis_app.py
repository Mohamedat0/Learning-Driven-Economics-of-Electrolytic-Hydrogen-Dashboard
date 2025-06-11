import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from regional_utils import (alpha_from_learning_rate,
                            generate_regional_stack_data,
                            generate_regional_bop_epc_data)
from lcoh_utils import (calculate_crf, calculate_lcoh,
                        generate_lcoh_projections, generate_lcoh_sensitivity)
from learning_investment_utils import (generate_stack_learning_investments,
                                       generate_bop_epc_learning_investments)
from target_cost_utils import (generate_target_cost_data_stack,
                              generate_target_cost_data_bop_epc)
from learning_investment_tab_new import render_learning_investment_tab
# No longer needed - using render_learning_investment_tab instead

# Configure page
st.set_page_config(page_title="Electrolysis Cost Projections Dashboard",
                   page_icon="⚡",
                   layout="wide")

# ==================== INITIALIZE SESSION STATE ====================
def initialize_session_state():
    """Initialize session state with default values if not already set"""
    defaults = {
        # Stack learning rates
        "wpem_lr": 20.0,
        "walk_lr": 20.0,
        "cpem_lr": 20.0,
        "calk_lr": 20.0,
        
        # Stack costs
        "wpem_cost": 600.0,
        "walk_cost": 340.0,
        "cpem_cost": 600.0,
        "calk_cost": 110.0,
        
        # BoP & EPC learning rates
        "usa_lr": 10.0,
        "eu_lr": 10.0,
        "china_lr": 10.0,
        "row_lr": 10.0,
        
        # BoP & EPC costs
        "usa_cost_pem": 1900.0,
        "eu_cost_pem": 1900.0,
        "china_cost_pem": 430.0,
        "row_cost_pem": 1160.0,
        "usa_cost_alk": 2150.0,
        "eu_cost_alk": 2150.0,
        "china_cost_alk": 490.0,
        "row_cost_alk": 1320.0
    }
    
    # Add capacity and growth rate defaults
    for region in ["usa", "eu", "china", "row"]:
        for tech in ["wpem", "walk", "cpem", "calk"]:
            defaults[f"{region}_{tech}_cap"] = 100.0
            defaults[f"{region}_{tech}_growth"] = 10.0
    
    # Add WACC defaults
    for region in ["usa", "eu", "china", "row"]:
        defaults[f"{region}_wacc"] = 10.0
        defaults[f"{region}_fom_percentage"] = 2.0
        defaults[f"{region}_electricity"] = 50.0
        defaults[f"{region}_utilization"] = 50.0
        defaults[f"{region}_efficiency"] = 55.0
    
    # Add projection parameter defaults
    defaults["projection_years"] = 25
    defaults["base_year"] = 2025
    
    # Set defaults only if not already in session state
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize session state
initialize_session_state()

# Title and introduction
st.title("Learning-Driven Economics of Electrolytic Hydrogen Dashboard")
st.markdown("""
Advanced electrolysis cost modeling platform for electrolytic hydrogen industry analysis. This tool generates comprehensive cost projections and techno-economic analysis based on various learning curve models across various regions.

**Core Capabilities**:
1. **Technology Analysis**: Four electrolysis stack technologies (Western/Chinese PEM & ALK) with three learning models:
   - **Shared Learning**: All technologies benefit from global capacity expansion.
   - **Technological Fragmentation**: PEM and ALK technologies learn independently.
   - **Regional Fragmentation**: Assumes fragmentation of supply chains between Chinese and Western technologies (e.g., Western PEM and Chinese PEM learning independently).

2. **Regional Market Modeling**: Balance of Plant & EPC cost projections across key markets (USA, EU, China, Rest of World) with two learning scenarios:
   - **Local Learning**: Costs decrease based on regional capacity deployment.
   - **Global Learning**: Costs decrease based on worldwide capacity expansion.

3. **Investment Planning**: LCOH calculations, sensitivity analysis, and capacity growth projections. Includes learning investment analysis and capacity requirements modeling, crucial for technology roadmapping and strategic decision-making.

Designed for researchers, industry analysts, investment professionals, and policy analysts and makers requiring detailed cost projections for hydrogen production technology assessment.

**To review the conceptual basis behind the different learning models, please refer to the accompanying research paper: [Link to be provided]**
""")

# Define the technologies and regions
TECHNOLOGIES = ['western_pem', 'chinese_pem', 'western_alk', 'chinese_alk']
REGIONS = ['usa', 'eu', 'china', 'row']


# Helper function to create nice display names for stacks
def get_stack_display_name(tech):
    parts = tech.split('_')
    return f"{parts[0].capitalize()} {parts[1].upper()}"


# Helper function to create nice display names for regions
def get_region_display_name(region):
    if region == 'usa':
        return "USA"
    elif region == 'eu':
        return "European Union"
    elif region == 'china':
        return "China"
    elif region == 'row':
        return "Rest of World"
    else:
        return region.upper()


# Helper function to calculate learning rate from alpha parameter
def calculate_learning_rate(alpha):
    """
    Convert the learning parameter (alpha) to a learning rate.

    The learning rate represents the percentage reduction in cost
    for each doubling of installed capacity.

    Parameters:
    -----------
    alpha : float
        Learning parameter

    Returns:
    --------
    float
        Learning rate (% reduction per doubling)
    """
    # Calculate learning rate
    lr = (1 - 2**alpha) * 100
    return lr


# Initialize variables that need to be shared across tabs
region_base_capacities = {}
region_tech_growth_rates = {}

# Create main tabs for Stack vs BoP+EPC vs LCOH
main_tabs = st.tabs([
    "Electrolysis Stacks", "BoP & EPC", "Regional Growth",
    "LCOH Calculator", "Learning Investment"
])

# ==================== SIDEBAR PARAMETERS ====================
with st.sidebar:
    st.subheader("Model Parameters")
    
    # Add Reset to Defaults button
    if st.button("Reset to Defaults", use_container_width=True, type="primary"):
        # First clear all existing session state
        keys_to_clear = [k for k in st.session_state.keys() if not str(k).startswith('_')]
        for key in keys_to_clear:
            del st.session_state[key]
        
        # Then set the exact default values that match widget defaults
        defaults = {
            # Stack learning rates (match widget defaults)
            "wpem_lr": 20.0,
            "walk_lr": 20.0, 
            "cpem_lr": 20.0,
            "calk_lr": 20.0,
            
            # Stack costs (match widget defaults)
            "wpem_cost": 600.0,
            "walk_cost": 340.0,
            "cpem_cost": 600.0,
            "calk_cost": 110.0,
            
            # BoP & EPC learning rates (match widget defaults)
            "usa_lr": 10.0,
            "eu_lr": 10.0,
            "china_lr": 10.0,
            "row_lr": 10.0,
            
            # BoP & EPC costs (match widget defaults)
            "usa_cost_pem": 1900.0,
            "eu_cost_pem": 1900.0,
            "china_cost_pem": 430.0,
            "row_cost_pem": 1160.0,
            "usa_cost_alk": 2150.0,
            "eu_cost_alk": 2150.0,
            "china_cost_alk": 490.0,
            "row_cost_alk": 1320.0
        }
        
        # Add capacity and growth rate defaults
        for region in ["usa", "eu", "china", "row"]:
            for tech in ["wpem", "walk", "cpem", "calk"]:
                defaults[f"{region}_{tech}_cap"] = 100.0
                defaults[f"{region}_{tech}_growth"] = 10.0
        
        # Set all defaults in session state
        for key, value in defaults.items():
            st.session_state[key] = value
        
        st.rerun()

    # Create tabs for different parameter categories
    params_tabs = st.tabs([
        "Technology Parameters", "Regional Parameters", "Projection Parameters",
        "Growth Rates"
    ])

    # ========== TECHNOLOGY PARAMETERS ==========
    with params_tabs[0]:
        # Stack Learning Rates
        st.subheader("Stack Learning Rates (%)")

        col1, col2 = st.columns(2)

        with col1:
            western_pem_lr = st.slider(
                "Western PEM",
                min_value=10.0,
                max_value=30.0,
                step=1.0,
                key="wpem_lr",
                help=
                "Percentage reduction in cost for each doubling of capacity")

            western_alk_lr = st.slider(
                "Western ALK",
                min_value=10.0,
                max_value=30.0,
                step=1.0,
                key="walk_lr",
                help=
                "Percentage reduction in cost for each doubling of capacity")

        with col2:
            chinese_pem_lr = st.slider(
                "Chinese PEM",
                min_value=10.0,
                max_value=30.0,
                step=1.0,
                key="cpem_lr",
                help=
                "Percentage reduction in cost for each doubling of capacity")

            chinese_alk_lr = st.slider(
                "Chinese ALK",
                min_value=10.0,
                max_value=30.0,
                step=1.0,
                key="calk_lr",
                help=
                "Percentage reduction in cost for each doubling of capacity")

        # Convert learning rates to alpha parameters for stacks
        stack_alphas = {
            'western_pem': alpha_from_learning_rate(western_pem_lr),
            'chinese_pem': alpha_from_learning_rate(chinese_pem_lr),
            'western_alk': alpha_from_learning_rate(western_alk_lr),
            'chinese_alk': alpha_from_learning_rate(chinese_alk_lr)
        }

        # Stack Current Costs
        st.subheader("Stack Current Costs ($/kW)")

        col1, col2 = st.columns(2)

        with col1:
            western_pem_cost = st.number_input(
                "Western PEM",
                min_value=100.0,
                max_value=5000.0,
                step=50.0,
                key="wpem_cost",
                help="Current capital cost in $/kW")

            western_alk_cost = st.number_input(
                "Western ALK",
                min_value=100.0,
                max_value=5000.0,
                step=50.0,
                key="walk_cost",
                help="Current capital cost in $/kW")

        with col2:
            chinese_pem_cost = st.number_input(
                "Chinese PEM",
                min_value=100.0,
                max_value=5000.0,
                step=50.0,
                key="cpem_cost",
                help="Current capital cost in $/kW")

            chinese_alk_cost = st.number_input(
                "Chinese ALK",
                min_value=100.0,
                max_value=5000.0,
                step=50.0,
                key="calk_cost",
                help="Current capital cost in $/kW")

        # Dictionary of costs for stacks
        stack_costs_0 = {
            'western_pem': western_pem_cost,
            'chinese_pem': chinese_pem_cost,
            'western_alk': western_alk_cost,
            'chinese_alk': chinese_alk_cost
        }

    # ========== REGIONAL PARAMETERS ==========
    with params_tabs[1]:
        # BoP & EPC Learning Rates
        st.subheader("BoP & EPC Learning Rates (%)")

        col1, col2 = st.columns(2)

        with col1:
            usa_lr = st.slider(
                "USA",
                min_value=5.0,
                max_value=20.0,
                step=0.5,
                key="usa_lr",
                help=
                "Percentage reduction in cost for each doubling of capacity")

            eu_lr = st.slider(
                "European Union",
                min_value=5.0,
                max_value=20.0,
                step=0.5,
                key="eu_lr",
                help=
                "Percentage reduction in cost for each doubling of capacity")

        with col2:
            china_lr = st.slider(
                "China",
                min_value=5.0,
                max_value=20.0,
                step=0.5,
                key="china_lr",
                help=
                "Percentage reduction in cost for each doubling of capacity")

            row_lr = st.slider(
                "Rest of World",
                min_value=5.0,
                max_value=20.0,
                step=0.5,
                key="row_lr",
                help=
                "Percentage reduction in cost for each doubling of capacity")

        # Convert learning rates to alpha parameters for BoP & EPC
        bop_epc_alphas = {
            'usa': alpha_from_learning_rate(usa_lr),
            'eu': alpha_from_learning_rate(eu_lr),
            'china': alpha_from_learning_rate(china_lr),
            'row': alpha_from_learning_rate(row_lr)
        }

        # BoP & EPC Current Costs
        st.subheader("BoP & EPC Current Costs ($/kW)")

        # Create tabs for PEM and ALK costs
        cost_tabs = st.tabs(["PEM Costs", "ALK Costs"])

        with cost_tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                usa_cost_pem = st.number_input(
                    "USA PEM",
                    min_value=100.0,
                    max_value=5000.0,
                    step=50.0,
                    key="usa_cost_pem",
                    help="Current BoP & EPC cost for PEM in $/kW")

                eu_cost_pem = st.number_input(
                    "European Union PEM",
                    min_value=100.0,
                    max_value=5000.0,
                    step=50.0,
                    key="eu_cost_pem",
                    help="Current BoP & EPC cost for PEM in $/kW")

            with col2:
                china_cost_pem = st.number_input(
                    "China PEM",
                    min_value=100.0,
                    max_value=5000.0,
                    step=50.0,
                    key="china_cost_pem",
                    help="Current BoP & EPC cost for PEM in $/kW")

                row_cost_pem = st.number_input(
                    "Rest of World PEM",
                    min_value=100.0,
                    max_value=5000.0,
                    step=50.0,
                    key="row_cost_pem",
                    help="Current BoP & EPC cost for PEM in $/kW")

        with cost_tabs[1]:
            col1, col2 = st.columns(2)
            with col1:
                usa_cost_alk = st.number_input(
                    "USA ALK",
                    min_value=100.0,
                    max_value=5000.0,
                    step=50.0,
                    key="usa_cost_alk",
                    help="Current BoP & EPC cost for ALK in $/kW")

                eu_cost_alk = st.number_input(
                    "European Union ALK",
                    min_value=100.0,
                    max_value=5000.0,
                    step=50.0,
                    key="eu_cost_alk",
                    help="Current BoP & EPC cost for ALK in $/kW")

            with col2:
                china_cost_alk = st.number_input(
                    "China ALK",
                    min_value=100.0,
                    max_value=5000.0,
                    step=50.0,
                    key="china_cost_alk",
                    help="Current BoP & EPC cost for ALK in $/kW")

                row_cost_alk = st.number_input(
                    "Rest of World ALK",
                    min_value=100.0,
                    max_value=5000.0,
                    step=50.0,
                    key="row_cost_alk",
                    help="Current BoP & EPC cost for ALK in $/kW")

        # Dictionaries of costs for BoP & EPC
        bop_epc_costs_0_pem = {
            'usa': usa_cost_pem,
            'eu': eu_cost_pem,
            'china': china_cost_pem,
            'row': row_cost_pem
        }

        bop_epc_costs_0_alk = {
            'usa': usa_cost_alk,
            'eu': eu_cost_alk,
            'china': china_cost_alk,
            'row': row_cost_alk
        }

        bop_epc_costs_0 = {
            'usa_pem': usa_cost_pem,
            'eu_pem': eu_cost_pem,
            'china_pem': china_cost_pem,
            'row_pem': row_cost_pem,
            'usa_alk': usa_cost_alk,
            'eu_alk': eu_cost_alk,
            'china_alk': china_cost_alk,
            'row_alk': row_cost_alk,
        }

        # Current capacities for each technology in each region
        st.subheader("Base capacities for capacity growth calculations (MW)")

        # Use the global region_base_capacities variable

        # Create tabs for each region
        region_names = ["USA", "European Union", "China", "Rest of World"]
        capacity_tabs = st.tabs(region_names)

        # Let users set initial capacities by region and technology
        for region_idx, region in enumerate(REGIONS):
            with capacity_tabs[region_idx]:
                col1, col2 = st.columns(2)
                tech_base_capacities = {}

                with col1:
                    tech_base_capacities['western_pem'] = st.number_input(
                        "Western PEM",
                        min_value=0.0,
                        max_value=10000.0,
                        step=10.0,
                        key=f"{region}_wpem_cap",
                        help=f"Current installed Western PEM capacity in {region_names[region_idx]} (MW)"
                    )

                    tech_base_capacities['western_alk'] = st.number_input(
                        "Western ALK",
                        min_value=0.0,
                        max_value=10000.0,
                        step=10.0,
                        key=f"{region}_walk_cap",
                        help=f"Current installed Western ALK capacity in {region_names[region_idx]} (MW)"
                    )

                with col2:
                    tech_base_capacities['chinese_pem'] = st.number_input(
                        "Chinese PEM",
                        min_value=0.0,
                        max_value=10000.0,
                        step=10.0,
                        key=f"{region}_cpem_cap",
                        help=f"Current installed Chinese PEM capacity in {region_names[region_idx]} (MW)"
                    )

                    tech_base_capacities['chinese_alk'] = st.number_input(
                        "Chinese ALK",
                        min_value=0.0,
                        max_value=10000.0,
                        step=10.0,
                        key=f"{region}_calk_cap",
                        help=f"Current installed Chinese ALK capacity in {region_names[region_idx]} (MW)"
                    )

                region_base_capacities[region] = tech_base_capacities

    # ========== PROJECTION PARAMETERS ==========
    with params_tabs[2]:
        st.subheader("Annual Growth Rates by Region (%)")

        # Use the global region_tech_growth_rates variable

        # Create tabs for each region
        region_names = ["USA", "European Union", "China", "Rest of World"]
        growth_tabs = st.tabs(region_names)

        # Let users set growth rates by region and technology
        for region_idx, region in enumerate(REGIONS):
            with growth_tabs[region_idx]:
                col1, col2 = st.columns(2)
                tech_growth_rates = {}

                with col1:
                    tech_growth_rates['western_pem'] = st.slider(
                        "Western PEM",
                        min_value=0.0,
                        max_value=50.0,
                        step=1.0,
                        key=f"{region}_wpem_growth",
                        help=f"Annual growth rate for Western PEM in {region_names[region_idx]}"
                    ) / 100.0  # Convert to decimal

                    tech_growth_rates['western_alk'] = st.slider(
                        "Western ALK",
                        min_value=0.0,
                        max_value=50.0,
                        step=1.0,
                        key=f"{region}_walk_growth",
                        help=f"Annual growth rate for Western ALK in {region_names[region_idx]}"
                    ) / 100.0  # Convert to decimal

                with col2:
                    tech_growth_rates['chinese_pem'] = st.slider(
                        "Chinese PEM",
                        min_value=0.0,
                        max_value=50.0,
                        step=1.0,
                        key=f"{region}_cpem_growth",
                        help=f"Annual growth rate for Chinese PEM in {region_names[region_idx]}"
                    ) / 100.0  # Convert to decimal

                    tech_growth_rates['chinese_alk'] = st.slider(
                        "Chinese ALK",
                        min_value=0.0,
                        max_value=50.0,
                        step=1.0,
                        key=f"{region}_calk_growth",
                        help=f"Annual growth rate for Chinese ALK in {region_names[region_idx]}"
                    ) / 100.0  # Convert to decimal

                region_tech_growth_rates[region] = tech_growth_rates

        # Create a heatmap of growth rates
        heatmap_data = pd.DataFrame()

        for tech in TECHNOLOGIES:
            heatmap_data[get_stack_display_name(tech)] = [
                region_tech_growth_rates[region][tech] * 100
                for region in REGIONS
            ]

        heatmap_data.index = [
            get_region_display_name(region) for region in REGIONS
        ]

        # Plot heatmap
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Technology",
                        y="Region",
                        color="Growth Rate (%)"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            text_auto='.1f',
            aspect="auto",
            title="Annual Growth Rates (%) by Technology and Region",
            color_continuous_scale="Viridis",
            zmin=0,
            zmax=50)

        fig.update_layout(autosize=True, height=400)

        st.plotly_chart(fig, use_container_width=True)

        # Add description
        st.info("""
        **Growth Rate Overview**:

        1. Use the tabs to navigate between different regions
        2. Adjust the sliders to set the annual growth rate for each technology
        3. The heatmap shows a summary of all growth rates across regions
        4. These growth rates will be used in both stack and BoP/EPC projections
        """)

        # Regardless of which tab was used, region_tech_growth_rates now contains all the growth rates

    # ========== PROJECTION PARAMETERS ==========
    with params_tabs[3]:
        # Projection timeframe
        st.subheader("Projection Timeframe")

        projection_years = st.slider(
            "Projection Years",
            min_value=5,
            max_value=30,
            value=st.session_state.get("projection_years", 25),
            step=1,
            key="projection_years",
            help="Number of years to project into the future")

        base_year = st.number_input("Base Year",
                                    min_value=2020,
                                    max_value=2030,
                                    value=st.session_state.get("base_year", 2025),
                                    step=1,
                                    key="base_year",
                                    help="Starting year for projections")



# ==================== HELPER FUNCTIONS ====================
def calculate_fom_values(fom_percentages, selected_techs, stack_costs_0, bop_epc_costs_0, regions):
    """Calculate FOM values as percentage of CAPEX for all regions."""
    fom_values = {}
    for region in regions:
        tech_type = selected_techs[region]
        tech_category = 'alk' if 'alk' in tech_type else 'pem'
        stack_cost = stack_costs_0[tech_type]
        bop_epc_cost = bop_epc_costs_0[f"{region}_{tech_category}"]
        total_capex = stack_cost + bop_epc_cost
        fom_values[region] = (fom_percentages[region] / 100.0) * total_capex
    return fom_values

# ==================== GENERATE DATA ====================
# Generate stack data with region-specific growth rates
stack_data = generate_regional_stack_data(TECHNOLOGIES, REGIONS, stack_costs_0,
                                          region_base_capacities,
                                          region_tech_growth_rates,
                                          stack_alphas, projection_years,
                                          base_year)

# Generate BoP & EPC data with region-specific growth rates
bop_epc_data = generate_regional_bop_epc_data(
    REGIONS,
    TECHNOLOGIES,
    bop_epc_costs_0_pem,
    bop_epc_costs_0_alk,
    region_base_capacities,
    region_tech_growth_rates,
    bop_epc_alphas,  # For PEM
    bop_epc_alphas,  # For ALK (using same alphas)
    projection_years,
    base_year)

# Create consolidated dictionary of individual technology capacities
technologies_capacities_0 = {}
for tech in TECHNOLOGIES:
    # Sum up the capacity of this technology across all regions
    technologies_capacities_0[tech] = sum(
        [region_base_capacities[region][tech] for region in REGIONS])

# Generate learning investments for stack technologies
stack_learning_investments = generate_stack_learning_investments(
    TECHNOLOGIES, stack_costs_0, technologies_capacities_0, stack_alphas,
    stack_data)

# Use technology-specific costs for learning investments
# Generate learning investments for both stack and BoP+EPC
bop_epc_learning_investments = generate_bop_epc_learning_investments(
    REGIONS, 
    bop_epc_costs_0_pem,  # PEM-specific costs
    bop_epc_costs_0_alk,  # ALK-specific costs
    bop_epc_alphas, 
    bop_epc_data
)

# ==================== MAIN CONTENT ====================
# Electrolysis Stacks Tab Content
with main_tabs[0]:
    st.header("Electrolysis Stack Cost Projections")

    # Create tabs for different views
    stack_tabs = st.tabs([
        "Cost Projections by Technology", "Cost Projections by Model",
        "Data Tables"
    ])

    # Tab 1: View cost projections grouped by technology
    with stack_tabs[0]:
        st.subheader("Cost Projections by Technology")

        # Create subtabs for each technology
        tech_tabs = st.tabs(
            ["Western PEM", "Chinese PEM", "Western ALK", "Chinese ALK"])

        # Map technology keys to their positions in tech_tabs
        tech_tab_map = {
            'western_pem': 0,
            'chinese_pem': 1,
            'western_alk': 2,
            'chinese_alk': 3
        }

        # For each technology, show all three models side by side
        for tech, tab_idx in tech_tab_map.items():
            with tech_tabs[tab_idx]:
                st.subheader(
                    f"{get_stack_display_name(tech)} Cost Projections")

                # Create a DataFrame for this technology with all three models
                plot_df = pd.DataFrame({
                    'Year':
                    stack_data['shared'][tech]['year'],
                    'Shared Learning':
                    stack_data['shared'][tech]['cost'],
                    'Technological Fragmentation':
                    stack_data['first_layer'][tech]['cost'],
                    'Regional Fragmentation':
                    stack_data['second_layer'][tech]['cost']
                })

                # Melt the DataFrame for plotting
                plot_melted = pd.melt(plot_df,
                                      id_vars=['Year'],
                                      value_vars=[
                                          'Shared Learning',
                                          'Technological Fragmentation',
                                          'Regional Fragmentation'
                                      ],
                                      var_name='Learning Model',
                                      value_name='Cost ($/kW)')

                # Create line chart
                fig = px.line(
                    plot_melted,
                    x='Year',
                    y='Cost ($/kW)',
                    color='Learning Model',
                    markers=True,
                    title=
                    f"{get_stack_display_name(tech)} Stack Cost Projections")

                # Style the figure
                fig.update_layout(autosize=True,
                                  height=500,
                                  hovermode="x unified",
                                  legend=dict(orientation="h",
                                              yanchor="bottom",
                                              y=1.02,
                                              xanchor="right",
                                              x=1))

                # Set y-axis to start at 0
                fig.update_yaxes(rangemode="tozero")

                st.plotly_chart(fig, use_container_width=True)

                # Display final projected costs for all models
                st.subheader(
                    f"Projected Costs in {base_year + projection_years}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    final_cost_shared = stack_data['shared'][tech][
                        'cost'].iloc[-1]
                    st.metric(
                        label="Shared Learning",
                        value=f"${final_cost_shared:.0f}/kW",
                        delta=
                        f"{((final_cost_shared/stack_costs_0[tech])-1)*100:.1f}%"
                    )

                with col2:
                    final_cost_first = stack_data['first_layer'][tech][
                        'cost'].iloc[-1]
                    st.metric(
                        label="Technological Fragmentation",
                        value=f"${final_cost_first:.0f}/kW",
                        delta=
                        f"{((final_cost_first/stack_costs_0[tech])-1)*100:.1f}%"
                    )

                with col3:
                    final_cost_second = stack_data['second_layer'][tech][
                        'cost'].iloc[-1]
                    st.metric(
                        label="Regional Fragmentation",
                        value=f"${final_cost_second:.0f}/kW",
                        delta=
                        f"{((final_cost_second/stack_costs_0[tech])-1)*100:.1f}%"
                    )

    # Tab 2: View cost projections grouped by learning model
    with stack_tabs[1]:
        st.subheader("Cost Projections by Learning Model")

        # Create subtabs for each learning model
        model_tabs = st.tabs([
            "Shared Learning", "Technological Fragmentation",
            "Regional Fragmentation"
        ])

        # Map model data to model tabs
        model_data_map = {
            0: stack_data['shared'],
            1: stack_data['first_layer'],
            2: stack_data['second_layer']
        }

        model_names = {
            0: "Shared Learning",
            1: "Technological Fragmentation",
            2: "Regional Fragmentation"
        }

        # For each model, show all technologies
        for model_idx, model_data in model_data_map.items():
            with model_tabs[model_idx]:
                st.subheader(f"{model_names[model_idx]} Model")

                # Create a DataFrame with all technologies for this model
                technologies = list(model_data.keys())
                plot_df = pd.DataFrame(
                    {'Year': model_data[technologies[0]]['year']})

                # Add cost columns for each technology
                for tech in technologies:
                    plot_df[get_stack_display_name(
                        tech)] = model_data[tech]['cost']

                # Melt the DataFrame for plotting
                tech_columns = [
                    get_stack_display_name(tech) for tech in technologies
                ]
                plot_melted = pd.melt(plot_df,
                                      id_vars=['Year'],
                                      value_vars=tech_columns,
                                      var_name='Technology',
                                      value_name='Cost ($/kW)')

                # Create line chart
                fig = px.line(
                    plot_melted,
                    x='Year',
                    y='Cost ($/kW)',
                    color='Technology',
                    markers=True,
                    title=f"{model_names[model_idx]} Model - Cost Projections")

                # Style the figure
                fig.update_layout(autosize=True,
                                  height=500,
                                  hovermode="x unified",
                                  legend=dict(orientation="h",
                                              yanchor="bottom",
                                              y=1.02,
                                              xanchor="right",
                                              x=1))

                # Set y-axis to start at 0
                fig.update_yaxes(rangemode="tozero")

                st.plotly_chart(fig, use_container_width=True)

                # Display final projected costs for all technologies
                st.subheader(
                    f"Projected Costs in {base_year + projection_years}")

                # Display metrics in two rows for better spacing
                row1_cols = st.columns(2)
                row2_cols = st.columns(2)

                for i, tech in enumerate(technologies):
                    col_idx = i % 2
                    row_idx = i // 2

                    final_cost = model_data[tech]['cost'].iloc[-1]

                    if row_idx == 0:
                        with row1_cols[col_idx]:
                            st.metric(
                                label=get_stack_display_name(tech),
                                value=f"${final_cost:.0f}/kW",
                                delta=
                                f"{((final_cost/stack_costs_0[tech])-1)*100:.1f}%"
                            )
                    else:
                        with row2_cols[col_idx]:
                            st.metric(
                                label=get_stack_display_name(tech),
                                value=f"${final_cost:.0f}/kW",
                                delta=
                                f"{((final_cost/stack_costs_0[tech])-1)*100:.1f}%"
                            )



    # Tab 3: Data tables
    with stack_tabs[2]:
        st.subheader("Detailed Projection Data")

        # Create tabs for different models
        data_tabs = st.tabs([
            "Shared Learning", "Technological Fragmentation",
            "Regional Fragmentation"
        ])

        # Helper function to format the data table for a model
        def format_stack_data_table(model_data):
            # Create a combined DataFrame with all technologies
            combined_df = pd.DataFrame(
                {'Year': model_data['western_pem']['year']})

            # Add capacities in GW (subtract baseline values to show only user-defined deployments)
            baseline_capacities = {
                'western_pem': 1100,  # 1.1 GW baseline in MW
                'western_alk': 22580,  # 22.58 GW baseline in MW
                'chinese_pem': 1100,  # 1.1 GW baseline in MW
                'chinese_alk': 22580  # 22.58 GW baseline in MW
            }
            
            for tech in TECHNOLOGIES:
                # Subtract baseline to show only user deployment
                deployment_capacity = model_data[tech]['capacity'] - baseline_capacities[tech]
                combined_df[f'{get_stack_display_name(tech)} (GW)'] = deployment_capacity / 1000

            combined_df['Total (GW)'] = sum([
                combined_df[f'{get_stack_display_name(tech)} (GW)']
                for tech in TECHNOLOGIES
            ])

            # Add costs
            for tech in TECHNOLOGIES:
                combined_df[
                    f'{get_stack_display_name(tech)} ($/kW)'] = model_data[
                        tech]['cost']

            # Format numeric columns
            for col in combined_df.columns[1:]:
                if '(GW)' in col:
                    combined_df[col] = combined_df[col].round(2)
                elif '($/kW)' in col:
                    combined_df[col] = combined_df[col].round(0)

            return combined_df

        # Display data tables for each model
        with data_tabs[0]:
            shared_table = format_stack_data_table(stack_data['shared'])
            st.dataframe(shared_table, use_container_width=True)

            # Download button for shared learning data
            csv_shared = shared_table.to_csv(index=False)
            st.download_button(
                label="Download Shared Learning Data (CSV)",
                data=csv_shared,
                file_name="electrolysis_stacks_shared_learning.csv",
                mime="text/csv")

        with data_tabs[1]:
            first_layer_table = format_stack_data_table(
                stack_data['first_layer'])
            st.dataframe(first_layer_table, use_container_width=True)

            # Download button for first-layer data
            csv_first = first_layer_table.to_csv(index=False)
            st.download_button(
                label="Download Technological Fragmentation Data (CSV)",
                data=csv_first,
                file_name="electrolysis_stacks_technological_fragmentation.csv",
                mime="text/csv")

        with data_tabs[2]:
            second_layer_table = format_stack_data_table(
                stack_data['second_layer'])
            st.dataframe(second_layer_table, use_container_width=True)

            # Download button for second-layer data
            csv_second = second_layer_table.to_csv(index=False)
            st.download_button(
                label="Download Regional Fragmentation Data (CSV)",
                data=csv_second,
                file_name="electrolysis_stacks_regional_fragmentation.csv",
                mime="text/csv")

    # Add learning curve explanation at the bottom of the tab
    st.info("""
    **Learning Curve Starting Point**: All stack technologies begin learning from the user-defined capacities in Model Parameters, plus an additional baseline representing the existing global installed capacity:
    
    • **PEM Technologies**: User-defined capacity + 1.1 GW additional baseline.\\
    • **ALK Technologies**: User-defined capacity + 22.58 GW additional baseline.
    
    Cost reductions occur as cumulative capacity grows beyond these starting points. The additional baselines reflect real-world installed capacity that has already contributed to learning effects.
    """)

# Balance of Plant & EPC Tab Content
with main_tabs[1]:
    st.header("Balance of Plant & EPC Cost Projections")

    # Create tabs for different views
    bop_epc_tabs = st.tabs([
        "Cost Projections by Region", "Cost Projections by Model",
        "Data Tables"
    ])

    # Tab 1: View cost projections grouped by region
    with bop_epc_tabs[0]:
        st.subheader("Cost Projections by Region")

        # Create subtabs for each region
        region_tabs = st.tabs(
            ["USA", "European Union", "China", "Rest of World"])

        # Map region keys to their positions in region_tabs
        region_tab_map = {'usa': 0, 'eu': 1, 'china': 2, 'row': 3}

        # For each region, show both models side by side
        for region, tab_idx in region_tab_map.items():
            with region_tabs[tab_idx]:
                st.subheader(
                    f"{get_region_display_name(region)} Cost Projections")

                # Create a DataFrame for this region with both models and technologies
                plot_df = pd.DataFrame({
                    'Year':
                    bop_epc_data['local'][f"{region}_pem"]['year'],
                    'PEM - Local Learning':
                    bop_epc_data['local'][f"{region}_pem"]['cost'],
                    'PEM - Global Learning':
                    bop_epc_data['global'][f"{region}_pem"]['cost'],
                    'ALK - Local Learning':
                    bop_epc_data['local'][f"{region}_alk"]['cost'],
                    'ALK - Global Learning':
                    bop_epc_data['global'][f"{region}_alk"]['cost']
                })

                # Melt the DataFrame for plotting
                plot_melted = pd.melt(plot_df,
                                      id_vars=['Year'],
                                      value_vars=[
                                          'PEM - Local Learning',
                                          'PEM - Global Learning',
                                          'ALK - Local Learning',
                                          'ALK - Global Learning'
                                      ],
                                      var_name='Technology & Model',
                                      value_name='Cost ($/kW)')

                # Create line chart
                fig = px.line(
                    plot_melted,
                    x='Year',
                    y='Cost ($/kW)',
                    color='Technology & Model',
                    markers=True,
                    title=
                    f"{get_region_display_name(region)} BoP & EPC Cost Projections"
                )

                # Style the figure
                fig.update_layout(autosize=True,
                                  height=500,
                                  hovermode="x unified",
                                  legend=dict(orientation="h",
                                              yanchor="bottom",
                                              y=1.02,
                                              xanchor="right",
                                              x=1))

                # Set y-axis to start at 0
                fig.update_yaxes(rangemode="tozero")

                st.plotly_chart(fig, use_container_width=True)

                # Display final projected costs for both models
                st.subheader(
                    f"Projected Costs in {base_year + projection_years}")

                col1, col2 = st.columns(2)

                with col1:
                    final_cost_local_pem = bop_epc_data['local'][
                        f"{region}_pem"]['cost'].iloc[-1]
                    st.metric(
                        label="PEM - Local Learning",
                        value=f"${final_cost_local_pem:.0f}/kW",
                        delta=
                        f"{((final_cost_local_pem/bop_epc_costs_0[f'{region}_pem'])-1)*100:.1f}%"
                    )

                with col2:
                    final_cost_global_pem = bop_epc_data['global'][
                        f"{region}_pem"]['cost'].iloc[-1]
                    st.metric(
                        label="PEM - Global Learning",
                        value=f"${final_cost_global_pem:.0f}/kW",
                        delta=
                        f"{((final_cost_global_pem/bop_epc_costs_0[f'{region}_pem'])-1)*100:.1f}%"
                    )

                st.write("")  # Add some spacing
                col3, col4 = st.columns(2)

                with col3:
                    final_cost_local_alk = bop_epc_data['local'][
                        f"{region}_alk"]['cost'].iloc[-1]
                    st.metric(
                        label="ALK - Local Learning",
                        value=f"${final_cost_local_alk:.0f}/kW",
                        delta=
                        f"{((final_cost_local_alk/bop_epc_costs_0[f'{region}_alk'])-1)*100:.1f}%"
                    )

                with col4:
                    final_cost_global_alk = bop_epc_data['global'][
                        f"{region}_alk"]['cost'].iloc[-1]
                    st.metric(
                        label="ALK - Global Learning",
                        value=f"${final_cost_global_alk:.0f}/kW",
                        delta=
                        f"{((final_cost_global_alk/bop_epc_costs_0[f'{region}_alk'])-1)*100:.1f}%"
                    )

    # Tab 2: View cost projections grouped by learning model
    with bop_epc_tabs[1]:
        st.subheader("Cost Projections by Learning Model")

        # Create subtabs for each learning model
        model_tabs = st.tabs(["Local Learning", "Global Learning"])

        # Map model data to model tabs
        model_data_map = {0: bop_epc_data['local'], 1: bop_epc_data['global']}

        model_names = {0: "Local Learning", 1: "Global Learning"}

        # For each model, show all regions
        for model_idx, model_data in model_data_map.items():
            with model_tabs[model_idx]:
                st.subheader(f"{model_names[model_idx]} Model")

                # Create a DataFrame with all regions for this model
                regions = list(model_data.keys())
                plot_df = pd.DataFrame(
                    {'Year': model_data[regions[0]]['year']})

                # Add cost columns for each region
                for region in regions:
                    plot_df[get_region_display_name(
                        region)] = model_data[region]['cost']

                # Melt the DataFrame for plotting
                region_columns = [
                    get_region_display_name(region) for region in regions
                ]
                plot_melted = pd.melt(plot_df,
                                      id_vars=['Year'],
                                      value_vars=region_columns,
                                      var_name='Region',
                                      value_name='Cost ($/kW)')

                # Create line chart
                fig = px.line(
                    plot_melted,
                    x='Year',
                    y='Cost ($/kW)',
                    color='Region',
                    markers=True,
                    title=f"{model_names[model_idx]} Model - Cost Projections")

                # Style the figure
                fig.update_layout(autosize=True,
                                  height=500,
                                  hovermode="x unified",
                                  legend=dict(orientation="h",
                                              yanchor="bottom",
                                              y=1.02,
                                              xanchor="right",
                                              x=1))

                # Set y-axis to start at 0
                fig.update_yaxes(rangemode="tozero")

                st.plotly_chart(fig, use_container_width=True)

                # Display final projected costs for all regions
                st.subheader(
                    f"Projected Costs in {base_year + projection_years}")

                # Display metrics in rows by region
                for region in REGIONS:
                    st.write(f"**{get_region_display_name(region)}**")
                    col1, col2 = st.columns(2)

                    with col1:
                        final_cost_pem = model_data[f"{region}_pem"][
                            'cost'].iloc[-1]
                        st.metric(
                            label="PEM",
                            value=f"${final_cost_pem:.0f}/kW",
                            delta=
                            f"{((final_cost_pem/bop_epc_costs_0[f'{region}_pem'])-1)*100:.1f}%"
                        )

                    with col2:
                        final_cost_alk = model_data[f"{region}_alk"][
                            'cost'].iloc[-1]
                        st.metric(
                            label="ALK",
                            value=f"${final_cost_alk:.0f}/kW",
                            delta=
                            f"{((final_cost_alk/bop_epc_costs_0[f'{region}_alk'])-1)*100:.1f}%"
                        )

                    st.write("---")  # Add a separator between regions



    # Tab 3: Data tables
    with bop_epc_tabs[2]:
        st.subheader("Detailed Projection Data")

        # Create tabs for different models
        data_tabs = st.tabs(["Local Learning", "Global Learning"])

        # Helper function to format the data table for a model
        def format_bop_epc_data_table(model_data):
            # Create a combined DataFrame with all regions
            combined_df = pd.DataFrame({'Year': model_data['usa_pem']['year']})

            # Add capacities in GW (sum both PEM and ALK for each region)
            for region in REGIONS:
                # Combine PEM and ALK capacities for each region
                pem_capacity = model_data[f'{region}_pem']['capacity'] / 1000
                alk_capacity = model_data[f'{region}_alk']['capacity'] / 1000
                total_regional_capacity = pem_capacity + alk_capacity
                combined_df[f'{get_region_display_name(region)} (GW)'] = total_regional_capacity

            combined_df['Total (GW)'] = sum([
                combined_df[f'{get_region_display_name(region)} (GW)']
                for region in REGIONS
            ])

            # Add costs (using PEM costs as representative BoP & EPC costs)
            for region in REGIONS:
                combined_df[
                    f'{get_region_display_name(region)} BoP & EPC ($/kW)'] = model_data[
                        f'{region}_pem']['cost']

            # Format numeric columns
            for col in combined_df.columns[1:]:
                if '(GW)' in col:
                    combined_df[col] = combined_df[col].round(2)
                elif '($/kW)' in col:
                    combined_df[col] = combined_df[col].round(0)

            return combined_df

        # Display data tables for each model
        with data_tabs[0]:
            local_table = format_bop_epc_data_table(bop_epc_data['local'])
            st.dataframe(local_table, use_container_width=True)

            # Download button for local learning data
            csv_local = local_table.to_csv(index=False)
            st.download_button(label="Download Local Learning Data (CSV)",
                               data=csv_local,
                               file_name="bop_epc_local_learning.csv",
                               mime="text/csv")

        with data_tabs[1]:
            global_table = format_bop_epc_data_table(bop_epc_data['global'])
            st.dataframe(global_table, use_container_width=True)

            # Download button for global learning data
            csv_global = global_table.to_csv(index=False)
            st.download_button(label="Download Global Learning Data (CSV)",
                               data=csv_global,
                               file_name="bop_epc_global_learning.csv",
                               mime="text/csv")

    # Add learning curve explanation at the bottom of the tab
    st.info("""
    **Learning Curve Starting Point**: BoP & EPC costs begin learning from only the user-defined regional capacities in Model Parameters:
    
    • **Local Learning**: Each region learns independently from its own cumulative capacity deployment.\\
    • **Global Learning**: All regions benefit from worldwide cumulative capacity deployment.
    
    Cost reductions occur as cumulative regional or global capacity grows from the user-defined starting points.
    """)

# Regional Growth Tab Content
with main_tabs[2]:
    st.header("Technology Growth Rates by Region")
    


    # Create tabs for the different regions
    region_tabs = st.tabs(["USA", "European Union", "China", "Rest of World"])

    # Calculate global growth data once
    global_growth_data = pd.DataFrame(
        {'Year': bop_epc_data['local']['usa_pem']['year']})

    # Add global capacity by technology type
    for tech in TECHNOLOGIES:
        # Calculate total global capacity for this technology
        global_capacity_values = []
        total_base_capacity = sum(
            [region_base_capacities[region][tech] for region in REGIONS])

        global_capacity_values.append(total_base_capacity)
        for year in range(1, projection_years + 1):
            # Calculate new capacity considering growth in all regions
            year_capacity = 0
            for region in REGIONS:
                region_base = region_base_capacities[region][tech]
                region_growth = region_tech_growth_rates[region][tech]
                year_capacity += region_base * (1 + region_growth) ** year
            global_capacity_values.append(year_capacity)

        global_growth_data[f'{get_stack_display_name(tech)} (GW)'] = [
            round(val / 1000, 2) for val in global_capacity_values
        ]  # Convert MW to GW and round to 2 decimal places

    # Add total global capacity
    global_growth_data['Total (GW)'] = sum([
        global_growth_data[f'{get_stack_display_name(tech)} (GW)']
        for tech in TECHNOLOGIES
    ])

    # For each region, show growth by technology
    for region_idx, region in enumerate(REGIONS):
        with region_tabs[region_idx]:
            st.subheader(
                f"Technology Growth in {get_region_display_name(region)}")

            # Get this region's capacity data for projection
            regional_growth_data = pd.DataFrame(
                {'Year': bop_epc_data['local'][f'{region}_pem']['year']})

            # Add capacity by technology type for this region
            for tech in TECHNOLOGIES:
                # Calculate projected capacity for this technology in this region
                base_capacity = region_base_capacities[region][tech]
                capacity_values = [base_capacity]

                for year in range(1, projection_years + 1):
                    # Use proper compound growth formula: base * (1 + rate)^year
                    current_capacity = base_capacity * (
                        1 + region_tech_growth_rates[region][tech]) ** year
                    capacity_values.append(current_capacity)

                regional_growth_data[
                    f'{get_stack_display_name(tech)} (GW)'] = [
                        round(val / 1000, 2) for val in capacity_values
                    ]  # Convert MW to GW and round to 2 decimal places

            # Add total capacity for this region
            regional_growth_data['Total (GW)'] = sum([
                regional_growth_data[f'{get_stack_display_name(tech)} (GW)']
                for tech in TECHNOLOGIES
            ])

            # Create two columns for the plots
            col1, col2 = st.columns(2)

            # Calculate max y-axis value for both plots
            max_regional = max(regional_growth_data[[
                f'{get_stack_display_name(tech)} (GW)' for tech in TECHNOLOGIES
            ]].sum(axis=1))
            max_global = max(global_growth_data[[
                f'{get_stack_display_name(tech)} (GW)' for tech in TECHNOLOGIES
            ]].sum(axis=1))
            y_axis_max = max(max_regional, max_global) * 1.1  # Add 10% padding

            with col1:
                st.subheader(f"Growth in {get_region_display_name(region)}")
                # Create display DataFrame with clean column names for legend
                regional_display_data = regional_growth_data.copy()
                for tech in TECHNOLOGIES:
                    regional_display_data[get_stack_display_name(tech)] = regional_display_data[f'{get_stack_display_name(tech)} (GW)']
                
                # Create technology growth chart for this region
                fig_regional = px.area(
                    regional_display_data,
                    x='Year',
                    y=[get_stack_display_name(tech) for tech in TECHNOLOGIES],
                    title="",
                    labels={
                        "value": "Installed Capacity (GW)",
                        "variable": "Technology"
                    })

                # Style the figure with synchronized y-axis
                fig_regional.update_layout(autosize=True,
                                           height=500,
                                           hovermode="x unified",
                                           legend=dict(orientation="h",
                                                       yanchor="bottom",
                                                       y=1.02,
                                                       xanchor="right",
                                                       x=1),
                                           yaxis=dict(range=[0, y_axis_max]))

                st.plotly_chart(fig_regional,
                                use_container_width=True,
                                key=f"regional_growth_{region}")

            with col2:
                st.subheader("Global Growth")
                # Create display DataFrame with clean column names for legend
                global_display_data = global_growth_data.copy()
                for tech in TECHNOLOGIES:
                    global_display_data[get_stack_display_name(tech)] = global_display_data[f'{get_stack_display_name(tech)} (GW)']
                
                # Create technology growth chart for global data
                fig_global = px.area(global_display_data,
                                     x='Year',
                                     y=[get_stack_display_name(tech) for tech in TECHNOLOGIES],
                                     title="",
                                     labels={
                                         "value": "Installed Capacity (GW)",
                                         "variable": "Technology"
                                     })

                # Style the figure with synchronized y-axis
                fig_global.update_layout(autosize=True,
                                         height=500,
                                         hovermode="x unified",
                                         legend=dict(orientation="h",
                                                     yanchor="bottom",
                                                     y=1.02,
                                                     xanchor="right",
                                                     x=1),
                                         yaxis=dict(range=[0, y_axis_max]))

                st.plotly_chart(fig_global,
                                use_container_width=True,
                                key=f"global_growth_{region}")

            # Create columns for regional and global pie charts
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Regional Technology Mix")
                # Calculate final year technology percentages for regional data
                final_techs_regional = {
                    tech:
                    regional_growth_data[
                        f'{get_stack_display_name(tech)} (GW)'].iloc[-1]
                    for tech in TECHNOLOGIES
                }
                final_total_regional = sum(final_techs_regional.values())

                # Create a pie chart of regional technology mix
                pie_data_regional = pd.DataFrame({
                    'Technology':
                    [get_stack_display_name(tech) for tech in TECHNOLOGIES],
                    'Capacity (GW)':
                    [final_techs_regional[tech] for tech in TECHNOLOGIES],
                    'Percentage': [
                        f"{(final_techs_regional[tech]/final_total_regional)*100:.1f}%"
                        for tech in TECHNOLOGIES
                    ]
                })

                fig_pie_regional = px.pie(
                    pie_data_regional,
                    values='Capacity (GW)',
                    names='Technology',
                    title=
                    f"{get_region_display_name(region)} Technology Mix in {base_year + projection_years}",
                    hover_data=['Percentage'])

                fig_pie_regional.update_layout(autosize=True, height=400)

                st.plotly_chart(fig_pie_regional,
                                use_container_width=True,
                                key=f"pie_regional_{region}")

            with col2:
                st.subheader("Global Technology Mix")
                # Calculate final year technology percentages for global data
                final_techs_global = {
                    tech:
                    global_growth_data[f'{get_stack_display_name(tech)} (GW)'].
                    iloc[-1]
                    for tech in TECHNOLOGIES
                }
                final_total_global = sum(final_techs_global.values())

                # Create a pie chart of global technology mix
                pie_data_global = pd.DataFrame({
                    'Technology':
                    [get_stack_display_name(tech) for tech in TECHNOLOGIES],
                    'Capacity (GW)':
                    [final_techs_global[tech] for tech in TECHNOLOGIES],
                    'Percentage': [
                        f"{(final_techs_global[tech]/final_total_global)*100:.1f}%"
                        for tech in TECHNOLOGIES
                    ]
                })

                fig_pie_global = px.pie(
                    pie_data_global,
                    values='Capacity (GW)',
                    names='Technology',
                    title=
                    f"Global Technology Mix in {base_year + projection_years}",
                    hover_data=['Percentage'])

                fig_pie_global.update_layout(autosize=True, height=400)

                st.plotly_chart(fig_pie_global,
                                use_container_width=True,
                                key=f"pie_global_{region}")

    # Capacity Growth Calculation Methodology (at bottom of Regional Growth tab)
    st.info(r"""
    **Regional Growth Calculations**

    The capacity projections are calculated using compound annual growth rates applied to the base capacity values:

    $$CAP_{t} = CAP_0 \times (1 + g)^t$$

    Where:
    - $CAP_t$ = Capacity in year $t$.
    - $CAP_0$ = Initial capacity (from Model Parameters).
    - $g$ = Annual growth rate (from Model Parameters).
    - $t$ = Number of years from base year.

    **Data Sources:**
    - **Base Capacities**: User-defined values in Model Parameters section.
    - **Growth Rates**: User-defined rates in Model Parameters section.
    - **Base Year**: User-selected starting year in Model Parameters.

    **Display Format:**
    - **Regional Growth**: Capacity deployment within the selected region.
    - **Global Growth**: Worldwide capacity deployment across all regions.
    
    """)

# ==================== LCOH CALCULATOR TAB ====================
with main_tabs[3]:
    st.header("Levelized Cost of Hydrogen (LCOH) Calculator")



    # Create tabs for different LCOH views
    lcoh_tabs = st.tabs(
        ["LCOH Parameters", "Regional Projections", "Sensitivity Analysis"])

    # ========== LCOH PARAMETERS TAB ==========
    with lcoh_tabs[0]:
        st.subheader("LCOH Parameters")

        # Set up LCOH parameters for each region
        st.write("### Technology Selection and Learning Model")

        # Technology and learning model selection
        col1, col2 = st.columns(2)

        with col1:
            tech_choices = {
                'western_pem': 'Western PEM',
                'chinese_pem': 'Chinese PEM', 
                'western_alk': 'Western Alkaline',
                'chinese_alk': 'Chinese Alkaline'
            }

            selected_techs = {}
            for region in REGIONS:
                # Default technology based on region
                default_tech = 'chinese_alk' if region == 'china' else 'western_pem'
                selected_techs[region] = st.selectbox(
                    f"Technology for {get_region_display_name(region)}",
                    options=list(tech_choices.keys()),
                    format_func=lambda x: tech_choices[x],
                    index=list(tech_choices.keys()).index(default_tech),
                    key=f"{region}_tech_select"
                )

        with col2:
            learning_models = {
                'shared': 'Shared Learning',
                'first_layer': 'Technological Fragmentation',
                'second_layer': 'Regional Fragmentation'
            }

            bop_epc_models = {
                'local': 'Local Learning',
                'global': 'Global Learning'  
            }

            col1, col2 = st.columns(2)

            with col1:
                selected_model = st.selectbox(
                    "Stack Learning Model",
                    options=list(learning_models.keys()),
                    format_func=lambda x: learning_models[x],
                    index=2,  # Default to second_layer
                    help="Select the learning model to use for stack cost projections"
                )

            with col2:
                # Synchronize with LCOH Calculator tab selection if it exists
                if "lcoh_calculator_bop_epc_model" in st.session_state:
                    default_bop_idx = 0 if st.session_state["lcoh_calculator_bop_epc_model"] == "local" else 1
                else:
                    default_bop_idx = 0
                    
                selected_bop_model = st.selectbox(
                    "BoP & EPC Learning Model",
                    options=list(bop_epc_models.keys()),
                    format_func=lambda x: bop_epc_models[x],
                    index=default_bop_idx,  # Sync with LCOH Calculator tab
                    help="Select the learning model to use for BoP & EPC cost projections",
                    key="params_bop_epc_learning_model"
                )

        st.write("### Financial Parameters")

        # WACC parameters
        col1, col2 = st.columns(2)
        with col1:
            wacc_values = {}
            for region_idx, region in enumerate(REGIONS):
                wacc_values[region] = st.slider(
                    f"WACC for {get_region_display_name(region)} (%)",
                    min_value=1.0,
                    max_value=15.0,
                    step=0.5,
                    key=f"{region}_wacc",
                    help=
                    f"Weighted Average Cost of Capital for {get_region_display_name(region)}"
                ) / 100.0  # Convert to decimal

        with col2:
            # Display the calculated CRF
            for region in REGIONS:
                crf = calculate_crf(wacc_values[region], lifetime=20)
                st.metric(
                    label=f"CRF for {get_region_display_name(region)}",
                    value=f"{crf:.3f}",
                    help=f"CRF = WACC * (1 + WACC)^20 / ((1 + WACC)^20 - 1)")

        # FOM and Electricity Cost parameters side by side
        st.write("### Operating Parameters")
        col1, col2 = st.columns(2)

        with col1:
            st.write("#### Fixed Operations & Maintenance (FOM)")
            fom_percentages = {}
            for region_idx, region in enumerate(REGIONS):
                fom_percentages[region] = st.slider(
                    f"FOM for {get_region_display_name(region)} (% of CAPEX)",
                    min_value=1.0,
                    max_value=10.0,
                    step=0.1,
                    key=f"{region}_fom_percentage",
                    help=
                    f"Fixed Operations and Maintenance costs for {get_region_display_name(region)} (default: 2% of CAPEX)"
                )
            


        with col2:
            st.write("#### Electricity Costs")
            electricity_costs = {}
            for region_idx, region in enumerate(REGIONS):
                electricity_cost_mwh = st.slider(
                    f"Electricity Cost for {get_region_display_name(region)} ($/MWh)",
                    min_value=0.0,
                    max_value=200.0,
                    step=5.0,
                    key=f"{region}_electricity",
                    help=
                    f"Electricity cost in {get_region_display_name(region)} ($/MWh)"
                )
                # Convert from $/MWh to $/kWh
                electricity_costs[region] = electricity_cost_mwh / 1000.0

        # Utilization Rate and Electrolyzer Efficiency parameters side by side
        st.write("### Performance Parameters")
        col1, col2 = st.columns(2)

        with col1:
            st.write("#### Utilization Rate (Capacity Factor)")
            utilization_rates = {}
            for region_idx, region in enumerate(REGIONS):
                utilization_rates[region] = st.slider(
                    f"Utilization Rate for {get_region_display_name(region)} (%)",
                    min_value=10.0,
                    max_value=100.0,
                    step=5.0,
                    key=f"{region}_utilization",
                    help=
                    f"Percentage of time the electrolyzer operates in {get_region_display_name(region)}"
                ) / 100.0  # Convert to decimal

        with col2:
            st.write("#### Electrolyzer Efficiency")
            electrolyzer_efficiencies = {}
            for region_idx, region in enumerate(REGIONS):
                # Set default efficiency to 55.0 kWh/kg for all regions
                default_efficiency = 55.0  # Consistent 55 kWh/kg for all regions
                electrolyzer_efficiencies[region] = st.slider(
                    f"Efficiency for {get_region_display_name(region)} (kWh/kg H₂)",
                    min_value=40.0,
                    max_value=80.0,
                    step=1.0,
                    key=f"{region}_efficiency",
                    help=
                    f"Energy consumption per kg of hydrogen in {get_region_display_name(region)}"
                )

        # Create a stacked bar chart with LCOH components
        # LCOH Components
        st.write("### LCOH Components")

        # Calculate FOM values in $/kW/year based on percentage of CAPEX
        fom_values = calculate_fom_values(fom_percentages, selected_techs, stack_costs_0, bop_epc_costs_0, REGIONS)

        # Create a stacked bar chart with LCOH components
        lcoh_components = {}
        for region in REGIONS:
            # Use selected technology for this region
            stack_cost = stack_costs_0[selected_techs[region]]

            # Get BoP & EPC cost for this region
            tech_type = 'alk' if 'alk' in selected_techs[region] else 'pem'
            bop_epc_cost = bop_epc_costs_0[f'{region}_{tech_type}']

            # Calculate total CAPEX
            total_capex = stack_cost + bop_epc_cost

            # Set default learning model to second_layer (most realistic)
            learning_model = 'second_layer'

            # Calculate LCOH with proper parameters
            # Use the BoP model selected by user in Parameters tab
            lcoh = calculate_lcoh(
                selected_techs[region],  # Pass the full technology name
                region,
                stack_data,
                bop_epc_data,
                wacc_values[region],
                0,  # FOM will be calculated from percentage
                utilization_rates[region],
                electricity_costs[region],
                electrolyzer_efficiencies[region],
                learning_model=learning_model,
                bop_epc_model=selected_bop_model,
                fom_percentage=fom_percentages[region])[0]

            # Calculate LCOH components
            crf = calculate_crf(wacc_values[region])
            
            # Add safeguards against division by zero
            if utilization_rates[region] > 0:
                # Split CAPEX into Stack and BoP & EPC components
                stack_component = (crf * stack_cost) / (
                    8760 *
                    utilization_rates[region]) * electrolyzer_efficiencies[region]
                    
                bop_epc_component = (crf * bop_epc_cost) / (
                    8760 *
                    utilization_rates[region]) * electrolyzer_efficiencies[region]
                    
                fom_component = fom_values[region] / (
                    8760 *
                    utilization_rates[region]) * electrolyzer_efficiencies[region]
            else:
                stack_component = 0
                bop_epc_component = 0
                fom_component = 0
                
            electricity_component = electricity_costs[
                region] * electrolyzer_efficiencies[region]

            lcoh_components[region] = {
                'Stack Component': stack_component,
                'BoP & EPC Component': bop_epc_component,
                'FOM Component': fom_component,
                'Electricity Component': electricity_component
            }

        # Create a DataFrame for the stacked bar chart
        lcoh_components_df = pd.DataFrame(lcoh_components).T.reset_index()
        lcoh_components_df = pd.melt(lcoh_components_df,
                                     id_vars=['index'],
                                     var_name='Component',
                                     value_name='Cost ($/kg)')
        lcoh_components_df.rename(columns={'index': 'Region'}, inplace=True)

        # Add option for projection year comparison
        st.write("### Current vs Projected LCOH Components")
        projection_year = st.selectbox(
            "Select Projection Year for Comparison",
            options=list(range(base_year + 1, base_year + projection_years + 1)),
            index=min(4, projection_years - 1),  # Default to base_year + 5 or less if fewer years
            key="lcoh_projection_year_select"
        )
        
        # Generate projected LCOH components
        projected_lcoh_components = {}
        
        # Calculate FOM values for projected components
        fom_values = calculate_fom_values(fom_percentages, selected_techs, stack_costs_0, bop_epc_costs_0, REGIONS)
        
        # Calculate projected LCOH for each region
        for region in REGIONS:
            # Generate projections using the selected models
            projected_data = generate_lcoh_projections(
                stack_data, 
                bop_epc_data, 
                [region], 
                wacc_values, 
                {},  # Empty dict since we're using percentages
                utilization_rates, 
                electricity_costs, 
                electrolyzer_efficiencies,
                projection_years, 
                base_year, 
                learning_model=selected_model,  # Use the model selected in the parameters tab
                selected_tech=selected_techs,
                bop_epc_model=selected_bop_model,  # Use the model selected in the parameters tab
                fom_percentages=fom_percentages
            )
            
            # Get the LCOH components for the selected projection year
            year_idx = projection_year - base_year
            
            # Calculate the LCOH components using the calculate_lcoh function
            # First, determine the technology type
            if isinstance(selected_techs, dict):
                tech_type = selected_techs.get(region, 'chinese_alk' if region == 'china' else 'western_pem')
            else:
                tech_type = selected_techs if selected_techs else ('chinese_alk' if region == 'china' else 'western_pem')
            
            # Calculate LCOH for the projection year
            year_lcoh = calculate_lcoh(
                tech_type,
                region,
                stack_data,
                bop_epc_data,
                wacc_values[region],
                0,  # FOM will be calculated from percentage
                utilization_rates[region],
                electricity_costs[region],
                electrolyzer_efficiencies[region],
                learning_model=selected_model,
                bop_epc_model=selected_bop_model,
                year_index=year_idx,
                fom_percentage=fom_percentages[region]
            )

            # Extract detailed components
            components = year_lcoh[1]
            
            # Calculate projected FOM based on projected CAPEX
            projected_capex = components['stack_cost'] + components['bop_cost']
            projected_fom = (fom_percentages[region] / 100.0) * projected_capex
            projected_fom_component = projected_fom / (8760 * utilization_rates[region]) * electrolyzer_efficiencies[region]
            
            projected_lcoh_components[region] = {
                'Stack Component': components['stack_cost'] * calculate_crf(wacc_values[region]) / (8760 * utilization_rates[region]) * electrolyzer_efficiencies[region],
                'BoP & EPC Component': components['bop_cost'] * calculate_crf(wacc_values[region]) / (8760 * utilization_rates[region]) * electrolyzer_efficiencies[region],
                'FOM Component': projected_fom_component,
                'Electricity Component': components['electricity_component']
            }
        
        # Create DataFrame for projected components
        projected_components_df = pd.DataFrame(projected_lcoh_components).T.reset_index()
        projected_components_df = pd.melt(projected_components_df,
                                      id_vars=['index'],
                                      var_name='Component',
                                      value_name='Cost ($/kg)')
        projected_components_df.rename(columns={'index': 'Region'}, inplace=True)
        
        # Simpler approach for side-by-side comparison
        import plotly.graph_objects as go
        
        # Create a standard order for components (bottom to top of stack) - reordered as requested
        component_order = ['Stack Component', 'BoP & EPC Component', 'FOM Component', 'Electricity Component']
        
        # Create component colors - updated for better visual appeal
        colors = {
            'Stack Component': '#2E86AB',      # Steel blue
            'BoP & EPC Component': '#A23B72',  # Deep rose
            'FOM Component': '#F18F01',        # Bright orange
            'Electricity Component': '#C73E1D'  # Dark red
        }
        
        # Calculate projected LCOH components for each region
        # For projected data, get the correct year_index for 2050
        year_idx = projection_year - base_year
        
        # Create the figure
        fig = go.Figure()
        
        # Organize regions and bar positions - with China in all caps and using ROW
        regions = ["USA", "EU", "CHINA", "ROW"]
        bar_positions = {}  # Map of (region, year_type) -> x-position
        x_labels = []
        x_tickvals = []
        
        # Set up x-axis positions and labels with improved formatting
        pos = 0
        for region in regions:
            # Midpoint for region label
            region_midpoint = pos + 0.5
            
            # Current year position
            bar_positions[(region, "Current")] = pos
            x_labels.append(f"{base_year}")  # Just show the year
            x_tickvals.append(pos)
            pos += 1
            
            # Projected year position
            bar_positions[(region, "Projected")] = pos
            x_labels.append(f"{projection_year}")  # Just show the year
            x_tickvals.append(pos)
            pos += 1
            
            # Add region label at the midpoint - closer to the bars
            fig.add_annotation(
                x=region_midpoint,
                y=-0.08,  # Position closer to the x-axis
                text=region,
                showarrow=False,
                xref="x",
                yref="paper",
                font=dict(size=14, family="Arial, sans-serif")
            )
            
            # Add smaller spacing between regions (0.5 instead of 1)
            pos += 0.5
            
        # Get current year LCOH components directly from lcoh_components dataframe
        current_components = {}
        for region in REGIONS:
            filtered_df = lcoh_components_df[lcoh_components_df['Region'] == region]
            current_components[region] = {}
            
            for component in component_order:
                component_rows = filtered_df[filtered_df['Component'] == component]
                if not component_rows.empty:
                    current_components[region][component] = component_rows['Cost ($/kg)'].values[0]
                else:
                    current_components[region][component] = 0.0
        
        # Calculate projected LCOH components
        projected_components = {}
        for region in REGIONS:
            # Determine technology for this region
            tech_type = selected_techs[region] if isinstance(selected_techs, dict) else 'western_pem'
            if region == 'china' and tech_type == 'western_pem':
                tech_type = 'chinese_alk'
                
            # Calculate LCOH for projected year
            lcoh_result = calculate_lcoh(
                tech_type,
                region,
                stack_data,
                bop_epc_data,
                wacc_values[region],
                0,  # FOM will be calculated from percentage
                utilization_rates[region],
                electricity_costs[region],
                electrolyzer_efficiencies[region],
                learning_model=selected_model,
                bop_epc_model=selected_bop_model,
                year_index=year_idx,
                fom_percentage=fom_percentages[region]
            )
            
            # Get the components from calculation
            components = lcoh_result[1]
            
            # Calculate components with proper methodology 
            crf = calculate_crf(wacc_values[region])
            util = max(0.00001, utilization_rates[region])  # Prevent division by zero
            
            # Store the components
            projected_components[region] = {
                'Stack Component': crf * components['stack_cost'] / (8760 * util) * electrolyzer_efficiencies[region],
                'BoP & EPC Component': crf * components['bop_cost'] / (8760 * util) * electrolyzer_efficiencies[region],
                'FOM Component': components['fom_component'],
                'Electricity Component': components['electricity_component']
            }
        
        # Store total LCOH values for labels and summary
        current_totals = {}
        projected_totals = {}
        
        # Add each component as a separate bar segment
        for region_idx, region in enumerate(regions):
            # Convert region display name to internal name
            internal_region = region.lower()
            # Handle "Rest of World" -> "row" mapping
            if internal_region == "rest of world":
                internal_region = "row"
                
            # Add current year components
            current_pos = bar_positions[(region, "Current")]
            current_base = 0
            
            # Add projected year components
            projected_pos = bar_positions[(region, "Projected")]
            projected_base = 0
            
            # Add each component in order (from bottom to top)
            for component in component_order:
                # Current year component
                if internal_region in current_components and component in current_components[internal_region]:
                    current_value = current_components[internal_region][component]
                else:
                    st.warning(f"Missing data for {region} - {component} (current year)")
                    current_value = 0.0
                    
                # Only show labels if value is significant - increased threshold to 0.3
                show_label = current_value >= 0.3
                fig.add_trace(go.Bar(
                    x=[current_pos],
                    y=[current_value],
                    name=component,
                    marker_color=colors[component],
                    base=current_base,
                    text=f"{current_value:.2f}" if show_label else "",
                    textposition='inside',
                    textfont=dict(size=12, family="Arial, sans-serif"),  # Increased uniform font size
                    showlegend=region_idx == 0,  # Only add to legend for the first region
                    legendgroup=component
                ))
                current_base += current_value
                
                # Projected year component
                if internal_region in projected_components and component in projected_components[internal_region]:
                    projected_value = projected_components[internal_region][component]
                else:
                    st.warning(f"Missing data for {region} - {component} (projected year)")
                    projected_value = 0.0
                
                # Only show labels if value is significant - increased threshold to 0.3 for consistency
                show_label = projected_value >= 0.3    
                fig.add_trace(go.Bar(
                    x=[projected_pos],
                    y=[projected_value],
                    name=component,
                    marker_color=colors[component],
                    base=projected_base,
                    text=f"{projected_value:.2f}" if show_label else "",
                    textposition='inside',
                    textfont=dict(size=12, family="Arial, sans-serif"),  # Increased uniform font size
                    showlegend=False,  # Don't add to legend
                    legendgroup=component
                ))
                projected_base += projected_value
            
            # Store totals for this region
            current_totals[region] = current_base
            projected_totals[region] = projected_base
            
            # Add total LCOH labels well above each bar
            base_offset = max(current_base, projected_base) * 0.08  # Dynamic offset based on bar height
            # Increase offset for China region due to higher values
            if region.lower() == "china":
                label_offset = base_offset * 1.5  # 50% more offset for China
            else:
                label_offset = base_offset
                
            fig.add_annotation(
                x=current_pos,
                y=current_base + label_offset,
                text=f"${current_base:.2f}",
                showarrow=False,
                font=dict(size=13, color="black", family="Arial Black"),
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="black",
                borderwidth=1,
                borderpad=4
            )
            
            fig.add_annotation(
                x=projected_pos,
                y=projected_base + label_offset,
                text=f"${projected_base:.2f}",
                showarrow=False,
                font=dict(size=13, color="black", family="Arial Black"),
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="black",
                borderwidth=1,
                borderpad=4
            )
        
        # Calculate the maximum total to set appropriate y-axis range
        max_total = max(max(current_totals.values()), max(projected_totals.values()))
        label_offset = max_total * 0.08  # Calculate label offset
        y_range_max = max_total + label_offset + (max_total * 0.15)  # Add space for labels plus extra padding
        
        # Update the layout with improved formatting
        fig.update_layout(
            title=f"LCOH Components by Region: {base_year} vs {projection_year}",
            xaxis=dict(
                title="",
                tickvals=x_tickvals,
                ticktext=x_labels,
                tickangle=0,
                # Add extra padding at the bottom for region labels
                domain=[0, 1],  # Full width
            ),
            yaxis=dict(
                title="Cost ($/kg)",
                range=[0, y_range_max],  # Set explicit range to prevent label overlap
                # Add a bit more padding at the bottom for region labels
                domain=[0.1, 1]  
            ),
            barmode='stack',
            legend=dict(
                orientation="h",
                yanchor="bottom", 
                y=1.02,
                xanchor="right", 
                x=1,
                # Make the component names more readable
                title=""
            ),
            height=650,  # Increased height to accommodate labels
            bargap=0.15,
            margin=dict(b=80, t=100)  # Increased top margin for labels
        )
        
        # Display the optimized chart (using the new figure - 'fig', not fig_components_combined)
        st.plotly_chart(fig, use_container_width=True)
        
        # Add summary section below the chart
        st.subheader("LCOH Summary")
        
        # Create columns for the summary table
        summary_cols = st.columns(len(regions))
        
        for i, region in enumerate(regions):
            with summary_cols[i]:
                st.markdown(f"**{region}**")
                
                current_total = current_totals[region]
                projected_total = projected_totals[region]
                reduction = current_total - projected_total
                reduction_pct = (reduction / current_total) * 100 if current_total > 0 else 0
                
                # Calculate component reductions
                region_key = region.lower()
                if region_key in current_components and region_key in projected_components:
                    current_comp = current_components[region_key]
                    projected_comp = projected_components[region_key]
                    
                    stack_reduction = current_comp.get('Stack Component', 0) - projected_comp.get('Stack Component', 0)
                    bop_reduction = current_comp.get('BoP & EPC Component', 0) - projected_comp.get('BoP & EPC Component', 0)
                    
                    # Calculate percentages based only on capital cost reductions (stack + BoP & EPC)
                    # FOM reduction is proportional to both, so we exclude it to get clean percentages
                    capital_reduction = stack_reduction + bop_reduction
                    if capital_reduction > 0:
                        stack_pct = (stack_reduction / capital_reduction) * 100
                        bop_pct = (bop_reduction / capital_reduction) * 100
                    else:
                        stack_pct = bop_pct = 0
                else:
                    stack_pct = bop_pct = 0
                
                # Create a nice formatted display
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 5px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-weight: bold;">Current ({base_year}):</span>
                        <span style="font-weight: bold; color: #1f77b4;">${current_total:.2f}/kg</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-weight: bold;">Projected ({projection_year}):</span>
                        <span style="font-weight: bold; color: #2ca02c;">${projected_total:.2f}/kg</span>
                    </div>
                    <hr style="margin: 10px 0; border: 1px solid #ddd;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="font-weight: bold;">Reduction:</span>
                        <span style="font-weight: bold; color: #d62728;">${reduction:.2f}/kg</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-weight: bold;">% Reduction:</span>
                        <span style="font-weight: bold; color: #d62728;">{reduction_pct:.1f}%</span>
                    </div>
                    <hr style="margin: 8px 0; border: 1px solid #ddd;">
                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">
                        <strong>Reduction Sources:</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 3px; font-size: 12px;">
                        <span>Stack:</span>
                        <span style="color: #1f77b4;">{stack_pct:.0f}%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px;">
                        <span>BoP & EPC:</span>
                        <span style="color: #ff7f0e;">{bop_pct:.0f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        


    # ========== REGIONAL PROJECTIONS TAB ==========
    with lcoh_tabs[1]:
        st.subheader("LCOH Projections by Region")

        # Create columns for model selection
        col1, col2 = st.columns(2)
        
        with col1:
            # Select learning model to use for stack projections
            stack_learning_model = st.selectbox(
                "Select Learning Model for Stack Costs",
                options=['shared', 'first_layer', 'second_layer'],
                index=2,  # Default to second_layer (most realistic)
                format_func=lambda x: {
                    'shared': 'Shared Learning',
                    'first_layer': 'Technological Fragmentation',
                    'second_layer': 'Regional Fragmentation'
                }[x],
                key="lcoh_stack_learning_model")
        
        with col2:
            # Select learning model to use for BoP/EPC projections
            # Synchronize with Parameters tab selection if it exists
            if "params_bop_epc_learning_model" in st.session_state:
                default_bop_idx = 0 if st.session_state["params_bop_epc_learning_model"] == "local" else 1
            else:
                default_bop_idx = 0
                
            bop_epc_learning_model = st.selectbox(
                "Select Learning Model for BoP/EPC Costs",
                options=['local', 'global'],
                index=default_bop_idx,  # Sync with Parameters tab
                format_func=lambda x: {
                    'local': 'Local Learning (Region-specific)',
                    'global': 'Global Learning (Cross-regional)'
                }[x],
                key="lcoh_calculator_bop_epc_model")

        # Calculate FOM values for LCOH Calculator tab
        fom_values = calculate_fom_values(fom_percentages, selected_techs, stack_costs_0, bop_epc_costs_0, REGIONS)
        
        # Generate LCOH projections with selected parameters
        lcoh_projections = generate_lcoh_projections(
            stack_data, 
            bop_epc_data, 
            REGIONS, 
            wacc_values, 
            {},  # Empty dict since we're using percentages
            utilization_rates, 
            electricity_costs, 
            electrolyzer_efficiencies,
            projection_years, 
            base_year, 
            learning_model=stack_learning_model,  # Use user-selected stack model
            selected_tech=selected_techs,        # Pass the selected technologies
            bop_epc_model=bop_epc_learning_model,  # Use user-selected BoP/EPC model
            fom_percentages=fom_percentages)

        # Create visualizations
        st.write("### LCOH Projections Over Time")

        # Create a DataFrame with projections for all regions
        lcoh_df = pd.DataFrame(
            {'Year': list(range(base_year, base_year + projection_years + 1))})

        for region in REGIONS:
            lcoh_df[get_region_display_name(
                region)] = lcoh_projections[region]['LCOH ($/kg)'].values

        # Melt the DataFrame for plotting
        lcoh_melted = pd.melt(
            lcoh_df,
            id_vars=['Year'],
            value_vars=[get_region_display_name(region) for region in REGIONS],
            var_name='Region',
            value_name='LCOH ($/kg)')

        # Create line chart
        stack_model_display = {
            'shared': 'Shared',
            'first_layer': 'Technological Fragmentation',
            'second_layer': 'Regional Fragmentation'
        }[stack_learning_model]
        
        bop_epc_model_display = {
            'local': 'Local',
            'global': 'Global'
        }[bop_epc_learning_model]
        
        fig = px.line(
            lcoh_melted,
            x='Year',
            y='LCOH ($/kg)',
            color='Region',
            markers=True,
            title=
            f"Projected LCOH by Region (Stack: {stack_model_display}, BoP/EPC: {bop_epc_model_display} Learning Model)"
        )

        fig.update_layout(autosize=True,
                          height=500,
                          hovermode="x unified",
                          legend=dict(orientation="h",
                                      yanchor="bottom",
                                      y=1.02,
                                      xanchor="right",
                                      x=1))

        st.plotly_chart(fig,
                        use_container_width=True,
                        key=f"lcoh_projection_line_{stack_learning_model}_{bop_epc_learning_model}")

        # Show LCOH components over time for a selected region
        st.write("### LCOH Components Over Time")

        selected_region = st.selectbox("Select Region to Analyze",
                                       options=REGIONS,
                                       format_func=get_region_display_name,
                                       key="lcoh_region_select")

        # Get components data for the selected region
        # We need to generate stack and bop_epc components from CAPEX
        # First, get the projection data
        df = lcoh_projections[selected_region]
        
        # For each year, calculate the Stack and BoP & EPC components
        stack_components = []
        bop_epc_components = []
        
        for idx in range(len(df)):
            # Get the stack and BoP costs for this year
            tech_type = selected_techs.get(selected_region, 'chinese_alk' if selected_region == 'china' else 'western_pem') if isinstance(selected_techs, dict) else (selected_techs if selected_techs else ('chinese_alk' if selected_region == 'china' else 'western_pem'))
            
            # Calculate LCOH for this year to get the detailed components
            year_lcoh = calculate_lcoh(
                tech_type,
                selected_region,
                stack_data,
                bop_epc_data,
                wacc_values[selected_region],
                0,  # FOM will be calculated from percentage
                utilization_rates[selected_region],
                electricity_costs[selected_region],
                electrolyzer_efficiencies[selected_region],
                learning_model=stack_learning_model,
                bop_epc_model=bop_epc_learning_model,
                year_index=idx,
                fom_percentage=fom_percentages[selected_region]
            )
            
            # Extract component details
            components = year_lcoh[1]
            
            # Calculate Stack and BoP & EPC components
            crf = calculate_crf(wacc_values[selected_region])
            util = max(0.00001, utilization_rates[selected_region])  # Prevent division by zero
            
            stack_component = crf * components['stack_cost'] / (8760 * util) * electrolyzer_efficiencies[selected_region]
            bop_epc_component = crf * components['bop_cost'] / (8760 * util) * electrolyzer_efficiencies[selected_region]
            
            stack_components.append(stack_component)
            bop_epc_components.append(bop_epc_component)
        
        # Create DataFrame with detailed components
        components_df = pd.DataFrame({
            'Year': lcoh_projections[selected_region]['Year'],
            'Stack Component': stack_components,
            'BoP & EPC Component': bop_epc_components,
            'FOM Component': lcoh_projections[selected_region]['FOM Component ($/kg)'],
            'Electricity Component': lcoh_projections[selected_region]['Electricity Component ($/kg)']
        })

        # Melt the DataFrame for plotting
        components_melted = pd.melt(components_df,
                                    id_vars=['Year'],
                                    value_vars=[
                                        'Stack Component', 'BoP & EPC Component', 
                                        'FOM Component', 'Electricity Component'
                                    ],
                                    var_name='Component',
                                    value_name='Cost ($/kg)')

        # Create stacked area chart
        fig_components = px.area(
            components_melted,
            x='Year',
            y='Cost ($/kg)',
            color='Component',
            title=
            f"LCOH Components Over Time for {get_region_display_name(selected_region)}"
        )

        fig_components.update_layout(autosize=True,
                                     height=500,
                                     hovermode="x unified",
                                     legend=dict(orientation="h",
                                                 yanchor="bottom",
                                                 y=1.02,
                                                 xanchor="right",
                                                 x=1))

        st.plotly_chart(fig_components,
                        use_container_width=True,
                        key=f"lcoh_components_area_{stack_learning_model}_{bop_epc_learning_model}_{selected_region}")

        # Display data table with projections
        st.write("### Detailed LCOH Projections")

        # Create tabs for each region
        region_tabs = st.tabs(
            [get_region_display_name(region) for region in REGIONS])

        for region_idx, region in enumerate(REGIONS):
            with region_tabs[region_idx]:
                st.dataframe(lcoh_projections[region],
                             use_container_width=True,
                             key=f"df_lcoh_{region}_{stack_learning_model}_{bop_epc_learning_model}")

                # Download button for this region's data
                csv_data = lcoh_projections[region].to_csv(index=False)
                st.download_button(
                    label=
                    f"Download {get_region_display_name(region)} LCOH Data (CSV)",
                    data=csv_data,
                    file_name=f"lcoh_projections_{region}_{stack_learning_model}_{bop_epc_learning_model}.csv",
                    mime="text/csv",
                    key=f"download_lcoh_{region}")

    # ========== SENSITIVITY ANALYSIS TAB ==========
    with lcoh_tabs[2]:
        st.subheader("LCOH Sensitivity Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # Select region for sensitivity analysis
            sens_region = st.selectbox("Select Region",
                                       options=REGIONS,
                                       format_func=get_region_display_name,
                                       key="sensitivity_region")

            # Select target year
            sens_year = st.slider("Target Year",
                                  min_value=base_year,
                                  max_value=base_year + projection_years,
                                  value=base_year + 5,
                                  step=1,
                                  key="sensitivity_year")

        with col2:
                # Use the same learning models as selected in the LCOH parameters tab
            st.info(f"Using {selected_model} for Stack and {selected_bop_model} for BoP & EPC learning models from LCOH Parameters")

            st.info(f"""
            This analysis shows how changes in key parameters affect the LCOH in {sens_year} 
            for {get_region_display_name(sens_region)}.
            """)

        # Calculate FOM values for sensitivity analysis
        fom_values = calculate_fom_values(fom_percentages, selected_techs, stack_costs_0, bop_epc_costs_0, REGIONS)
        
        # Run sensitivity analysis
        sensitivity_results = generate_lcoh_sensitivity(
            stack_data,
            bop_epc_data,
            sens_region,
            wacc_values[sens_region],
            fom_values[sens_region],
            utilization_rates[sens_region],
            electricity_costs[sens_region],
            electrolyzer_efficiencies[sens_region],
            sens_year,
            base_year,
            wacc_range=(0.01, 0.15),
            utilization_range=(0.2, 1.0),
            electricity_range=(0.01, 0.15),
            efficiency_range=(40, 70),
            learning_model=selected_model,
            stack_model=selected_model,
            bop_epc_model=selected_bop_model)

        # Create visualizations for sensitivity results
        st.write("### Parameter Sensitivity")

        # Create a 2x2 grid of sensitivity charts
        col1, col2 = st.columns(2)

        # WACC Sensitivity
        with col1:
            # Create a DataFrame for projected LCOH values
            wacc_df = pd.DataFrame({
                'WACC (%)': sensitivity_results['wacc']['parameter_values'] * 100,
                f'LCOH ($/kg) in {sens_year}': sensitivity_results['wacc']['lcoh_values']
            })
            
            # Add current LCOH values if available
            if sensitivity_results['wacc']['current_lcoh_values'] is not None:
                wacc_df[f'LCOH ($/kg) in {base_year}'] = sensitivity_results['wacc']['current_lcoh_values']
                
                # Create the figure with both current and future values
                fig_wacc = px.line(wacc_df,
                                  x='WACC (%)',
                                  y=[f'LCOH ($/kg) in {base_year}', f'LCOH ($/kg) in {sens_year}'],
                                  title="Sensitivity to WACC",
                                  markers=True,
                                  color_discrete_sequence=['blue', 'green'])
            else:
                # Create the figure with just future values
                fig_wacc = px.line(wacc_df,
                                  x='WACC (%)',
                                  y=f'LCOH ($/kg) in {sens_year}',
                                  title="Sensitivity to WACC",
                                  markers=True)

            fig_wacc.update_layout(autosize=True, height=300)

            fig_wacc.add_vline(x=wacc_values[sens_region] * 100,
                              line_dash="dash",
                              line_color="red",
                              annotation_text="Current Value")

            st.plotly_chart(fig_wacc,
                           use_container_width=True,
                           key="sens_wacc")

        # Utilization Rate Sensitivity
        with col2:
            # Create a DataFrame for projected LCOH values
            util_df = pd.DataFrame({
                'Utilization Rate (%)': sensitivity_results['utilization']['parameter_values'] * 100,
                f'LCOH ($/kg) in {sens_year}': sensitivity_results['utilization']['lcoh_values']
            })
            
            # Add current LCOH values if available
            if sensitivity_results['utilization']['current_lcoh_values'] is not None:
                util_df[f'LCOH ($/kg) in {base_year}'] = sensitivity_results['utilization']['current_lcoh_values']
                
                # Create the figure with both current and future values
                fig_util = px.line(util_df,
                                  x='Utilization Rate (%)',
                                  y=[f'LCOH ($/kg) in {base_year}', f'LCOH ($/kg) in {sens_year}'],
                                  title="Sensitivity to Utilization Rate",
                                  markers=True,
                                  color_discrete_sequence=['blue', 'green'])
            else:
                # Create the figure with just future values
                fig_util = px.line(util_df,
                                  x='Utilization Rate (%)',
                                  y=f'LCOH ($/kg) in {sens_year}',
                                  title="Sensitivity to Utilization Rate",
                                  markers=True)

            fig_util.update_layout(autosize=True, height=300)

            fig_util.add_vline(x=utilization_rates[sens_region] * 100,
                              line_dash="dash",
                              line_color="red",
                              annotation_text="Current Value")

            st.plotly_chart(fig_util,
                           use_container_width=True,
                           key="sens_util")

        # Electricity Cost Sensitivity
        with col1:
            # Create a DataFrame for projected LCOH values
            elec_df = pd.DataFrame({
                'Electricity Cost ($/kWh)': sensitivity_results['electricity']['parameter_values'],
                f'LCOH ($/kg) in {sens_year}': sensitivity_results['electricity']['lcoh_values']
            })
            
            # Add current LCOH values if available
            if sensitivity_results['electricity']['current_lcoh_values'] is not None:
                elec_df[f'LCOH ($/kg) in {base_year}'] = sensitivity_results['electricity']['current_lcoh_values']
                
                # Create the figure with both current and future values
                fig_elec = px.line(elec_df,
                                   x='Electricity Cost ($/kWh)',
                                   y=[f'LCOH ($/kg) in {base_year}', f'LCOH ($/kg) in {sens_year}'],
                                   title="Sensitivity to Electricity Cost",
                                   markers=True,
                                   color_discrete_sequence=['blue', 'green'])
            else:
                # Create the figure with just future values
                fig_elec = px.line(elec_df,
                                   x='Electricity Cost ($/kWh)',
                                   y=f'LCOH ($/kg) in {sens_year}',
                                   title="Sensitivity to Electricity Cost",
                                   markers=True)

            fig_elec.update_layout(autosize=True, height=300)

            fig_elec.add_vline(x=electricity_costs[sens_region],
                               line_dash="dash",
                               line_color="red",
                               annotation_text="Current Value")

            st.plotly_chart(fig_elec,
                            use_container_width=True,
                            key="sens_elec")

        # Efficiency Sensitivity
        with col2:
            # Create a DataFrame for projected LCOH values
            eff_df = pd.DataFrame({
                'Electrolyzer Efficiency (kWh/kg)': sensitivity_results['efficiency']['parameter_values'],
                f'LCOH ($/kg) in {sens_year}': sensitivity_results['efficiency']['lcoh_values']
            })
            
            # Add current LCOH values if available
            if sensitivity_results['efficiency']['current_lcoh_values'] is not None:
                eff_df[f'LCOH ($/kg) in {base_year}'] = sensitivity_results['efficiency']['current_lcoh_values']
                
                # Create the figure with both current and future values
                fig_eff = px.line(eff_df,
                                  x='Electrolyzer Efficiency (kWh/kg)',
                                  y=[f'LCOH ($/kg) in {base_year}', f'LCOH ($/kg) in {sens_year}'],
                                  title="Sensitivity to Electrolyzer Efficiency",
                                  markers=True,
                                  color_discrete_sequence=['blue', 'green'])
            else:
                # Create the figure with just future values
                fig_eff = px.line(eff_df,
                                  x='Electrolyzer Efficiency (kWh/kg)',
                                  y=f'LCOH ($/kg) in {sens_year}',
                                  title="Sensitivity to Electrolyzer Efficiency",
                                  markers=True)

            fig_eff.update_layout(autosize=True, height=300)

            fig_eff.add_vline(x=electrolyzer_efficiencies[sens_region],
                              line_dash="dash",
                              line_color="red",
                              annotation_text="Current Value")

            st.plotly_chart(fig_eff, use_container_width=True, key="sens_eff")

        # Note on sensitivity analysis
        st.info("""
        **Sensitivity Analysis Interpretation**:

        The charts above show how changes in each parameter affect the LCOH. 
        - Compare the blue line (current year values) with the green line (projected values) to see how the sensitivity to each parameter will change over time.
        - The steeper the slope, the more sensitive LCOH is to that parameter.
        - The red dashed line indicates the current parameter value.
        """)

    # LCOH Formula and Methodology (at bottom of LCOH tab)
    st.info("""
    **LCOH Calculator Methodology**

    The Levelized Cost of Hydrogen (LCOH) represents the break-even cost of hydrogen production over the project lifetime, accounting for all capital and operational expenses. The calculation uses the following equation:

    $$LCOH = \\left(\\frac{CRF \\times CAPEX + FOM}{CF} + C_{elec}\\right) \\times \\eta  $$

    **Parameter Definitions:**
    - **CRF** (Capital Recovery Factor): $\\frac{WACC \\times (1 + WACC)^{L}}{(1 + WACC)^{L} - 1}$ where WACC is the weighted average cost of capital, and L=20 is the assumed project lifetime in years.
    - **CAPEX**: Total capital expenditure including stack costs and BOP & EPC costs ($/kW)
    - **FOM**: Fixed Operations and Maintenance costs ($/kW/year)
    - **CF**: Capacity factor/Utilization rate - fraction of time the electrolyzer operates (hours/year)
    - **η**: Electrolyzer efficiency - energy consumption per kg of hydrogen (kWh/kg H₂)
    - **C_elec**: Electricity costs ($/kWh)

    The calculator incorporates projected cost reductions from learning curves based on cumulative capacity deployment and selected learning models.
    """)





# ==================== LEARNING INVESTMENT TAB ====================
with main_tabs[4]:
    # Render the Learning Investment tab with our new implementation
    render_learning_investment_tab(
        TECHNOLOGIES, get_stack_display_name, stack_costs_0, technologies_capacities_0, stack_alphas,
        get_region_display_name, bop_epc_costs_0, region_base_capacities, bop_epc_alphas, REGIONS
    )