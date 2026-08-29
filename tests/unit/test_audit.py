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



def _minimal_release_root(root: Path, generated_version: str = "1.2.0") -> None:
    (root / "src" / "rivet").mkdir(parents=True)
    (root / "src" / "rivet_robot_runtime.egg-info").mkdir(parents=True)
    (root / "examples").mkdir()
    (root / "site").mkdir()
    (root / "src" / "rivet" / "version.py").write_text('__version__ = "1.2.0"\n', encoding="utf-8")
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (root / "README.md").write_text("Rivet 1.2.0 is verification-gated.\n", encoding="utf-8")
    (root / "site" / "index.html").write_text("Rivet 1.2.0 verification-gated beta", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        """[project]
name = \"rivet-robot-runtime\"
description = \"test package\"
readme = \"README.md\"
license = \"MIT\"
classifiers = [\"Development Status :: 4 - Beta\"]
""",
        encoding="utf-8",
    )
    (root / "src" / "rivet_robot_runtime.egg-info" / "PKG-INFO").write_text(
        f"Version: {generated_version}\nClassifier: Development Status :: 4 - Beta\n", encoding="utf-8"
    )
    (root / "src" / "rivet_robot_runtime.egg-info" / "entry_points.txt").write_text(
        "rivet-dev = rivet.dev_cli:main\n", encoding="utf-8"
    )


def test_release_audit_flags_stale_generated_metadata(tmp_path: Path):
    _minimal_release_root(tmp_path, generated_version="0.4.0")
    issues = ReleaseAuditor(tmp_path)._metadata_checks()
    assert any(issue.category == "metadata" and "stale" in issue.detail for issue in issues)


def test_release_audit_flags_broken_markdown_and_html_assets(tmp_path: Path):
    _minimal_release_root(tmp_path)
    (tmp_path / "README.md").write_text(
        "[missing](docs/missing.md)\nRivet 1.2.0 is verification-gated.\n", encoding="utf-8"
    )
    (tmp_path / "site" / "index.html").write_text(
        '<img src="missing.svg"> Rivet 1.2.0 verification-gated beta', encoding="utf-8"
    )
    issues = ReleaseAuditor(tmp_path)._documentation_checks()
    assert any(issue.category == "documentation" for issue in issues)
    assert any(issue.category == "site asset" for issue in issues)


def test_release_audit_reports_package_build_failure(tmp_path: Path, monkeypatch):
    _minimal_release_root(tmp_path)
    auditor = ReleaseAuditor(tmp_path)

    def fail_build(label, _command):
        if label == "package build":
            from rivet.audit import AuditIssue

            return AuditIssue("command", label, "forced build failure")
        return None

    monkeypatch.setattr(auditor, "_command_check", fail_build)
    report = auditor.run(run_tests=False, run_build=True)
    assert not report.ok
    assert any(issue.path == "package build" for issue in report.issues)
