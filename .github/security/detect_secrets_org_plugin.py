"""detect-secrets custom plugin: flag any org-name reference.

The pattern is written as n[a]acp so this file doesn't match itself.
"""

import re

from detect_secrets.plugins.base import RegexBasedDetector


class OrgNameDetector(RegexBasedDetector):
    secret_type = "Organization name reference"  # pragma: allowlist secret

    denylist = [re.compile(r"(?i)n[a]acp")]
