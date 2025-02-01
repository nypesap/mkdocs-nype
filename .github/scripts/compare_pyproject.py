import argparse
import sys
import tomllib


def main():
    parser = argparse.ArgumentParser(
        description="Compare versions in [project] section of main and dev TOML files."
    )
    parser.add_argument("--dev-toml", help="Path to the dev branch TOML file")
    parser.add_argument("--main-toml", help="Path to the main branch TOML file")

    args = parser.parse_args()

    try:
        with open(args.dev_toml, "rb") as file:
            dev_toml = tomllib.load(file)
    except FileNotFoundError:
        sys.exit(f"File not found: {args.dev_toml}")
    except Exception as e:
        sys.exit(f"Error reading file {args.dev_toml}: {e}")

    try:
        with open(args.main_toml, "rb") as file:
            main_toml = tomllib.load(file)
    except FileNotFoundError:
        sys.exit(f"File not found: {args.main_toml}")
    except Exception as e:
        sys.exit(f"Error reading file {args.main_toml}: {e}")

    # Extracting versions
    dev_version = dev_toml.get("project").get("version")
    main_version = main_toml.get("project").get("version")

    print(f"{dev_version=}")
    print(f"{main_version=}")

    if dev_version == main_version:
        sys.exit(
            "Versions between dev and main branch match."
            "\nThe version needs to be bumped to make sure it will be installed."
        )


if __name__ == "__main__":
    main()
