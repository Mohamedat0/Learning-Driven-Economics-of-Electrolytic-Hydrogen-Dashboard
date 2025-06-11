import numpy as np
import pandas as pd

def calculate_stack_learning_investment_shared(
    tech,
    costs_0,
    capacities_0,
    alphas,
    stack_data
):
    """
    Calculate the learning investment for stack technologies in the shared learning model.
    
    Formula:
    Learning_investment = 1/(1+alpha) * (C_tech*x_total - C_0_tech*x_0_total)
    
    Parameters:
    -----------
    tech : str
        Technology name (e.g., 'western_pem')
    costs_0 : dict
        Dictionary of initial costs for each technology
    capacities_0 : dict
        Dictionary of initial capacities (MW) for each technology
    alphas : dict
        Dictionary of learning parameters for each technology
    stack_data : dict
        Dictionary with stack cost and capacity projections
        
    Returns:
    --------
    dict
        Dictionary with year and learning investment values
    """
    alpha = alphas[tech]
    c_0 = costs_0[tech]
    
    # Calculate total initial capacity (x_0_total)
    x_0_total = sum(capacities_0.values())
    
    # Extract the data for the technology
    df = stack_data['shared'][tech]
    
    # Calculate learning investments for each year
    learning_investments = []
    
    for idx, row in df.iterrows():
        if idx == 0:  # Skip base year
            learning_investments.append(0)
        else:
            c_y = row['cost']
            x_y = row['capacity']
            
            # For shared learning, we need total capacity across all techs
            total_capacity_y = sum([stack_data['shared'][t].iloc[idx]['capacity'] for t in costs_0.keys()])
            
            # Calculate learning investment
            # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
            learning_inv = (1 / (1 + alpha)) * (c_y * total_capacity_y - c_0 * x_0_total)
            learning_investments.append(learning_inv)
    
    # Create result dictionary
    result = {
        'year': df['year'],
        'learning_investment': learning_investments
    }
    
    return result

def calculate_stack_learning_investment_first_layer(
    tech,
    costs_0,
    capacities_0,
    alphas,
    stack_data
):
    """
    Calculate the learning investment for stack technologies in the first-layer fragmented model.
    
    Formula depends on technology type (PEM or ALK):
    - For PEM: Learning_investment = 1/(1+alpha) * (C_tech*x_pem_total - C_0_tech*x_0_pem_total)
    - For ALK: Learning_investment = 1/(1+alpha) * (C_tech*x_alk_total - C_0_tech*x_0_alk_total)
    
    Parameters:
    -----------
    tech : str
        Technology name (e.g., 'western_pem')
    costs_0 : dict
        Dictionary of initial costs for each technology
    capacities_0 : dict
        Dictionary of initial capacities (MW) for each technology
    alphas : dict
        Dictionary of learning parameters for each technology
    stack_data : dict
        Dictionary with stack cost and capacity projections
        
    Returns:
    --------
    dict
        Dictionary with year and learning investment values
    """
    alpha = alphas[tech]
    c_0 = costs_0[tech]
    
    # Determine technology type and calculate initial capacity
    if tech in ['western_pem', 'chinese_pem']:
        tech_type = 'pem'
        x_0_type_total = capacities_0['western_pem'] + capacities_0['chinese_pem']
        related_techs = ['western_pem', 'chinese_pem']
    else:  # ALK technologies
        tech_type = 'alk'
        x_0_type_total = capacities_0['western_alk'] + capacities_0['chinese_alk']
        related_techs = ['western_alk', 'chinese_alk']
    
    # Extract the data for the technology
    df = stack_data['first_layer'][tech]
    
    # Calculate learning investments for each year
    learning_investments = []
    
    for idx, row in df.iterrows():
        if idx == 0:  # Skip base year
            learning_investments.append(0)
        else:
            c_y = row['cost']
            
            # For first-layer learning, we need total capacity of the related techs (PEM or ALK)
            type_capacity_y = sum([stack_data['first_layer'][t].iloc[idx]['capacity'] for t in related_techs])
            
            # Calculate learning investment
            # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
            learning_inv = (1 / (1 + alpha)) * (c_y * type_capacity_y - c_0 * x_0_type_total)
            learning_investments.append(learning_inv)
    
    # Create result dictionary
    result = {
        'year': df['year'],
        'learning_investment': learning_investments
    }
    
    return result

