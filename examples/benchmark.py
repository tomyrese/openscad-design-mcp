import argparse
import json
import statistics
import time
from pathlib import Path

from openscad_design_mcp.config import Settings
from openscad_design_mcp.service import DesignService

MODELS = {
    "cube": "cube([20,20,10],center=true);",
    "plate": "difference(){cube([60,40,4],center=true);"
    "for(x=[-20,0,20],y=[-10,10])translate([x,y,0])cylinder(h=8,r=3,center=true,$fn=48);}",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 20:
        parser.error("repeats must be between 1 and 20")
    settings = Settings(workspace=Path.cwd() / "workspace" / "benchmarks")
    if args.workers is not None:
        settings = Settings.model_validate(
            {**settings.model_dump(), "preview_workers": args.workers}
        )
    service = DesignService(settings)
    records = []
    for name, code in MODELS.items():
        for repeat in range(args.repeats):
            timings = {}
            with service.workspace.lock:
                start = time.perf_counter()
                created = service.create_project(name, "Benchmark", "", code)
                timings["create"] = time.perf_counter() - start
                pid = created.project_id
                if not created.success or not created.data["validation"]["success"]:
                    raise RuntimeError(str(created.model_dump()))
                for step, action in (
                    ("validate", lambda pid=pid: service.validate_scad(pid)),
                    ("previews", lambda pid=pid: service.render_preview_set(pid)),
                    ("export", lambda pid=pid: service.export_model(pid)),
                    ("inspect", lambda pid=pid: service.inspect_mesh(pid)),
                    ("finalize", lambda pid=pid: service.finalize_model(pid)),
                ):
                    start = time.perf_counter()
                    result = action()
                    timings[step] = time.perf_counter() - start
                    if not result.success:
                        raise RuntimeError(str(result.model_dump()))
            records.append({"model": name, "repeat": repeat, "seconds": timings})
            print(json.dumps(records[-1]), flush=True)
    summary = {
        name: {
            step: statistics.median(r["seconds"][step] for r in records if r["model"] == name)
            for step in records[0]["seconds"]
        }
        for name in MODELS
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"records": records, "median_seconds": summary}, indent=2))


if __name__ == "__main__":
    main()
