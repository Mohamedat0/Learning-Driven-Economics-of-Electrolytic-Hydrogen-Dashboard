import numpy as np
import pandas as pd

def calculate_required_capacity_stack(tech, target_cost, costs_0, capacities_0, alphas, learning_model, pem_additional_capacity=0, alk_additional_capacity=0):
    """
    Calculate the capacity required to reach a target cost for stack technologies.
    
    Parameters:
    -----------
    tech : str
        Technology name (e.g., 'western_pem')
    target_cost : float
        Target cost to achieve ($/kW)
    costs_0 : dict
        Dictionary of initial costs for each technology
    capacities_0 : dict
        Dictionary of initial capacities (MW) for each technology
    alphas : dict
        Dictionary of learning parameters for each technology
    learning_model : str
        Learning model to use ('shared', 'first_layer', or 'second_layer')
        
    Returns:
    --------
    float
        Required capacity to reach the target cost (MW)
    """
    alpha = alphas[tech]
    c_0 = costs_0[tech]
    
    # Check if target cost is achievable
    if target_cost >= c_0:
        # Return capacity based on the learning model
        if learning_model == 'shared':
            # For shared model, return sum of all technologies + additional capacities
            base_capacity = sum(capacities_0.values())
            return base_capacity + pem_additional_capacity + alk_additional_capacity
            
        elif learning_model == 'first_layer':
            # For first layer, return all of the technology type + relevant additional capacity
            if tech in ['western_pem', 'chinese_pem']:
                base_pem_capacity = capacities_0['western_pem'] + capacities_0['chinese_pem']
                return base_pem_capacity + pem_additional_capacity
            else:  # ALK technologies
                base_alk_capacity = capacities_0['western_alk'] + capacities_0['chinese_alk']
                return base_alk_capacity + alk_additional_capacity
                
        else:  # second_layer
            # For second layer, return specific technology + relevant additional capacity
            if tech in ['western_pem', 'chinese_pem']:
                return capacities_0[tech] + pem_additional_capacity
            else:  # ALK technologies
                return capacities_0[tech] + alk_additional_capacity
    
    if learning_model == 'shared':
        # For shared learning, we need the combined capacity of all technologies
        # plus the additional PEM and ALK capacities
        base_capacity = sum(capacities_0.values())
        x_0_total = base_capacity + pem_additional_capacity + alk_additional_capacity
        
        # Calculate required total capacity
        x_required_total = x_0_total * (target_cost / c_0)**(1/alpha)
        
        return x_required_total
        
    elif learning_model == 'first_layer':
        # Determine technology type (PEM or ALK) and get the appropriate capacity
        if tech in ['western_pem', 'chinese_pem']:
            tech_type = 'pem'
            base_capacity = capacities_0['western_pem'] + capacities_0['chinese_pem']
            x_0_type = base_capacity + pem_additional_capacity
        else:  # ALK technologies
            tech_type = 'alk'
            base_capacity = capacities_0['western_alk'] + capacities_0['chinese_alk']
            x_0_type = base_capacity + alk_additional_capacity
        
        # Calculate required capacity for the technology type
        x_required_type = x_0_type * (target_cost / c_0)**(1/alpha)
        
        return x_required_type
        
    else:  # second_layer
        # For second layer, we need the capacity of this specific technology
        # plus the appropriate additional capacity
        base_capacity = capacities_0[tech]
        
        if tech in ['western_pem', 'chinese_pem']:
            x_0 = base_capacity + pem_additional_capacity
        else:  # ALK technologies
            x_0 = base_capacity + alk_additional_capacity
            
        # Calculate required capacity
        x_required = x_0 * (target_cost / c_0)**(1/alpha)
        
        return x_required


def calculate_required_capacity_bop_epc(region, tech_type, target_cost, costs_0, region_capacities, alphas, learning_model, regions):
    """
    Calculate the capacity required to reach a target cost for BoP & EPC.
    
    Parameters:
    -----------
    region : str
        Region name (e.g., 'usa')
    tech_type : str
        Technology type ('pem' or 'alk')
    target_cost : float
        Target cost to achieve ($/kW)
    costs_0 : dict
        Dictionary of initial costs for each region and technology
    region_capacities : dict
        Dictionary of initial capacities (MW) for each region
    alphas : dict
        Dictionary of learning parameters for each region
    learning_model : str
        Learning model to use ('local' or 'global')
    regions : list
        List of all regions
        
    Returns:
    --------
    float
        Required capacity to reach the target cost (MW)
    """
    alpha = alphas[region]
    c_0 = costs_0[f"{region}_{tech_type}"]
    
    # Check if target cost is achievable
    if target_cost >= c_0:
        if learning_model == 'local':
            return sum(region_capacities[region].values())  # Return regional capacity for local model
        else:  # global
            return sum([sum(region_capacities[r].values()) for r in regions])  # Return global capacity for global model
    
    if learning_model == 'local':
        # Calculate total initial capacity in the region (PEM + ALK)
        x_0_region = sum(region_capacities[region].values())
        
        # Calculate required capacity for the region
        x_required_region = x_0_region * (target_cost / c_0)**(1/alpha)
        
        return x_required_region
        
    else:  # global
        # Calculate total initial capacity across all regions (PEM + ALK)
        x_0_total = sum([sum(region_capacities[r].values()) for r in regions])
        
        # Calculate required total capacity
        x_required_total = x_0_total * (target_cost / c_0)**(1/alpha)
        
        return x_required_total


