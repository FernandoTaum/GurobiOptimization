from __future__ import annotations

"""Advanced teaching example: stochastic facility location with Benders."""

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
    """Advanced instance with demand scenarios and modular capacity expansion."""
    facilities = ["F1", "F2", "F3", "F4", "F5"]
    customers = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
    scenarios = ["Low", "Base", "High"]

    scenario_probability = {
        "Low": 0.20,
        "Base": 0.50,
        "High": 0.30,
    }

    fixed_cost = {
        "F1": 165,
        "F2": 150,
        "F3": 180,
        "F4": 155,
        "F5": 170,
    }

    base_capacity = {
        "F1": 70,
        "F2": 60,
        "F3": 85,
        "F4": 65,
        "F5": 75,
    }

    module_capacity = {
        "F1": 25,
        "F2": 30,
        "F3": 35,
        "F4": 20,
        "F5": 25,
    }

    module_cost = {
        "F1": 55,
        "F2": 52,
        "F3": 68,
        "F4": 45,
        "F5": 58,
    }

    max_modules = {
        "F1": 2,
        "F2": 2,
        "F3": 2,
        "F4": 3,
        "F5": 2,
    }

    transport_cost = {
        ("F1", "C1"): 4,
        ("F1", "C2"): 5,
        ("F1", "C3"): 7,
        ("F1", "C4"): 8,
        ("F1", "C5"): 9,
        ("F1", "C6"): 6,
        ("F1", "C7"): 7,
        ("F1", "C8"): 8,
        ("F2", "C1"): 6,
        ("F2", "C2"): 4,
        ("F2", "C3"): 5,
        ("F2", "C4"): 7,
        ("F2", "C5"): 8,
        ("F2", "C6"): 9,
        ("F2", "C7"): 6,
        ("F2", "C8"): 5,
        ("F3", "C1"): 8,
        ("F3", "C2"): 7,
        ("F3", "C3"): 4,
        ("F3", "C4"): 3,
        ("F3", "C5"): 5,
        ("F3", "C6"): 6,
        ("F3", "C7"): 7,
        ("F3", "C8"): 8,
        ("F4", "C1"): 9,
        ("F4", "C2"): 8,
        ("F4", "C3"): 6,
        ("F4", "C4"): 4,
        ("F4", "C5"): 3,
        ("F4", "C6"): 5,
        ("F4", "C7"): 6,
        ("F4", "C8"): 7,
        ("F5", "C1"): 7,
        ("F5", "C2"): 6,
        ("F5", "C3"): 8,
        ("F5", "C4"): 7,
        ("F5", "C5"): 4,
        ("F5", "C6"): 3,
        ("F5", "C7"): 4,
        ("F5", "C8"): 5,
    }

    demand = {
        ("Low", "C1"): 18,
        ("Low", "C2"): 20,
        ("Low", "C3"): 16,
        ("Low", "C4"): 22,
        ("Low", "C5"): 14,
        ("Low", "C6"): 25,
        ("Low", "C7"): 19,
        ("Low", "C8"): 16,
        ("Base", "C1"): 24,
        ("Base", "C2"): 28,
        ("Base", "C3"): 20,
        ("Base", "C4"): 30,
        ("Base", "C5"): 18,
        ("Base", "C6"): 32,
        ("Base", "C7"): 24,
        ("Base", "C8"): 20,
        ("High", "C1"): 30,
        ("High", "C2"): 35,
        ("High", "C3"): 26,
        ("High", "C4"): 36,
        ("High", "C5"): 22,
        ("High", "C6"): 40,
        ("High", "C7"): 28,
        ("High", "C8"): 26,
    }

    total_demand = {
        scenario: sum(demand[scenario, customer] for customer in customers)
        for scenario in scenarios
    }

    return {
        "facilities": facilities,
        "customers": customers,
        "scenarios": scenarios,
        "scenario_probability": scenario_probability,
        "fixed_cost": fixed_cost,
        "base_capacity": base_capacity,
        "module_capacity": module_capacity,
        "module_cost": module_cost,
        "max_modules": max_modules,
        "transport_cost": transport_cost,
        "demand": demand,
        "total_demand": total_demand,
    }


