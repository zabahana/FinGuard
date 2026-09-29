import argparse
import json
from .agent import investigate
from .evaluation import evaluate, write_results
from .policy import Guard


def main():
    parser = argparse.ArgumentParser(description="FinGuard synthetic banking research testbed")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("investigate", help="Run a deterministic account takeover investigation")
    run.add_argument("--mode", choices=Guard.MODES, default="adaptive")
    bench = commands.add_parser("evaluate", help="Replay virtual attack and legitimate action traces")
    bench.add_argument("--mode", choices=Guard.MODES, default="adaptive")
    bench.add_argument("--count", type=int, default=1000)
    bench.add_argument("--seed", type=int, default=42)
    bench.add_argument("--output", default="artifacts/latest")
    args = parser.parse_args()
    if args.command == "investigate":
        report, _ = investigate(args.mode)
    else:
        if args.count < 1:
            parser.error("--count must be positive")
        report, events = evaluate(args.mode, args.count, args.seed)
        write_results(args.output, report, events)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
