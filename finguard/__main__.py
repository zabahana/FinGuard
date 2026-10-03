import argparse
import json
from .agent import investigate
from .evaluation import evaluate, write_results
from .policy import Guard


def main():
    parser = argparse.ArgumentParser(description="FinGuard guarded fraud investigation testbed")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("investigate", help="Run a deterministic account takeover investigation")
    run.add_argument("--mode", choices=Guard.MODES, default="adaptive")
    run.add_argument("--agent", choices=("deterministic", "ollama"), default="deterministic")
    run.add_argument("--model", default="qwen3:8b")
    run.add_argument("--max-steps", type=int, default=12)
    run.add_argument("--output", help="Write report.json and redacted events.jsonl")
    bench = commands.add_parser("evaluate", help="Replay virtual attack and legitimate action traces")
    bench.add_argument("--mode", choices=Guard.MODES, default="adaptive")
    bench.add_argument("--count", type=int, default=1000)
    bench.add_argument("--seed", type=int, default=42)
    bench.add_argument("--output", default="artifacts/latest")
    train = commands.add_parser("train-fraud", help="Train and evaluate the real ULB fraud detector")
    train.add_argument("--csv", default=".local/datasets/ulb/creditcard.csv")
    train.add_argument("--output", default="artifacts/ulb")
    transaction = commands.add_parser("investigate-transaction", help="Review a held-out ULB transaction with Qwen")
    transaction.add_argument("--artifacts", default="artifacts/ulb")
    transaction.add_argument("--transaction-id", help="ULB source-row ID; default is highest held-out model score")
    transaction.add_argument("--model", default="qwen3:8b")
    transaction.add_argument("--max-steps", type=int, default=12)
    transaction.add_argument("--output", default="artifacts/ulb-investigation")
    args = parser.parse_args()
    if args.command == "investigate":
        if args.agent == "ollama":
            from .llm import investigate_model
            if not 1 <= args.max_steps <= 50:
                parser.error("--max-steps must be between 1 and 50")
            report, events = investigate_model(args.mode, args.model, args.max_steps)
        else:
            report, events = investigate(args.mode)
        if args.output:
            write_results(args.output, report, events)
    elif args.command == "evaluate":
        if args.count < 1:
            parser.error("--count must be positive")
        report, events = evaluate(args.mode, args.count, args.seed)
        write_results(args.output, report, events)
    else:
        try:
            if args.command == "train-fraud":
                from .fraud import train
                report = train(args.csv, args.output)
            else:
                from .ulb import investigate_transaction
                report, events = investigate_transaction(args.artifacts, args.transaction_id,
                                                        args.model, args.max_steps)
                write_results(args.output, report, events)
        except ImportError:
            parser.error("Install fraud dependencies: .venv/bin/python -m pip install -e '.[fraud]'")
        except (ValueError, OSError) as exc:
            parser.error(str(exc))
    print(json.dumps(report, indent=2))
    if report.get("status") in {"error", "incomplete"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
