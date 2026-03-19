from __future__ import annotations

"""PhD-thesis level example: multi-echelon stochastic network design with CVaR."""

from typing import Dict

try:
    import gurobipy as gp
    from gurobipy import GRB
except ModuleNotFoundError as exc:
    raise SystemExit(
        "This example requires Python + gurobipy. "
        "Install Python, install gurobipy, and make sure a Gurobi license is available."
    ) from exc


TOL = 1e-6


def compute_cvar(probability: Dict[str, float], scenario_costs: Dict[str, float], alpha: float) -> Dict[str, object]:
    candidate_etas = sorted({0.0, *scenario_costs.values()})
    best = None
    coefficient = 1.0 / (1.0 - alpha)

    for eta in candidate_etas:
        xi = {scenario: max(scenario_costs[scenario] - eta, 0.0) for scenario in scenario_costs}
        cvar_value = eta + coefficient * sum(probability[scenario] * xi[scenario] for scenario in scenario_costs)
        if best is None or cvar_value < best["cvar_value"] - TOL:
            best = {"eta": eta, "xi": xi, "cvar_value": cvar_value}

    return best


def build_data() -> Dict[str, object]:
    suppliers = ["S1", "S2"]
    plants = ["PL1", "PL2", "PL3"]
    dcs = ["D1", "D2", "D3"]
    customers = ["C1", "C2", "C3", "C4"]
    products = ["G1", "G2"]
    periods = [1, 2, 3]
    scenarios = ["Baseline", "Expansion", "Stress"]

    probability = {
        "Baseline": 0.45,
        "Expansion": 0.25,
        "Stress": 0.30,
    }

    demand_factor = {
        "Baseline": 1.00,
        "Expansion": 1.15,
        "Stress": 1.30,
    }

    supply_factor = {
        "Baseline": 1.00,
        "Expansion": 1.05,
        "Stress": 0.85,
    }

    carbon_cap = {
        "Baseline": 100.0,
        "Expansion": 110.0,
        "Stress": 95.0,
    }

    fixed_plant_open_cost = {
        "PL1": 320,
        "PL2": 300,
        "PL3": 340,
    }

    fixed_dc_open_cost = {
        "D1": 180,
        "D2": 170,
        "D3": 175,
    }

    plant_module_cost = {
        "PL1": 95,
        "PL2": 90,
        "PL3": 100,
    }

    dc_module_cost = {
        "D1": 60,
        "D2": 58,
        "D3": 62,
    }

    max_plant_modules = {
        "PL1": 2,
        "PL2": 2,
        "PL3": 2,
    }

    max_dc_modules = {
        "D1": 2,
        "D2": 2,
        "D3": 2,
    }

    base_plant_capacity = {
        ("PL1", 1): 85,
        ("PL1", 2): 90,
        ("PL1", 3): 95,
        ("PL2", 1): 80,
        ("PL2", 2): 85,
        ("PL2", 3): 90,
        ("PL3", 1): 90,
        ("PL3", 2): 95,
        ("PL3", 3): 100,
    }

    plant_module_capacity = {
        "PL1": 30,
        "PL2": 28,
        "PL3": 32,
    }

    base_dc_throughput = {
        ("D1", 1): 100,
        ("D1", 2): 105,
        ("D1", 3): 110,
        ("D2", 1): 95,
        ("D2", 2): 100,
        ("D2", 3): 105,
        ("D3", 1): 90,
        ("D3", 2): 95,
        ("D3", 3): 100,
    }

    dc_module_throughput = {
        "D1": 25,
        "D2": 24,
        "D3": 26,
    }

    base_dc_storage = {
        ("D1", 1): 45,
        ("D1", 2): 48,
        ("D1", 3): 50,
        ("D2", 1): 42,
        ("D2", 2): 44,
        ("D2", 3): 46,
        ("D3", 1): 40,
        ("D3", 2): 42,
        ("D3", 3): 44,
    }

    dc_module_storage = {
        "D1": 15,
        "D2": 14,
        "D3": 15,
    }

    processing_time = {
        "G1": 1.00,
        "G2": 1.10,
    }

    base_supplier_capacity = {
        ("S1", "G1", 1): 70,
        ("S1", "G1", 2): 72,
        ("S1", "G1", 3): 75,
        ("S1", "G2", 1): 55,
        ("S1", "G2", 2): 58,
        ("S1", "G2", 3): 60,
        ("S2", "G1", 1): 65,
        ("S2", "G1", 2): 68,
        ("S2", "G1", 3): 70,
        ("S2", "G2", 1): 50,
        ("S2", "G2", 2): 52,
        ("S2", "G2", 3): 55,
    }

    purchase_base = {
        ("S1", "PL1"): 2.4,
        ("S1", "PL2"): 2.7,
        ("S1", "PL3"): 2.9,
        ("S2", "PL1"): 2.6,
        ("S2", "PL2"): 2.5,
        ("S2", "PL3"): 2.8,
    }

    plant_dc_base = {
        ("PL1", "D1"): 1.8,
        ("PL1", "D2"): 2.4,
        ("PL1", "D3"): 3.0,
        ("PL2", "D1"): 2.5,
        ("PL2", "D2"): 1.9,
        ("PL2", "D3"): 2.3,
        ("PL3", "D1"): 3.0,
        ("PL3", "D2"): 2.4,
        ("PL3", "D3"): 1.8,
    }

    dc_customer_base = {
        ("D1", "C1"): 2.0,
        ("D1", "C2"): 2.6,
        ("D1", "C3"): 3.1,
        ("D1", "C4"): 3.4,
        ("D2", "C1"): 2.8,
        ("D2", "C2"): 2.0,
        ("D2", "C3"): 2.5,
        ("D2", "C4"): 2.9,
        ("D3", "C1"): 3.3,
        ("D3", "C2"): 2.7,
        ("D3", "C3"): 2.0,
        ("D3", "C4"): 2.3,
    }

    product_purchase_premium = {"G1": 0.0, "G2": 0.5}
    product_ship_premium = {"G1": 0.0, "G2": 0.2}

    purchase_cost = {
        (supplier, plant, product): purchase_base[supplier, plant] + product_purchase_premium[product]
        for supplier in suppliers
        for plant in plants
        for product in products
    }

    production_cost = {
        ("PL1", "G1"): 1.9,
        ("PL1", "G2"): 2.3,
        ("PL2", "G1"): 1.8,
        ("PL2", "G2"): 2.2,
        ("PL3", "G1"): 2.0,
        ("PL3", "G2"): 2.4,
    }

    plant_dc_cost = {
        (plant, dc, product): plant_dc_base[plant, dc] + product_ship_premium[product]
        for plant in plants
        for dc in dcs
        for product in products
    }

    dc_customer_cost = {
        (dc, customer, product): dc_customer_base[dc, customer] + product_ship_premium[product]
        for dc in dcs
        for customer in customers
        for product in products
    }

    plant_holding_cost = {
        ("PL1", "G1"): 0.35,
        ("PL1", "G2"): 0.45,
        ("PL2", "G1"): 0.33,
        ("PL2", "G2"): 0.42,
        ("PL3", "G1"): 0.37,
        ("PL3", "G2"): 0.47,
    }

    dc_holding_cost = {
        ("D1", "G1"): 0.40,
        ("D1", "G2"): 0.50,
        ("D2", "G1"): 0.38,
        ("D2", "G2"): 0.48,
        ("D3", "G1"): 0.39,
        ("D3", "G2"): 0.49,
    }

    backlog_penalty = {
        "G1": 36.0,
        "G2": 42.0,
    }

    base_demand = {
        ("C1", "G1", 1): 9,
        ("C1", "G1", 2): 10,
        ("C1", "G1", 3): 11,
        ("C1", "G2", 1): 6,
        ("C1", "G2", 2): 7,
        ("C1", "G2", 3): 7,
        ("C2", "G1", 1): 10,
        ("C2", "G1", 2): 11,
        ("C2", "G1", 3): 12,
        ("C2", "G2", 1): 7,
        ("C2", "G2", 2): 8,
        ("C2", "G2", 3): 8,
        ("C3", "G1", 1): 8,
        ("C3", "G1", 2): 9,
        ("C3", "G1", 3): 10,
        ("C3", "G2", 1): 5,
        ("C3", "G2", 2): 6,
        ("C3", "G2", 3): 6,
        ("C4", "G1", 1): 9,
        ("C4", "G1", 2): 10,
        ("C4", "G1", 3): 11,
        ("C4", "G2", 1): 6,
        ("C4", "G2", 2): 7,
        ("C4", "G2", 3): 7,
    }

    buy_emission = {
        (supplier, plant, product): (0.30 if supplier == "S1" else 0.34) + (0.04 if product == "G2" else 0.0)
        for supplier in suppliers
        for plant in plants
        for product in products
    }

    plant_dc_emission = {
        (plant, dc, product): 0.10 + 0.03 * list(plants).index(plant) + 0.02 * list(dcs).index(dc) + (0.02 if product == "G2" else 0.0)
        for plant in plants
        for dc in dcs
        for product in products
    }

    dc_customer_emission = {
        (dc, customer, product): 0.08 + 0.015 * list(dcs).index(dc) + 0.012 * list(customers).index(customer) + (0.02 if product == "G2" else 0.0)
        for dc in dcs
        for customer in customers
        for product in products
    }

    demand = {}
    supplier_capacity = {}
    for scenario in scenarios:
        for customer in customers:
            for product in products:
                for period in periods:
                    demand[scenario, customer, product, period] = int(
                        round(base_demand[customer, product, period] * demand_factor[scenario])
                    )
        for supplier in suppliers:
            for product in products:
                for period in periods:
                    supplier_capacity[scenario, supplier, product, period] = (
                        base_supplier_capacity[supplier, product, period] * supply_factor[scenario]
                    )

    return {
        "suppliers": suppliers,
        "plants": plants,
        "dcs": dcs,
        "customers": customers,
        "products": products,
        "periods": periods,
        "scenarios": scenarios,
        "probability": probability,
        "fixed_plant_open_cost": fixed_plant_open_cost,
        "fixed_dc_open_cost": fixed_dc_open_cost,
        "plant_module_cost": plant_module_cost,
        "dc_module_cost": dc_module_cost,
        "max_plant_modules": max_plant_modules,
        "max_dc_modules": max_dc_modules,
        "base_plant_capacity": base_plant_capacity,
        "plant_module_capacity": plant_module_capacity,
        "base_dc_throughput": base_dc_throughput,
        "dc_module_throughput": dc_module_throughput,
        "base_dc_storage": base_dc_storage,
        "dc_module_storage": dc_module_storage,
        "processing_time": processing_time,
        "supplier_capacity": supplier_capacity,
        "purchase_cost": purchase_cost,
        "production_cost": production_cost,
        "plant_dc_cost": plant_dc_cost,
        "dc_customer_cost": dc_customer_cost,
        "plant_holding_cost": plant_holding_cost,
        "dc_holding_cost": dc_holding_cost,
        "backlog_penalty": backlog_penalty,
        "demand": demand,
        "buy_emission": buy_emission,
        "plant_dc_emission": plant_dc_emission,
        "dc_customer_emission": dc_customer_emission,
        "carbon_cap": carbon_cap,
        "risk_alpha": 0.80,
        "risk_weight": 0.40,
        "carbon_excess_penalty": 9.0,
    }


