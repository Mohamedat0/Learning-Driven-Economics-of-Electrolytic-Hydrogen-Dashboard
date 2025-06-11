import numpy as np
import pandas as pd


def calculate_crf(wacc, lifetime=20):
    """
    Calculate the Capital Recovery Factor (CRF).

    Parameters:
    -----------
    wacc : float
        Weighted Average Cost of Capital (as a decimal, e.g., 0.08 for 8%)
    lifetime : int
        Project lifetime in years

    Returns:
    --------
    float
        Capital Recovery Factor
    """
    return wacc * (1 + wacc)**lifetime / ((1 + wacc)**lifetime - 1)


def calculate_lcoh(tech_type, region, stack_data, bop_epc_data, wacc, fom, utilization_rate,
                   electricity_cost, electrolyzer_efficiency, learning_model='second_layer', bop_epc_model='local', year_index=None, fom_percentage=None):
    """
    Calculate the Levelized Cost of Hydrogen (LCOH) for a specific technology.

    LCOH formula:
    LCOH = ((CRF * CAPEX + FOM) / Utilization_rate + electricity_costs) * electrolyzer_efficiency

    Parameters:
    -----------
    tech_type : str
        Stack technology ('western_pem', 'western_alk', 'chinese_pem', 'chinese_alk')
    region : str
        Region for BoP/EPC costs ('usa', 'eu', 'china', 'row')  
    stack_data : dict
        Stack cost projections data
    bop_epc_data : dict
        BoP & EPC cost projections data
    wacc : float
        Weighted Average Cost of Capital (as a decimal)
    fom : float  
        Fixed Operations and Maintenance costs in $/kW/year
    utilization_rate : float
        Utilization rate as a decimal
    electricity_cost : float
        Electricity costs in $/kWh
    electrolyzer_efficiency : float
        Electrolyzer efficiency in kWh/kg H2
    learning_model : str
        Learning model to use ('shared', 'first_layer', or 'second_layer')
    bop_epc_model : str
        Learning model to use for BoP & EPC ('local' or 'global')
    year_index : int, optional
        Index of the year to calculate LCOH for. If None, defaults to the most recent year.

    Returns:
    --------
    float
        Levelized Cost of Hydrogen in $/kg
    """
    crf = calculate_crf(wacc)

    # Get stack and BoP costs using selected learning models
    tech_type_str = tech_type[region] if isinstance(tech_type, dict) else tech_type
    
    # Get costs for the specified year or the most recent year if not specified
    if year_index is not None:
        stack_cost = stack_data[learning_model][tech_type_str]['cost'].iloc[year_index]
        tech_base = 'pem' if 'pem' in str(tech_type_str).lower() else 'alk'
        bop_epc_key = f"{region}_{tech_base}"
        bop_cost = bop_epc_data[bop_epc_model][bop_epc_key]['cost'].iloc[year_index]
    else:
        stack_cost = stack_data[learning_model][tech_type_str]['cost'].iloc[-1]
        tech_base = 'pem' if 'pem' in str(tech_type_str).lower() else 'alk'
        bop_epc_key = f"{region}_{tech_base}"
        bop_cost = bop_epc_data[bop_epc_model][bop_epc_key]['cost'].iloc[-1]

    # Total CAPEX
    capex = stack_cost + bop_cost

    # Calculate FOM based on percentage of CAPEX if provided, otherwise use absolute value
    if fom_percentage is not None:
        actual_fom = (fom_percentage / 100.0) * capex
    else:
        actual_fom = fom

    # Calculate annual capital costs
    annual_capital_costs = crf * capex

    # Ensure utilization rate is not zero to avoid division by zero
    safe_utilization_rate = max(0.00001, utilization_rate) 

    # Calculate LCOH components
    capital_component = (crf * capex) / (8760 * safe_utilization_rate)
    fom_component = actual_fom / (8760 * safe_utilization_rate)
    total_component = (capital_component + fom_component + electricity_cost) * electrolyzer_efficiency

    return total_component, {
        'stack_cost': stack_cost,
        'bop_cost': bop_cost,
        'capex': capex,
        'capital_component': capital_component * electrolyzer_efficiency,
        'fom_component': fom_component * electrolyzer_efficiency,
        'electricity_component': electricity_cost * electrolyzer_efficiency
    }