def calculate_learning_investment_stack(tech, target_cost, required_capacity, costs_0, capacities_0, alphas, learning_model, pem_additional_capacity=0, alk_additional_capacity=0):
    """
    Calculate the learning investment required to reach a target cost for stack technologies.
    
    Parameters:
    -----------
    tech : str
        Technology name (e.g., 'western_pem')
    target_cost : float
        Target cost to achieve ($/kW)
    required_capacity : float
        Required capacity to reach the target cost (MW)
    costs_0 : dict
        Dictionary of initial costs for each technology
    capacities_0 : dict
        Dictionary of initial capacities (MW) for each technology
    alphas : dict
        Dictionary of learning parameters for each technology
    learning_model : str
        Learning model to use ('shared', 'first_layer', or 'second_layer')
        
    Returns:
    --------
    float
        Required learning investment to reach the target cost ($)
    """
    alpha = alphas[tech]
    c_0 = costs_0[tech]
    
    # Check if target cost is achievable
    if target_cost >= c_0:
        return 0  # No investment needed if target >= initial
    
    if learning_model == 'shared':
        # For shared learning, we need the combined capacity of all technologies
        # plus the additional PEM and ALK capacities
        base_capacity = sum(capacities_0.values())
        x_0_total = base_capacity + pem_additional_capacity + alk_additional_capacity
        
        # Calculate learning investment
        # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
        learning_investment = (1 / (1 + alpha)) * (target_cost * required_capacity - c_0 * x_0_total)
        
        return learning_investment
        
    elif learning_model == 'first_layer':
        # Determine technology type (PEM or ALK) and get the appropriate capacity
        if tech in ['western_pem', 'chinese_pem']:
            tech_type = 'pem'
            base_capacity = capacities_0['western_pem'] + capacities_0['chinese_pem']
            x_0_type = base_capacity + pem_additional_capacity
        else:  # ALK technologies
            tech_type = 'alk'
            base_capacity = capacities_0['western_alk'] + capacities_0['chinese_alk']
            x_0_type = base_capacity + alk_additional_capacity
        
        # Calculate learning investment
        # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
        learning_investment = (1 / (1 + alpha)) * (target_cost * required_capacity - c_0 * x_0_type)
        
        return learning_investment
        
    else:  # second_layer
        # For second layer, we need the capacity of this specific technology
        # plus the appropriate additional capacity
        base_capacity = capacities_0[tech]
        
        if tech in ['western_pem', 'chinese_pem']:
            x_0 = base_capacity + pem_additional_capacity
        else:  # ALK technologies
            x_0 = base_capacity + alk_additional_capacity
        
        # Calculate learning investment
        # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
        learning_investment = (1 / (1 + alpha)) * (target_cost * required_capacity - c_0 * x_0)
        
        return learning_investment


def calculate_learning_investment_bop_epc(region, tech_type, target_cost, required_capacity, costs_0, region_capacities, alphas, learning_model, regions):
    """
    Calculate the learning investment required to reach a target cost for BoP & EPC.
    
    Parameters:
    -----------
    region : str
        Region name (e.g., 'usa')
    tech_type : str
        Technology type ('pem' or 'alk')
    target_cost : float
        Target cost to achieve ($/kW)
    required_capacity : float
        Required capacity to reach the target cost (MW)
    costs_0 : dict
        Dictionary of initial costs for each region and technology
    region_capacities : dict
        Dictionary of initial capacities (MW) for each region
    alphas : dict
        Dictionary of learning parameters for each region
    learning_model : str
        Learning model to use ('local' or 'global')
    regions : list
        List of all regions
        
    Returns:
    --------
    float
        Required learning investment to reach the target cost ($)
    """
    alpha = alphas[region]
    c_0 = costs_0[f"{region}_{tech_type}"]
    
    # Check if target cost is achievable
    if target_cost >= c_0:
        return 0  # No investment needed if target >= initial
    
    if learning_model == 'local':
        # Calculate total initial capacity in the region (PEM + ALK)
        x_0_region = sum(region_capacities[region].values())
        
        # Calculate learning investment
        # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
        learning_investment = (1 / (1 + alpha)) * (target_cost * required_capacity - c_0 * x_0_region)
        
        return learning_investment
        
    else:  # global
        # Calculate total initial capacity across all regions (PEM + ALK)
        x_0_total = sum([sum(region_capacities[r].values()) for r in regions])
        
        # Calculate learning investment
        # Since alpha is negative, we use 1/(1+alpha) instead of 1/(1-alpha)
        learning_investment = (1 / (1 + alpha)) * (target_cost * required_capacity - c_0 * x_0_total)
        
        return learning_investment