def solve_scenario_subproblem(
    data: Dict[str, object],
    open_plant_solution: Dict[str, int],
    open_dc_solution: Dict[str, int],
    plant_modules_solution: Dict[str, int],
    dc_modules_solution: Dict[str, int],
    scenario: str,
) -> Dict[str, object]:
    suppliers = data["suppliers"]
    plants = data["plants"]
    dcs = data["dcs"]
    customers = data["customers"]
    products = data["products"]
    periods = data["periods"]
    processing_time = data["processing_time"]
    supplier_capacity = data["supplier_capacity"]
    base_plant_capacity = data["base_plant_capacity"]
    plant_module_capacity = data["plant_module_capacity"]
    base_dc_throughput = data["base_dc_throughput"]
    dc_module_throughput = data["dc_module_throughput"]
    base_dc_storage = data["base_dc_storage"]
    dc_module_storage = data["dc_module_storage"]
    purchase_cost = data["purchase_cost"]
    production_cost = data["production_cost"]
    plant_dc_cost = data["plant_dc_cost"]
    dc_customer_cost = data["dc_customer_cost"]
    plant_holding_cost = data["plant_holding_cost"]
    dc_holding_cost = data["dc_holding_cost"]
    backlog_penalty = data["backlog_penalty"]
    demand = data["demand"]
    buy_emission = data["buy_emission"]
    plant_dc_emission = data["plant_dc_emission"]
    dc_customer_emission = data["dc_customer_emission"]
    carbon_cap = data["carbon_cap"]
    carbon_excess_penalty = data["carbon_excess_penalty"]

    sp = gp.Model(f"phd_subproblem_{scenario}")
    sp.Params.OutputFlag = 0

    buy = sp.addVars(suppliers, plants, products, periods, lb=0.0, name="buy")
    flow_pd = sp.addVars(plants, dcs, products, periods, lb=0.0, name="flow_pd")
    plant_inv = sp.addVars(plants, products, periods, lb=0.0, name="plant_inv")
    flow_dc = sp.addVars(dcs, customers, products, periods, lb=0.0, name="flow_dc")
    dc_inv = sp.addVars(dcs, products, periods, lb=0.0, name="dc_inv")
    backlog = sp.addVars(customers, products, periods, lb=0.0, name="backlog")
    carbon_excess = sp.addVar(lb=0.0, name="carbon_excess")

    supplier_con = {}
    plant_cap_con = {}
    dc_throughput_con = {}
    dc_storage_con = {}
    demand_con = {}

    for supplier in suppliers:
        for product in products:
            for period in periods:
                supplier_con[supplier, product, period] = sp.addConstr(
                    gp.quicksum(buy[supplier, plant, product, period] for plant in plants)
                    <= supplier_capacity[scenario, supplier, product, period],
                    name=f"supplier_cap_{supplier}_{product}_{period}",
                )

    for plant in plants:
        for period in periods:
            plant_cap_con[plant, period] = sp.addConstr(
                gp.quicksum(
                    processing_time[product] * buy[supplier, plant, product, period]
                    for supplier in suppliers
                    for product in products
                )
                <= base_plant_capacity[plant, period] * open_plant_solution[plant]
                + plant_module_capacity[plant] * plant_modules_solution[plant],
                name=f"plant_cap_{plant}_{period}",
            )

    for plant in plants:
        for product in products:
            for period in periods:
                if period == periods[0]:
                    sp.addConstr(
                        gp.quicksum(buy[supplier, plant, product, period] for supplier in suppliers)
                        - gp.quicksum(flow_pd[plant, dc, product, period] for dc in dcs)
                        - plant_inv[plant, product, period]
                        == 0.0,
                        name=f"plant_balance_{plant}_{product}_{period}",
                    )
                else:
                    sp.addConstr(
                        plant_inv[plant, product, period - 1]
                        + gp.quicksum(buy[supplier, plant, product, period] for supplier in suppliers)
                        - gp.quicksum(flow_pd[plant, dc, product, period] for dc in dcs)
                        - plant_inv[plant, product, period]
                        == 0.0,
                        name=f"plant_balance_{plant}_{product}_{period}",
                    )

    for dc in dcs:
        for period in periods:
            dc_throughput_con[dc, period] = sp.addConstr(
                gp.quicksum(flow_dc[dc, customer, product, period] for customer in customers for product in products)
                <= base_dc_throughput[dc, period] * open_dc_solution[dc]
                + dc_module_throughput[dc] * dc_modules_solution[dc],
                name=f"dc_throughput_{dc}_{period}",
            )
            dc_storage_con[dc, period] = sp.addConstr(
                gp.quicksum(dc_inv[dc, product, period] for product in products)
                <= base_dc_storage[dc, period] * open_dc_solution[dc]
                + dc_module_storage[dc] * dc_modules_solution[dc],
                name=f"dc_storage_{dc}_{period}",
            )

    for dc in dcs:
        for product in products:
            for period in periods:
                if period == periods[0]:
                    sp.addConstr(
                        gp.quicksum(flow_pd[plant, dc, product, period] for plant in plants)
                        - gp.quicksum(flow_dc[dc, customer, product, period] for customer in customers)
                        - dc_inv[dc, product, period]
                        == 0.0,
                        name=f"dc_balance_{dc}_{product}_{period}",
                    )
                else:
                    sp.addConstr(
                        dc_inv[dc, product, period - 1]
                        + gp.quicksum(flow_pd[plant, dc, product, period] for plant in plants)
                        - gp.quicksum(flow_dc[dc, customer, product, period] for customer in customers)
                        - dc_inv[dc, product, period]
                        == 0.0,
                        name=f"dc_balance_{dc}_{product}_{period}",
                    )

    for customer in customers:
        for product in products:
            for period in periods:
                if period == periods[0]:
                    demand_con[customer, product, period] = sp.addConstr(
                        gp.quicksum(flow_dc[dc, customer, product, period] for dc in dcs)
                        + backlog[customer, product, period]
                        == demand[scenario, customer, product, period],
                        name=f"demand_{customer}_{product}_{period}",
                    )
                else:
                    demand_con[customer, product, period] = sp.addConstr(
                        gp.quicksum(flow_dc[dc, customer, product, period] for dc in dcs)
                        + backlog[customer, product, period]
                        - backlog[customer, product, period - 1]
                        == demand[scenario, customer, product, period],
                        name=f"demand_{customer}_{product}_{period}",
                    )

    carbon_expr = (
        gp.quicksum(
            buy_emission[supplier, plant, product] * buy[supplier, plant, product, period]
            for supplier in suppliers
            for plant in plants
            for product in products
            for period in periods
        )
        + gp.quicksum(
            plant_dc_emission[plant, dc, product] * flow_pd[plant, dc, product, period]
            for plant in plants
            for dc in dcs
            for product in products
            for period in periods
        )
        + gp.quicksum(
            dc_customer_emission[dc, customer, product] * flow_dc[dc, customer, product, period]
            for dc in dcs
            for customer in customers
            for product in products
            for period in periods
        )
    )

    carbon_con = sp.addConstr(
        carbon_expr - carbon_excess <= carbon_cap[scenario],
        name=f"carbon_{scenario}",
    )

    sp.setObjective(
        gp.quicksum(
            (purchase_cost[supplier, plant, product] + production_cost[plant, product]) * buy[supplier, plant, product, period]
            for supplier in suppliers
            for plant in plants
            for product in products
            for period in periods
        )
        + gp.quicksum(
            plant_dc_cost[plant, dc, product] * flow_pd[plant, dc, product, period]
            for plant in plants
            for dc in dcs
            for product in products
            for period in periods
        )
        + gp.quicksum(
            dc_customer_cost[dc, customer, product] * flow_dc[dc, customer, product, period]
            for dc in dcs
            for customer in customers
            for product in products
            for period in periods
        )
        + gp.quicksum(
            plant_holding_cost[plant, product] * plant_inv[plant, product, period]
            for plant in plants
            for product in products
            for period in periods
        )
        + gp.quicksum(
            dc_holding_cost[dc, product] * dc_inv[dc, product, period]
            for dc in dcs
            for product in products
            for period in periods
        )
        + gp.quicksum(
            backlog_penalty[product] * (1.0 + 0.30 * (period - 1)) * backlog[customer, product, period]
            for customer in customers
            for product in products
            for period in periods
        )
        + carbon_excess_penalty * carbon_excess,
        GRB.MINIMIZE,
    )

    sp.optimize()

    if sp.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Unexpected subproblem status for {scenario}: {sp.Status}")

    return {
        "scenario_cost": sp.ObjVal,
        "dual_supplier": {key: constr.Pi for key, constr in supplier_con.items()},
        "dual_plant_cap": {key: constr.Pi for key, constr in plant_cap_con.items()},
        "dual_dc_throughput": {key: constr.Pi for key, constr in dc_throughput_con.items()},
        "dual_dc_storage": {key: constr.Pi for key, constr in dc_storage_con.items()},
        "dual_demand": {key: constr.Pi for key, constr in demand_con.items()},
        "dual_carbon": carbon_con.Pi,
        "ending_backlog": sum(backlog[customer, product, periods[-1]].X for customer in customers for product in products),
        "carbon_excess": carbon_excess.X,
    }


