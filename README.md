<!--
SPDX-FileCopyrightText: 2026 Helmholtz-Zentrum Dresden - Rossendorf e.V. (HZDR)
SPDX-FileContributor: David Pape

SPDX-License-Identifier: CC-BY-4.0
-->

# hermes-plugin-software-card

HERMES curation plugin using the Software CaRD framework.

Install it:

``` bash
pip install git+https://github.com/softwarepub/hermes-plugin-software-card.git
```

Configure it in `hermes.toml`:

``` toml
[curate]
plugin = "software_card"
```

## Development

```bash
python3.11 -m venv venv
source venv/bin/activate
python -m pip install -e .
```

For testing of CI environments (on Linux), source one of these files:

```bash
source env-github.sh
source env-gitlab.sh
```
