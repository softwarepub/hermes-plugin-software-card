# SPDX-FileCopyrightText: 2026 Helmholtz-Zentrum Dresden - Rossendorf e.V. (HZDR)
# SPDX-FileContributor: David Pape
#
# SPDX-License-Identifier: Apache-2.0

"""Module containing the Software CaRD curation plugin for HERMES."""

import json
from pathlib import Path

from hermes.commands.curate.base import BaseCuratePlugin
from software_card_policies.config import Config
from software_card_policies.data_model import (
    make_shacl_graph,
    read_rdf_resource,
    validate_graph,
)
from software_card_policies.report import create_report

from hermes_plugin_software_card import environment


class SoftwareCaRDCuratePlugin(BaseCuratePlugin):
    """Software CaRD curation plugin."""

    def __init__(self, command, ctx):
        """Initialize the plugin."""
        super().__init__(command, ctx)
        self._data_graph = None
        self._shacl_graph = None
        self._conforms = False
        self._validation_graph = None
        self._report = None

        self._environment = environment.get()
        self._app_base_url = "https://software-metadata.pub/software-card/"
        self._validation_config = {
            "policies": {
                "authors": {
                    "source": (
                        "https://software-metadata.pub/software-card-policies/"
                        "example-policies/policies/authors-affiliation.ttl"
                    ),
                },
                "description": {
                    "parameters": {"description_min_length": 10},
                    "source": (
                        "https://software-metadata.pub/software-card-policies/"
                        "example-policies/policies/description-parameterizable.ttl"
                    ),
                },
                "licenses": {
                    "parameters": {
                        "suggested_licenses": [
                            "https://spdx.org/licenses/MIT",
                            "https://spdx.org/licenses/Apache-2.0",
                            "https://spdx.org/licenses/GPL-3.0-or-later",
                        ]
                    },
                    "source": (
                        "https://software-metadata.pub/software-card-policies/"
                        "example-policies/policies/licenses-parameterizable.ttl"
                    ),
                },
            }
        }

    def prepare(self):
        """Prepare the validation.

        The metadata given in the context is parsed as an RDF graph and then validated
        using the Software CaRD validation.
        """
        text = json.dumps(self.ctx.get_data()["curate"])
        self._data_graph = read_rdf_resource(format="json-ld", data=text)
        self._shacl_graph = make_shacl_graph(Config.from_dict(self._validation_config))

    def validate(self):
        """Run Software CaRD validation."""
        conforms, validation_graph = validate_graph(self._data_graph, self._shacl_graph)
        self._conforms = conforms
        self._validation_graph = validation_graph

    def create_report(self):
        """Create basic text report."""
        self._report = create_report(self._validation_graph)
        if self._environment is None:
            print("Software CaRD plugin not running in CI environment.")
        else:
            print(
                "Find the Software CaRD user interface at:",
                environment.format_app_url(self._app_base_url, self._environment),
            )

    def is_publication_approved(self) -> bool:
        """Decide whether the publication of the software is approved."""
        return self._conforms

    def process_decision_positive(self):
        """Write the given metadata into the curate directory."""
        curate_output = Path(self.ctx.get_cache("curate", self.ctx.hermes_name))
        Path.mkdir(curate_output.parent)
        with open(curate_output, "w") as curate_output_fh:
            json.dump(self.ctx.get_data(), curate_output_fh)
