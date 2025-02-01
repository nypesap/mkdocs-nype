import subprocess
import sys
import tomllib


def main():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    dev_deps = data.get("project", {}).get("optional-dependencies", {}).get("dev", [])

    if not dev_deps:
        sys.exit("Could not find dev deps")

    subprocess.run(["pip", "install", *dev_deps], check=True)


if __name__ == "__main__":
    main()