def calculate_stack_learning_investment_second_layer(
    tech,
    costs_0,
    capacities_0,
    alphas,
    stack_data
):
    """
    Calculate the learning investment for stack technologies in the second-layer fragmented model.
    
    Formula:
    Learning_investment = 1/(1+alpha) * (C_tech*x_tech - C_0_tech*x_0_tech)
    
    Parameters:
    -----------
    tech : str
        Technology name (e.g., 'western_pem')
    costs_0 : dict
        Dictionary of initial costs for each technology
    capacities_0 : dict
        Dictionary of initial capacities (MW) for each technology
    alphas : dict
        Dictionary of learning parameters for each technology
    stack_data : dict
        Dictionary with stack cost and capacity projections
        
    Returns:
    --------
    dict
        Dictionary with year and learning investment values
    """
    alpha = alphas[tech]
    c_0 = costs_0[tech]
    x_0 = capacities_0[tech]
    
    # Extract the data for the technology
    df = stack_data['second_layer'][tech]
    
    # Calculate learning investments for each year
    learning_investments = []
    
    for idx, row in df.iterrows():
        if idx == 0:  # Skip base year
            learning_investments.append(0)
        else:
            c_y = row['cost']
            x_y = row['capacity']
            
            # Calculate learning investment
            # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
            learning_inv = (1 / (1 + alpha)) * (c_y * x_y - c_0 * x_0)
            learning_investments.append(learning_inv)
    
    # Create result dictionary
    result = {
        'year': df['year'],
        'learning_investment': learning_investments
    }
    
    return result

def calculate_bop_epc_learning_investment_local_tech(
    region,
    tech_type,
    costs_0,
    regional_capacities,
    alphas,
    bop_epc_data
):
    """
    Calculate the learning investment for BoP & EPC in the local learning model for a specific technology.
    
    Formula:
    Learning_investment = 1/(1+alpha) * (C_region_tech*x_region - C_0_region_tech*x_0_region)
    
    Parameters:
    -----------
    region : str
        Region name (e.g., 'usa')
    tech_type : str
        Technology type ('pem' or 'alk')
    costs_0 : dict
        Dictionary of initial costs for each region and technology
    regional_capacities : dict
        Dictionary of initial capacities (MW) for each region
    alphas : dict
        Dictionary of learning parameters for each region
    bop_epc_data : dict
        Dictionary with BoP & EPC cost and capacity projections
        
    Returns:
    --------
    dict
        Dictionary with year and learning investment values
    """
    alpha = alphas[region]
    key = f"{region}_{tech_type}"
    
    # Extract the data for both PEM and ALK to get total capacity
    df_pem = bop_epc_data['local'][f"{region}_pem"]
    df_alk = bop_epc_data['local'][f"{region}_alk"]
    
    # Get technology-specific data
    df_tech = bop_epc_data['local'][key]
    
    # Use technology-specific costs but total capacities
    df = pd.DataFrame({
        'year': df_tech['year'],
        'cost': df_tech['cost'],
        'capacity': df_pem['capacity'] + df_alk['capacity']  # Total capacity for the region
    })
    
    # Get initial capacity and cost
    x_0 = df['capacity'].iloc[0]
    c_0 = costs_0[key]
    
    # Calculate learning investments for each year
    learning_investments = []
    
    for idx, row in df.iterrows():
        if idx == 0:  # Skip base year
            learning_investments.append(0)
        else:
            c_y = row['cost']
            x_y = row['capacity']
            
            # Calculate learning investment
            # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
            learning_inv = (1 / (1 + alpha)) * (c_y * x_y - c_0 * x_0)
            learning_investments.append(learning_inv)
    
    # Create result dictionary
    result = {
        'year': df['year'],
        'learning_investment': learning_investments
    }
    
    return result


def calculate_bop_epc_learning_investment_local(
    region,
    costs_0,
    regional_capacities,
    alphas,
    bop_epc_data
):
    """
    Calculate the learning investment for BoP & EPC in the local learning model.
    
    Formula:
    Learning_investment = 1/(1+alpha) * (C_region*x_region - C_0_region*x_0_region)
    
    Parameters:
    -----------
    region : str
        Region name (e.g., 'usa')
    costs_0 : dict
        Dictionary of initial costs for each region
    regional_capacities : dict
        Dictionary of initial capacities (MW) for each region
    alphas : dict
        Dictionary of learning parameters for each region
    bop_epc_data : dict
        Dictionary with BoP & EPC cost and capacity projections
        
    Returns:
    --------
    dict
        Dictionary with year and learning investment values
    """
    alpha = alphas[region]
    
    # Extract the data for both PEM and ALK
    df_pem = bop_epc_data['local'][f"{region}_pem"]
    df_alk = bop_epc_data['local'][f"{region}_alk"]
    
    # Use average of PEM and ALK costs and capacities
    df = pd.DataFrame({
        'year': df_pem['year'],
        'cost': (df_pem['cost'] + df_alk['cost']) / 2,
        'capacity': df_pem['capacity'] + df_alk['capacity']
    })
    
    x_0 = df['capacity'].iloc[0]
    c_0 = costs_0[region]
    
    # Calculate learning investments for each year
    learning_investments = []
    
    for idx, row in df.iterrows():
        if idx == 0:  # Skip base year
            learning_investments.append(0)
        else:
            c_y = row['cost']
            x_y = row['capacity']
            
            # Calculate learning investment
            # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
            learning_inv = (1 / (1 + alpha)) * (c_y * x_y - c_0 * x_0)
            learning_investments.append(learning_inv)
    
    # Create result dictionary
    result = {
        'year': df['year'],
        'learning_investment': learning_investments
    }
    
    return result