def solve_with_benders(
    data: Dict[str, object],
    max_iterations: int = 90,
    tolerance: float = 1e-6,
) -> Dict[str, object]:
    suppliers = data["suppliers"]
    plants = data["plants"]
    dcs = data["dcs"]
    customers = data["customers"]
    products = data["products"]
    periods = data["periods"]
    scenarios = data["scenarios"]
    probability = data["probability"]
    fixed_plant_open_cost = data["fixed_plant_open_cost"]
    fixed_dc_open_cost = data["fixed_dc_open_cost"]
    plant_module_cost = data["plant_module_cost"]
    dc_module_cost = data["dc_module_cost"]
    max_plant_modules = data["max_plant_modules"]
    max_dc_modules = data["max_dc_modules"]
    base_plant_capacity = data["base_plant_capacity"]
    plant_module_capacity = data["plant_module_capacity"]
    base_dc_throughput = data["base_dc_throughput"]
    dc_module_throughput = data["dc_module_throughput"]
    base_dc_storage = data["base_dc_storage"]
    dc_module_storage = data["dc_module_storage"]
    supplier_capacity = data["supplier_capacity"]
    demand = data["demand"]
    carbon_cap = data["carbon_cap"]
    risk_alpha = data["risk_alpha"]
    risk_weight = data["risk_weight"]

    master = gp.Model("phd_master")
    master.Params.OutputFlag = 0

    y = master.addVars(plants, vtype=GRB.BINARY, name="open_plant")
    w = master.addVars(dcs, vtype=GRB.BINARY, name="open_dc")
    mp = master.addVars(plants, lb=0, vtype=GRB.INTEGER, name="plant_modules")
    md = master.addVars(dcs, lb=0, vtype=GRB.INTEGER, name="dc_modules")
    theta = master.addVars(scenarios, lb=0.0, name="theta")
    eta = master.addVar(lb=0.0, name="eta")
    xi = master.addVars(scenarios, lb=0.0, name="xi")

    master.addConstrs((mp[plant] <= max_plant_modules[plant] * y[plant] for plant in plants), name="activate_plant_modules")
    master.addConstrs((md[dc] <= max_dc_modules[dc] * w[dc] for dc in dcs), name="activate_dc_modules")
    master.addConstrs((xi[scenario] >= theta[scenario] - eta for scenario in scenarios), name="cvar_link")

    cvar_coefficient = 1.0 / (1.0 - risk_alpha)
    master.setObjective(
        gp.quicksum(fixed_plant_open_cost[plant] * y[plant] + plant_module_cost[plant] * mp[plant] for plant in plants)
        + gp.quicksum(fixed_dc_open_cost[dc] * w[dc] + dc_module_cost[dc] * md[dc] for dc in dcs)
        + gp.quicksum(probability[scenario] * theta[scenario] for scenario in scenarios)
        + risk_weight * (eta + cvar_coefficient * gp.quicksum(probability[scenario] * xi[scenario] for scenario in scenarios)),
        GRB.MINIMIZE,
    )

    lower_bound = float("-inf")
    upper_bound = float("inf")
    optimality_cuts = 0
    best_solution = None

    print("=" * 104)
    print("PHD-THESIS LEVEL BENDERS: MULTI-ECHELON + STOCHASTIC DEMAND + CARBON + CVAR RISK")
    print("=" * 104)

    for iteration in range(1, max_iterations + 1):
        master.optimize()

        if master.Status != GRB.OPTIMAL:
            raise RuntimeError(f"Unexpected master status: {master.Status}")

        lower_bound = master.ObjVal
        open_plant_solution = {plant: int(round(y[plant].X)) for plant in plants}
        open_dc_solution = {dc: int(round(w[dc].X)) for dc in dcs}
        plant_modules_solution = {plant: int(round(mp[plant].X)) for plant in plants}
        dc_modules_solution = {dc: int(round(md[dc].X)) for dc in dcs}
        theta_solution = {scenario: theta[scenario].X for scenario in scenarios}

        fixed_plant_cost_value = sum(fixed_plant_open_cost[plant] * open_plant_solution[plant] for plant in plants)
        fixed_dc_cost_value = sum(fixed_dc_open_cost[dc] * open_dc_solution[dc] for dc in dcs)
        plant_module_cost_value = sum(plant_module_cost[plant] * plant_modules_solution[plant] for plant in plants)
        dc_module_cost_value = sum(dc_module_cost[dc] * dc_modules_solution[dc] for dc in dcs)

        print(f"\nIteration {iteration}")
        print(f"  Open plants: {[plant for plant in plants if open_plant_solution[plant] > 0.5]}")
        print(f"  Open DCs: {[dc for dc in dcs if open_dc_solution[dc] > 0.5]}")
        print(f"  Plant modules: {plant_modules_solution}")
        print(f"  DC modules: {dc_modules_solution}")
        print(
            f"  Fixed cost = {fixed_plant_cost_value + fixed_dc_cost_value:.2f}, "
            f"module cost = {plant_module_cost_value + dc_module_cost_value:.2f}"
        )
        print(f"  Bounds before recourse: LB = {lower_bound:.2f}, UB = {upper_bound:.2f}")

        if best_solution is not None and upper_bound - lower_bound <= tolerance:
            print("  Global gap already closed with a feasible incumbent.")
            print("  Stop before resolving scenario subproblems.")
            break

        scenario_results = {
            scenario: solve_scenario_subproblem(
                data,
                open_plant_solution,
                open_dc_solution,
                plant_modules_solution,
                dc_modules_solution,
                scenario,
            )
            for scenario in scenarios
        }

        scenario_costs = {scenario: scenario_results[scenario]["scenario_cost"] for scenario in scenarios}
        expected_operating_cost = sum(probability[scenario] * scenario_costs[scenario] for scenario in scenarios)
        cvar_result = compute_cvar(probability, scenario_costs, risk_alpha)
        candidate_total = (
            fixed_plant_cost_value
            + fixed_dc_cost_value
            + plant_module_cost_value
            + dc_module_cost_value
            + expected_operating_cost
            + risk_weight * cvar_result["cvar_value"]
        )

        if candidate_total < upper_bound - tolerance:
            upper_bound = candidate_total
            best_solution = {
                "open_plants": open_plant_solution,
                "open_dcs": open_dc_solution,
                "plant_modules": plant_modules_solution,
                "dc_modules": dc_modules_solution,
                "fixed_cost": fixed_plant_cost_value + fixed_dc_cost_value,
                "module_cost": plant_module_cost_value + dc_module_cost_value,
                "expected_operating_cost": expected_operating_cost,
                "scenario_costs": scenario_costs,
                "ending_backlog": {scenario: scenario_results[scenario]["ending_backlog"] for scenario in scenarios},
                "carbon_excess": {scenario: scenario_results[scenario]["carbon_excess"] for scenario in scenarios},
                "eta": cvar_result["eta"],
                "xi": cvar_result["xi"],
                "cvar_value": cvar_result["cvar_value"],
                "risk_term": risk_weight * cvar_result["cvar_value"],
                "total_cost": candidate_total,
            }
            print(f"  New incumbent found -> UB updated to {upper_bound:.2f}")

        print(f"  Expected operating cost: {expected_operating_cost:.2f}")
        print(f"  CVaR term value: {cvar_result['cvar_value']:.2f}")
        print(f"  Candidate total cost: {candidate_total:.2f}")

        added_cuts = 0
        for scenario in scenarios:
            constant_term = sum(
                demand[scenario, customer, product, period] * scenario_results[scenario]["dual_demand"][customer, product, period]
                for customer in customers
                for product in products
                for period in periods
            )
            constant_term += sum(
                supplier_capacity[scenario, supplier, product, period]
                * scenario_results[scenario]["dual_supplier"][supplier, product, period]
                for supplier in suppliers
                for product in products
                for period in periods
            )
            constant_term += carbon_cap[scenario] * scenario_results[scenario]["dual_carbon"]

            cut_rhs = constant_term
            cut_rhs += gp.quicksum(
                base_plant_capacity[plant, period]
                * scenario_results[scenario]["dual_plant_cap"][plant, period]
                * y[plant]
                for plant in plants
                for period in periods
            )
            cut_rhs += gp.quicksum(
                plant_module_capacity[plant]
                * scenario_results[scenario]["dual_plant_cap"][plant, period]
                * mp[plant]
                for plant in plants
                for period in periods
            )
            cut_rhs += gp.quicksum(
                base_dc_throughput[dc, period]
                * scenario_results[scenario]["dual_dc_throughput"][dc, period]
                * w[dc]
                for dc in dcs
                for period in periods
            )
            cut_rhs += gp.quicksum(
                dc_module_throughput[dc]
                * scenario_results[scenario]["dual_dc_throughput"][dc, period]
                * md[dc]
                for dc in dcs
                for period in periods
            )
            cut_rhs += gp.quicksum(
                base_dc_storage[dc, period]
                * scenario_results[scenario]["dual_dc_storage"][dc, period]
                * w[dc]
                for dc in dcs
                for period in periods
            )
            cut_rhs += gp.quicksum(
                dc_module_storage[dc]
                * scenario_results[scenario]["dual_dc_storage"][dc, period]
                * md[dc]
                for dc in dcs
                for period in periods
            )

            cut_violation = scenario_costs[scenario] - theta_solution[scenario]
            print(
                f"    Scenario {scenario}: theta = {theta_solution[scenario]:.2f}, "
                f"cost = {scenario_costs[scenario]:.2f}, "
                f"carbon excess = {scenario_results[scenario]['carbon_excess']:.2f}, "
                f"violation = {cut_violation:.6f}"
            )

            if cut_violation > tolerance:
                master.addConstr(theta[scenario] >= cut_rhs, name=f"opt_cut_{iteration}_{scenario}")
                optimality_cuts += 1
                added_cuts += 1

        print(f"  Bounds after recourse: LB = {lower_bound:.2f}, UB = {upper_bound:.2f}")
        if added_cuts == 0:
            print("  No new optimality cuts were required.")

        if upper_bound - lower_bound <= tolerance:
            print("\nConvergence reached: UB - LB <= tolerance")
            break

    else:
        raise RuntimeError("Benders did not converge within the iteration limit.")

    if best_solution is None:
        raise RuntimeError("No feasible incumbent was found.")

    best_solution["lower_bound"] = lower_bound
    best_solution["upper_bound"] = upper_bound
    best_solution["optimality_cuts"] = optimality_cuts
    return best_solution


