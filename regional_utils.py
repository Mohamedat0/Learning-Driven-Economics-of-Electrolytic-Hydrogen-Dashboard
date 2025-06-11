import numpy as np
import pandas as pd
import math

def alpha_from_learning_rate(learning_rate):
    """
    Convert learning rate to alpha parameter.

    Parameters:
    -----------
    learning_rate : float
        Learning rate (% reduction per doubling)

    Returns:
    --------
    float
        Alpha parameter
    """
    # Convert percentage to decimal
    lr_decimal = learning_rate / 100
    # Calculate alpha
    alpha = math.log(1 - lr_decimal, 2)
    return alpha

def calculate_regional_capacity_growth(technology, regions, region_tech_growth_rates, base_capacities, years, base_year=2023):
    """
    Calculate capacity growth for a specific technology across all regions.

    Parameters:
    -----------
    technology : str
        Technology name (e.g., 'western_pem')
    regions : list
        List of regions (e.g., ['usa', 'eu', 'china', 'row'])
    region_tech_growth_rates : dict
        Dictionary with region keys, each containing a dict of technology growth rates
    base_capacities : dict
        Dictionary with region keys, each containing a dict of technology base capacities
    years : int
        Number of years to project
    base_year : int
        Starting year for projections

    Returns:
    --------
    dict
        Dictionary with year, total capacity, and capacity by region
    """
    # Initialize result dictionary
    data = {
        'year': list(range(base_year, base_year + years + 1)),
        'capacity': [],
        'capacity_by_region': {}
    }

    # Initialize region-specific capacities
    for region in regions:
        data['capacity_by_region'][region] = []

    # Get initial capacities for each region for this technology
    current_capacities = {}
    for region in regions:
        current_capacities[region] = base_capacities[region][technology]
        data['capacity_by_region'][region].append(current_capacities[region])

    # Calculate total initial capacity
    total_capacity = sum(current_capacities.values())
    data['capacity'].append(total_capacity)

    # Project for each year
    for year_idx in range(1, years + 1):
        # Update capacities based on growth rates
        for region in regions:
            growth_rate = region_tech_growth_rates[region][technology]
            current_capacities[region] *= (1 + growth_rate)
            data['capacity_by_region'][region].append(current_capacities[region])

        # Calculate total capacity
        total_capacity = sum(current_capacities.values())
        data['capacity'].append(total_capacity)

    return data

