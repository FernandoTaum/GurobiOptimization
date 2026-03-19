from __future__ import annotations

"""Master-thesis level example: multi-period, multi-product stochastic Benders."""

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


def build_data() -> Dict[str, object]:
    facilities = ["F1", "F2", "F3", "F4"]
    customers = ["C1", "C2", "C3", "C4", "C5"]
    products = ["P1", "P2"]
    periods = [1, 2, 3]
    scenarios = ["Calm", "Base", "Surge"]

    scenario_probability = {
        "Calm": 0.20,
        "Base": 0.50,
        "Surge": 0.30,
    }

    scenario_demand_factor = {
        "Calm": 0.90,
        "Base": 1.00,
        "Surge": 1.25,
    }

    fixed_open_cost = {
        "F1": 230,
        "F2": 215,
        "F3": 250,
        "F4": 240,
    }

    base_production_capacity = {
        ("F1", 1): 90,
        ("F1", 2): 92,
        ("F1", 3): 95,
        ("F2", 1): 82,
        ("F2", 2): 84,
        ("F2", 3): 86,
        ("F3", 1): 102,
        ("F3", 2): 104,
        ("F3", 3): 107,
        ("F4", 1): 96,
        ("F4", 2): 98,
        ("F4", 3): 100,
    }

    base_storage_capacity = {
        ("F1", 1): 40,
        ("F1", 2): 42,
        ("F1", 3): 44,
        ("F2", 1): 34,
        ("F2", 2): 35,
        ("F2", 3): 36,
        ("F3", 1): 45,
        ("F3", 2): 46,
        ("F3", 3): 47,
        ("F4", 1): 41,
        ("F4", 2): 42,
        ("F4", 3): 43,
    }

    module_production_capacity = {
        "F1": 24,
        "F2": 22,
        "F3": 26,
        "F4": 24,
    }

    module_storage_capacity = {
        "F1": 10,
        "F2": 9,
        "F3": 11,
        "F4": 10,
    }

    module_investment_cost = {
        ("F1", 1): 70,
        ("F1", 2): 66,
        ("F1", 3): 62,
        ("F2", 1): 64,
        ("F2", 2): 60,
        ("F2", 3): 58,
        ("F3", 1): 76,
        ("F3", 2): 72,
        ("F3", 3): 68,
        ("F4", 1): 69,
        ("F4", 2): 65,
        ("F4", 3): 61,
    }

    max_new_modules = {
        ("F1", 1): 1,
        ("F1", 2): 1,
        ("F1", 3): 1,
        ("F2", 1): 1,
        ("F2", 2): 1,
        ("F2", 3): 1,
        ("F3", 1): 1,
        ("F3", 2): 1,
        ("F3", 3): 1,
        ("F4", 1): 1,
        ("F4", 2): 1,
        ("F4", 3): 1,
    }

    processing_time = {
        "P1": 1.00,
        "P2": 1.15,
    }

    production_cost = {
        ("F1", "P1"): 4.3,
        ("F1", "P2"): 5.1,
        ("F2", "P1"): 4.1,
        ("F2", "P2"): 4.8,
        ("F3", "P1"): 4.8,
        ("F3", "P2"): 5.5,
        ("F4", "P1"): 4.5,
        ("F4", "P2"): 5.0,
    }

    transport_base = {
        ("F1", "C1"): 3.4,
        ("F1", "C2"): 4.8,
        ("F1", "C3"): 5.6,
        ("F1", "C4"): 6.1,
        ("F1", "C5"): 5.0,
        ("F2", "C1"): 4.0,
        ("F2", "C2"): 3.5,
        ("F2", "C3"): 4.7,
        ("F2", "C4"): 5.9,
        ("F2", "C5"): 4.6,
        ("F3", "C1"): 5.6,
        ("F3", "C2"): 4.8,
        ("F3", "C3"): 3.2,
        ("F3", "C4"): 3.8,
        ("F3", "C5"): 4.5,
        ("F4", "C1"): 6.0,
        ("F4", "C2"): 5.4,
        ("F4", "C3"): 4.0,
        ("F4", "C4"): 3.6,
        ("F4", "C5"): 3.4,
    }

    product_freight_premium = {
        "P1": 0.0,
        "P2": 0.7,
    }

    transport_cost = {
        (facility, customer, product): transport_base[facility, customer] + product_freight_premium[product]
        for facility in facilities
        for customer in customers
        for product in products
    }

    holding_cost = {
        ("F1", "P1"): 0.50,
        ("F1", "P2"): 0.65,
        ("F2", "P1"): 0.45,
        ("F2", "P2"): 0.60,
        ("F3", "P1"): 0.55,
        ("F3", "P2"): 0.72,
        ("F4", "P1"): 0.52,
        ("F4", "P2"): 0.68,
    }

    backlog_penalty = {
        "P1": 26.0,
        "P2": 30.0,
    }

    base_demand = {
        ("C1", "P1", 1): 10,
        ("C1", "P1", 2): 11,
        ("C1", "P1", 3): 12,
        ("C1", "P2", 1): 7,
        ("C1", "P2", 2): 8,
        ("C1", "P2", 3): 9,
        ("C2", "P1", 1): 12,
        ("C2", "P1", 2): 13,
        ("C2", "P1", 3): 14,
        ("C2", "P2", 1): 8,
        ("C2", "P2", 2): 9,
        ("C2", "P2", 3): 10,
        ("C3", "P1", 1): 8,
        ("C3", "P1", 2): 9,
        ("C3", "P1", 3): 10,
        ("C3", "P2", 1): 6,
        ("C3", "P2", 2): 6,
        ("C3", "P2", 3): 7,
        ("C4", "P1", 1): 11,
        ("C4", "P1", 2): 12,
        ("C4", "P1", 3): 14,
        ("C4", "P2", 1): 7,
        ("C4", "P2", 2): 8,
        ("C4", "P2", 3): 9,
        ("C5", "P1", 1): 9,
        ("C5", "P1", 2): 10,
        ("C5", "P1", 3): 11,
        ("C5", "P2", 1): 6,
        ("C5", "P2", 2): 7,
        ("C5", "P2", 3): 8,
    }

    demand = {}
    for scenario in scenarios:
        for customer in customers:
            for product in products:
                for period in periods:
                    demand[scenario, customer, product, period] = int(
                        round(base_demand[customer, product, period] * scenario_demand_factor[scenario])
                    )

    return {
        "facilities": facilities,
        "customers": customers,
        "products": products,
        "periods": periods,
        "scenarios": scenarios,
        "scenario_probability": scenario_probability,
        "fixed_open_cost": fixed_open_cost,
        "base_production_capacity": base_production_capacity,
        "base_storage_capacity": base_storage_capacity,
        "module_production_capacity": module_production_capacity,
        "module_storage_capacity": module_storage_capacity,
        "module_investment_cost": module_investment_cost,
        "max_new_modules": max_new_modules,
        "processing_time": processing_time,
        "production_cost": production_cost,
        "transport_cost": transport_cost,
        "holding_cost": holding_cost,
        "backlog_penalty": backlog_penalty,
        "demand": demand,
    }