def calculate_bop_epc_learning_investment_global_tech(
    region,
    tech_type,
    costs_0,
    regions,
    alphas,
    bop_epc_data
):
    """
    Calculate the learning investment for BoP & EPC in the global learning model for a specific technology.
    
    Formula:
    Learning_investment = 1/(1+alpha) * (C_region_tech*x_total - C_0_region_tech*x_0_total)
    
    Parameters:
    -----------
    region : str
        Region name (e.g., 'usa')
    tech_type : str
        Technology type ('pem' or 'alk')
    costs_0 : dict
        Dictionary of initial costs for each region and technology
    regions : list
        List of all regions
    alphas : dict
        Dictionary of learning parameters for each region
    bop_epc_data : dict
        Dictionary with BoP & EPC cost and capacity projections
        
    Returns:
    --------
    dict
        Dictionary with year and learning investment values
    """
    alpha = alphas[region]
    key = f"{region}_{tech_type}"
    c_0 = costs_0[key]
    
    # Get technology-specific data
    df_tech = bop_epc_data['global'][key]
    
    # Use technology-specific costs
    df = pd.DataFrame({
        'year': df_tech['year'],
        'cost': df_tech['cost']
    })
    
    # Calculate total initial capacity (x_0_total) for all regions and both technologies
    x_0_total = sum([
        bop_epc_data['global'][f"{r}_pem"]['capacity'].iloc[0] +
        bop_epc_data['global'][f"{r}_alk"]['capacity'].iloc[0]
        for r in regions
    ])
    
    # Calculate learning investments for each year
    learning_investments = []
    
    for idx, row in df.iterrows():
        if idx == 0:  # Skip base year
            learning_investments.append(0)
        else:
            c_y = row['cost']
            
            # For global learning, we need total capacity across all regions for both PEM and ALK
            total_capacity_y = sum([
                bop_epc_data['global'][f"{r}_pem"]['capacity'].iloc[idx] +
                bop_epc_data['global'][f"{r}_alk"]['capacity'].iloc[idx]
                for r in regions
            ])
            
            # Calculate learning investment
            # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
            learning_inv = (1 / (1 + alpha)) * (c_y * total_capacity_y - c_0 * x_0_total)
            learning_investments.append(learning_inv)
    
    # Create result dictionary
    result = {
        'year': df['year'],
        'learning_investment': learning_investments
    }
    
    return result


def calculate_bop_epc_learning_investment_global(
    region,
    costs_0,
    regions,
    alphas,
    bop_epc_data
):
    """
    Calculate the learning investment for BoP & EPC in the global learning model.
    
    Formula:
    Learning_investment = 1/(1+alpha) * (C_region*x_total - C_0_region*x_0_total)
    
    Parameters:
    -----------
    region : str
        Region name (e.g., 'usa')
    costs_0 : dict
        Dictionary of initial costs for each region
    regions : list
        List of all regions
    alphas : dict
        Dictionary of learning parameters for each region
    bop_epc_data : dict
        Dictionary with BoP & EPC cost and capacity projections
        
    Returns:
    --------
    dict
        Dictionary with year and learning investment values
    """
    alpha = alphas[region]
    c_0 = costs_0[region]
    
    # Extract the data for both PEM and ALK for this region
    df_pem = bop_epc_data['global'][f"{region}_pem"]
    df_alk = bop_epc_data['global'][f"{region}_alk"]
    
    # Combine PEM and ALK data
    df = pd.DataFrame({
        'year': df_pem['year'],
        'cost': (df_pem['cost'] + df_alk['cost']) / 2,
        'capacity': df_pem['capacity'] + df_alk['capacity']
    })
    
    # Calculate total initial capacity (x_0_total)
    x_0_total = sum([
        bop_epc_data['global'][f"{r}_pem"]['capacity'].iloc[0] +
        bop_epc_data['global'][f"{r}_alk"]['capacity'].iloc[0]
        for r in regions
    ])
    
    # Calculate learning investments for each year
    learning_investments = []
    
    for idx, row in df.iterrows():
        if idx == 0:  # Skip base year
            learning_investments.append(0)
        else:
            c_y = row['cost']
            
            # For global learning, we need total capacity across all regions for both PEM and ALK
            total_capacity_y = sum([
                bop_epc_data['global'][f"{r}_pem"]['capacity'].iloc[idx] +
                bop_epc_data['global'][f"{r}_alk"]['capacity'].iloc[idx]
                for r in regions
            ])
            
            # Calculate learning investment
            # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
            learning_inv = (1 / (1 + alpha)) * (c_y * total_capacity_y - c_0 * x_0_total)
            learning_investments.append(learning_inv)
    
    # Create result dictionary
    result = {
        'year': df['year'],
        'learning_investment': learning_investments
    }
    
    return result