def generate_regional_stack_data(
    technologies,
    regions,
    costs_0,
    base_capacities,
    region_tech_growth_rates,
    alphas,
    years,
    base_year=2023
):
    """
    Generate data for stack technologies with region-specific growth rates.

    Parameters:
    -----------
    technologies : list
        List of technology names (e.g., ['western_pem', 'chinese_pem', ...])
    regions : list
        List of regions (e.g., ['usa', 'eu', 'china', 'row'])
    costs_0 : dict
        Dictionary of initial costs for each technology
    base_capacities : dict
        Dictionary with region keys, each containing a dict of technology base capacities
    region_tech_growth_rates : dict
        Dictionary with region keys, each containing a dict of technology growth rates
    alphas : dict
        Dictionary of learning parameters for each technology
    years : int
        Number of years to project
    base_year : int
        Starting year for projections

    Returns:
    --------
    dict
        Dictionary of capacity and cost data for all technologies
    """
    # Define the additional capacities to add
    additional_pem_capacity = 1100  # 1.1 GW in MW
    additional_alk_capacity = 22580  # 22.58 GW in MW
    
    # -----------------------------------------------------
    # Calculate base capacities from user inputs WITHOUT additional capacity
    # -----------------------------------------------------
    
    # Calculate base PEM capacity from user inputs
    base_x_0_pem = sum([
        sum([base_capacities[region]['western_pem'] for region in regions]),
        sum([base_capacities[region]['chinese_pem'] for region in regions])
    ])

    # Calculate base ALK capacity from user inputs
    base_x_0_alk = sum([
        sum([base_capacities[region]['western_alk'] for region in regions]),
        sum([base_capacities[region]['chinese_alk'] for region in regions])
    ])

    # Total base capacity from user inputs
    base_x_0_total = base_x_0_pem + base_x_0_alk
    
    # Calculate tech-specific base capacities from user inputs
    base_tech_capacities = {}
    for tech in technologies:
        base_tech_capacities[tech] = sum([base_capacities[region][tech] for region in regions])
    
    # -----------------------------------------------------
    # Calculate adjusted initial capacities (x_0) - WITH additional capacity 
    # for learning curve denominator
    # -----------------------------------------------------
    
    # Adjusted initial PEM capacity (user inputs + 1.1 GW)
    x_0_pem = base_x_0_pem + additional_pem_capacity
    
    # Adjusted initial ALK capacity (user inputs + 22.58 GW)
    x_0_alk = base_x_0_alk + additional_alk_capacity
    
    # Adjusted total capacity (user inputs + 1.1 GW + 22.58 GW)
    x_0_total = x_0_pem + x_0_alk
    
    # Tech-specific adjusted initial capacities
    x_0_tech = {}
    for tech in technologies:
        if tech == 'western_pem':
            x_0_tech[tech] = base_tech_capacities[tech] + additional_pem_capacity
        elif tech == 'chinese_pem':
            x_0_tech[tech] = base_tech_capacities[tech] + additional_pem_capacity
        elif tech == 'western_alk':
            x_0_tech[tech] = base_tech_capacities[tech] + additional_alk_capacity
        elif tech == 'chinese_alk':
            x_0_tech[tech] = base_tech_capacities[tech] + additional_alk_capacity
    
    # -----------------------------------------------------
    # First, calculate capacity growth based on user inputs ONLY
    # -----------------------------------------------------
    
    # Calculate capacities for each technology across regions using original base capacities
    capacity_data_base = {}
    for tech in technologies:
        capacity_data_base[tech] = calculate_regional_capacity_growth(
            tech, regions, region_tech_growth_rates, base_capacities, years, base_year
        )
    
    # -----------------------------------------------------
    # Now, add the additional capacity to each year's values without affecting growth rates
    # -----------------------------------------------------
    
    capacity_data = {}
    for tech in technologies:
        # Start with the base capacity data (from user inputs)
        capacity_data[tech] = {
            'year': capacity_data_base[tech]['year'],
            'capacity': [],
            'capacity_by_region': {}
        }
        
        # For each region, set up capacity tracking
        for region in regions:
            capacity_data[tech]['capacity_by_region'][region] = []
        
        # Handle the additional capacity for each year
        for year_idx in range(years + 1):
            total_year_capacity = 0
            
            # Process each region
            for region in regions:
                # Get base capacity for this region/tech/year
                region_base_capacity = capacity_data_base[tech]['capacity_by_region'][region][year_idx]
                
                # Add the appropriate additional capacity for each technology
                if tech == 'western_pem':
                    adjusted_capacity = region_base_capacity + (additional_pem_capacity if region == 'usa' else 0)
                elif tech == 'chinese_pem':
                    adjusted_capacity = region_base_capacity + (additional_pem_capacity if region == 'usa' else 0)
                elif tech == 'western_alk':
                    adjusted_capacity = region_base_capacity + (additional_alk_capacity if region == 'usa' else 0)
                elif tech == 'chinese_alk':
                    adjusted_capacity = region_base_capacity + (additional_alk_capacity if region == 'usa' else 0)
                else:
                    adjusted_capacity = region_base_capacity
                    
                # Add to the adjusted capacity data
                capacity_data[tech]['capacity_by_region'][region].append(adjusted_capacity)
                total_year_capacity += adjusted_capacity
            
            # Store total capacity for this year
            capacity_data[tech]['capacity'].append(total_year_capacity)

    # Initialize result dictionary for all learning models
    results = {
        'shared': {},
        'first_layer': {},
        'second_layer': {}
    }

    # Create dataframes for each technology and learning model
    for tech in technologies:
        # Initialize cost arrays with the same length as year array
        years_count = len(capacity_data[tech]['year'])
        shared_costs = [costs_0[tech]] * years_count  # Start with initial cost for all years
        first_layer_costs = [costs_0[tech]] * years_count
        second_layer_costs = [costs_0[tech]] * years_count
        
        # Create DataFrames with equal length arrays
        df_shared = pd.DataFrame({
            'year': capacity_data[tech]['year'],
            'capacity': capacity_data[tech]['capacity'],
            'cost': shared_costs
        })
        
        df_first = pd.DataFrame({
            'year': capacity_data[tech]['year'],
            'capacity': capacity_data[tech]['capacity'],
            'cost': first_layer_costs
        })
        
        df_second = pd.DataFrame({
            'year': capacity_data[tech]['year'],
            'capacity': capacity_data[tech]['capacity'],
            'cost': second_layer_costs
        })
        
        # Calculate costs for year 0 (base year) and all subsequent years
        for year_idx in range(0, years + 1):
            if year_idx == 0:
                # For year 0 (base year), the cost should exactly match the user input
                df_shared.loc[year_idx, 'cost'] = costs_0[tech]
                df_first.loc[year_idx, 'cost'] = costs_0[tech]
                df_second.loc[year_idx, 'cost'] = costs_0[tech]
            else:
                # Get raw capacity without additional capacity for this technology and year 
                raw_x_tech = capacity_data_base[tech]['capacity'][year_idx]
                
                # Get capacity with additional capacity for this technology and year
                x_tech = capacity_data[tech]['capacity'][year_idx]
                
                # Shared learning model calculations
                # Sum of all technology raw capacities for this year - no additional capacity
                raw_x_total = sum([capacity_data_base[t]['capacity'][year_idx] for t in technologies])
                
                # Add the additional capacities (1.1 GW + 22.58 GW) to match x_0_total's definition
                x_total = raw_x_total + additional_pem_capacity + additional_alk_capacity
                
                # C_tech = C_0_tech * (x_total/x_0_total)^alpha
                # Where both numerator and denominator include the additional capacities
                shared_cost = costs_0[tech] * (x_total / x_0_total) ** alphas[tech]
                df_shared.loc[year_idx, 'cost'] = shared_cost
                
                # First-layer fragmented model calculations
                if tech in ['western_pem', 'chinese_pem']:
                    # Sum of raw PEM technologies for this year
                    raw_x_pem = capacity_data_base['western_pem']['capacity'][year_idx] + capacity_data_base['chinese_pem']['capacity'][year_idx]
                    
                    # Add additional PEM capacity to match x_0_pem's definition
                    x_pem = raw_x_pem + additional_pem_capacity
                    
                    # C_PEM = C_0_PEM * (x_pem/x_0_pem)^alpha
                    # Where both numerator and denominator include the additional PEM capacity
                    first_cost = costs_0[tech] * (x_pem / x_0_pem) ** alphas[tech]
                else:
                    # Sum of raw ALK technologies for this year
                    raw_x_alk = capacity_data_base['western_alk']['capacity'][year_idx] + capacity_data_base['chinese_alk']['capacity'][year_idx]
                    
                    # Add additional ALK capacity to match x_0_alk's definition
                    x_alk = raw_x_alk + additional_alk_capacity
                    
                    # C_ALK = C_0_ALK * (x_alk/x_0_alk)^alpha
                    # Where both numerator and denominator include the additional ALK capacity
                    first_cost = costs_0[tech] * (x_alk / x_0_alk) ** alphas[tech]
                df_first.loc[year_idx, 'cost'] = first_cost
                
                # Second-layer fragmented model calculations
                # Get raw technology-specific capacity
                raw_tech_capacity = capacity_data_base[tech]['capacity'][year_idx]
                
                # Add appropriate additional capacity based on technology type
                if tech in ['western_pem', 'chinese_pem']:
                    tech_capacity = raw_tech_capacity + additional_pem_capacity
                else:  # ALK technologies
                    tech_capacity = raw_tech_capacity + additional_alk_capacity
                
                # C_tech = C_0_tech * (tech_capacity/x_0_tech)^alpha
                # Where both numerator and denominator include the appropriate additional capacity
                second_cost = costs_0[tech] * (tech_capacity / x_0_tech[tech]) ** alphas[tech]
                df_second.loc[year_idx, 'cost'] = second_cost
        
        # Store the dataframes in the results dictionary
        results['shared'][tech] = df_shared
        results['first_layer'][tech] = df_first
        results['second_layer'][tech] = df_second

    return results

