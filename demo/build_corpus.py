from __future__ import annotations

import argparse
import json

from demo.config import settings
from demo.corpus import build_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the deterministic BrowseComp+ Demo Slice")
    parser.add_argument("--distractors", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(build_corpus(settings, args.distractors, args.seed), indent=2))


if __name__ == "__main__":
    main()
