from pathlib import Path

from rivet.audit import ContentAuditor, ReleaseAuditor


def test_content_audit_flags_unfinished_python(tmp_path: Path):
    (tmp_path / "src" / "rivet").mkdir(parents=True)
    (tmp_path / "src" / "rivet" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "rivet" / "unfinished.py").write_text("def unfinished():\n    pass\n", encoding="utf-8")
    report = ContentAuditor(tmp_path).audit()
    assert not report.ok
    assert any(issue.category == "placeholder" for issue in report.issues)


def test_release_audit_validates_repository_without_external_commands():
    report = ReleaseAuditor(Path(__file__).parents[2]).run(run_tests=False, run_build=False)
    assert report.ok, report.text()