def generate_regional_bop_epc_data(
    regions,
    technologies,
    costs_0_pem,
    costs_0_alk,
    base_capacities,
    region_tech_growth_rates,
    alphas_pem,
    alphas_alk,
    years,
    base_year=2023
):
    """
    Generate data for BoP & EPC costs with region-specific growth rates.

    Parameters:
    -----------
    regions : list
        List of regions (e.g., ['usa', 'eu', 'china', 'row'])
    technologies : list
        List of technology names (e.g., ['western_pem', 'chinese_pem', ...])
    costs_0 : dict
        Dictionary of initial costs for each region
    base_capacities : dict
        Dictionary with region keys, each containing a dict of technology base capacities
    region_tech_growth_rates : dict
        Dictionary with region keys, each containing a dict of technology growth rates
    alphas : dict
        Dictionary of learning parameters for each region
    years : int
        Number of years to project
    base_year : int
        Starting year for projections

    Returns:
    --------
    dict
        Dictionary of capacity and cost data for all regions
    """
    # BoP & EPC calculations should use only actual user-input capacities
    # No additional baseline capacities for BoP & EPC learning curves
    # Calculate regional capacities
    regional_capacities = {}

    for region in regions:
        # Calculate total capacity growth for the region considering all technologies
        regional_capacities[region] = {
            'year': list(range(base_year, base_year + years + 1)),
            'capacity': [],
            'capacity_by_tech': {}
        }

        # Initialize with base capacities
        total_capacity = 0
        for tech in technologies:
            regional_capacities[region]['capacity_by_tech'][tech] = [base_capacities[region][tech]]
            total_capacity += base_capacities[region][tech]

        regional_capacities[region]['capacity'].append(total_capacity)

        # Project for each year
        for year_idx in range(1, years + 1):
            year_capacity = 0

            # Update capacities based on growth rates for each technology
            for tech in technologies:
                prev_capacity = regional_capacities[region]['capacity_by_tech'][tech][-1]
                growth_rate = region_tech_growth_rates[region][tech]
                new_capacity = prev_capacity * (1 + growth_rate)
                regional_capacities[region]['capacity_by_tech'][tech].append(new_capacity)
                year_capacity += new_capacity

            # Add the total regional capacity for this year
            regional_capacities[region]['capacity'].append(year_capacity)

    # Calculate total initial capacity across all regions (only user inputs)
    x_0_total = sum([regional_capacities[region]['capacity'][0] for region in regions])

    # Initialize result dictionary
    results = {
        'local': {},
        'global': {}
    }

    # For each region, create separate entries for PEM and ALK
    for region in regions:
        year_range = list(range(base_year, base_year + years + 1))
        
        # Calculate PEM and ALK capacities for this region
        pem_capacities = []
        alk_capacities = []
        
        for year_idx in range(years + 1):
            # PEM capacity (western + chinese PEM)
            pem_cap = 0
            if 'western_pem' in regional_capacities[region]['capacity_by_tech']:
                pem_cap += regional_capacities[region]['capacity_by_tech']['western_pem'][year_idx]
            if 'chinese_pem' in regional_capacities[region]['capacity_by_tech']:
                pem_cap += regional_capacities[region]['capacity_by_tech']['chinese_pem'][year_idx]
            pem_capacities.append(pem_cap)
            
            # ALK capacity (western + chinese ALK)
            alk_cap = 0
            if 'western_alk' in regional_capacities[region]['capacity_by_tech']:
                alk_cap += regional_capacities[region]['capacity_by_tech']['western_alk'][year_idx]
            if 'chinese_alk' in regional_capacities[region]['capacity_by_tech']:
                alk_cap += regional_capacities[region]['capacity_by_tech']['chinese_alk'][year_idx]
            alk_capacities.append(alk_cap)

        results['local'][f"{region}_pem"] = {
            'year': year_range,
            'capacity': pem_capacities,
            'cost': [costs_0_pem[region]] * (years + 1)
        }
        results['local'][f"{region}_alk"] = {
            'year': year_range,
            'capacity': alk_capacities,
            'cost': [costs_0_alk[region]] * (years + 1)
        }
        results['global'][f"{region}_pem"] = {
            'year': year_range,
            'capacity': pem_capacities.copy(),
            'cost': [costs_0_pem[region]] * (years + 1)
        }
        results['global'][f"{region}_alk"] = {
            'year': year_range,
            'capacity': alk_capacities.copy(),
            'cost': [costs_0_alk[region]] * (years + 1)
        }


    # For each region, calculate costs under different learning models
    for region in regions:
        # Initialize cost arrays
        local_costs_pem = [costs_0_pem[region]] * (years + 1)
        local_costs_alk = [costs_0_alk[region]] * (years + 1)
        global_costs_pem = [costs_0_pem[region]] * (years + 1)
        global_costs_alk = [costs_0_alk[region]] * (years + 1)
        #This part needs to be updated to handle PEM and ALK separately.
        # Calculate costs for each year including base year
        for year_idx in range(0, years + 1):
            if year_idx == 0:
                # For year 0 (base year), the cost should exactly match the user input
                local_costs_pem[year_idx] = costs_0_pem[region]
                local_costs_alk[year_idx] = costs_0_alk[region]
                global_costs_pem[year_idx] = costs_0_pem[region]
                global_costs_alk[year_idx] = costs_0_alk[region]
            else:
                # Get regional capacities
                # First get the raw capacity values for PEM and ALK
                region_capacity_pem = regional_capacities[region]['capacity_by_tech']['western_pem'][year_idx] + regional_capacities[region]['capacity_by_tech']['chinese_pem'][year_idx] if 'western_pem' in regional_capacities[region]['capacity_by_tech'] and 'chinese_pem' in regional_capacities[region]['capacity_by_tech'] else 0
                region_capacity_alk = regional_capacities[region]['capacity_by_tech']['western_alk'][year_idx] + regional_capacities[region]['capacity_by_tech']['chinese_alk'][year_idx] if 'western_alk' in regional_capacities[region]['capacity_by_tech'] and 'chinese_alk' in regional_capacities[region]['capacity_by_tech'] else 0

                # Get initial capacities 
                region_initial_capacity_pem = regional_capacities[region]['capacity_by_tech']['western_pem'][0] + regional_capacities[region]['capacity_by_tech']['chinese_pem'][0] if 'western_pem' in regional_capacities[region]['capacity_by_tech'] and 'chinese_pem' in regional_capacities[region]['capacity_by_tech'] else 0
                region_initial_capacity_alk = regional_capacities[region]['capacity_by_tech']['western_alk'][0] + regional_capacities[region]['capacity_by_tech']['chinese_alk'][0] if 'western_alk' in regional_capacities[region]['capacity_by_tech'] and 'chinese_alk' in regional_capacities[region]['capacity_by_tech'] else 0

                # Calculate total regional capacity (PEM + ALK) using only user inputs
                region_total_capacity = region_capacity_pem + region_capacity_alk
                region_total_initial_capacity = region_initial_capacity_pem + region_initial_capacity_alk

                # Set initial capacities to 100MW to avoid division by zero
                region_total_initial_capacity = max(100, region_total_initial_capacity)

                # Store costs for later appending using single regional learning rate
                learning_factor = (region_total_capacity / region_total_initial_capacity) ** alphas_pem[region]
                local_costs_pem[year_idx] = costs_0_pem[region] * learning_factor
                local_costs_alk[year_idx] = costs_0_alk[region] * learning_factor

                # 2. Global Learning Model
                # Calculate total global capacity (PEM + ALK) for each region
                global_capacities = []
                for r in regions:
                    r_capacity_pem = regional_capacities[r]['capacity_by_tech']['western_pem'][year_idx] + regional_capacities[r]['capacity_by_tech']['chinese_pem'][year_idx] if 'western_pem' in regional_capacities[r]['capacity_by_tech'] and 'chinese_pem' in regional_capacities[r]['capacity_by_tech'] else 0
                    r_capacity_alk = regional_capacities[r]['capacity_by_tech']['western_alk'][year_idx] + regional_capacities[r]['capacity_by_tech']['chinese_alk'][year_idx] if 'western_alk' in regional_capacities[r]['capacity_by_tech'] and 'chinese_alk' in regional_capacities[r]['capacity_by_tech'] else 0
                    global_capacities.append(r_capacity_pem + r_capacity_alk)
                
                # Total global capacity using only user inputs
                total_global_capacity = sum(global_capacities)

                # Set minimum total capacity to 100MW
                x_0_total_adjusted = max(100, x_0_total)

                # Store global costs using region-specific learning rate
                global_learning_factor = (total_global_capacity / x_0_total_adjusted) ** alphas_pem[region]
                global_costs_pem[year_idx] = costs_0_pem[region] * global_learning_factor
                global_costs_alk[year_idx] = costs_0_alk[region] * global_learning_factor

    # Assign the cost arrays to results
        results['local'][f"{region}_pem"]['cost'] = local_costs_pem
        results['local'][f"{region}_alk"]['cost'] = local_costs_alk
        results['global'][f"{region}_pem"]['cost'] = global_costs_pem
        results['global'][f"{region}_alk"]['cost'] = global_costs_alk

        # Convert to DataFrames
        for model in results:
            if f"{region}_pem" in results[model]:
                results[model][f"{region}_pem"] = pd.DataFrame(results[model][f"{region}_pem"])
            if f"{region}_alk" in results[model]:
                results[model][f"{region}_alk"] = pd.DataFrame(results[model][f"{region}_alk"])

    return results