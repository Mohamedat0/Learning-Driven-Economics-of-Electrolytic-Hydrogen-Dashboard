# BoP & EPC Cost Projection Equations Breakdown

## Overview
The BoP & EPC cost projections use two learning models: **Local Learning** and **Global Learning**. Both models apply standard learning curves but differ in how they calculate cumulative capacity.

## Initial Parameters

### Base Costs (C₀)
- **PEM Technologies**: Region-specific initial costs
  - USA: $400/kW
  - EU: $420/kW  
  - China: $350/kW
  - Rest of World: $380/kW

- **ALK Technologies**: Region-specific initial costs
  - USA: $350/kW
  - EU: $370/kW
  - China: $300/kW
  - Rest of World: $330/kW

### Learning Parameters (α)
Region-specific learning parameters for both PEM and ALK:
- USA: α = 0.1 (10% learning rate)
- EU: α = 0.1 (10% learning rate)
- China: α = 0.15 (15% learning rate)
- Rest of World: α = 0.12 (12% learning rate)

### Additional Capacity Adjustments
To ensure realistic learning curves, additional baseline capacities are added:
- **Additional PEM Capacity**: 1,100 MW (1.1 GW)
- **Additional ALK Capacity**: 22,580 MW (22.58 GW)

## Learning Curve Models

### 1. Local Learning Model

**Equation:**
```
C_region,tech(t) = C₀_region,tech × (X_region,total(t) / X₀_region,total)^α_region
```

**Where:**
- `C_region,tech(t)` = Cost for region and technology at year t
- `C₀_region,tech` = Initial cost for region and technology
- `X_region,total(t)` = Total regional capacity (PEM + ALK) at year t (with additional capacity)
- `X₀_region,total` = Initial total regional capacity (with additional capacity)
- `α_region` = Learning parameter for the region

**Capacity Calculation:**
```
X_region,total(t) = [X_region,PEM(t) + X_region,ALK(t)] + Additional_Capacity
```

Where:
```
X_region,PEM(t) = X_region,western_pem(t) + X_region,chinese_pem(t)
X_region,ALK(t) = X_region,western_alk(t) + X_region,chinese_alk(t)
Additional_Capacity = 1,100 MW (PEM) + 22,580 MW (ALK) = 23,680 MW
```

### 2. Global Learning Model

**Equation:**
```
C_region,tech(t) = C₀_region,tech × (X_global,total(t) / X₀_global,total)^α_region
```

**Where:**
- `C_region,tech(t)` = Cost for region and technology at year t
- `C₀_region,tech` = Initial cost for region and technology (region-specific)
- `X_global,total(t)` = Total global capacity (all regions, PEM + ALK) at year t
- `X₀_global,total` = Initial total global capacity (all regions, with additional capacity)
- `α_region` = Learning parameter for the region (still region-specific)

**Global Capacity Calculation:**
```
X_global,total(t) = Σ[X_region,total(t)] + Additional_Capacity
                  = Σ[X_region,PEM(t) + X_region,ALK(t)] + 23,680 MW

Where the sum is over all regions: USA, EU, China, Rest of World
```

## Key Differences Between Models

| Aspect | Local Learning | Global Learning |
|--------|----------------|-----------------|
| **Capacity Source** | Regional capacity only | Global capacity (sum of all regions) |
| **Learning Parameter** | Region-specific α | Region-specific α (same as local) |
| **Initial Costs** | Region-specific C₀ | Region-specific C₀ (same as local) |
| **Cost Reduction** | From regional growth only | From global growth (benefits from all regions) |

## Implementation Details

### Growth Rate Application
Each technology in each region has its own annual growth rate:
```
X_region,tech(t) = X₀_region,tech × (1 + g_region,tech)^t
```

Where `g_region,tech` is the annual growth rate for technology in region.

### Minimum Capacity Constraint
To avoid division by zero in learning calculations:
```
X₀_total = max(100 MW, calculated_initial_capacity)
```

## Usage in LCOH Calculations

The BoP & EPC costs from these models are used in LCOH as:
```
LCOH = ((CRF × (Stack_Cost + BoP_EPC_Cost) + FOM) / Utilization_Rate + Electricity_Cost) × Efficiency
```

Where:
- `BoP_EPC_Cost` comes from either local or global learning model
- Costs are combined as: `(PEM_Cost + ALK_Cost) / 2` for mixed technology scenarios