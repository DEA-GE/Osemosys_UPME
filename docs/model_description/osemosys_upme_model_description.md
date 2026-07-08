# OSeMOSYS UPME Model Description

## Source Scenario

The previous version of this documentation was generated from the repository's root `CSV` input folder. That scenario had 1 timeslice, 394 technologies, 109 fuels, 3 emissions, 33 years, 364,717 Pyomo variable entries, and 409,207 active constraints.

This updated version describes the attached SAND workbook:

```text
SAND/PD_2TS_41D_2055_SAND_03Jun2026.xlsx
```

The workbook was converted to OSeMOSYS CSV inputs with the repository converter in `backend/app/simulation/core/excel_to_csv.py`, preserving all timeslices with `div=1`. The generated intermediate CSVs are stored under:

```text
docs/model_description/generated/PD_2TS_41D_2055_SAND_03Jun2026_csv
```

The workbook conversion produced no active storage or UDC CSV files, so the Pyomo model was instantiated with `has_storage=False` and `has_udc=False`.

## Executive Summary

This repository runs a Pyomo implementation of OSeMOSYS, a long-term energy-system optimization model. The updated `PD_2TS_41D_2055_SAND_03Jun2026.xlsx` instance is a large deterministic linear programming problem when solved with continuous capacity and activity decisions.

Strictly, the code declares integer variables for technology unit investments through `NumberOfNewTechnologyUnits`. In this workbook, `CapacityOfOneTechnologyUnit` is zero everywhere, so those discrete unit-size constraints are inactive. In practical terms, the solved instance behaves as a linear program.

## Mathematical Problem Type

The model minimizes total discounted system cost subject to technical, economic, demand, emissions, reserve-margin, and policy constraints.

Objective:

```text
Minimize total discounted system cost over all regions and years
```

The cost accounting includes investment costs, fixed and variable operating costs, emissions penalties, salvage value, disposal cost, and recovery value.

## Solver Interfaces

The repository maps solver names to Pyomo solver factories as follows:

| Requested solver | Pyomo solver factory |
|---|---|
| `highs` | `appsi_highs` |
| `gurobi` | `gurobi` |
| `glpk` | `glpk` |

If `GLPX` is mentioned, the intended solver is almost certainly `GLPK`.

## Current Model Instance Size

The following counts were obtained by converting `PD_2TS_41D_2055_SAND_03Jun2026.xlsx` to CSV inputs and instantiating the repository's Pyomo model.

| Characteristic | Count |
|---|---:|
| Regions | 1 |
| Technologies | 405 |
| Fuels | 114 |
| Emissions | 11 |
| Years | 34 |
| Year range | 2022-2055 |
| Timeslices | 2 |
| Modes of operation | 1 |
| Active storage technologies | 0 |
| UDC groups | 0 |
| Pyomo variable entries | 744,574 |
| Declared integer variable entries | 13,770 |
| Binary variables | 0 |
| Active constraints/equations | 812,409 |
| Approximate nonzero variable appearances in constraints | 4,642,606 |

Important note: storage and user-defined constraint features exist in the codebase, but this workbook conversion did not produce active storage or UDC input files. Therefore storage variables, storage equations, and UDC equations are inactive for this documented run.

## Main Decision and Accounting Variables

| Variable family | Meaning |
|---|---|
| `NewCapacity` | New technology capacity installed |
| `RateOfActivity` | Technology activity or dispatch by timeslice |
| `CapitalInvestment` | Investment cost accounting |
| `OperatingCost` | Fixed and variable operating cost accounting |
| `AnnualTechnologyEmission` | Emissions by technology, emission type, and year |
| `AnnualEmissions` | Total annual emissions by emission type |
| `TotalDiscountedCost` | Annual discounted system cost |
| `TotalCapacityInReserveMargin` | Capacity counted toward reserve margin |
| `NumberOfNewTechnologyUnits` | Integer unit count, declared but inactive in this dataset |

## Largest Active Variable Blocks

| Variable block | Count |
|---|---:|
| `AnnualTechnologyEmissionByMode` | 151,470 |
| `AnnualTechnologyEmission` | 151,470 |
| `AnnualTechnologyEmissionPenaltyByEmission` | 151,470 |
| `RateOfActivity` | 27,540 |
| `VariableOperatingCost` | 27,540 |
| `NumberOfNewTechnologyUnits` | 13,770 |
| `NewCapacity` | 13,770 |
| `SalvageValue` | 13,770 |
| `DiscountedSalvageValue` | 13,770 |
| `OperatingCost` | 13,770 |
| `CapitalInvestment` | 13,770 |
| `DiscountedCapitalInvestment` | 13,770 |

## Main Constraint Categories

The model includes the following main groups of constraints:

