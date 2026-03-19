from __future__ import annotations

"""Teaching example: capacitated facility location solved with Benders."""

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


def get_open_facilities(open_solution: Dict[str, int]) -> list[str]:
    """Return the facilities selected in a binary open/close solution."""
    return [facility for facility, is_open in open_solution.items() if is_open > 0.5]


def build_data() -> Dict[str, object]:
    """Small capacitated facility location instance."""
    facilities = ["F1", "F2", "F3", "F4"]
    customers = ["C1", "C2", "C3", "C4", "C5", "C6"]

    fixed_cost = {
        "F1": 120,
        "F2": 100,
        "F3": 130,
        "F4": 115,
    }

    capacity = {
        "F1": 90,
        "F2": 80,
        "F3": 110,
        "F4": 100,
    }

    demand = {
        "C1": 30,
        "C2": 25,
        "C3": 20,
        "C4": 40,
        "C5": 35,
        "C6": 20,
    }

    transport_cost = {
        ("F1", "C1"): 4,
        ("F1", "C2"): 6,
        ("F1", "C3"): 9,
        ("F1", "C4"): 5,
        ("F1", "C5"): 8,
        ("F1", "C6"): 7,
        ("F2", "C1"): 5,
        ("F2", "C2"): 4,
        ("F2", "C3"): 7,
        ("F2", "C4"): 8,
        ("F2", "C5"): 6,
        ("F2", "C6"): 5,
        ("F3", "C1"): 8,
        ("F3", "C2"): 7,
        ("F3", "C3"): 3,
        ("F3", "C4"): 4,
        ("F3", "C5"): 5,
        ("F3", "C6"): 6,
        ("F4", "C1"): 6,
        ("F4", "C2"): 5,
        ("F4", "C3"): 8,
        ("F4", "C4"): 6,
        ("F4", "C5"): 4,
        ("F4", "C6"): 3,
    }

    return {
        "facilities": facilities,
        "customers": customers,
        "fixed_cost": fixed_cost,
        "capacity": capacity,
        "demand": demand,
        "transport_cost": transport_cost,
        "total_demand": sum(demand.values()),
    }


