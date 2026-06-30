# SPDX-FileCopyrightText: 2026 Helmholtz-Zentrum Dresden - Rossendorf e.V. (HZDR)
# SPDX-FileContributor: David Pape
#
# SPDX-License-Identifier: Apache-2.0

"""Module containing the Software CaRD curation plugin for HERMES."""

import json

from hermes.commands.curate.base import HermesCurateCommand, HermesCuratePlugin
from hermes.model import SoftwareMetadata
from hermes.model.hermes_cache import HermesCacheManager
from software_card_policies.config import Config
from software_card_policies.data_model import (
    make_shacl_graph,
    read_rdf_resource,
    validate_graph,
)
from software_card_policies.report import create_report

from hermes_plugin_software_card import environment


class SoftwareCaRDCuratePlugin(HermesCuratePlugin):
    """Software CaRD curation plugin."""

    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self._data_graph = None
        self._shacl_graph = None
        self._conforms = False
        self._validation_graph = None

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

    def __call__(
        self,
        command: HermesCurateCommand,  # noqa: ARG002
        metadata: SoftwareMetadata,
    ) -> SoftwareMetadata:
        """Entry point of the callable.

        This method runs the main logic of the plugin. It calls the other methods of the
        object in the correct order. Depending on the result of
        ``is_publication_approved`` either the valid metadata or a new, empty
        ``SoftwareMetadata`` object is returned.
        """
        self.prepare(metadata)
        self.validate()
        self.create_report()

        if not self.is_publication_approved():
            return SoftwareMetadata()

        return metadata

    def prepare(self, metadata: SoftwareMetadata):
        """Prepare the validation.

        The metadata given in ``metadata`` is parsed as an RDF graph for validation.
        """
        self._data_graph = read_rdf_resource(
            format="json-ld", data=json.dumps(metadata.ld_value)
        )
        self._shacl_graph = make_shacl_graph(Config.from_dict(self._validation_config))

    def validate(self):
        """Run Software CaRD validation on the given software metadata."""
        conforms, validation_graph = validate_graph(self._data_graph, self._shacl_graph)
        self._conforms = conforms
        self._validation_graph = validation_graph

    def create_report(self):
        """Create validation report.

        This creates the report both as a machine-readble JSON-LD file, and prints a
        human-readable report, and the URL to the Software CaRD web app to the screen.
        """
        ctx = HermesCacheManager()
        validation_file = ctx.cache_dir / "curate" / "validation.json"
        validation_file.parent.mkdir(exist_ok=True, parents=True)
        self._validation_graph.serialize(validation_file, format="json-ld")

        print(create_report(self._validation_graph), end="\n\n")
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