def cumulative_modules(module_solution: Dict[tuple[str, int], int], facility: str, period: int, periods: list[int]) -> int:
    return sum(module_solution[facility, tau] for tau in periods if tau <= period)


def solve_scenario_subproblem(
    data: Dict[str, object],
    open_solution: Dict[str, int],
    module_solution: Dict[tuple[str, int], int],
    scenario: str,
) -> Dict[str, object]:
    facilities = data["facilities"]
    customers = data["customers"]
    products = data["products"]
    periods = data["periods"]
    base_production_capacity = data["base_production_capacity"]
    base_storage_capacity = data["base_storage_capacity"]
    module_production_capacity = data["module_production_capacity"]
    module_storage_capacity = data["module_storage_capacity"]
    processing_time = data["processing_time"]
    production_cost = data["production_cost"]
    transport_cost = data["transport_cost"]
    holding_cost = data["holding_cost"]
    backlog_penalty = data["backlog_penalty"]
    demand = data["demand"]

    sp = gp.Model(f"master_thesis_subproblem_{scenario}")
    sp.Params.OutputFlag = 0

    prod = sp.addVars(facilities, products, periods, lb=0.0, name="prod")
    ship = sp.addVars(facilities, customers, products, periods, lb=0.0, name="ship")
    inv = sp.addVars(facilities, products, periods, lb=0.0, name="inv")
    backlog = sp.addVars(customers, products, periods, lb=0.0, name="backlog")

    demand_con = {}
    for customer in customers:
        for product in products:
            for period in periods:
                if period == periods[0]:
                    demand_con[customer, product, period] = sp.addConstr(
                        gp.quicksum(ship[facility, customer, product, period] for facility in facilities)
                        + backlog[customer, product, period]
                        == demand[scenario, customer, product, period],
                        name=f"demand_{customer}_{product}_{period}",
                    )
                else:
                    demand_con[customer, product, period] = sp.addConstr(
                        gp.quicksum(ship[facility, customer, product, period] for facility in facilities)
                        + backlog[customer, product, period]
                        - backlog[customer, product, period - 1]
                        == demand[scenario, customer, product, period],
                        name=f"demand_{customer}_{product}_{period}",
                    )

    for facility in facilities:
        for product in products:
            for period in periods:
                if period == periods[0]:
                    sp.addConstr(
                        prod[facility, product, period]
                        - gp.quicksum(ship[facility, customer, product, period] for customer in customers)
                        - inv[facility, product, period]
                        == 0.0,
                        name=f"flow_{facility}_{product}_{period}",
                    )
                else:
                    sp.addConstr(
                        inv[facility, product, period - 1]
                        + prod[facility, product, period]
                        - gp.quicksum(ship[facility, customer, product, period] for customer in customers)
                        - inv[facility, product, period]
                        == 0.0,
                        name=f"flow_{facility}_{product}_{period}",
                    )

    production_capacity_con = {}
    storage_capacity_con = {}
    for facility in facilities:
        for period in periods:
            available_modules = cumulative_modules(module_solution, facility, period, periods)
            production_capacity_con[facility, period] = sp.addConstr(
                gp.quicksum(processing_time[product] * prod[facility, product, period] for product in products)
                <= base_production_capacity[facility, period] * open_solution[facility]
                + module_production_capacity[facility] * available_modules,
                name=f"prod_cap_{facility}_{period}",
            )
            storage_capacity_con[facility, period] = sp.addConstr(
                gp.quicksum(inv[facility, product, period] for product in products)
                <= base_storage_capacity[facility, period] * open_solution[facility]
                + module_storage_capacity[facility] * available_modules,
                name=f"store_cap_{facility}_{period}",
            )

    sp.setObjective(
        gp.quicksum(
            production_cost[facility, product] * prod[facility, product, period]
            for facility in facilities
            for product in products
            for period in periods
        )
        + gp.quicksum(
            transport_cost[facility, customer, product] * ship[facility, customer, product, period]
            for facility in facilities
            for customer in customers
            for product in products
            for period in periods
        )
        + gp.quicksum(
            holding_cost[facility, product] * inv[facility, product, period]
            for facility in facilities
            for product in products
            for period in periods
        )
        + gp.quicksum(
            backlog_penalty[product] * (1.0 + 0.35 * (period - 1)) * backlog[customer, product, period]
            for customer in customers
            for product in products
            for period in periods
        ),
        GRB.MINIMIZE,
    )

    sp.optimize()

    if sp.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Unexpected subproblem status for {scenario}: {sp.Status}")

    return {
        "scenario_cost": sp.ObjVal,
        "dual_demand": {key: constr.Pi for key, constr in demand_con.items()},
        "dual_prod_cap": {key: constr.Pi for key, constr in production_capacity_con.items()},
        "dual_store_cap": {key: constr.Pi for key, constr in storage_capacity_con.items()},
        "ending_backlog": sum(backlog[customer, product, periods[-1]].X for customer in customers for product in products),
    }


