import argparse
import json

from app.services.generator import generate
from app.services.validation import validate


def main():
    parser = argparse.ArgumentParser(description="Generate and validate reusable asset coordination data")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--output", default="data")
    generate_parser.add_argument("--seed", type=int, default=20261022)
    generate_parser.add_argument("--assets", type=int, default=100)
    generate_parser.add_argument("--shipments", type=int, default=50)
    generate_parser.add_argument("--custody-events", type=int, default=250)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    result = generate(args.output, args.seed, args.assets, args.shipments, args.custody_events) if args.command == "generate" else validate(args.data_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