def solve_scenario_subproblem(
    data: Dict[str, object],
    open_solution: Dict[str, int],
    module_solution: Dict[str, int],
    scenario: str,
) -> Dict[str, object]:
    """
    Distribution subproblem for one demand scenario.

    The recourse problem remains a transportation LP:
        - demand must be satisfied in the selected scenario
        - capacity depends on both facility openings and installed modules
    """
    facilities = data["facilities"]
    customers = data["customers"]
    base_capacity = data["base_capacity"]
    module_capacity = data["module_capacity"]
    transport_cost = data["transport_cost"]
    demand = data["demand"]

    sp = gp.Model(f"subproblem_{scenario}")
    sp.Params.OutputFlag = 0
    sp.Params.InfUnbdInfo = 1

    x = sp.addVars(facilities, customers, lb=0.0, name="ship")

    demand_con = sp.addConstrs(
        (
            gp.quicksum(x[i, j] for i in facilities) == demand[scenario, j]
            for j in customers
        ),
        name="demand",
    )

    capacity_con = sp.addConstrs(
        (
            gp.quicksum(x[i, j] for j in customers)
            <= base_capacity[i] * open_solution[i] + module_capacity[i] * module_solution[i]
            for i in facilities
        ),
        name="capacity",
    )

    sp.setObjective(
        gp.quicksum(transport_cost[i, j] * x[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE,
    )

    sp.optimize()

    if sp.Status == GRB.INFEASIBLE:
        return {"status": "infeasible"}

    if sp.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Unexpected subproblem status for {scenario}: {sp.Status}")

    shipments = {
        (i, j): x[i, j].X
        for i in facilities
        for j in customers
        if x[i, j].X > TOL
    }

    dual_demand = {j: demand_con[j].Pi for j in customers}
    dual_capacity = {i: capacity_con[i].Pi for i in facilities}

    return {
        "status": "optimal",
        "transport_cost": sp.ObjVal,
        "shipments": shipments,
        "dual_demand": dual_demand,
        "dual_capacity": dual_capacity,
    }


def solve_with_benders(
    data: Dict[str, object],
    max_iterations: int = 60,
    tolerance: float = 1e-6,
) -> Dict[str, object]:
    facilities = data["facilities"]
    customers = data["customers"]
    scenarios = data["scenarios"]
    scenario_probability = data["scenario_probability"]
    fixed_cost = data["fixed_cost"]
    base_capacity = data["base_capacity"]
    module_capacity = data["module_capacity"]
    module_cost = data["module_cost"]
    max_modules = data["max_modules"]
    demand = data["demand"]
    total_demand = data["total_demand"]

    master = gp.Model("advanced_facility_master")
    master.Params.OutputFlag = 0

    y = master.addVars(facilities, vtype=GRB.BINARY, name="open")
    z = master.addVars(
        facilities,
        lb=0,
        ub=gp.tupledict(max_modules),
        vtype=GRB.INTEGER,
        name="modules",
    )
    theta = master.addVars(scenarios, lb=0.0, name="theta")

    master.addConstrs(
        (z[i] <= max_modules[i] * y[i] for i in facilities),
        name="activate_modules_only_if_open",
    )

    master.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] + module_cost[i] * z[i] for i in facilities)
        + gp.quicksum(scenario_probability[s] * theta[s] for s in scenarios),
        GRB.MINIMIZE,
    )

    lower_bound = float("-inf")
    upper_bound = float("inf")
    feasibility_cuts = 0
    optimality_cuts = 0
    best_solution = None

    print("=" * 90)
    print("ADVANCED BENDERS: STOCHASTIC FACILITY LOCATION WITH CAPACITY EXPANSION")
    print("=" * 90)

    for iteration in range(1, max_iterations + 1):
        master.optimize()

        if master.Status != GRB.OPTIMAL:
            raise RuntimeError(f"Unexpected master status: {master.Status}")

        lower_bound = master.ObjVal
        open_solution = {i: int(round(y[i].X)) for i in facilities}
        module_solution = {i: int(round(z[i].X)) for i in facilities}
        theta_solution = {s: theta[s].X for s in scenarios}

        fixed_value = sum(fixed_cost[i] * open_solution[i] for i in facilities)
        module_value = sum(module_cost[i] * module_solution[i] for i in facilities)
        installed_capacity = sum(
            base_capacity[i] * open_solution[i] + module_capacity[i] * module_solution[i]
            for i in facilities
        )

        print(f"\nIteration {iteration}")
        print(f"  Master open decisions: {open_solution}")
        print(f"  Master expansion modules: {module_solution}")
        print(f"  Installed capacity: {installed_capacity:.2f}")
        print(f"  Fixed opening cost: {fixed_value:.2f}")
        print(f"  Module investment cost: {module_value:.2f}")
        print(f"  Bounds before scenarios: LB = {lower_bound:.2f}, UB = {upper_bound:.2f}")

        if best_solution is not None and upper_bound - lower_bound <= tolerance:
            print("  Global gap already closed with a feasible incumbent.")
            print("  Stop before resolving scenario subproblems.")
            break

        scenario_results = {}
        infeasible_scenarios = []

        for scenario in scenarios:
            scenario_result = solve_scenario_subproblem(
                data,
                open_solution,
                module_solution,
                scenario,
            )
            if scenario_result["status"] == "infeasible":
                infeasible_scenarios.append(scenario)
            else:
                scenario_results[scenario] = scenario_result

        if infeasible_scenarios:
            required_capacity = max(total_demand[s] for s in infeasible_scenarios)
            master.addConstr(
                gp.quicksum(
                    base_capacity[i] * y[i] + module_capacity[i] * z[i]
                    for i in facilities
                )
                >= required_capacity,
                name=f"feasibility_cut_{iteration}",
            )
            feasibility_cuts += 1
            print(f"  Infeasible scenarios: {infeasible_scenarios}")
            print(f"  Add strongest feasibility cut: total installed capacity >= {required_capacity}")
            continue

        expected_transport = sum(
            scenario_probability[s] * scenario_results[s]["transport_cost"] for s in scenarios
        )
        candidate_total = fixed_value + module_value + expected_transport

        if candidate_total < upper_bound - tolerance:
            upper_bound = candidate_total
            best_solution = {
                "open_facilities": open_solution,
                "expansion_modules": module_solution,
                "fixed_cost": fixed_value,
                "module_cost": module_value,
                "expected_transport_cost": expected_transport,
                "scenario_transport_costs": {
                    s: scenario_results[s]["transport_cost"] for s in scenarios
                },
                "scenario_shipments": {
                    s: scenario_results[s]["shipments"] for s in scenarios
                },
                "total_cost": candidate_total,
            }
            print(f"  New incumbent found -> UB updated to {upper_bound:.2f}")

        print(f"  Expected transport cost: {expected_transport:.2f}")
        print(f"  Candidate total cost: {candidate_total:.2f}")

        added_optimality_cuts = 0
        for scenario in scenarios:
            transport_value = scenario_results[scenario]["transport_cost"]
            theta_value = theta_solution[scenario]

            constant_term = sum(
                demand[scenario, customer] * scenario_results[scenario]["dual_demand"][customer]
                for customer in customers
            )

            cut_rhs = constant_term + gp.quicksum(
                base_capacity[i] * scenario_results[scenario]["dual_capacity"][i] * y[i]
                + module_capacity[i] * scenario_results[scenario]["dual_capacity"][i] * z[i]
                for i in facilities
            )

            cut_violation = transport_value - theta_value
            print(
                f"    Scenario {scenario}: theta = {theta_value:.2f}, "
                f"transport = {transport_value:.2f}, violation = {cut_violation:.6f}"
            )

            if cut_violation > tolerance:
                master.addConstr(
                    theta[scenario] >= cut_rhs,
                    name=f"optimality_cut_{iteration}_{scenario}",
                )
                optimality_cuts += 1
                added_optimality_cuts += 1

        print(f"  Bounds after scenarios: LB = {lower_bound:.2f}, UB = {upper_bound:.2f}")

        if added_optimality_cuts == 0:
            print("  No new optimality cuts were needed for this master solution.")

        if upper_bound - lower_bound <= tolerance:
            print("\nConvergence reached: UB - LB <= tolerance")
            break

    else:
        raise RuntimeError("Benders did not converge within the iteration limit.")

    if best_solution is None:
        raise RuntimeError("No feasible solution found by Benders.")

    best_solution["lower_bound"] = lower_bound
    best_solution["upper_bound"] = upper_bound
    best_solution["feasibility_cuts"] = feasibility_cuts
    best_solution["optimality_cuts"] = optimality_cuts
    return best_solution