def solve_integrated_model(data: Dict[str, object]) -> Dict[str, object]:
    suppliers = data["suppliers"]
    plants = data["plants"]
    dcs = data["dcs"]
    customers = data["customers"]
    products = data["products"]
    periods = data["periods"]
    scenarios = data["scenarios"]
    probability = data["probability"]
    fixed_plant_open_cost = data["fixed_plant_open_cost"]
    fixed_dc_open_cost = data["fixed_dc_open_cost"]
    plant_module_cost = data["plant_module_cost"]
    dc_module_cost = data["dc_module_cost"]
    max_plant_modules = data["max_plant_modules"]
    max_dc_modules = data["max_dc_modules"]
    base_plant_capacity = data["base_plant_capacity"]
    plant_module_capacity = data["plant_module_capacity"]
    base_dc_throughput = data["base_dc_throughput"]
    dc_module_throughput = data["dc_module_throughput"]
    base_dc_storage = data["base_dc_storage"]
    dc_module_storage = data["dc_module_storage"]
    processing_time = data["processing_time"]
    supplier_capacity = data["supplier_capacity"]
    purchase_cost = data["purchase_cost"]
    production_cost = data["production_cost"]
    plant_dc_cost = data["plant_dc_cost"]
    dc_customer_cost = data["dc_customer_cost"]
    plant_holding_cost = data["plant_holding_cost"]
    dc_holding_cost = data["dc_holding_cost"]
    backlog_penalty = data["backlog_penalty"]
    demand = data["demand"]
    buy_emission = data["buy_emission"]
    plant_dc_emission = data["plant_dc_emission"]
    dc_customer_emission = data["dc_customer_emission"]
    carbon_cap = data["carbon_cap"]
    carbon_excess_penalty = data["carbon_excess_penalty"]
    risk_alpha = data["risk_alpha"]
    risk_weight = data["risk_weight"]

    model = gp.Model("phd_integrated")
    model.Params.OutputFlag = 0

    y = model.addVars(plants, vtype=GRB.BINARY, name="open_plant")
    w = model.addVars(dcs, vtype=GRB.BINARY, name="open_dc")
    mp = model.addVars(plants, lb=0, vtype=GRB.INTEGER, name="plant_modules")
    md = model.addVars(dcs, lb=0, vtype=GRB.INTEGER, name="dc_modules")
    eta = model.addVar(lb=0.0, name="eta")
    xi = model.addVars(scenarios, lb=0.0, name="xi")
    op_cost = model.addVars(scenarios, lb=0.0, name="op_cost")

    buy = model.addVars(scenarios, suppliers, plants, products, periods, lb=0.0, name="buy")
    flow_pd = model.addVars(scenarios, plants, dcs, products, periods, lb=0.0, name="flow_pd")
    plant_inv = model.addVars(scenarios, plants, products, periods, lb=0.0, name="plant_inv")
    flow_dc = model.addVars(scenarios, dcs, customers, products, periods, lb=0.0, name="flow_dc")
    dc_inv = model.addVars(scenarios, dcs, products, periods, lb=0.0, name="dc_inv")
    backlog = model.addVars(scenarios, customers, products, periods, lb=0.0, name="backlog")
    carbon_excess = model.addVars(scenarios, lb=0.0, name="carbon_excess")

    model.addConstrs((mp[plant] <= max_plant_modules[plant] * y[plant] for plant in plants), name="activate_plant_modules")
    model.addConstrs((md[dc] <= max_dc_modules[dc] * w[dc] for dc in dcs), name="activate_dc_modules")

    for scenario in scenarios:
        for supplier in suppliers:
            for product in products:
                for period in periods:
                    model.addConstr(
                        gp.quicksum(buy[scenario, supplier, plant, product, period] for plant in plants)
                        <= supplier_capacity[scenario, supplier, product, period],
                        name=f"supplier_cap_{scenario}_{supplier}_{product}_{period}",
                    )

        for plant in plants:
            for period in periods:
                model.addConstr(
                    gp.quicksum(
                        processing_time[product] * buy[scenario, supplier, plant, product, period]
                        for supplier in suppliers
                        for product in products
                    )
                    <= base_plant_capacity[plant, period] * y[plant]
                    + plant_module_capacity[plant] * mp[plant],
                    name=f"plant_cap_{scenario}_{plant}_{period}",
                )

        for plant in plants:
            for product in products:
                for period in periods:
                    if period == periods[0]:
                        model.addConstr(
                            gp.quicksum(buy[scenario, supplier, plant, product, period] for supplier in suppliers)
                            - gp.quicksum(flow_pd[scenario, plant, dc, product, period] for dc in dcs)
                            - plant_inv[scenario, plant, product, period]
                            == 0.0,
                            name=f"plant_balance_{scenario}_{plant}_{product}_{period}",
                        )
                    else:
                        model.addConstr(
                            plant_inv[scenario, plant, product, period - 1]
                            + gp.quicksum(buy[scenario, supplier, plant, product, period] for supplier in suppliers)
                            - gp.quicksum(flow_pd[scenario, plant, dc, product, period] for dc in dcs)
                            - plant_inv[scenario, plant, product, period]
                            == 0.0,
                            name=f"plant_balance_{scenario}_{plant}_{product}_{period}",
                        )

        for dc in dcs:
            for period in periods:
                model.addConstr(
                    gp.quicksum(flow_dc[scenario, dc, customer, product, period] for customer in customers for product in products)
                    <= base_dc_throughput[dc, period] * w[dc]
                    + dc_module_throughput[dc] * md[dc],
                    name=f"dc_throughput_{scenario}_{dc}_{period}",
                )
                model.addConstr(
                    gp.quicksum(dc_inv[scenario, dc, product, period] for product in products)
                    <= base_dc_storage[dc, period] * w[dc]
                    + dc_module_storage[dc] * md[dc],
                    name=f"dc_storage_{scenario}_{dc}_{period}",
                )

        for dc in dcs:
            for product in products:
                for period in periods:
                    if period == periods[0]:
                        model.addConstr(
                            gp.quicksum(flow_pd[scenario, plant, dc, product, period] for plant in plants)
                            - gp.quicksum(flow_dc[scenario, dc, customer, product, period] for customer in customers)
                            - dc_inv[scenario, dc, product, period]
                            == 0.0,
                            name=f"dc_balance_{scenario}_{dc}_{product}_{period}",
                        )
                    else:
                        model.addConstr(
                            dc_inv[scenario, dc, product, period - 1]
                            + gp.quicksum(flow_pd[scenario, plant, dc, product, period] for plant in plants)
                            - gp.quicksum(flow_dc[scenario, dc, customer, product, period] for customer in customers)
                            - dc_inv[scenario, dc, product, period]
                            == 0.0,
                            name=f"dc_balance_{scenario}_{dc}_{product}_{period}",
                        )

        for customer in customers:
            for product in products:
                for period in periods:
                    if period == periods[0]:
                        model.addConstr(
                            gp.quicksum(flow_dc[scenario, dc, customer, product, period] for dc in dcs)
                            + backlog[scenario, customer, product, period]
                            == demand[scenario, customer, product, period],
                            name=f"demand_{scenario}_{customer}_{product}_{period}",
                        )
                    else:
                        model.addConstr(
                            gp.quicksum(flow_dc[scenario, dc, customer, product, period] for dc in dcs)
                            + backlog[scenario, customer, product, period]
                            - backlog[scenario, customer, product, period - 1]
                            == demand[scenario, customer, product, period],
                            name=f"demand_{scenario}_{customer}_{product}_{period}",
                        )

        carbon_expr = (
            gp.quicksum(
                buy_emission[supplier, plant, product] * buy[scenario, supplier, plant, product, period]
                for supplier in suppliers
                for plant in plants
                for product in products
                for period in periods
            )
            + gp.quicksum(
                plant_dc_emission[plant, dc, product] * flow_pd[scenario, plant, dc, product, period]
                for plant in plants
                for dc in dcs
                for product in products
                for period in periods
            )
            + gp.quicksum(
                dc_customer_emission[dc, customer, product] * flow_dc[scenario, dc, customer, product, period]
                for dc in dcs
                for customer in customers
                for product in products
                for period in periods
            )
        )

        model.addConstr(carbon_expr - carbon_excess[scenario] <= carbon_cap[scenario], name=f"carbon_{scenario}")

        scenario_expr = (
            gp.quicksum(
                (purchase_cost[supplier, plant, product] + production_cost[plant, product])
                * buy[scenario, supplier, plant, product, period]
                for supplier in suppliers
                for plant in plants
                for product in products
                for period in periods
            )
            + gp.quicksum(
                plant_dc_cost[plant, dc, product] * flow_pd[scenario, plant, dc, product, period]
                for plant in plants
                for dc in dcs
                for product in products
                for period in periods
            )
            + gp.quicksum(
                dc_customer_cost[dc, customer, product] * flow_dc[scenario, dc, customer, product, period]
                for dc in dcs
                for customer in customers
                for product in products
                for period in periods
            )
            + gp.quicksum(
                plant_holding_cost[plant, product] * plant_inv[scenario, plant, product, period]
                for plant in plants
                for product in products
                for period in periods
            )
            + gp.quicksum(
                dc_holding_cost[dc, product] * dc_inv[scenario, dc, product, period]
                for dc in dcs
                for product in products
                for period in periods
            )
            + gp.quicksum(
                backlog_penalty[product] * (1.0 + 0.30 * (period - 1)) * backlog[scenario, customer, product, period]
                for customer in customers
                for product in products
                for period in periods
            )
            + carbon_excess_penalty * carbon_excess[scenario]
        )
        model.addConstr(op_cost[scenario] == scenario_expr, name=f"op_cost_{scenario}")

    model.addConstrs((xi[scenario] >= op_cost[scenario] - eta for scenario in scenarios), name="cvar_link")

    cvar_coefficient = 1.0 / (1.0 - risk_alpha)
    model.setObjective(
        gp.quicksum(fixed_plant_open_cost[plant] * y[plant] + plant_module_cost[plant] * mp[plant] for plant in plants)
        + gp.quicksum(fixed_dc_open_cost[dc] * w[dc] + dc_module_cost[dc] * md[dc] for dc in dcs)
        + gp.quicksum(probability[scenario] * op_cost[scenario] for scenario in scenarios)
        + risk_weight * (eta + cvar_coefficient * gp.quicksum(probability[scenario] * xi[scenario] for scenario in scenarios)),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Unexpected integrated model status: {model.Status}")

    return {
        "open_plants": {plant: int(round(y[plant].X)) for plant in plants},
        "open_dcs": {dc: int(round(w[dc].X)) for dc in dcs},
        "plant_modules": {plant: int(round(mp[plant].X)) for plant in plants},
        "dc_modules": {dc: int(round(md[dc].X)) for dc in dcs},
        "scenario_costs": {scenario: op_cost[scenario].X for scenario in scenarios},
        "ending_backlog": {
            scenario: sum(backlog[scenario, customer, product, periods[-1]].X for customer in customers for product in products)
            for scenario in scenarios
        },
        "carbon_excess": {scenario: carbon_excess[scenario].X for scenario in scenarios},
        "eta": eta.X,
        "xi": {scenario: xi[scenario].X for scenario in scenarios},
        "total_cost": model.ObjVal,
    }


def print_solution(title: str, solution: Dict[str, object], data: Dict[str, object]) -> None:
    scenarios = data["scenarios"]

    print("\n" + "=" * 104)
    print(title)
    print("=" * 104)

    print(f"Open plants: {[plant for plant, value in solution['open_plants'].items() if value > 0.5]}")
    print(f"Open DCs: {[dc for dc, value in solution['open_dcs'].items() if value > 0.5]}")
    print(f"Plant modules: {solution['plant_modules']}")
    print(f"DC modules: {solution['dc_modules']}")

    if "fixed_cost" in solution:
        print(f"Fixed opening cost: {solution['fixed_cost']:.2f}")
    if "module_cost" in solution:
        print(f"Module cost: {solution['module_cost']:.2f}")
    if "expected_operating_cost" in solution:
        print(f"Expected operating cost: {solution['expected_operating_cost']:.2f}")
    if "risk_term" in solution:
        print(f"Risk term: {solution['risk_term']:.2f}")
    if "cvar_value" in solution:
        print(f"CVaR value: {solution['cvar_value']:.2f}")
    if "total_cost" in solution:
        print(f"Total cost: {solution['total_cost']:.2f}")
    if "lower_bound" in solution and "upper_bound" in solution:
        print(f"Final LB: {solution['lower_bound']:.2f}")
        print(f"Final UB: {solution['upper_bound']:.2f}")
        print(f"Optimality cuts: {solution['optimality_cuts']}")

    print("\nScenario summary:")
    for scenario in scenarios:
        print(
            f"  {scenario}: cost = {solution['scenario_costs'][scenario]:.2f}, "
            f"ending backlog = {solution['ending_backlog'][scenario]:.2f}, "
            f"carbon excess = {solution['carbon_excess'][scenario]:.2f}, "
            f"xi = {solution['xi'][scenario]:.2f}"
        )


def main() -> None:
    data = build_data()
    benders_solution = solve_with_benders(data)
    integrated_solution = solve_integrated_model(data)

    print_solution("PhD-thesis Benders solution", benders_solution, data)
    print_solution("Integrated equivalent with CVaR (validation)", integrated_solution, data)

    if abs(benders_solution["total_cost"] - integrated_solution["total_cost"]) > TOL:
        print("\nWARNING: Benders and integrated model do not match.")
    else:
        print("\nValidation passed: PhD-thesis Benders matches the integrated model.")


if __name__ == "__main__":
    main()