| Category | Purpose |
|---|---|
| Demand balance | Energy supplied must satisfy demand by fuel, year, and timeslice |
| Capacity constraints | Activity cannot exceed available installed capacity |
| Investment constraints | New capacity is bounded by annual min/max investment limits |
| Activity constraints | Technologies may have lower or upper activity bounds |
| Emissions accounting and limits | Emissions are calculated, penalized, and optionally bounded |
| Reserve margin | Capacity adequacy constraints for selected technologies and fuels |
| User-defined constraints | Supported by the code, but inactive in this workbook conversion |
| Storage constraints | Supported by the code, but inactive in this workbook conversion |

## Largest Active Constraint Blocks

| Constraint family | Active constraints |
|---|---:|
| `AnnualEmissionProductionByMode` | 151,470 |
| `AnnualEmissionProduction` | 151,470 |
| `EmissionPenaltyByTechAndEmission` | 151,470 |
| `ConstraintCapacity` | 27,540 |
| `PlannedMaintenance` | 13,770 |
| `UndiscountedCapitalInvestment` | 13,770 |
| `DiscountedCapitalInvestment_constraint` | 13,770 |
| `OperatingCostsVariable` | 13,770 |
| `OperatingCostsFixedAnnual` | 13,770 |
| `OperatingCostsTotalAnnual` | 13,770 |
| `DiscountedOperatingCostsTotalAnnual` | 13,770 |
| `TotalDiscountedCostByTechnology_constraint` | 13,770 |
| `TotalAnnualMinCapacityConstraint` | 13,770 |
| `SalvageValueAtEndOfPeriod1` | 13,770 |
| `SalvageValueDiscountedToStartYear` | 13,770 |

In optimization terminology, the word "equations" is often used informally for all expanded active constraints, including both equalities and inequalities. This documented workbook instance has 812,409 active constraints/equations.

## Technologies With Restrictions

There are 405 technologies in the active model set. Using non-default capacity, activity, reserve-margin, renewable-energy tag, unit-size, and UDC parameters as the definition of having an active restriction, all 405 technologies have at least one active restriction in this workbook-derived instance.

| Restriction parameter | Technologies affected | Active rows |
|---|---:|---:|
| `TotalAnnualMaxCapacity` | 404 | 13,736 |
| `TotalAnnualMaxCapacityInvestment` | 405 | 13,770 |
| `TotalAnnualMinCapacity` | 2 | 60 |
| `TotalAnnualMinCapacityInvestment` | 16 | 209 |
| `TotalTechnologyAnnualActivityUpperLimit` | 404 | 13,736 |
| `TotalTechnologyAnnualActivityLowerLimit` | 211 | 6,084 |
| `TotalTechnologyModelPeriodActivityUpperLimit` | 405 | 405 |
| `ReserveMarginTagTechnology` | 25 | 850 |

No active technology restrictions were found for the following categories in this workbook-derived instance:

| Parameter or category | Status |
|---|---|
| `CapacityOfOneTechnologyUnit` | All zero, so integer unit constraints are inactive |
| `TotalTechnologyModelPeriodActivityLowerLimit` | No nonzero active values |
| `RETagTechnology` | No active technology tags |
| `UDCMultiplierTotalCapacity` | No UDC CSV was generated for this workbook |
| Storage technology constraints | Storage set is empty |

## Suggested Narrative Description

The model can be described as follows:

> We run a Pyomo implementation of OSeMOSYS, a deterministic long-term energy-system optimization model. The model minimizes total discounted system cost while satisfying demand, capacity, activity, emissions, reserve-margin, and policy constraints. The documented instance is based on `PD_2TS_41D_2055_SAND_03Jun2026.xlsx` and covers 1 region, 405 technologies, 114 fuels, 11 emissions, 2 timeslices, and 34 model years from 2022 through 2055. It expands to 744,574 Pyomo variable entries and 812,409 active constraints. Although the formulation supports integer capacity-unit decisions, this workbook has no active unit-size constraints, so the solved problem is effectively a large linear program. The model can be solved with HiGHS, Gurobi, or GLPK through Pyomo.

## Repository References

Key implementation files:

| File | Role |
|---|---|
| `backend/app/simulation/core/model_definition.py` | Defines sets, parameters, variables, objective, and constraints |
| `backend/app/simulation/core/instance_builder.py` | Loads CSV sets and parameters into the Pyomo model |
| `backend/app/simulation/core/excel_to_csv.py` | Converts SAND Excel workbooks into OSeMOSYS CSV inputs |
| `backend/app/simulation/core/solver.py` | Maps solver names and runs HiGHS, Gurobi, or GLPK |
| `backend/app/simulation/README.md` | Documents the simulation workflow |

External OSeMOSYS references:

- OSeMOSYS documentation: https://osemosys.readthedocs.io/en/latest/
- OSeMOSYS model structure: https://osemosys.readthedocs.io/en/latest/manual/Structure%20of%20OSeMOSYS.html
- OSeMOSYS project overview: https://osemosys.github.io/about/
