"""SI AquaBot — Intelligent Water Lab."""

import argparse

from app import WaterLab


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--screenshot", help="Save a PNG during the smoke test")
    args = parser.parse_args()
    WaterLab().run(args.smoke_test, args.screenshot)


if __name__ == "__main__":
    main()
