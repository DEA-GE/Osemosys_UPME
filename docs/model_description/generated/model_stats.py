from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from pyomo.core.expr.visitor import identify_variables
from pyomo.environ import Constraint, Var

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.simulation.core.instance_builder import build_instance  # noqa: E402
from app.simulation.core.model_definition import create_abstract_model  # noqa: E402


DEFAULT_HIGH = {
    "TotalAnnualMaxCapacity": 9999999,
    "TotalAnnualMaxCapacityInvestment": 9999999,
    "TotalTechnologyAnnualActivityUpperLimit": 9999999,
    "TotalTechnologyModelPeriodActivityUpperLimit": 9999999,
}


def count_non_default_rows(csv_dir: Path, name: str) -> dict[str, int]:
    path = csv_dir / f"{name}.csv"
    if not path.exists():
        return {"technologies": 0, "rows": 0}
    df = pd.read_csv(path)
    if df.empty or "VALUE" not in df.columns or "TECHNOLOGY" not in df.columns:
        return {"technologies": 0, "rows": 0}
    values = pd.to_numeric(df["VALUE"], errors="coerce")
    if name in DEFAULT_HIGH:
        mask = values.notna() & (values != DEFAULT_HIGH[name])
    else:
        mask = values.notna() & (values != 0)
    active = df.loc[mask]
    return {
        "technologies": int(active["TECHNOLOGY"].astype(str).nunique()),
        "rows": int(len(active)),
    }


def main() -> None:
    csv_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "CSV"
    has_storage = (csv_dir / "STORAGE.csv").exists() and pd.read_csv(csv_dir / "STORAGE.csv").shape[0] > 0
    has_udc = (csv_dir / "UDC.csv").exists() and pd.read_csv(csv_dir / "UDC.csv").shape[0] > 0

    model = create_abstract_model(has_storage=has_storage, has_udc=has_udc)
    instance = build_instance(model, str(csv_dir), has_storage=has_storage, has_udc=has_udc)

    var_blocks = {
        comp.local_name: sum(1 for _ in comp.values())
        for comp in instance.component_objects(Var, active=True)
    }
    con_blocks = {
        comp.local_name: sum(1 for _ in comp.values())
        for comp in instance.component_objects(Constraint, active=True)
    }

    approx_var_appearances = 0
    for constraint in instance.component_data_objects(Constraint, active=True):
        approx_var_appearances += len(list(identify_variables(constraint.body, include_fixed=False)))

    restrictions = {}
    for name in [
        "TotalAnnualMaxCapacity",
        "TotalAnnualMaxCapacityInvestment",
        "TotalAnnualMinCapacity",
        "TotalAnnualMinCapacityInvestment",
        "TotalTechnologyAnnualActivityUpperLimit",
        "TotalTechnologyAnnualActivityLowerLimit",
        "TotalTechnologyModelPeriodActivityUpperLimit",
        "TotalTechnologyModelPeriodActivityLowerLimit",
        "CapacityOfOneTechnologyUnit",
        "ReserveMarginTagTechnology",
        "RETagTechnology",
        "UDCMultiplierTotalCapacity",
    ]:
        restrictions[name] = count_non_default_rows(csv_dir, name)

    restricted_techs = set()
    for name, counts in restrictions.items():
        if counts["rows"] == 0:
            continue
        path = csv_dir / f"{name}.csv"
        df = pd.read_csv(path)
        values = pd.to_numeric(df["VALUE"], errors="coerce")
        mask = values.notna() & (values != (DEFAULT_HIGH.get(name, 0)))
        restricted_techs.update(df.loc[mask, "TECHNOLOGY"].astype(str).tolist())

    result = {
        "csv_dir": str(csv_dir),
        "has_storage": has_storage,
        "has_udc": has_udc,
        "sets": {
            "regions": len(instance.REGION),
            "technologies": len(instance.TECHNOLOGY),
            "fuels": len(instance.FUEL),
            "emissions": len(instance.EMISSION),
            "years": len(instance.YEAR),
            "timeslices": len(instance.TIMESLICE),
            "modes": len(instance.MODE_OF_OPERATION),
            "storage": len(instance.STORAGE) if has_storage else 0,
            "udc": len(instance.UDC) if has_udc else 0,
        },
        "year_min": min(int(y) for y in instance.YEAR),
        "year_max": max(int(y) for y in instance.YEAR),
        "variable_entries": sum(1 for _ in instance.component_data_objects(Var, active=True)),
        "integer_variable_entries": sum(
            1 for v in instance.component_data_objects(Var, active=True) if v.is_integer()
        ),
        "binary_variables": sum(
            1 for v in instance.component_data_objects(Var, active=True) if v.is_binary()
        ),
        "active_constraints": sum(
            1 for _ in instance.component_data_objects(Constraint, active=True)
        ),
        "approx_nonzero_variable_appearances": approx_var_appearances,
        "largest_var_blocks": dict(sorted(var_blocks.items(), key=lambda kv: kv[1], reverse=True)[:12]),
        "largest_constraint_blocks": dict(
            sorted(con_blocks.items(), key=lambda kv: kv[1], reverse=True)[:15]
        ),
        "restrictions": restrictions,
        "restricted_technologies": len(restricted_techs),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