def generate_target_cost_data_stack(tech, costs_0, capacities_0, alphas, cost_steps=20, min_cost_factor=0.1, learning_model='second_layer', pem_additional_capacity=0, alk_additional_capacity=0):
    """
    Generate data for a range of target costs for stack technologies.
    
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
    cost_steps : int
        Number of cost steps to generate
    min_cost_factor : float
        Minimum cost as a fraction of initial cost
    learning_model : str
        Learning model to use ('shared', 'first_layer', or 'second_layer')
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with target costs, required capacities, and learning investments
    """
    c_0 = costs_0[tech]
    
    # Generate range of target costs
    min_cost = c_0 * min_cost_factor
    target_costs = np.linspace(c_0, min_cost, cost_steps)
    
    # Calculate required capacities and learning investments for each target cost
    required_capacities = []
    learning_investments = []
    
    for target_cost in target_costs:
        req_cap = calculate_required_capacity_stack(
            tech, 
            target_cost, 
            costs_0, 
            capacities_0, 
            alphas, 
            learning_model,
            pem_additional_capacity=pem_additional_capacity,
            alk_additional_capacity=alk_additional_capacity
        )
        learn_inv = calculate_learning_investment_stack(
            tech, 
            target_cost, 
            req_cap, 
            costs_0, 
            capacities_0, 
            alphas, 
            learning_model,
            pem_additional_capacity=pem_additional_capacity,
            alk_additional_capacity=alk_additional_capacity
        )
        
        required_capacities.append(req_cap)
        learning_investments.append(learn_inv)
    
    # Create DataFrame
    df = pd.DataFrame({
        'target_cost': target_costs,
        'cost_reduction_pct': (1 - target_costs / c_0) * 100,
        'required_capacity': required_capacities,
        'learning_investment': learning_investments
    })
    
    return df


def generate_target_cost_data_bop_epc(region, tech_type, costs_0, region_capacities, alphas, regions, cost_steps=20, min_cost_factor=0.1, learning_model='local'):
    """
    Generate data for a range of target costs for BoP & EPC.
    
    Parameters:
    -----------
    region : str
        Region name (e.g., 'usa')
    tech_type : str
        Technology type ('pem' or 'alk')
    costs_0 : dict
        Dictionary of initial costs for each region and technology
    region_capacities : dict
        Dictionary of initial capacities (MW) for each region
    alphas : dict
        Dictionary of learning parameters for each region
    regions : list
        List of all regions
    cost_steps : int
        Number of cost steps to generate
    min_cost_factor : float
        Minimum cost as a fraction of initial cost
    learning_model : str
        Learning model to use ('local' or 'global')
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with target costs, required capacities, and learning investments
    """
    c_0 = costs_0[f"{region}_{tech_type}"]
    
    # Generate range of target costs
    min_cost = c_0 * min_cost_factor
    target_costs = np.linspace(c_0, min_cost, cost_steps)
    
    # Calculate required capacities and learning investments for each target cost
    required_capacities = []
    learning_investments = []
    
    for target_cost in target_costs:
        req_cap = calculate_required_capacity_bop_epc(region, tech_type, target_cost, costs_0, region_capacities, alphas, learning_model, regions)
        learn_inv = calculate_learning_investment_bop_epc(region, tech_type, target_cost, req_cap, costs_0, region_capacities, alphas, learning_model, regions)
        
        required_capacities.append(req_cap)
        learning_investments.append(learn_inv)
    
    # Create DataFrame
    df = pd.DataFrame({
        'target_cost': target_costs,
        'cost_reduction_pct': (1 - target_costs / c_0) * 100,
        'required_capacity': required_capacities,
        'learning_investment': learning_investments
    })
    
    return df