def solve_transport_subproblem(
    data: Dict[str, object],
    open_solution: Dict[str, int],
) -> Dict[str, object]:
    """
    Transportation problem for a fixed open/close decision y.

    Min  sum c_ij * x_ij
    s.t. sum_i x_ij = demand_j                 for each customer j
         sum_j x_ij <= capacity_i * y_i       for each facility i
         x_ij >= 0
    """
    facilities = data["facilities"]
    customers = data["customers"]
    capacity = data["capacity"]
    demand = data["demand"]
    transport_cost = data["transport_cost"]

    sp = gp.Model("transport_subproblem")
    sp.Params.OutputFlag = 0
    sp.Params.InfUnbdInfo = 1

    x = sp.addVars(facilities, customers, lb=0.0, name="ship")

    demand_con = sp.addConstrs(
        (
            gp.quicksum(x[i, j] for i in facilities) == demand[j]
            for j in customers
        ),
        name="demand",
    )

    capacity_con = sp.addConstrs(
        (
            gp.quicksum(x[i, j] for j in customers) <= capacity[i] * open_solution[i]
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
        raise RuntimeError(f"Unexpected subproblem status: {sp.Status}")

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
    max_iterations: int = 50,
    tolerance: float = 1e-6,
) -> Dict[str, object]:
    """
    Manual single-cut Benders loop.

    Master:
        - binary open/close variables y[i]
        - continuous theta that approximates transportation cost

    Subproblem:
        - transportation LP for a fixed y
    """
    facilities = data["facilities"]
    customers = data["customers"]
    fixed_cost = data["fixed_cost"]
    capacity = data["capacity"]
    demand = data["demand"]
    total_demand = data["total_demand"]

    master = gp.Model("facility_master")
    master.Params.OutputFlag = 0

    y = master.addVars(facilities, vtype=GRB.BINARY, name="open")
    # theta is the master-side estimate of the subproblem value q(y).
    theta = master.addVar(lb=0.0, name="theta")

    master.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] for i in facilities) + theta,
        GRB.MINIMIZE,
    )

    best_solution = None
    lower_bound = float("-inf")
    upper_bound = float("inf")
    feasibility_cuts = 0
    optimality_cuts = 0

    print("=" * 78)
    print("BENDERS DECOMPOSITION FOR FACILITY LOCATION + DISTRIBUTION")
    print("=" * 78)

    for iteration in range(1, max_iterations + 1):
        master.optimize()

        if master.Status != GRB.OPTIMAL:
            raise RuntimeError(f"Unexpected master status: {master.Status}")

        lower_bound = master.ObjVal
        open_solution = {i: int(round(y[i].X)) for i in facilities}
        theta_value = theta.X
        open_capacity = sum(capacity[i] * open_solution[i] for i in facilities)
        fixed_value = sum(fixed_cost[i] * open_solution[i] for i in facilities)
        chosen_facilities = get_open_facilities(open_solution)

        print(f"\nIteration {iteration}")
        print(f"  Master y: {open_solution}")
        print(f"  Open facilities in master: {chosen_facilities}")
        print(f"  Master theta: {theta_value:.2f}")
        print(f"  Fixed cost from master: {fixed_value:.2f}")
        print(f"  Open capacity: {open_capacity:.2f} / demand {total_demand:.2f}")
        print(f"  Bounds before subproblem: LB = {lower_bound:.2f}, UB = {upper_bound:.2f}")

        # Once a feasible incumbent exists, LB = UB is enough to certify optimality.
        # We can stop before solving another subproblem and avoid a redundant cut.
        if best_solution is not None and upper_bound - lower_bound <= tolerance:
            print("  Global gap already closed with an incumbent solution.")
            print("  Stop before solving another subproblem.")
            break

        subproblem = solve_transport_subproblem(data, open_solution)

        if subproblem["status"] == "infeasible":
            # In this teaching example the network is complete, so infeasibility
            # happens exactly when total open capacity is smaller than total demand.
            master.addConstr(
                gp.quicksum(capacity[i] * y[i] for i in facilities) >= total_demand,
                name=f"feasibility_cut_{iteration}",
            )
            feasibility_cuts += 1
            print("  Subproblem infeasible -> add feasibility cut:")
            print(f"    sum(capacity[i] * y[i]) >= {total_demand}")
            continue

        transport_value = subproblem["transport_cost"]
        candidate_total = fixed_value + transport_value

        if candidate_total < upper_bound - tolerance:
            upper_bound = candidate_total
            best_solution = {
                "open_facilities": open_solution,
                "shipments": subproblem["shipments"],
                "fixed_cost": fixed_value,
                "transport_cost": transport_value,
                "total_cost": candidate_total,
            }
            print(f"  New incumbent found -> UB updated to {upper_bound:.2f}")

        constant_term = sum(
            demand[j] * subproblem["dual_demand"][j] for j in customers
        )

        # Benders optimality cut:
        # theta >= sum_j demand[j] * pi_j + sum_i capacity[i] * alpha_i * y_i
        cut_rhs = constant_term + gp.quicksum(
            capacity[i] * subproblem["dual_capacity"][i] * y[i] for i in facilities
        )

        cut_violation = transport_value - theta_value

        print(f"  Subproblem transport cost: {transport_value:.2f}")
        print(f"  Candidate total cost: {candidate_total:.2f}")
        print(f"  Bounds after subproblem: LB = {lower_bound:.2f}, UB = {upper_bound:.2f}")

        if cut_violation > tolerance:
            master.addConstr(theta >= cut_rhs, name=f"optimality_cut_{iteration}")
            optimality_cuts += 1
            print(f"  Add optimality cut (violation = {cut_violation:.6f})")
        else:
            print("  Current theta already supports this master solution.")

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
    """Direct MIP used only to validate the Benders result."""
    facilities = data["facilities"]
    customers = data["customers"]
    fixed_cost = data["fixed_cost"]
    capacity = data["capacity"]
    demand = data["demand"]
    transport_cost = data["transport_cost"]

    model = gp.Model("integrated_model")
    model.Params.OutputFlag = 0

    y = model.addVars(facilities, vtype=GRB.BINARY, name="open")
    x = model.addVars(facilities, customers, lb=0.0, name="ship")

    model.addConstrs(
        (
            gp.quicksum(x[i, j] for i in facilities) == demand[j]
            for j in customers
        ),
        name="demand",
    )

    model.addConstrs(
        (
            gp.quicksum(x[i, j] for j in customers) <= capacity[i] * y[i]
            for i in facilities
        ),
        name="capacity",
    )

    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] for i in facilities)
        + gp.quicksum(transport_cost[i, j] * x[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Unexpected integrated model status: {model.Status}")

    shipments = {
        (i, j): x[i, j].X
        for i in facilities
        for j in customers
        if x[i, j].X > TOL
    }

    return {
        "open_facilities": {i: int(round(y[i].X)) for i in facilities},
        "shipments": shipments,
        "total_cost": model.ObjVal,
    }


def print_solution(title: str, solution: Dict[str, object]) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)

    open_facilities = solution["open_facilities"]
    chosen = [i for i, value in open_facilities.items() if value > 0.5]
    print(f"Open facilities: {chosen}")

    if "fixed_cost" in solution:
        print(f"Fixed cost: {solution['fixed_cost']:.2f}")
    if "transport_cost" in solution:
        print(f"Transport cost: {solution['transport_cost']:.2f}")
    if "total_cost" in solution:
        print(f"Total cost: {solution['total_cost']:.2f}")
    if "lower_bound" in solution and "upper_bound" in solution:
        print(f"Final LB: {solution['lower_bound']:.2f}")
        print(f"Final UB: {solution['upper_bound']:.2f}")
        print(f"Feasibility cuts: {solution['feasibility_cuts']}")
        print(f"Optimality cuts: {solution['optimality_cuts']}")

    print("\nShipments:")
    for (facility, customer), value in sorted(solution["shipments"].items()):
        print(f"  {facility} -> {customer}: {value:.2f}")


def main() -> None:
    data = build_data()
    benders_solution = solve_with_benders(data)
    integrated_solution = solve_integrated_model(data)

    print_solution("Benders solution", benders_solution)
    print_solution("Integrated MIP solution (validation)", integrated_solution)

    if abs(benders_solution["total_cost"] - integrated_solution["total_cost"]) > TOL:
        print("\nWARNING: Benders and integrated model do not match.")
    else:
        print("\nValidation passed: Benders matches the integrated model.")


if __name__ == "__main__":
    main()