def solve_integrated_model(data: Dict[str, object]) -> Dict[str, object]:
    """Deterministic equivalent with one recourse copy per scenario."""
    facilities = data["facilities"]
    customers = data["customers"]
    scenarios = data["scenarios"]
    scenario_probability = data["scenario_probability"]
    fixed_cost = data["fixed_cost"]
    base_capacity = data["base_capacity"]
    module_capacity = data["module_capacity"]
    module_cost = data["module_cost"]
    max_modules = data["max_modules"]
    transport_cost = data["transport_cost"]
    demand = data["demand"]

    model = gp.Model("advanced_integrated_model")
    model.Params.OutputFlag = 0

    y = model.addVars(facilities, vtype=GRB.BINARY, name="open")
    z = model.addVars(
        facilities,
        lb=0,
        ub=gp.tupledict(max_modules),
        vtype=GRB.INTEGER,
        name="modules",
    )
    x = model.addVars(scenarios, facilities, customers, lb=0.0, name="ship")

    model.addConstrs(
        (z[i] <= max_modules[i] * y[i] for i in facilities),
        name="activate_modules_only_if_open",
    )

    model.addConstrs(
        (
            gp.quicksum(x[s, i, j] for i in facilities) == demand[s, j]
            for s in scenarios
            for j in customers
        ),
        name="demand",
    )

    model.addConstrs(
        (
            gp.quicksum(x[s, i, j] for j in customers)
            <= base_capacity[i] * y[i] + module_capacity[i] * z[i]
            for s in scenarios
            for i in facilities
        ),
        name="capacity",
    )

    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] + module_cost[i] * z[i] for i in facilities)
        + gp.quicksum(
            scenario_probability[s] * transport_cost[i, j] * x[s, i, j]
            for s in scenarios
            for i in facilities
            for j in customers
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Unexpected integrated model status: {model.Status}")

    scenario_shipments = {}
    scenario_transport_costs = {}
    for scenario in scenarios:
        scenario_shipments[scenario] = {
            (i, j): x[scenario, i, j].X
            for i in facilities
            for j in customers
            if x[scenario, i, j].X > TOL
        }
        scenario_transport_costs[scenario] = sum(
            transport_cost[i, j] * x[scenario, i, j].X for i in facilities for j in customers
        )

    return {
        "open_facilities": {i: int(round(y[i].X)) for i in facilities},
        "expansion_modules": {i: int(round(z[i].X)) for i in facilities},
        "scenario_shipments": scenario_shipments,
        "scenario_transport_costs": scenario_transport_costs,
        "total_cost": model.ObjVal,
    }


def print_solution(title: str, solution: Dict[str, object], data: Dict[str, object]) -> None:
    facilities = data["facilities"]
    scenarios = data["scenarios"]

    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)

    open_facilities = solution["open_facilities"]
    modules = solution["expansion_modules"]
    chosen = [i for i in facilities if open_facilities[i] > 0.5]
    print(f"Open facilities: {chosen}")
    print(f"Installed modules: {modules}")

    if "fixed_cost" in solution:
        print(f"Fixed cost: {solution['fixed_cost']:.2f}")
    if "module_cost" in solution:
        print(f"Expansion module cost: {solution['module_cost']:.2f}")
    if "expected_transport_cost" in solution:
        print(f"Expected transport cost: {solution['expected_transport_cost']:.2f}")
    if "total_cost" in solution:
        print(f"Total cost: {solution['total_cost']:.2f}")
    if "lower_bound" in solution and "upper_bound" in solution:
        print(f"Final LB: {solution['lower_bound']:.2f}")
        print(f"Final UB: {solution['upper_bound']:.2f}")
        print(f"Feasibility cuts: {solution['feasibility_cuts']}")
        print(f"Optimality cuts: {solution['optimality_cuts']}")

    print("\nScenario transport costs:")
    for scenario in scenarios:
        scenario_cost = solution["scenario_transport_costs"][scenario]
        print(f"  {scenario}: {scenario_cost:.2f}")

    print("\nScenario shipments:")
    for scenario in scenarios:
        print(f"  {scenario}:")
        for (facility, customer), value in sorted(solution["scenario_shipments"][scenario].items()):
            print(f"    {facility} -> {customer}: {value:.2f}")


def main() -> None:
    data = build_data()
    benders_solution = solve_with_benders(data)
    integrated_solution = solve_integrated_model(data)

    print_solution("Advanced Benders solution", benders_solution, data)
    print_solution("Integrated stochastic equivalent (validation)", integrated_solution, data)

    if abs(benders_solution["total_cost"] - integrated_solution["total_cost"]) > TOL:
        print("\nWARNING: Benders and integrated model do not match.")
    else:
        print("\nValidation passed: Advanced Benders matches the integrated model.")


if __name__ == "__main__":
    main()
