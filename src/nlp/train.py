"""Command line entry point for baseline training and evaluation."""

import json

from .intent_classifier import train_and_evaluate

if __name__ == "__main__":
    print(json.dumps(train_and_evaluate(), indent=2, ensure_ascii=False))
