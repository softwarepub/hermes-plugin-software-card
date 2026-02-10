# SPDX-FileCopyrightText: 2026 Helmholtz-Zentrum Dresden - Rossendorf e.V. (HZDR)
# SPDX-FileContributor: David Pape
#
# SPDX-License-Identifier: Apache-2.0

"""Classes to get information about the execution environment."""

import os
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Self
from urllib.parse import urlencode


@dataclass(kw_only=True)
class Environment:
    """Base class for representing computing environments."""

    @classmethod
    def from_env(cls) -> Self | None:
        """Create object from environment variables.

        If not running in GitHub Actions, ``None`` is returned instead.
        """
        env = dict(os.environ)
        data = {}
        for field in fields(cls):
            key = field.name.casefold()
            value = env.get(field.name)
            type_ = field.type

            if type_ is str:
                pass
            if type_ is int:
                value = int(value)
            if type_ is bool:
                value = value.casefold() not in ["false", "f", "0", "none", "null", ""]
            if type_ is datetime:
                value = datetime.fromisoformat(value)

            data[key] = value

        return cls(**data)

    def url_data(self) -> dict[str, str]:
        """Return the data to be passed to the Software CaRD user interface."""
        return {}


class GitLabCIEnvironment(Environment):
    """Environment variables in the GitLab CI environment.

    This class exposes only a selection of the environment variables; more may be added.
    An overview of all variables available in GitLab CI can be found at:
    https://docs.gitlab.com/ci/variables/predefined_variables/
    """

    ci_commit_author: str  # author line, e.g. "Jane Doe <j.doe@example.com>"
    ci_commit_branch: str  # e.g. "main"
    ci_commit_title: str  # first line without newline
    ci_commit_message: str  # first line with newline
    ci_commit_description: str  # the following lines
    ci_commit_message_is_truncated: bool
    ci_commit_ref_name: str  # e.g. "main"
    ci_commit_ref_protected: bool
    ci_commit_sha: str  # the full SHA of the commit
    ci_commit_short_sha: str  # the shortened sha of the commit (8 characters)
    ci_commit_timestamp: datetime

    ci_default_branch: str  # e.g. "main"

    ci_job_group_name: str
    ci_job_id: int
    ci_job_name: str
    ci_job_stage: str
    ci_job_started_at: datetime
    ci_job_url: str  # e.g. "https://codebase.helmholtz.cloud/my-group/my-project/-/jobs/1234567"
    ci_pipeline_created_at: datetime
    ci_pipeline_id: int
    ci_pipeline_iid: int
    ci_pipeline_name: str
    ci_pipeline_source: str  # push/...
    # e.g. "https://codebase.helmholtz.cloud/my-group/my-project/-/pipelines/123456"
    ci_pipeline_url: str

    ci_project_id: int
    ci_project_name: str  # e.g. "my-project"
    ci_project_path: str  # e.g. "my-group/my-project"
    ci_project_title: str  # e.g. "My Project"
    # e.g. "https://codebase.helmholtz.cloud/my-group/my-project"
    ci_project_url: str

    ci_server_name: str  # e.g. "GitLab"
    ci_server_url: str  # e.g. "https://codebase.helmholtz.cloud"
    ci_server_version: str  # e.g. "18.7.2"

    gitlab_user_email: str  # full email address
    gitlab_user_id: int
    gitlab_user_login: str  # username
    gitlab_user_name: str  # display name

    @classmethod
    def from_env(cls) -> Self | None:
        """Create object from environment variables.

        If not running in GitLab CI, ``None`` is returned instead.
        """
        env = dict(os.environ)
        if env.get("CI") != "true" or env.get("GITLAB_CI") != "true":
            return None

        return super().from_env()

    def url_data(self):
        """Return the data to be passed to the Software CaRD user interface."""
        return {
            "gitlab_ci_server": self.ci_server_url,
            "gitlab_ci_job": self.ci_job_url,
        }


class GitHubActionsEnvironment(Environment):
    """Environment variables in the GitHub Actions environment.

    This class exposes only a selection of the environment variables; more may be added.
    An overview of all variables available in GitHub Actions can be found at:
    https://docs.github.com/en/actions/reference/workflows-and-actions/variables
    """

    github_event_name: str  # push/pull_request/schedule/...

    github_actor: str  # the username
    github_actor_id: int
    github_triggering_actor: str  # the username

    github_workflow: str  # Specified with `name:` in workflow config
    github_job: str  # key of the sections under `jobs:`
    github_run_attempt: int
    github_run_id: int
    github_run_number: int

    github_repository: str  # "<group or username>/<repo>"
    github_repository_id: int
    github_repository_owner: str  # group or username
    github_repository_owner_id: int

    github_sha: str  # the full SHA of the commit
    github_ref: str  # e.g. "refs/heads/main"
    github_ref_name: str  # e.g. "main"
    github_ref_protected: bool
    github_ref_type: str  # branch/tag/...

    github_api_url: str  # https://api.github.com
    github_server_url: str  # https://github.com

    @classmethod
    def from_env(cls) -> Self | None:
        """Create object from environment variables.

        If not running in GitHub Actions, ``None`` is returned instead.
        """
        env = dict(os.environ)
        if env.get("CI") != "true" or env.get("GITHUB_ACTIONS") != "true":
            return None

        return super().from_env()

    def url_data(self):
        """Return the data to be passed to the Software CaRD user interface."""
        return {
            "github_ci_server": self.github_server_url,
            "github_ci_job": self.github_run_id,
        }


def get() -> Environment | None:
    """Return the CI environment that we are running in, or ``None``."""
    github_actions = GitHubActionsEnvironment.from_env()
    gitlab_ci = GitLabCIEnvironment.from_env()

    if github_actions is not None and gitlab_ci is not None:
        message = "More than one CI environment detected"
        raise RuntimeError(message)

    return github_actions or gitlab_ci


def format_app_url(base_url: str, environment: Environment) -> str:
    """Format the url for visiting the Software CaRD web interface."""
    query = urlencode(environment.url_data())
    return f"{base_url}?{query}"