def generate_lcoh_projections(
        stack_data,
        bop_epc_data,
        regions,
        wacc_values,
        fom_values,
        utilization_rates,
        electricity_costs,
        electrolyzer_efficiencies,
        years,
        base_year,
        learning_model='second_layer',
        selected_tech=None,
        bop_epc_model='local',
        fom_percentages=None
):
    """
    Generate LCOH projections for all regions.

    Parameters:
    -----------
    stack_data : dict
        Dictionary with stack cost projections from generate_regional_stack_data
    bop_epc_data : dict
        Dictionary with BoP & EPC cost projections from generate_regional_bop_epc_data
    regions : list
        List of regions to generate projections for
    wacc_values : dict
        Dictionary with WACC values for each region
    fom_values : dict
        Dictionary with FOM values for each region
    utilization_rates : dict
        Dictionary with utilization rates for each region
    electricity_costs : dict
        Dictionary with electricity costs for each region
    electrolyzer_efficiencies : dict
        Dictionary with electrolyzer efficiencies for each region
    years : int
        Number of years to project
    base_year : int
        Starting year for projections
    learning_model : str
        Learning model to use for stack costs ('shared', 'first_layer', or 'second_layer')
    selected_tech: str, optional
        Technology to use for calculations. If None, defaults to region-specific tech.

    Returns:
    --------
    dict
        Dictionary with DataFrames for each region containing year and LCOH values
    """
    results = {}

    # For each region, calculate LCOH projections
    for region in regions:
        # Create a DataFrame for this region
        df = pd.DataFrame({'Year': list(range(base_year, base_year + years + 1))})

        # Determine technology type and get appropriate costs
        if isinstance(selected_tech, dict):
            tech_type = selected_tech.get(region, 'chinese_alk' if region == 'china' else 'western_pem')
        else:
            tech_type = selected_tech if selected_tech else ('chinese_alk' if region == 'china' else 'western_pem')
        
        # Determine tech base (pem or alk)
        tech_base = 'alk' if 'alk' in str(tech_type).lower() else 'pem'
        bop_epc_key = f'{region}_{tech_base}'

        # Calculate LCOH and components for each year
        lcoh_results = []
        lcoh_components = []

        for idx in range(len(df)):
            # Handle selected tech type correctly based on its type
            if isinstance(selected_tech, dict):
                tech = selected_tech.get(region, 'chinese_alk' if region == 'china' else 'western_pem')
            else:
                tech = selected_tech if selected_tech else ('chinese_alk' if region == 'china' else 'western_pem')

            # Calculate LCOH for this year
            year_lcoh = calculate_lcoh(
                tech,
                region,
                stack_data,
                bop_epc_data,
                wacc_values[region],
                0,  # FOM will be calculated from percentage
                utilization_rates[region],
                electricity_costs[region],
                electrolyzer_efficiencies[region],
                learning_model=learning_model,
                bop_epc_model=bop_epc_model,
                year_index=idx,  # Pass the year index to get costs for specific year
                fom_percentage=fom_percentages[region] if fom_percentages else None
            )

            lcoh_results.append(year_lcoh[0])  # Get LCOH value
            lcoh_components.append(year_lcoh[1])  # Get components

        # Add results to DataFrame
        df['Total CAPEX ($/kW)'] = stack_data[learning_model][tech_type]['cost'] + bop_epc_data[bop_epc_model][bop_epc_key]['cost']
        df['LCOH ($/kg)'] = lcoh_results
        df['CAPEX Component ($/kg)'] = [comp['capital_component'] for comp in lcoh_components]
        df['FOM Component ($/kg)'] = [comp['fom_component'] for comp in lcoh_components]
        df['Electricity Component ($/kg)'] = [comp['electricity_component'] for comp in lcoh_components]

        results[region] = df

    return results


