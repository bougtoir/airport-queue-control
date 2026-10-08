# Simulation output schema

Each CLI run writes four files.

## `summary.json`

One scalar record containing:

- demand, completion, and unfinished counts;
- throughput, utilization, and starvation;
- upstream, downstream, system, and percentile waiting times;
- movement distance, starts, stops, turning angle, and movement time;
- queue, count-density, footprint-density, release-surge, conflict-proxy, simultaneous-mover,
  residual-area, required-area, and capacity-efficiency metrics;
- wait inequality, overtaking, staffing/intervention, and subgroup wait gaps;
- policy, layout, row angle, seed, arrival process, service distribution, and accessibility
  dimensions.

## `passengers.csv`

One row per simulated passenger containing immutable attributes and event timestamps:
arrival, release, downstream-queue arrival, service start, completion, assigned server, bag count,
group/mobility class, static/moving footprint, movement endpoints, intervention status, and
stop-go episodes. Missing timestamps identify passengers unfinished at the drain limit.

## `trajectory.csv`

One row per simulation time step containing upstream waiting, in-transit passengers, downstream
queue, active/busy servers, count and footprint densities, release size/surge, and cumulative
completions.

## `config_resolved.yaml`

The complete resolved configuration used for the run. It is the authoritative parameter record
for that output directory.
