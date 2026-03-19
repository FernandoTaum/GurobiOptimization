# Facility Location and Distribution using Benders Decomposition

## Cover Page

**Title:** xxx  
**Course:** Any Course  
**Student:** Me  
**Professor:** Mr. Professor Aros-Vera  
**Institution:** Please accept me  
**Date:** Today  

## Abstract

In this report I wanted to show a small but complete facility location and distribution example solved with Benders Decomposition in Python and Gurobi. The main idea is to separate strategic opening decisions from day-to-day transportation decisions. Instead of solving everything at once, the master problem decides which facilities are open and the subproblem computes the minimum distribution cost for that network. Even though the instance is small, it is enough to show how Benders learns through cuts and converges to the same optimal solution as the integrated model.

**Keywords:** facility location, Benders decomposition, optimization, Gurobi, mathematical programming, distribution.

---

## 1. Introduction

Facility location problems are classical models in operations research and logistics. Their goal is to decide where to place service centers, plants, warehouses, or hubs while balancing fixed opening costs and variable distribution costs.

When a problem includes:

- binary opening decisions,
- continuous allocation or distribution decisions,
- capacity constraints,

the resulting formulation is a mixed-integer linear programming problem. For large instances, solving the full monolithic model can become difficult. That is where Benders Decomposition becomes useful, because it separates:

- strategic decisions, handled by the master problem,
- operational decisions, handled by the subproblem.

My goal in this document is to present the methodology in a way that stays technically rigorous but still feels easy to follow.

---

## 2. Problem description

Consider a set of candidate facilities `I` and a set of customers `J`.

Each facility `i in I` has:

- a fixed opening cost `f_i`,
- a maximum capacity `s_i`.

Each customer `j in J` has:

- a demand `d_j`.

Shipping one unit from facility `i` to customer `j` incurs a unit transportation cost `c_ij`.

The objective is to decide:

1. which facilities to open,
2. how much to ship from each open facility to each customer,

so that all customer demand is satisfied at minimum total cost.

---

## 3. Notation

### 3.1 Sets

- `I`: set of candidate facilities.
- `J`: set of customers.

### 3.2 Parameters

- `f_i`: fixed opening cost of facility `i`.
- `s_i`: capacity of facility `i`.
- `d_j`: demand of customer `j`.
- `c_ij`: unit transportation cost from facility `i` to customer `j`.

### 3.3 Decision variables

#### Variables in the integrated model

- `y_i in {0,1}`: equals `1` if facility `i` is opened, `0` otherwise.
- `x_ij >= 0`: quantity shipped from facility `i` to customer `j`.

#### Additional variable in Benders

- `theta`: approximation of the optimal distribution cost returned by the subproblem.

---

## 4. Integrated formulation

The monolithic formulation of the problem is:

```text
min  sum_{i in I} f_i y_i + sum_{i in I} sum_{j in J} c_ij x_ij

s.t. sum_{i in I} x_ij = d_j                      for all j in J
     sum_{j in J} x_ij <= s_i y_i                for all i in I
     y_i in {0,1}                                for all i in I
     x_ij >= 0                                   for all i in I, j in J
```

### Interpretation

- The first part of the objective represents fixed facility-opening costs.
- The second part represents variable transportation costs.
- The first family of constraints guarantees full demand satisfaction.
- The second family limits the total shipments from each facility by its available capacity.

---

## 5. Benders Decomposition

The key idea of Benders is to project the problem onto the binary variables `y`, leaving the transportation decisions to a separate subproblem.

### 5.1 Master problem

The master problem is:

```text
min  sum_{i in I} f_i y_i + theta

s.t. Benders cuts
     y_i in {0,1}                 for all i in I
     theta >= 0
```

#### Role of the master problem

The master problem handles the location decisions:

- which facilities are opened,
- what lower bound is currently valid for the transportation cost.

### 5.2 Subproblem

For a fixed solution `y = y^k`, the subproblem is:

```text
q(y^k) = min  sum_{i in I} sum_{j in J} c_ij x_ij

s.t.     sum_{i in I} x_ij = d_j                      for all j in J
         sum_{j in J} x_ij <= s_i y_i^k              for all i in I
         x_ij >= 0                                   for all i in I, j in J
```

#### Role of the subproblem

The subproblem computes the minimum transportation cost compatible with the facility-opening decision proposed by the master problem.

---

## 6. Relationship between the master and the subproblem

The key link between both models is the capacity restriction:

```text
sum_{j in J} x_ij <= s_i y_i
```

This means:

- if `y_i = 0`, facility `i` cannot ship anything,
- if `y_i = 1`, it can ship up to its capacity `s_i`.

Therefore:

- the master defines the network structure,
- the subproblem computes the best operating plan within that structure.

---

## 7. Intuition behind Benders Decomposition

Instead of solving a single large MIP, Benders follows an iterative process:

1. the master proposes a facility configuration,
2. the subproblem evaluates that configuration,
3. if it is infeasible, a feasibility cut is added,
4. if it is feasible, an optimality cut is added,
5. the master is solved again with the new information.

The intuition is that the master starts with incomplete knowledge and the cuts progressively correct that lack of information.

---

## 8. Benders cuts

### 8.1 Feasibility cut

In this example, every facility can serve every customer. Therefore, the subproblem is infeasible only when total open capacity is smaller than total demand.

The feasibility cut used here is:

```text
sum_{i in I} s_i y_i >= sum_{j in J} d_j
```

For this instance:

```text
sum_{i in I} s_i y_i >= 170
```

This cut is valid because the network is complete.

### 8.2 Optimality cut

The dual of the subproblem is:

```text
max  sum_{j in J} d_j pi_j + sum_{i in I} s_i y_i alpha_i

s.t. pi_j + alpha_i <= c_ij              for all i in I, j in J
     pi_j free                           for all j in J
     alpha_i <= 0                        for all i in I
```

Using an optimal dual solution `(pi^k, alpha^k)`, the optimality cut is:

```text
theta >= sum_{j in J} d_j pi_j^k + sum_{i in I} s_i alpha_i^k y_i
```

This cut forces the master problem to recognize a realistic lower bound on the transportation cost.

---

## 9. Solution algorithm

### 9.1 Pseudocode

```text
Initialize the master with variables y and theta
Initialize UB = +infinity
Initialize LB = -infinity

Repeat:
    Solve the master problem
    Obtain y^k
    Update LB

    If an incumbent already exists and UB - LB <= tolerance:
        stop

    Solve the subproblem with y = y^k

    If the subproblem is infeasible:
        add a feasibility cut to the master
    Else:
        compute the transportation cost q(y^k)
        update UB with fixed cost + q(y^k)
        recover the dual solution
        add an optimality cut to the master

Until UB - LB <= tolerance
```

### 9.2 Methodological remark

The algorithm implemented in the Python script is a manual and educational single-cut Benders loop. In larger production settings, cuts are typically generated through Gurobi callbacks.

---

## 10. Instance data

### 10.1 Facilities

- `F1, F2, F3, F4`

### 10.2 Customers

- `C1, C2, C3, C4, C5, C6`

### 10.3 Fixed opening costs

- `F1 = 120`
- `F2 = 100`
- `F3 = 130`
- `F4 = 115`

### 10.4 Capacities

- `F1 = 90`
- `F2 = 80`
- `F3 = 110`
- `F4 = 100`

### 10.5 Demands

- `C1 = 30`
- `C2 = 25`
- `C3 = 20`
- `C4 = 40`
- `C5 = 35`
- `C6 = 20`

Total demand:

- `170`

### 10.6 Transportation cost matrix

The full cost matrix is defined in [benders_facility_location.py](C:\Users\Ferna\Desktop\Facility Location and Distribution\01_basic\benders_facility_location.py).

---

## 11. Computational results

Running the algorithm yields:

- optimal total cost `975`,
- open facilities: `F2` and `F3`,
- `1` feasibility cut,
- `6` optimality cuts,
- convergence with `LB = UB = 975`.

