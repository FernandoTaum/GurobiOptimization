Title: xxx
Course: Any Course
Student: Me
Professor: Mr. Professor Aros-Vera
Institution: Please accept me
Date: Today

---

# PhD Thesis Level Model

## What makes this one feel research-oriented

In this last version I tried to move from a strong academic example to something that already looks like a research model. The point was not only to make it larger, but to combine several modeling dimensions that interact in a nontrivial way.

This version includes:

- multi-echelon network design,
- stochastic demand,
- supplier-side capacities,
- plant opening decisions,
- distribution-center opening decisions,
- modular capacity decisions,
- inventory at plant and DC levels,
- carbon-cap management with excess penalties,
- CVaR risk control in the master problem.

What makes the model interesting is that these pieces do not operate independently. Strategic design, operating cost, environmental performance, and risk exposure all influence each other.

## Master problem

The master contains the strategic and risk-related variables. It decides:

- which plants to open,
- which distribution centers to open,
- how many capacity modules to install,
- one `theta[s]` per scenario,
- the CVaR variables `eta` and `xi[s]`.

I kept those variables in the master because they define the long-run structure of the network and the risk attitude of the decision-maker.

## Subproblem

For each scenario, the subproblem handles the operational response. It decides:

- supplier-to-plant flows,
- plant-to-DC flows,
- DC-to-customer flows,
- plant inventory,
- DC inventory,
- backlog,
- carbon excess.

So each subproblem measures how expensive it is to operate the chosen network under one possible realization of demand.

## Why this is much more complex than the previous versions

### 1. The network has several layers

This is no longer a one-stage shipping problem. The model has four connected layers:

- suppliers,
- plants,
- distribution centers,
- customers.

That makes the operational structure richer because capacity and inventory choices at one layer affect the others.

### 2. There is an environmental trade-off

The model explicitly tracks emissions and allows carbon-cap violations through a penalized excess variable. I used this so the network does not become artificially infeasible when emissions are high, but the model still "feels" the cost of polluting more than the cap allows.

### 3. Risk is part of the design decision

This version does not optimize only expected cost. It also includes CVaR, which means the master is penalizing bad tail outcomes. That makes the design more conservative when extreme scenarios are expensive.

### 4. The recourse is complete

Backlog and carbon excess keep the subproblem feasible in all scenarios. From a decomposition point of view, that is convenient because the algorithm can focus on optimality cuts only.

### 5. The Benders cuts carry more structure

The cuts now summarize the operational effect of:

- supplier limits,
- plant capacity,
- DC capacity,
- storage decisions,
- environmental penalties,
- scenario-specific recourse values.

So the cuts are not only saying "this design is expensive." They are telling the master why the design becomes expensive under each scenario.

## Computational result

For the instance implemented here, the validated optimal solution was:

- open plants: `PL1`,
- open distribution centers: `D1`,
- capacity modules added: none,
- total objective value: `3907.51`,
- optimality cuts added: `55`.

The scenario-level carbon excess values were:

- `Baseline`: `5.93`,
- `Expansion`: `12.81`,
- `Stress`: `42.13`.

I like reporting these numbers because they show that the environmental part is actually active in the model and not just decorative.

## Main interpretation

What I find most interesting in this model is that the "best" network is no longer defined by cost alone. A design can be cheap in expectation and still perform badly in stress scenarios, or it can satisfy demand while generating a large emissions penalty. Once CVaR and carbon terms are included, the model starts balancing cost, resilience, and environmental pressure at the same time.

That is why this version feels closer to a PhD-style example. The challenge is not only computational size, but also the coexistence of multiple modeling objectives inside one decomposition framework.

## Run

```powershell
py "C:\Users\Ferna\Desktop\Facility Location and Distribution\04_phd_thesis\phd_thesis_multiechelon_benders.py"
```