def generate_lcoh_sensitivity(stack_data,
                              bop_epc_data,
                              region,
                              base_wacc,
                              base_fom,
                              base_utilization_rate,
                              base_electricity_cost,
                              base_electrolyzer_efficiency,
                              target_year,
                              base_year,
                              wacc_range=(0.01, 0.15),
                              utilization_range=(0.2, 1.0),
                              electricity_range=(0.01, 0.15),
                              efficiency_range=(45, 60),
                              learning_model='second_layer',
                              stack_model='second_layer', #added parameter for stack model
                              bop_epc_model='local', #added parameter for bop epc model
                              compare_with_current=True,
                              fom_percentage=None
                              ):
    # Determine technology type based on region (function docstring follows)
    """
    Generate LCOH sensitivity analysis for a specific region and year.

    Parameters:
    -----------
    stack_data : dict
        Dictionary with stack cost projections from generate_regional_stack_data
    bop_epc_data : dict
        Dictionary with BoP & EPC cost projections from generate_regional_bop_epc_data
    region : str
        Region to analyze
    base_wacc : float
        Base WACC value as a decimal
    base_fom : float
        Base FOM value in $/kW/year
    base_utilization_rate : float
        Base utilization rate as a decimal
    base_electricity_cost : float
        Base electricity cost in $/kWh
    base_electrolyzer_efficiency : float
        Base electrolyzer efficiency in kWh/kg
    target_year : int
        Year for which to perform sensitivity analysis
    base_year : int
        Starting year of projections
    wacc_range : tuple
        Range of WACC values to test (min, max)
    utilization_range : tuple
        Range of utilization rates to test (min, max)
    electricity_range : tuple
        Range of electricity costs to test (min, max)
    efficiency_range : tuple
        Range of electrolyzer efficiencies to test (min, max)
    learning_model : str
        Learning model to use for stack costs
    tech_type: str, optional
        Technology type to use for calculations. If None, defaults to region-specific tech.

    Returns:
    --------
    dict
        Dictionary with sensitivity analysis results for each parameter
    """
    # Get appropriate stack technology for this region
    tech_type = 'chinese_alk' if region == 'china' else 'western_pem'
    
    # Use the selected technology for this region
    stack_tech = tech_type

    # Get cost values for the target year
    year_idx = target_year - base_year

    # Determine appropriate technology suffix
    tech_base = 'alk' if 'alk' in tech_type.lower() else 'pem'
    bop_epc_key = f'{region}_{tech_base}'

    stack_cost = stack_data[stack_model][stack_tech]['cost'].iloc[year_idx]
    bop_epc_cost = bop_epc_data[bop_epc_model][bop_epc_key]['cost'].iloc[year_idx]
    total_capex = stack_cost + bop_epc_cost

    # Sensitivity results
    results = {
        'wacc': {
            'parameter_values': np.linspace(wacc_range[0], wacc_range[1], 20),
            'lcoh_values': [],
            'current_lcoh_values': [] if compare_with_current else None
        },
        'utilization': {
            'parameter_values':
            np.linspace(utilization_range[0], utilization_range[1], 20),
            'lcoh_values': [],
            'current_lcoh_values': [] if compare_with_current else None
        },
        'electricity': {
            'parameter_values':
            np.linspace(electricity_range[0], electricity_range[1], 20),
            'lcoh_values': [],
            'current_lcoh_values': [] if compare_with_current else None
        },
        'efficiency': {
            'parameter_values':
            np.linspace(efficiency_range[0], efficiency_range[1], 20),
            'lcoh_values': [],
            'current_lcoh_values': [] if compare_with_current else None
        }
    }

    # Calculate LCOH sensitivity to WACC
    for wacc in results['wacc']['parameter_values']:
        # Future values (target year)
        lcoh = calculate_lcoh(
            tech_type, 
            region,
            stack_data,
            bop_epc_data,
            wacc,
            0,  # FOM will be calculated from percentage
            base_utilization_rate,
            base_electricity_cost,
            base_electrolyzer_efficiency,
            learning_model=stack_model,
            bop_epc_model=bop_epc_model,
            year_index=year_idx,  # Use the correct year index
            fom_percentage=fom_percentage
        )[0]
        results['wacc']['lcoh_values'].append(lcoh)
        
        # Current values (base year)
        if compare_with_current:
            current_lcoh = calculate_lcoh(
                tech_type, 
                region,
                stack_data,
                bop_epc_data,
                wacc,
                0,  # FOM will be calculated from percentage
                base_utilization_rate,
                base_electricity_cost,
                base_electrolyzer_efficiency,
                learning_model=stack_model,
                bop_epc_model=bop_epc_model,
                year_index=0,  # Base year
                fom_percentage=fom_percentage
            )[0]
            results['wacc']['current_lcoh_values'].append(current_lcoh)

    # Calculate LCOH sensitivity to utilization rate
    for utilization in results['utilization']['parameter_values']:
        # Future values (target year)
        lcoh = calculate_lcoh(
            tech_type,
            region, 
            stack_data,
            bop_epc_data,
            base_wacc,
            0,  # FOM will be calculated from percentage
            utilization,
            base_electricity_cost,
            base_electrolyzer_efficiency,
            learning_model=stack_model,
            bop_epc_model=bop_epc_model,
            year_index=year_idx,  # Use the correct year index
            fom_percentage=fom_percentage
        )[0]
        results['utilization']['lcoh_values'].append(lcoh)
        
        # Current values (base year)
        if compare_with_current:
            current_lcoh = calculate_lcoh(
                tech_type,
                region, 
                stack_data,
                bop_epc_data,
                base_wacc,
                0,  # FOM will be calculated from percentage
                utilization,
                base_electricity_cost,
                base_electrolyzer_efficiency,
                learning_model=stack_model,
                bop_epc_model=bop_epc_model,
                year_index=0,  # Base year
                fom_percentage=fom_percentage
            )[0]
            results['utilization']['current_lcoh_values'].append(current_lcoh)

    # Calculate LCOH sensitivity to electricity cost
    for electricity in results['electricity']['parameter_values']:
        # Future values (target year)
        lcoh = calculate_lcoh(
            tech_type,
            region,
            stack_data,
            bop_epc_data,
            base_wacc,
            0,  # FOM will be calculated from percentage
            base_utilization_rate,
            electricity,
            base_electrolyzer_efficiency,
            learning_model=stack_model,
            bop_epc_model=bop_epc_model,
            year_index=year_idx,  # Use the correct year index
            fom_percentage=fom_percentage
        )[0]
        results['electricity']['lcoh_values'].append(lcoh)
        
        # Current values (base year)
        if compare_with_current:
            current_lcoh = calculate_lcoh(
                tech_type,
                region,
                stack_data,
                bop_epc_data,
                base_wacc,
                0,  # FOM will be calculated from percentage
                base_utilization_rate,
                electricity,
                base_electrolyzer_efficiency,
                learning_model=stack_model,
                bop_epc_model=bop_epc_model,
                year_index=0,  # Base year
                fom_percentage=fom_percentage
            )[0]
            results['electricity']['current_lcoh_values'].append(current_lcoh)

    # Calculate LCOH sensitivity to electrolyzer efficiency
    for efficiency in results['efficiency']['parameter_values']:
        # Future values (target year)
        lcoh = calculate_lcoh(
            tech_type,
            region,
            stack_data,
            bop_epc_data,
            base_wacc,
            0,  # FOM will be calculated from percentage
            base_utilization_rate,
            base_electricity_cost,
            efficiency,
            learning_model=stack_model,
            bop_epc_model=bop_epc_model,
            year_index=year_idx,  # Use the correct year index
            fom_percentage=fom_percentage
        )[0]
        results['efficiency']['lcoh_values'].append(lcoh)
        
        # Current values (base year)
        if compare_with_current:
            current_lcoh = calculate_lcoh(
                tech_type,
                region,
                stack_data,
                bop_epc_data,
                base_wacc,
                0,  # FOM will be calculated from percentage
                base_utilization_rate,
                base_electricity_cost,
                efficiency,
                learning_model=stack_model,
                bop_epc_model=bop_epc_model,
                year_index=0,  # Base year
                fom_percentage=fom_percentage
            )[0]
            results['efficiency']['current_lcoh_values'].append(current_lcoh)

    return results