"""
Learning Investment Tab Implementation for Regional App
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from target_cost_utils import (
    generate_target_cost_data_stack,
    generate_target_cost_data_bop_epc
)

def implement_stack_investment_tab(TECHNOLOGIES, get_stack_display_name, 
                                 stack_costs_0, technologies_capacities_0, stack_alphas):
    """Implement the Stack Technology Learning Investments tab"""
    
    st.subheader("Stack Technology Learning Investments")
    
    # Create technology and cost reduction target selections
    col1, col2 = st.columns(2)
    
    with col1:
        # Create stack technology selection
        selected_stack_tech = st.selectbox(
            "Select Stack Technology",
            options=TECHNOLOGIES,
            format_func=get_stack_display_name,
            key="investment_stack_tech")
    
    with col2:
        # Select target cost reduction percentage
        target_cost_reduction = st.slider(
            "Target Cost Reduction (%)",
            min_value=10,
            max_value=90,
            value=70,
            step=5,
            key="stack_target_reduction",
            help="Target cost reduction percentage (e.g., 70 = 70% reduction from initial cost)")
    
    # Calculate target cost based on reduction percentage
    initial_cost = stack_costs_0[selected_stack_tech]
    target_cost_factor = 1.0 - (target_cost_reduction / 100.0)
    target_cost = initial_cost * target_cost_factor
    
    # Display initial and target cost information
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Initial Cost", 
            f"${initial_cost:.0f}/kW", 
            delta=None
        )
    with col2:
        st.metric(
            "Target Cost", 
            f"${target_cost:.0f}/kW", 
            delta=f"-{target_cost_reduction}%",
            delta_color="normal"
        )
    
    # Generate data for all learning models
    learning_models = ['shared', 'first_layer', 'second_layer']
    model_display_names = {
        'shared': 'Shared Learning',
        'first_layer': 'Technological Fragmentation',
        'second_layer': 'Regional Fragmentation'
    }
    
    model_colors = {
        'shared': '#636EFA',  # blue
        'first_layer': '#EF553B',  # red
        'second_layer': '#00CC96',  # green
    }
    
    # Determine step size based on cost range
    cost_range = initial_cost - target_cost
    cost_step = max(10, round(cost_range / 40, -1))  # Round to nearest 10
    cost_steps = int(cost_range / cost_step) + 1
    
    # Adjust initial capacities for learning investment calculations
    # Following user requirements: add 1.1 GW to Western and Chinese PEM and 23.68 GW to Western and Chinese ALK
    # This represents additional capacity beyond what's included in the base data
    adjusted_capacities = technologies_capacities_0.copy()
    

    
    # Define additional capacities that will be used in learning calculations
    # These are NOT added to the base capacities, but used in the learning calculations
    # in a different way depending on the learning model
    pem_additional_capacity = 1100  # 1.1 GW in MW
    alk_additional_capacity = 22580  # 22.58 GW in MW
    
    # Generate data for each model
    all_models_data = {}
    
    for model in learning_models:
        target_cost_data = generate_target_cost_data_stack(
            selected_stack_tech,
            stack_costs_0,
            technologies_capacities_0,  # Use original capacities
            stack_alphas,
            cost_steps=cost_steps,
            min_cost_factor=target_cost_factor,
            learning_model=model,
            pem_additional_capacity=pem_additional_capacity,  # Pass the additional capacities separately
            alk_additional_capacity=alk_additional_capacity
        )
        all_models_data[model] = target_cost_data
    
    # Learning Investment Plot
    st.subheader("Learning Investment by Target Cost")
    
    # Create figure for investment
    fig_inv = go.Figure()
    
    for model in learning_models:
        model_data = all_models_data[model]
        
        # Round to nearest half integer and convert display to billions
        investment_millions = model_data['learning_investment'] / 1e6
        investment_millions_rounded = (investment_millions * 2).round() / 2  # Round to nearest 0.5
        
        fig_inv.add_trace(
            go.Scatter(
                x=model_data['target_cost'],
                y=investment_millions_rounded,
                mode='lines',
                name=model_display_names[model],
                line=dict(color=model_colors[model], width=3),
                hovertemplate='Target Cost: $%{x:.0f}/kW<br>Investment: $%{y:.1f}B<extra></extra>'
            )
        )
    
    # Add reference line for target cost
    fig_inv.add_vline(
        x=target_cost, 
        line_width=2, 
        line_dash="dash", 
        line_color="gray",
        annotation_text=f"Target: ${target_cost:.0f}/kW",
        annotation_position="top right"
    )
    
    # Format axes
    fig_inv.update_layout(
        title=f"Learning Investment for {get_stack_display_name(selected_stack_tech)}",
        hovermode="closest",
        xaxis=dict(
            title="Target Cost ($/kW)",
            range=[target_cost * 0.95, initial_cost * 1.05],  # Give some padding
            autorange="reversed"  # Higher costs on left, lower on right
        ),
        yaxis=dict(
            title="Cumulative Investment ($ billion)",
            tickformat=".1f"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Show the investment plot
    st.plotly_chart(fig_inv, use_container_width=True)
    
    # Required Capacity Plot
    st.subheader("Required Capacity by Target Cost")
    
    # Create figure for capacity
    fig_cap = go.Figure()
    
    for model in learning_models:
        model_data = all_models_data[model]
        
        # Round capacity to nearest half integer
        capacity_gw = model_data['required_capacity'] / 1000  # Convert from MW to GW
        capacity_gw_rounded = (capacity_gw * 2).round() / 2  # Round to nearest 0.5
        
        fig_cap.add_trace(
            go.Scatter(
                x=model_data['target_cost'],
                y=capacity_gw_rounded,
                mode='lines',
                name=model_display_names[model],
                line=dict(color=model_colors[model], width=3),
                hovertemplate='Target Cost: $%{x:.0f}/kW<br>Capacity: %{y:.1f} GW<extra></extra>'
            )
        )
    
    # Add reference line for target cost
    fig_cap.add_vline(
        x=target_cost, 
        line_width=2, 
        line_dash="dash", 
        line_color="gray",
        annotation_text=f"Target: ${target_cost:.0f}/kW",
        annotation_position="top right"
    )
    
    # Format axes
    fig_cap.update_layout(
        title=f"Required Capacity for {get_stack_display_name(selected_stack_tech)}",
        hovermode="closest",
        xaxis=dict(
            title="Target Cost ($/kW)",
            range=[target_cost * 0.95, initial_cost * 1.05],  # Give some padding
            autorange="reversed"  # Higher costs on left, lower on right
        ),
        yaxis=dict(
            title="Cumulative Required Capacity (GW)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Show the capacity plot
    st.plotly_chart(fig_cap, use_container_width=True)
    
    # Show the investment required to reach target
    st.subheader(f"Learning Investment Projections for {target_cost_reduction}% Cost Reduction")
    
    # Create three columns for the learning models
    col1, col2, col3 = st.columns(3)
    
    columns = [col1, col2, col3]
    
    for i, model in enumerate(learning_models):
        with columns[i]:
            st.write(f"#### {model_display_names[model]}")
            
            # Find the row closest to the target cost
            target_data = all_models_data[model]
            idx = (target_data['target_cost'] - target_cost).abs().idxmin()
            target_row = target_data.iloc[idx]
            
            # Display metrics with rounding to nearest half integer
            capacity_gw = target_row['required_capacity'] / 1000
            capacity_rounded = (capacity_gw * 2).round() / 2
            
            investment_millions = target_row['learning_investment'] / 1e6
            investment_rounded = (investment_millions * 2).round() / 2
            
            st.metric(
                "Required Capacity",
                f"{capacity_rounded:.1f} GW",
                delta=None
            )
            
            st.metric(
                "Learning Investment", 
                f"${investment_rounded:.1f}B",
                delta=None
            )
    
    # Explanation and notes
    st.info("""
    **How to interpret these charts:**
    
    - **Learning Investment by Target Cost**: Shows the total investment required to reach different cost targets under each learning model.
    - **Required Capacity by Target Cost**: Shows the total capacity required to reach different cost targets under each learning model.
    
    **Learning Models Explained:**
    - **Shared Learning**: Assumes knowledge transfer across all technologies (PEM and ALK share knowledge).
    - **Technological Fragmentation**: Assumes knowledge transfer within technology types (PEM technologies share knowledge, ALK technologies share knowledge).
    - **Regional Fragmentation**: Assumes no knowledge transfer between technologies (each technology learns independently).
    """)

def implement_bop_epc_investment_tab(get_region_display_name, bop_epc_costs_0, 
                                   region_base_capacities, bop_epc_alphas, REGIONS):
    """Implement the Balance of Plant & EPC Learning Investments tab"""
    
    st.subheader("Balance of Plant & EPC Learning Investments")
    
    # Create columns for selections
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Select region
        selected_bop_region = st.selectbox(
            "Select Region",
            options=['usa', 'eu', 'china', 'row'],
            format_func=get_region_display_name,
            key="investment_bop_region")
        
    with col2:
        # Select technology type
        selected_bop_tech_type = st.selectbox(
            "Select Technology Type",
            options=['pem', 'alk'],
            format_func=lambda x: "PEM" if x == "pem" else "Alkaline",
            key="investment_bop_tech_type")
    
    with col3:
        # Select target cost reduction percentage
        target_bop_reduction = st.slider(
            "Target Cost Reduction (%)",
            min_value=10,
            max_value=90,
            value=70,
            step=5,
            key="bop_target_reduction",
            help="Target cost reduction percentage (e.g., 70 = 70% reduction from initial cost)")
    
    # Calculate target cost based on reduction percentage
    # The format is different in the app, need to use the correct key
    key = f"{selected_bop_region}_{selected_bop_tech_type}"
    initial_bop_cost = bop_epc_costs_0[key]
    target_bop_factor = 1.0 - (target_bop_reduction / 100.0)
    target_bop_cost = initial_bop_cost * target_bop_factor
    
    # Display initial and target cost information
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Initial BoP & EPC Cost", 
            f"${initial_bop_cost:.0f}/kW", 
            delta=None
        )
    with col2:
        st.metric(
            "Target BoP & EPC Cost", 
            f"${target_bop_cost:.0f}/kW", 
            delta=f"-{target_bop_reduction}%",
            delta_color="normal"
        )
    
    # Generate data for both learning models
    bop_models = ['local', 'global']
    bop_model_display_names = {
        'local': 'Local Learning',
        'global': 'Global Learning'
    }
    
    bop_model_colors = {
        'local': '#AB63FA',  # purple
        'global': '#FFA15A',  # orange
    }
    
    # Determine step size based on cost range
    cost_range = initial_bop_cost - target_bop_cost
    cost_step = max(10, round(cost_range / 40, -1))  # Round to nearest 10
    cost_steps = int(cost_range / cost_step) + 1
    
    # Generate data for each model
    all_bop_models_data = {}
    
    for model in bop_models:
        target_bop_data = generate_target_cost_data_bop_epc(
            selected_bop_region,
            selected_bop_tech_type,
            bop_epc_costs_0,
            region_base_capacities,
            bop_epc_alphas,
            REGIONS,
            cost_steps=cost_steps,
            min_cost_factor=target_bop_factor,
            learning_model=model
        )
        all_bop_models_data[model] = target_bop_data
    
    # Learning Investment Plot
    st.subheader("Learning Investment by Target Cost")
    
    # Create figure for investment
    fig_inv = go.Figure()
    
    for model in bop_models:
        model_data = all_bop_models_data[model]
        
        # Round to nearest half integer and keep original scale
        investment_millions = model_data['learning_investment'] / 1e6
        investment_millions_rounded = (investment_millions * 2).round() / 2  # Round to nearest 0.5
        
        fig_inv.add_trace(
            go.Scatter(
                x=model_data['target_cost'],
                y=investment_millions_rounded,
                mode='lines',
                name=bop_model_display_names[model],
                line=dict(color=bop_model_colors[model], width=3),
                hovertemplate='Target Cost: $%{x:.0f}/kW<br>Investment: $%{y:.1f}B<extra></extra>'
            )
        )
    
    # Add reference line for target cost
    fig_inv.add_vline(
        x=target_bop_cost, 
        line_width=2, 
        line_dash="dash", 
        line_color="gray",
        annotation_text=f"Target: ${target_bop_cost:.0f}/kW",
        annotation_position="top right"
    )
    
    # Format axes
    fig_inv.update_layout(
        title=f"Learning Investment for {selected_bop_tech_type.upper()} BoP & EPC in {get_region_display_name(selected_bop_region)}",
        hovermode="closest",
        xaxis=dict(
            title="Target Cost ($/kW)",
            range=[target_bop_cost * 0.95, initial_bop_cost * 1.05],  # Give some padding
            autorange="reversed"  # Higher costs on left, lower on right
        ),
        yaxis=dict(
            title="Cumulative Investment ($ billion)",
            tickformat=".1f"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Show the investment plot
    st.plotly_chart(fig_inv, use_container_width=True)
    
    # Required Capacity Plot
    st.subheader("Required Capacity by Target Cost")
    
    # Create figure for capacity
    fig_cap = go.Figure()
    
    for model in bop_models:
        model_data = all_bop_models_data[model]
        
        # Round capacity to nearest half integer
        capacity_gw = model_data['required_capacity'] / 1000  # Convert from MW to GW
        capacity_gw_rounded = (capacity_gw * 2).round() / 2  # Round to nearest 0.5
        
        fig_cap.add_trace(
            go.Scatter(
                x=model_data['target_cost'],
                y=capacity_gw_rounded,
                mode='lines',
                name=bop_model_display_names[model],
                line=dict(color=bop_model_colors[model], width=3),
                hovertemplate='Target Cost: $%{x:.0f}/kW<br>Capacity: %{y:.1f} GW<extra></extra>'
            )
        )
    
    # Add reference line for target cost
    fig_cap.add_vline(
        x=target_bop_cost, 
        line_width=2, 
        line_dash="dash", 
        line_color="gray",
        annotation_text=f"Target: ${target_bop_cost:.0f}/kW",
        annotation_position="top right"
    )
    
    # No annotations needed
    
    # Format axes
    fig_cap.update_layout(
        title=f"Required Capacity for {selected_bop_tech_type.upper()} BoP & EPC in {get_region_display_name(selected_bop_region)}",
        hovermode="closest",
        xaxis=dict(
            title="Target Cost ($/kW)",
            range=[target_bop_cost * 0.95, initial_bop_cost * 1.05],  # Give some padding
            autorange="reversed"  # Higher costs on left, lower on right
        ),
        yaxis=dict(
            title="Cumulative Required Capacity (GW)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Show the capacity plot
    st.plotly_chart(fig_cap, use_container_width=True)
    
    # Show the investment required to reach target
    st.subheader(f"Learning Investment Projections for {target_bop_reduction}% Cost Reduction")
    
    # Create two columns for the learning models
    col1, col2 = st.columns(2)
    
    columns = [col1, col2]
    
    for i, model in enumerate(bop_models):
        with columns[i]:
            st.write(f"#### {bop_model_display_names[model]}")
            
            # Find the row closest to the target cost
            target_data = all_bop_models_data[model]
            idx = (target_data['target_cost'] - target_bop_cost).abs().idxmin()
            target_row = target_data.iloc[idx]
            
            # Display metrics with rounding to nearest half integer
            capacity_gw = target_row['required_capacity'] / 1000
            capacity_rounded = (capacity_gw * 2).round() / 2
            
            investment_millions = target_row['learning_investment'] / 1e6
            investment_rounded = (investment_millions * 2).round() / 2
            
            st.metric(
                "Required Capacity",
                f"{capacity_rounded:.1f} GW",
                delta=None
            )
            
            st.metric(
                "Learning Investment", 
                f"${investment_rounded:.1f}B",
                delta=None
            )
    
    # Explanation and notes
    st.info("""
    **How to interpret these charts:**
    
    - **Learning Investment by Target Cost**: Shows the total investment required to reach different cost targets under each learning model.
    - **Required Capacity by Target Cost**: Shows the total capacity required to reach different cost targets under each learning model.
    
    **Learning Models Explained:**
    - **Local Learning**: Assumes knowledge is localized within each region (learning happens independently in each region).
    - **Global Learning**: Assumes knowledge transfers across all regions (all regions benefit from global learning).
    """)

def render_learning_investment_tab(TECHNOLOGIES, get_stack_display_name, 
                                 stack_costs_0, technologies_capacities_0, stack_alphas,
                                 get_region_display_name, bop_epc_costs_0, 
                                 region_base_capacities, bop_epc_alphas, REGIONS):
    """Main function to render the Learning Investment tab"""
    
    st.header("Learning Investment Analysis")

    st.markdown("""
    This tab calculates the learning investments needed to achieve specific cost reduction targets.
    Learning investments represent the financial commitments needed to move technologies down their experience curves.
    
    Unlike the other tabs which project based on growth rates, this analysis shows what capacity and investment 
    would be required to reach specific cost targets.
    """)

    # Create tabs for different views
    investment_tabs = st.tabs([
        "Stack Technologies", "BoP & EPC"
    ])

    # Tab 1: Stack Technology Learning Investments
    with investment_tabs[0]:
        implement_stack_investment_tab(TECHNOLOGIES, get_stack_display_name, 
                                      stack_costs_0, technologies_capacities_0, stack_alphas)

    # Tab 2: BoP & EPC Learning Investments
    with investment_tabs[1]:
        implement_bop_epc_investment_tab(get_region_display_name, bop_epc_costs_0, 
                                        region_base_capacities, bop_epc_alphas, REGIONS)