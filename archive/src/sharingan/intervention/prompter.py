"""Write human intervention prompts to a markdown file."""

from __future__ import annotations

from datetime import datetime

from sharingan.config import SharinganConfig
from sharingan.intervention.detector import InterventionRequest


def write_intervention_prompt(
    request: InterventionRequest,
    config: SharinganConfig,
) -> None:
    """Write a human intervention prompt to SHARINGAN_NEEDS_HELP.md.

    The file tells the user what Sharingan got stuck on, shows a screenshot,
    and gives clear instructions for how to resolve and resume.

    Args:
        request: The intervention request.
        config: Sharingan configuration.
    """
    prompt_path = config.get_intervention_prompt_path()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# Sharingan Needs Your Help

*Generated: {now}*

Sharingan encountered a step that requires human intervention and cannot proceed automatically.

## What happened

**Test:** `{request.test_name}`
**Reason:** `{request.reason.value}`
**Stuck at:** {request.current_url}
**Page title:** {request.page_title}

## What you need to do

{request.instructions}

## Page context

```
{request.visible_text}
```

## Screenshot

"""

    if request.screenshot_path:
        content += f"![Screenshot]({request.screenshot_path})\n\n"
    else:
        content += "*(No screenshot captured)*\n\n"

    content += """## How to resume

Once you've resolved the issue (verified the email, solved the CAPTCHA, etc.), run:

```
/sharingan-resume
```

Sharingan will pick up where it left off and retry the failing test.

## How to skip

If this test cannot be automated and you want to skip it, run:

```
/sharingan-resume --skip
```

This will mark the test as "needs human review" in the final report.
"""

    prompt_path.write_text(content)


def clear_intervention_prompt(config: SharinganConfig) -> None:
    """Remove the intervention prompt file after resolution.

    Args:
        config: Sharingan configuration.
    """
    prompt_path = config.get_intervention_prompt_path()
    if prompt_path.exists():
        prompt_path.unlink()