def solve_with_benders(
    data: Dict[str, object],
    max_iterations: int = 80,
    tolerance: float = 1e-6,
) -> Dict[str, object]:
    facilities = data["facilities"]
    customers = data["customers"]
    products = data["products"]
    periods = data["periods"]
    scenarios = data["scenarios"]
    scenario_probability = data["scenario_probability"]
    fixed_open_cost = data["fixed_open_cost"]
    module_investment_cost = data["module_investment_cost"]
    max_new_modules = data["max_new_modules"]
    base_production_capacity = data["base_production_capacity"]
    base_storage_capacity = data["base_storage_capacity"]
    module_production_capacity = data["module_production_capacity"]
    module_storage_capacity = data["module_storage_capacity"]
    demand = data["demand"]

    master = gp.Model("master_thesis_master")
    master.Params.OutputFlag = 0

    y = master.addVars(facilities, vtype=GRB.BINARY, name="open")
    m = master.addVars(facilities, periods, lb=0, vtype=GRB.INTEGER, name="module_add")
    theta = master.addVars(scenarios, lb=0.0, name="theta")

    master.addConstrs(
        (m[facility, period] <= max_new_modules[facility, period] * y[facility] for facility in facilities for period in periods),
        name="activate_modules_only_if_open",
    )

    master.setObjective(
        gp.quicksum(fixed_open_cost[facility] * y[facility] for facility in facilities)
        + gp.quicksum(module_investment_cost[facility, period] * m[facility, period] for facility in facilities for period in periods)
        + gp.quicksum(scenario_probability[scenario] * theta[scenario] for scenario in scenarios),
        GRB.MINIMIZE,
    )

    lower_bound = float("-inf")
    upper_bound = float("inf")
    optimality_cuts = 0
    best_solution = None

    print("=" * 94)
    print("MASTER-THESIS LEVEL BENDERS: MULTI-PERIOD + MULTI-PRODUCT + STOCHASTIC DEMAND")
    print("=" * 94)

    for iteration in range(1, max_iterations + 1):
        master.optimize()

        if master.Status != GRB.OPTIMAL:
            raise RuntimeError(f"Unexpected master status: {master.Status}")

        lower_bound = master.ObjVal
        open_solution = {facility: int(round(y[facility].X)) for facility in facilities}
        module_solution = {
            (facility, period): int(round(m[facility, period].X))
            for facility in facilities
            for period in periods
        }
        theta_solution = {scenario: theta[scenario].X for scenario in scenarios}

        fixed_value = sum(fixed_open_cost[facility] * open_solution[facility] for facility in facilities)
        module_value = sum(
            module_investment_cost[facility, period] * module_solution[facility, period]
            for facility in facilities
            for period in periods
        )

        print(f"\nIteration {iteration}")
        print(f"  Open facilities: {[facility for facility in facilities if open_solution[facility] > 0.5]}")
        print(f"  Module additions: {module_solution}")
        print(f"  Fixed cost: {fixed_value:.2f}")
        print(f"  Expansion cost: {module_value:.2f}")
        print(f"  Bounds before recourse: LB = {lower_bound:.2f}, UB = {upper_bound:.2f}")

        if best_solution is not None and upper_bound - lower_bound <= tolerance:
            print("  Global gap already closed with a feasible incumbent.")
            print("  Stop before resolving scenario subproblems.")
            break

        scenario_results = {
            scenario: solve_scenario_subproblem(data, open_solution, module_solution, scenario)
            for scenario in scenarios
        }

        expected_recourse = sum(
            scenario_probability[scenario] * scenario_results[scenario]["scenario_cost"]
            for scenario in scenarios
        )
        candidate_total = fixed_value + module_value + expected_recourse

        if candidate_total < upper_bound - tolerance:
            upper_bound = candidate_total
            best_solution = {
                "open_facilities": open_solution,
                "module_additions": module_solution,
                "fixed_cost": fixed_value,
                "expansion_cost": module_value,
                "expected_recourse_cost": expected_recourse,
                "scenario_costs": {scenario: scenario_results[scenario]["scenario_cost"] for scenario in scenarios},
                "ending_backlog": {scenario: scenario_results[scenario]["ending_backlog"] for scenario in scenarios},
                "total_cost": candidate_total,
            }
            print(f"  New incumbent found -> UB updated to {upper_bound:.2f}")

        print(f"  Expected recourse cost: {expected_recourse:.2f}")
        print(f"  Candidate total cost: {candidate_total:.2f}")

        added_cuts = 0
        for scenario in scenarios:
            scenario_cost = scenario_results[scenario]["scenario_cost"]
            theta_value = theta_solution[scenario]

            constant_term = sum(
                demand[scenario, customer, product, period] * scenario_results[scenario]["dual_demand"][customer, product, period]
                for customer in customers
                for product in products
                for period in periods
            )

            cut_rhs = constant_term
            cut_rhs += gp.quicksum(
                base_production_capacity[facility, period]
                * scenario_results[scenario]["dual_prod_cap"][facility, period]
                * y[facility]
                for facility in facilities
                for period in periods
            )
            cut_rhs += gp.quicksum(
                module_production_capacity[facility]
                * scenario_results[scenario]["dual_prod_cap"][facility, period]
                * gp.quicksum(m[facility, tau] for tau in periods if tau <= period)
                for facility in facilities
                for period in periods
            )
            cut_rhs += gp.quicksum(
                base_storage_capacity[facility, period]
                * scenario_results[scenario]["dual_store_cap"][facility, period]
                * y[facility]
                for facility in facilities
                for period in periods
            )
            cut_rhs += gp.quicksum(
                module_storage_capacity[facility]
                * scenario_results[scenario]["dual_store_cap"][facility, period]
                * gp.quicksum(m[facility, tau] for tau in periods if tau <= period)
                for facility in facilities
                for period in periods
            )

            cut_violation = scenario_cost - theta_value
            print(
                f"    Scenario {scenario}: theta = {theta_value:.2f}, "
                f"cost = {scenario_cost:.2f}, ending backlog = {scenario_results[scenario]['ending_backlog']:.2f}, "
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
    facilities = data["facilities"]
    customers = data["customers"]
    products = data["products"]
    periods = data["periods"]
    scenarios = data["scenarios"]
    scenario_probability = data["scenario_probability"]
    fixed_open_cost = data["fixed_open_cost"]
    base_production_capacity = data["base_production_capacity"]
    base_storage_capacity = data["base_storage_capacity"]
    module_production_capacity = data["module_production_capacity"]
    module_storage_capacity = data["module_storage_capacity"]
    module_investment_cost = data["module_investment_cost"]
    max_new_modules = data["max_new_modules"]
    processing_time = data["processing_time"]
    production_cost = data["production_cost"]
    transport_cost = data["transport_cost"]
    holding_cost = data["holding_cost"]
    backlog_penalty = data["backlog_penalty"]
    demand = data["demand"]

    model = gp.Model("master_thesis_integrated")
    model.Params.OutputFlag = 0

    y = model.addVars(facilities, vtype=GRB.BINARY, name="open")
    m = model.addVars(facilities, periods, lb=0, vtype=GRB.INTEGER, name="module_add")
    prod = model.addVars(scenarios, facilities, products, periods, lb=0.0, name="prod")
    ship = model.addVars(scenarios, facilities, customers, products, periods, lb=0.0, name="ship")
    inv = model.addVars(scenarios, facilities, products, periods, lb=0.0, name="inv")
    backlog = model.addVars(scenarios, customers, products, periods, lb=0.0, name="backlog")

    model.addConstrs(
        (m[facility, period] <= max_new_modules[facility, period] * y[facility] for facility in facilities for period in periods),
        name="activate_modules_only_if_open",
    )

    for scenario in scenarios:
        for customer in customers:
            for product in products:
                for period in periods:
                    if period == periods[0]:
                        model.addConstr(
                            gp.quicksum(ship[scenario, facility, customer, product, period] for facility in facilities)
                            + backlog[scenario, customer, product, period]
                            == demand[scenario, customer, product, period],
                            name=f"demand_{scenario}_{customer}_{product}_{period}",
                        )
                    else:
                        model.addConstr(
                            gp.quicksum(ship[scenario, facility, customer, product, period] for facility in facilities)
                            + backlog[scenario, customer, product, period]
                            - backlog[scenario, customer, product, period - 1]
                            == demand[scenario, customer, product, period],
                            name=f"demand_{scenario}_{customer}_{product}_{period}",
                        )

        for facility in facilities:
            for product in products:
                for period in periods:
                    if period == periods[0]:
                        model.addConstr(
                            prod[scenario, facility, product, period]
                            - gp.quicksum(ship[scenario, facility, customer, product, period] for customer in customers)
                            - inv[scenario, facility, product, period]
                            == 0.0,
                            name=f"flow_{scenario}_{facility}_{product}_{period}",
                        )
                    else:
                        model.addConstr(
                            inv[scenario, facility, product, period - 1]
                            + prod[scenario, facility, product, period]
                            - gp.quicksum(ship[scenario, facility, customer, product, period] for customer in customers)
                            - inv[scenario, facility, product, period]
                            == 0.0,
                            name=f"flow_{scenario}_{facility}_{product}_{period}",
                        )

            for period in periods:
                model.addConstr(
                    gp.quicksum(
                        processing_time[product] * prod[scenario, facility, product, period]
                        for product in products
                    )
                    <= base_production_capacity[facility, period] * y[facility]
                    + module_production_capacity[facility] * gp.quicksum(m[facility, tau] for tau in periods if tau <= period),
                    name=f"prod_cap_{scenario}_{facility}_{period}",
                )
                model.addConstr(
                    gp.quicksum(inv[scenario, facility, product, period] for product in products)
                    <= base_storage_capacity[facility, period] * y[facility]
                    + module_storage_capacity[facility] * gp.quicksum(m[facility, tau] for tau in periods if tau <= period),
                    name=f"store_cap_{scenario}_{facility}_{period}",
                )

    model.setObjective(
        gp.quicksum(fixed_open_cost[facility] * y[facility] for facility in facilities)
        + gp.quicksum(module_investment_cost[facility, period] * m[facility, period] for facility in facilities for period in periods)
        + gp.quicksum(
            scenario_probability[scenario]
            * (
                gp.quicksum(
                    production_cost[facility, product] * prod[scenario, facility, product, period]
                    for facility in facilities
                    for product in products
                    for period in periods
                )
                + gp.quicksum(
                    transport_cost[facility, customer, product] * ship[scenario, facility, customer, product, period]
                    for facility in facilities
                    for customer in customers
                    for product in products
                    for period in periods
                )
                + gp.quicksum(
                    holding_cost[facility, product] * inv[scenario, facility, product, period]
                    for facility in facilities
                    for product in products
                    for period in periods
                )
                + gp.quicksum(
                    backlog_penalty[product] * (1.0 + 0.35 * (period - 1)) * backlog[scenario, customer, product, period]
                    for customer in customers
                    for product in products
                    for period in periods
                )
            )
            for scenario in scenarios
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Unexpected integrated model status: {model.Status}")

    scenario_costs = {}
    ending_backlog = {}
    for scenario in scenarios:
        scenario_costs[scenario] = (
            sum(
                production_cost[facility, product] * prod[scenario, facility, product, period].X
                for facility in facilities
                for product in products
                for period in periods
            )
            + sum(
                transport_cost[facility, customer, product] * ship[scenario, facility, customer, product, period].X
                for facility in facilities
                for customer in customers
                for product in products
                for period in periods
            )
            + sum(
                holding_cost[facility, product] * inv[scenario, facility, product, period].X
                for facility in facilities
                for product in products
                for period in periods
            )
            + sum(
                backlog_penalty[product] * (1.0 + 0.35 * (period - 1)) * backlog[scenario, customer, product, period].X
                for customer in customers
                for product in products
                for period in periods
            )
        )
        ending_backlog[scenario] = sum(
            backlog[scenario, customer, product, periods[-1]].X
            for customer in customers
            for product in products
        )

    return {
        "open_facilities": {facility: int(round(y[facility].X)) for facility in facilities},
        "module_additions": {(facility, period): int(round(m[facility, period].X)) for facility in facilities for period in periods},
        "scenario_costs": scenario_costs,
        "ending_backlog": ending_backlog,
        "total_cost": model.ObjVal,
    }


def print_solution(title: str, solution: Dict[str, object], data: Dict[str, object]) -> None:
    facilities = data["facilities"]
    periods = data["periods"]
    scenarios = data["scenarios"]

    print("\n" + "=" * 94)
    print(title)
    print("=" * 94)

    print(f"Open facilities: {[facility for facility in facilities if solution['open_facilities'][facility] > 0.5]}")
    print(
        "Module additions: "
        + str({(facility, period): solution["module_additions"][facility, period] for facility in facilities for period in periods})
    )

    if "fixed_cost" in solution:
        print(f"Fixed opening cost: {solution['fixed_cost']:.2f}")
    if "expansion_cost" in solution:
        print(f"Expansion cost: {solution['expansion_cost']:.2f}")
    if "expected_recourse_cost" in solution:
        print(f"Expected recourse cost: {solution['expected_recourse_cost']:.2f}")
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
            f"ending backlog = {solution['ending_backlog'][scenario]:.2f}"
        )


def main() -> None:
    data = build_data()
    benders_solution = solve_with_benders(data)
    integrated_solution = solve_integrated_model(data)

    print_solution("Master-thesis Benders solution", benders_solution, data)
    print_solution("Integrated equivalent (validation)", integrated_solution, data)

    if abs(benders_solution["total_cost"] - integrated_solution["total_cost"]) > TOL:
        print("\nWARNING: Benders and integrated model do not match.")
    else:
        print("\nValidation passed: Master-thesis Benders matches the integrated model.")


if __name__ == "__main__":
    main()
