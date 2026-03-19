Title: xxx
Course: Any Course
Student: Me
Professor: Mr. Professor Aros-Vera
Institution: Please accept me
Date: Today

---

# Master Thesis Level Model

## What I wanted to do with this version

In the basic and advanced examples, the logic of Benders is already clear, but the operational side is still fairly simple. In this version I wanted to move to something that feels closer to a real planning problem. That is why this model adds time, products, uncertainty, and operational carry-over decisions.

In practical terms, this version includes:

- multiple periods,
- multiple products,
- demand scenarios,
- inventory carried from one period to the next,
- time-phased capacity expansion,
- one Benders recourse variable per scenario.

Because of that, the model is no longer just "open facilities and ship to customers." It becomes a two-stage stochastic planning problem in which the strategic design must remain sensible across several possible demand realizations.

## Master problem

The master keeps the long-term decisions. In this case, it decides:

- which facilities are opened,
- how many capacity modules are added in each period,
- one `theta[s]` variable for each scenario.

I kept the strategic variables in the master because they are the hard combinatorial part of the model. This is the part that Benders tries to handle separately from the operational detail.

## Subproblem

Once the master fixes the strategic decisions, each scenario solves its own operational problem. The subproblem decides:

- production,
- shipments,
- inventory,
- backlog.

This means that each scenario answers a question like this: "Given the network I chose in the master, what is the cheapest way to operate it over time if this demand scenario happens?"

## Why this version is harder

### 1. Time matters

A capacity decision made in an early period affects every later period. So the model is not only choosing how much capacity to install, but also when it is better to install it.

### 2. Products compete for the same capacity

Different products consume capacity differently. Because of that, the model cannot optimize each product independently. There is a real coupling effect at the facility level.

### 3. Inventory creates intertemporal trade-offs

Producing now and storing for later can be cheaper than waiting, but only if that helps enough to compensate for holding costs. This adds another layer of planning logic.

### 4. Backlog gives complete recourse

I used backlog as a recourse mechanism so that the subproblem is always feasible. This avoids feasibility cuts and leaves the decomposition with optimality cuts only. That makes the implementation cleaner and also reflects a realistic idea: if demand is not served immediately, it is delayed at a penalty.

### 5. Multi-cut Benders improves the information flow

Instead of using a single `theta`, the master has one `theta[s]` per scenario. I used this because it gives more informative cuts and usually improves convergence in stochastic models.

## Computational result

The final validated solution for this instance was:

- open facilities: `F2` and `F4`,
- capacity modules added: none,
- total cost: `2984.73`,
- optimality cuts added: `27`.

The ending backlog is zero in every scenario, which is a good sign in this instance because it means the chosen network can absorb the demand without relying on delayed service in the last period.

## How I would explain the main takeaway

For me, the interesting part of this model is not just that it is bigger. The main difference is that the strategic design is now judged under uncertainty and over time. In other words, a facility decision is not good only because it is cheap today; it also has to remain useful across periods, products, and scenarios.

That is exactly the type of setting where Benders becomes attractive. The binary design remains in the master, while the operational complexity is pushed into scenario subproblems that can be solved more systematically.

## Run

```powershell
py "C:\Users\Ferna\Desktop\Facility Location and Distribution\03_master_thesis\master_thesis_multiperiod_benders.py"
```
