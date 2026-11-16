# Staged simulation model

## Scope

The model is a generic airport-security checkpoint abstraction. It is not calibrated to a named
airport. It separates an upstream holding region, a controlled release gate, pedestrian transit,
a downstream screening queue, and parallel stochastic screening servers.

## Passenger flow

1. Synthetic passengers arrive under one of five processes: homogeneous Poisson,
   piecewise-nonhomogeneous Poisson, bursts, flight banks, or batched group arrivals.
2. Each passenger receives simulated bag count, group, reduced-mobility, compliance,
   walking-speed, static/moving footprint, and service-time attributes.
3. A policy S0--S5 releases passengers from the holding region.
4. Released passengers traverse a policy-specific parameterized route.
5. Passengers join a finite downstream queue and receive FCFS service from parallel servers.
6. Secondary screening and rare long inspections add explicit service-time components.

The one-second event grid is an engineering discretization. Arrival and completion times remain
continuous values, while gate decisions and service assignment occur on the grid.

## Policies

- **S0:** continuous conventional release toward a target downstream inventory.
- **S1:** full-row stationary batch release.
- **S2:** stationary sub-batch release.
- **S3:** batch release when the downstream queue is at or below a threshold.
- **S4:** release against noisy predicted near-term server capacity.
- **S5:** virtual-queue benchmark with just-in-time release.

Maximum holding time prevents an incomplete batch from waiting indefinitely. Downstream capacity
is enforced for every policy.

## State, action, and safeguard interface

At each decision epoch, the controller observes upstream waiting count, oldest waiting time,
downstream count, idle screening servers, and expected near-term completions. Its action is the
number of passengers released, bounded by waiting demand and downstream capacity. S3 withholds a
batch while downstream count exceeds its threshold, but the maximum-hold rule can force release
to prevent indefinite waiting. The primary throughput safeguard requires S3 to remain within 2%
of the paired S0 baseline; it does not encode or create additional screening capacity.

## Movement accounting

Route distance, turn count, row orientation, and gate delay are explicit geometry/control
parameters. Each passenger's movement time combines route traversal, startup/reaction delay,
slowdown delay, gate delay, luggage, and reduced mobility.
Under S0, every conventional-queue release increments `stop_go_events` for each passenger who
remains upstream. When that passenger is later released, starts equal one plus the accumulated
events and stops equal the accumulated events. S3 instead releases a bounded group when its
downstream-state rule permits, or when maximum hold is reached, and assigns one coordinated
movement with zero intermediate stops. The start/stop contrast is therefore a model-dependent
dynamic result produced by an explicit queue-progression rule interacting with congestion and
release timing. It is not an externally validated airport-passenger effect.

These are modeled locomotion endpoints. They are not physiological energy expenditure, injury,
or safety outcomes.

## Endpoint interpretation

| Endpoint | Mechanism | Classification |
|---|---|---|
| Distance | Configured route definition | Structural |
| Turning | Configured route definition | Structural |
| Movement starts/stops | Queue-progression and control rules plus congestion | Model-dependent dynamic |
| Throughput | Arrival, service, route, and control interaction | Dynamic |
| Waiting | Arrival, service, route, and control interaction | Dynamic |
| Required waiting area | Demand realization plus spatial assumptions | Conditional engineering outcome |

## Capacity, density, and accessibility

The model represents B0 belt switchback, B1 manual-gated rows, B2 automatic-gated rows, B3 visual
guidance, and B4 hybrid guidance as generic parameterized cases. It records count density, static
and moving footprint occupancy, density-limit exceedance, release-surge/conflict proxies,
required area, residual area, and capacity efficiency. Configuration validation rejects
accessible-route widths below 0.915 m and turning diameters below 1.525 m, based on the retained
ADA source. Passing these checks does not establish real-site regulatory compliance.

## Stochastic integrity

A single seed initializes arrivals, passenger attributes, service times, and predictive-control
error. Identical seeds preserve common synthetic passengers across policy runs. Policy-specific
random draws occur only after passenger generation.

Screening lanes may open or close on a deterministic schedule. Utilization uses available
server-time rather than treating closed lanes as idle capacity.

## Limits of the Phase 3 implementation

The geometry is route-level rather than a continuous collision-avoidance model. Footprint,
release-surge, conflict, density, and simultaneous-mover measures are operational proxies, not
validated crowd-safety measures. B0--B4 are not real airport layouts. Field calibration and
empirical validation remain outside the current evidence base. Validation of absolute starts
and stops per passenger requires passenger trajectories that also identify advance distance,
advance interval, luggage state, release compliance, simultaneous movers, staffing workload,
and screening starvation.
