"""Command line interface.

    msk run cases/padel_germany.yaml            # report + charts + Excel into reports/
    msk run cases/*.yaml                        # all cases
    msk new my_case                             # copy the template to cases/my_case.yaml
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .charts import human
from .model import load_case
from .report import build_report

TEMPLATE = Path(__file__).resolve().parents[2] / "cases" / "_template.yaml"


def cmd_run(args: argparse.Namespace) -> None:
    for p in args.cases:
        path = Path(p)
        if path.name.startswith("_"):
            continue
        case = load_case(path)
        report = build_report(case, args.out, path.stem)
        tam = case.funnel("base")["TAM"]
        print(f"✔ {case.name}: TAM base {human(tam, case.currency)}  →  {report}")


def cmd_new(args: argparse.Namespace) -> None:
    dest = Path("cases") / f"{args.name}.yaml"
    if dest.exists():
        raise SystemExit(f"{dest} already exists")
    dest.parent.mkdir(exist_ok=True)
    shutil.copy(TEMPLATE, dest)
    print(f"Created {dest}. Fill in the drivers and run: msk run {dest}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="msk", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="build report(s)")
    run.add_argument("cases", nargs="+")
    run.add_argument("--out", default="reports")
    run.set_defaults(func=cmd_run)
    new = sub.add_parser("new", help="start a new case from the template")
    new.add_argument("name")
    new.set_defaults(func=cmd_new)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
