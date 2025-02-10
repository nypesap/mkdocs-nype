---
title: Development
---

# Theme development

The theme's GitHub repository is split into 2 branches, `main` and `dev`. The development branch gets
changes first and then later they're moved to the public branch, ready for usage in Nype projects.

## Setup

Install the project as an editable package with the development and docs dependencies:

```shell
git clone https://github.com/nypesap/mkdocs-nype
cd mkdocs-nype
python -m venv venv
source venv/bin/activate ; venv/Scripts/activate.ps1 # depending on your system
pip install -e ".[dev,docs]"
```

## Docstrings

The reference is automatically generated with [mkdocstrings], so the code should be documented with
docstrings.

[mkdocstrings]: https://github.com/mkdocstrings/mkdocstrings

## Dependency versioning

To prevent unforeseen issues with updates to upstream dependencies, they're locked to specific version
tags or commit hashes, and are updated manually when the need arises.

## Testing

There are currently no unit tests or other focused tests, however after each commit to the development
branch, a basic test workflow runs and validates that all of the Nype projects build successfully with it.

This basic testing approach allows to detect obvious regressions. However, it also creates a codependency,
where an upstream dependency like the Material for MkDocs theme could break the test with a major release,
because the downstream projects are set up for the previous version and this theme can't really patch each
of the incoming breaking changes.

In case of this codependency preventing from updating the main branch, turn off the branch protection
requiring the development workflow to pass :v:

## Deployment

Any push to the `dev` branch will also deploy these docs. As for the downstream projects, there is
typically no need to update them to the latest version of the theme, so there is no automatic "deploy all"
workflow yet. Sometimes a bug could impact all of the downstream projects, therefore such workflow will be
added sooner or later :v: For now rerun the deploy action in the downstream project's CI or make a change.