### 11.1 Optimal distribution plan

- `F2 -> C1 = 30`
- `F2 -> C2 = 25`
- `F2 -> C6 = 20`
- `F3 -> C3 = 20`
- `F3 -> C4 = 40`
- `F3 -> C5 = 35`

### 11.2 Cost breakdown

- total fixed cost = `230`
- total transportation cost = `745`
- total cost = `975`

### 11.3 Validation

The script also solves the integrated model directly. The result matches the Benders solution exactly. Therefore, the decomposition-based implementation is correct for this instance.

---

## 12. Interpretation of the solution

The optimal result indicates that opening facilities `F2` and `F3` provides the best trade-off between:

- fixed opening cost,
- unit transportation cost,
- sufficient total capacity.

It is not enough to open the cheapest facilities, because that may increase the operating cost. Likewise, it is not enough to minimize transportation cost alone, because that may require opening too many facilities. The optimization model balances both effects simultaneously.

---

## 13. Common mistakes

1. Omitting `theta` in the master problem.
   In that case, the master ignores transportation cost and usually opens too few facilities.

2. Getting the dual signs wrong.
   In this formulation, the dual variables associated with facility capacities must be non-positive.

3. Making the subproblem integer.
   Classical dual-based Benders requires a continuous linear subproblem.

4. Using an oversimplified feasibility cut in a non-complete network.
   The aggregate capacity cut used here is valid only because every facility can serve every customer.

5. Misinterpreting convergence.
   If a feasible incumbent exists and `LB = UB`, the optimum is already certified.

---

## 14. Recommendations for scaling the model

1. Use the integrated model as a benchmark for small instances.

2. Move cut generation to Gurobi callbacks for better scalability.

3. Use multi-cuts when the subproblem structure justifies it.

4. Strengthen the master problem with additional valid inequalities.

5. Reduce the transportation network whenever infeasible arcs can be removed.

6. Consider realistic extensions:
   - multi-period planning,
   - stepwise fixed costs,
   - uncertain demand,
   - multiple products.

---

## 15. Conclusions

For me, this example is useful because it shows in a very transparent way how the logic of Benders works on a classical facility location setting.

The main takeaways are:

- the master problem keeps the strategic opening decisions,
- the subproblem handles the operational distribution decisions,
- Benders cuts are what allow both parts to communicate,
- the decomposition-based approach matches the integrated model exactly for this instance.

From a teaching point of view, I think this is a good starting example because it is small enough to follow step by step, but still rich enough to show why separating binary strategic decisions from continuous operational ones can be so effective.

---

## 16. Suggested references

- Benders, J. F. (1962). Partitioning procedures for solving mixed-variables programming problems.
- Daskin, M. S. Facility Location: Applications and Theory.
- Conejo, Castillo, Minguez, and Garcia-Bertrand. Decomposition Techniques in Mathematical Programming.
- Official Gurobi documentation for MIP modeling and LP dual values.

---

## Appendix A. Project files

- [benders_facility_location.py](C:\Users\Ferna\Desktop\Facility Location and Distribution\01_basic\benders_facility_location.py)
- [README.md](C:\Users\Ferna\Desktop\Facility Location and Distribution\README.md)
- [INFORME_BENDERS_FACILITY_LOCATION.md](C:\Users\Ferna\Desktop\Facility Location and Distribution\01_basic\INFORME_BENDERS_FACILITY_LOCATION.md)
- [ENTREGA_ACADEMICA_BENDERS.md](C:\Users\Ferna\Desktop\Facility Location and Distribution\01_basic\ENTREGA_ACADEMICA_BENDERS.md)
- [ACADEMIC_REPORT_BENDERS_EN.md](C:\Users\Ferna\Desktop\Facility Location and Distribution\01_basic\ACADEMIC_REPORT_BENDERS_EN.md)
- [requirements.txt](C:\Users\Ferna\Desktop\Facility Location and Distribution\requirements.txt)
