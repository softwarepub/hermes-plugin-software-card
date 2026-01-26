# SPDX-FileCopyrightText: 2026 Helmholtz-Zentrum Dresden - Rossendorf e.V. (HZDR)
# SPDX-FileContributor: David Pape
#
# SPDX-License-Identifier: Apache-2.0

"""Module containing the Software CaRD curation plugin for HERMES."""

from hermes.commands.curate.base import BaseCuratePlugin


class SoftwareCaRDCuratePlugin(BaseCuratePlugin):
    """Software CaRD curation plugin."""

    def is_publication_approved(self):
        """Decide whether the publication of the software is approved."""
        return False