def generate_stack_learning_investments(
    technologies,
    costs_0,
    capacities_0,
    alphas,
    stack_data
):
    """
    Generate learning investments for all stack technologies under different learning models.
    
    Parameters:
    -----------
    technologies : list
        List of technology names
    costs_0 : dict
        Dictionary of initial costs for each technology
    capacities_0 : dict
        Dictionary of initial capacities (MW) for each technology
    alphas : dict
        Dictionary of learning parameters for each technology
    stack_data : dict
        Dictionary with stack cost and capacity projections
        
    Returns:
    --------
    dict
        Dictionary with learning investments for all technologies under different models
    """
    # Initialize result structure
    learning_investments = {
        'shared': {},
        'first_layer': {},
        'second_layer': {}
    }
    
    # Calculate learning investments for each technology under each model
    for tech in technologies:
        # Shared learning model
        learning_investments['shared'][tech] = calculate_stack_learning_investment_shared(
            tech, costs_0, capacities_0, alphas, stack_data
        )
        
        # First-layer fragmented model
        learning_investments['first_layer'][tech] = calculate_stack_learning_investment_first_layer(
            tech, costs_0, capacities_0, alphas, stack_data
        )
        
        # Second-layer fragmented model
        learning_investments['second_layer'][tech] = calculate_stack_learning_investment_second_layer(
            tech, costs_0, capacities_0, alphas, stack_data
        )
        
        # Convert to DataFrames
        for model in learning_investments:
            learning_investments[model][tech] = pd.DataFrame(learning_investments[model][tech])
    
    return learning_investments

def generate_bop_epc_learning_investments(
    regions,
    pem_costs_0,  # PEM-specific costs
    alk_costs_0,  # ALK-specific costs
    alphas,
    bop_epc_data
):
    """
    Generate learning investments for BoP & EPC for all regions under different learning models.
    
    Parameters:
    -----------
    regions : list
        List of region names
    pem_costs_0 : dict
        Dictionary of initial PEM costs for each region
    alk_costs_0 : dict
        Dictionary of initial ALK costs for each region
    alphas : dict
        Dictionary of learning parameters for each region
    bop_epc_data : dict
        Dictionary with BoP & EPC cost and capacity projections
        
    Returns:
    --------
    dict
        Dictionary with learning investments for all regions under different models
    """
    # Initialize result structure
    learning_investments = {
        'local': {},
        'global': {}
    }
    
    # Calculate learning investments for each region under each model
    for region in regions:
        # Create dictionaries with tech-specific costs
        costs_0_pem = {f"{region}_pem": pem_costs_0[region]}
        costs_0_alk = {f"{region}_alk": alk_costs_0[region]}
        
        # Local learning model for PEM
        learning_investments_pem_local = calculate_bop_epc_learning_investment_local_tech(
            region, 'pem', costs_0_pem, {}, alphas, bop_epc_data
        )
        
        # Local learning model for ALK
        learning_investments_alk_local = calculate_bop_epc_learning_investment_local_tech(
            region, 'alk', costs_0_alk, {}, alphas, bop_epc_data
        )
        
        # Global learning model for PEM
        learning_investments_pem_global = calculate_bop_epc_learning_investment_global_tech(
            region, 'pem', costs_0_pem, regions, alphas, bop_epc_data
        )
        
        # Global learning model for ALK
        learning_investments_alk_global = calculate_bop_epc_learning_investment_global_tech(
            region, 'alk', costs_0_alk, regions, alphas, bop_epc_data
        )
        
        # Average the investments for the region (to maintain compatibility)
        # First convert to DataFrames
        df_pem_local = pd.DataFrame(learning_investments_pem_local)
        df_alk_local = pd.DataFrame(learning_investments_alk_local)
        df_pem_global = pd.DataFrame(learning_investments_pem_global)
        df_alk_global = pd.DataFrame(learning_investments_alk_global)
        
        # Then create averaged DataFrames
        df_local = pd.DataFrame({
            'year': df_pem_local['year'],
            'learning_investment': (df_pem_local['learning_investment'] + df_alk_local['learning_investment']) / 2
        })
        
        df_global = pd.DataFrame({
            'year': df_pem_global['year'],
            'learning_investment': (df_pem_global['learning_investment'] + df_alk_global['learning_investment']) / 2
        })
        
        learning_investments['local'][region] = df_local
        learning_investments['global'][region] = df_global
    
    return learning_investments