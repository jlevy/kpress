from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish.yml"


def test_publish_workflow_uses_release_payload_tag() -> None:
    workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")

    assert "ref: ${{ github.event.release.tag_name }}" in workflow
    assert "RELEASE_TAG: ${{ github.event.release.tag_name }}" in workflow
    assert "GITHUB_REF_NAME" not in workflow


def test_publish_workflow_reports_version_mismatch() -> None:
    workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")

    assert 'if [ "$actual" != "$expected" ]; then' in workflow
    assert "Release version mismatch:" in workflow
    assert '"$expected" "$RELEASE_TAG" "$actual"' in workflow
