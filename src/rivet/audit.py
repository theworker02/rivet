from __future__ import annotations

import ast
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 support; the fallback handles this file's small audit section.
    tomllib = None  # type: ignore[assignment]


_MARKERS = (
    "TODO: implement",
    "FIXME",
    "NotImplementedError",
    "placeholder",
    "stub",
    "coming soon",
    "dummy implementation",
)
_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
_REQUIREMENT_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+(?:\[[^\]]+\])?(?:[<>=!~]=?.+)?$")
_LINK_PATTERN = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


def _fallback_toml(path: Path) -> dict[str, Any]:
    """Parse the small TOML subset needed by the release audit on Python 3.10."""
    document: dict[str, Any] = {}
    section: tuple[str, ...] = ()
    pending: list[str] | None = None
    pending_key = ""
    pending_section: tuple[str, ...] = ()

    def assign(key: str, raw_value: str, target_section: tuple[str, ...]) -> None:
        try:
            value = ast.literal_eval(raw_value)
        except (SyntaxError, ValueError):
            return
        target: dict[str, Any] = document
        for part in target_section:
            target = target.setdefault(part, {})
        target[key] = value

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if pending is not None:
            pending.append(line)
            if "]" in line and line.count("]") >= line.count("["):
                assign(pending_key, " ".join(pending), pending_section)
                pending = None
            continue
        if line.startswith("[") and line.endswith("]"):
            section = tuple(part.strip() for part in line[1:-1].split("."))
            continue
        if "=" not in line:
            continue
        key, raw_value = (part.strip() for part in line.split("=", 1))
        if raw_value.startswith("[") and raw_value.count("]") < raw_value.count("["):
            pending = [raw_value]
            pending_key = key
            pending_section = section
        else:
            assign(key, raw_value, section)
    return document


def _load_toml(path: Path) -> dict[str, Any]:
    if tomllib is not None:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    return _fallback_toml(path)


@dataclass(frozen=True)
class AuditIssue:
    category: str
    path: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class AuditReport:
    issues: tuple[AuditIssue, ...]
    checks: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "checks": list(self.checks), "issues": [issue.to_dict() for issue in self.issues]}

    def text(self, heading: str = "RELEASE AUDIT") -> str:
        lines = [heading, ""]
        if self.issues:
            lines.append("RELEASE BLOCKED")
            lines.extend(f"✗ {issue.path}: {issue.detail}" for issue in self.issues)
        else:
            lines.append("RELEASE READY")
            lines.extend(f"✓ {check}" for check in self.checks)
        return "\n".join(lines)


class ContentAuditor:
    """Find unfinished release code while allowing explicit, reviewable exceptions."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()
        self.config = self._load_config()
        self.ignored = tuple(self.config.get("ignore", ()))
        self.excluded = tuple(self.config.get("exclude", ()))

    def audit(self) -> AuditReport:
        issues: list[AuditIssue] = []
        checks: list[str] = []
        source_files = list(self._source_files())
        for path in source_files:
            issues.extend(self._scan_python(path))
        issues.extend(self._scan_empty_packages())
        issues.extend(self._scan_empty_readmes())
        issues = [issue for issue in issues if not self._is_ignored(issue)]
        checks.append(f"content scanned: {len(source_files)} Python files")
        checks.append("explicit audit exceptions loaded")
        return AuditReport(tuple(issues), tuple(checks))

    def _source_files(self) -> Iterable[Path]:
        for directory in (self.root / "src", self.root / "drivers", self.root / "sdk"):
            if not directory.exists():
                continue
            for path in directory.rglob("*.py"):
                if any(part in {"__pycache__", ".venv", "build", "dist"} for part in path.parts):
                    continue
                relative = self._relative(path)
                if any(fnmatch.fnmatch(relative, pattern) for pattern in self.excluded):
                    continue
                yield path

    def _scan_python(self, path: Path) -> list[AuditIssue]:
        relative = self._relative(path)
        issues: list[AuditIssue] = []
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=relative)
        except SyntaxError as exc:
            return [AuditIssue("syntax", relative, str(exc))]
        for node in ast.walk(tree):
            if isinstance(node, ast.Pass):
                issues.append(AuditIssue("placeholder", relative, f"pass statement at line {node.lineno}"))
        for line_number, line in enumerate(text.splitlines(), 1):
            if path.name == "audit.py":
                continue
            lowered = line.lower()
            for marker in _MARKERS:
                if marker.lower() in lowered:
                    issues.append(AuditIssue("placeholder", relative, f"{marker} at line {line_number}"))
        return issues

    def _scan_empty_packages(self) -> list[AuditIssue]:
        issues: list[AuditIssue] = []
        for directory in (self.root / "src", self.root / "drivers", self.root / "sdk"):
            if not directory.exists():
                continue
            for init in directory.rglob("__init__.py"):
                children = [path for path in init.parent.rglob("*") if path.is_file() and path.name != "__init__.py"]
                if not children:
                    issues.append(AuditIssue("empty-package", self._relative(init.parent), "package contains only __init__.py"))
        return issues

    def _scan_empty_readmes(self) -> list[AuditIssue]:
        issues: list[AuditIssue] = []
        candidates = [self.root / "README.md"]
        docs = self.root / "docs"
        if docs.exists():
            candidates.extend(docs.rglob("README.md"))
        for path in candidates:
            if path.exists() and not path.read_text(encoding="utf-8").strip():
                issues.append(AuditIssue("empty-readme", self._relative(path), "README is empty"))
        return issues

    def _is_ignored(self, issue: AuditIssue) -> bool:
        value = f"{issue.path}:{issue.category}"
        marker_value = f"{issue.path}:pass"
        return any(
            pattern == issue.path
            or fnmatch.fnmatch(issue.path, pattern)
            or fnmatch.fnmatch(value, pattern)
            or (issue.category == "placeholder" and fnmatch.fnmatch(marker_value, pattern))
            for pattern in self.ignored
        )

    def _load_config(self) -> dict[str, list[str]]:
        path = self.root / "pyproject.toml"
        if not path.exists():
            return {}
        data = _load_toml(path)
        section = data.get("tool", {}).get("rivet", {}).get("audit", {})
        return {key: list(value) for key, value in section.items() if isinstance(value, list)}

    @staticmethod
    def _fallback_config(path: Path) -> dict[str, list[str]]:
        data = _fallback_toml(path)
        section = data.get("tool", {}).get("rivet", {}).get("audit", {})
        return {key: list(value) for key, value in section.items() if isinstance(value, list)}

    def _relative(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()


class ReleaseAuditor:
    """Strict release gate: every failed quality signal becomes a blocking issue."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def run(self, run_tests: bool = True, run_build: bool = True) -> AuditReport:
        issues: list[AuditIssue] = []
        checks: list[str] = []
        issues.extend(self._metadata_checks())
        issues.extend(self._documentation_checks())
        issues.extend(self._example_checks())
        content = ContentAuditor(self.root).audit()
        issues.extend(content.issues)
        checks.extend(content.checks)
        if run_tests:
            issue = self._command_check("tests", [sys.executable, "-m", "pytest", "-q"])
            if issue:
                issues.append(issue)
            else:
                checks.append("pytest suite")
        else:
            checks.append("pytest suite skipped by explicit option")
        if run_build:
            build_script = (
                "from pathlib import Path; "
                "from setuptools.build_meta import build_sdist, build_wheel; "
                "out = Path('dist'); out.mkdir(exist_ok=True); "
                "build_sdist(str(out)); build_wheel(str(out))"
            )
            issue = self._command_check("package build", [sys.executable, "-c", build_script])
            if issue:
                issues.append(issue)
            else:
                artifact_issues = self._artifact_checks()
                issues.extend(artifact_issues)
                if not artifact_issues:
                    checks.append("wheel and sdist build")
        else:
            checks.append("package build skipped by explicit option")
        return AuditReport(tuple(issues), tuple(checks))

    def _metadata_checks(self) -> list[AuditIssue]:
        issues: list[AuditIssue] = []
        pyproject = self.root / "pyproject.toml"
        if not pyproject.exists():
            return [AuditIssue("metadata", "pyproject.toml", "package metadata file is missing")]
        data = self._toml(pyproject)
        project = data.get("project", {})
        version = self._version()
        if not _VERSION_PATTERN.fullmatch(version):
            issues.append(AuditIssue("metadata", "src/rivet/version.py", f"invalid version: {version!r}"))
        for required in ("name", "description", "readme", "license"):
            if not project.get(required):
                issues.append(AuditIssue("metadata", "pyproject.toml", f"missing project.{required}"))
        classifiers = project.get("classifiers", [])
        if "Development Status :: 4 - Beta" not in classifiers:
            issues.append(AuditIssue("metadata", "pyproject.toml", "package must declare Development Status :: 4 - Beta"))
        if "Development Status :: 3 - Alpha" in classifiers:
            issues.append(AuditIssue("metadata", "pyproject.toml", "package still declares Alpha status"))
        license_path = self.root / "LICENSE"
        if not license_path.exists() or not license_path.read_text(encoding="utf-8").strip():
            issues.append(AuditIssue("metadata", "LICENSE", "license metadata file is missing or empty"))
        generated = self.root / "src" / "rivet_robot_runtime.egg-info" / "PKG-INFO"
        if not generated.exists():
            issues.append(AuditIssue("metadata", self._relative(generated), "generated package metadata is missing; run the package metadata build"))
        else:
            generated_text = generated.read_text(encoding="utf-8")
            if f"Version: {version}" not in generated_text:
                issues.append(AuditIssue("metadata", self._relative(generated), "generated package version is stale"))
            if "Classifier: Development Status :: 4 - Beta" not in generated_text:
                issues.append(AuditIssue("metadata", self._relative(generated), "generated package is missing Beta status"))
            if "Development Status :: 3 - Alpha" in generated_text:
                issues.append(AuditIssue("metadata", self._relative(generated), "generated package still declares Alpha status"))
        entry_points = self.root / "src" / "rivet_robot_runtime.egg-info" / "entry_points.txt"
        if not entry_points.exists() or "rivet-dev = rivet.dev_cli:main" not in entry_points.read_text(encoding="utf-8"):
            issues.append(AuditIssue("metadata", self._relative(entry_points), "rivet-dev console entry point is missing"))
        for group, requirements in project.get("optional-dependencies", {}).items():
            for requirement in requirements:
                if not isinstance(requirement, str) or not _REQUIREMENT_PATTERN.fullmatch(requirement):
                    issues.append(AuditIssue("dependencies", "pyproject.toml", f"invalid {group} dependency: {requirement!r}"))
        for schema in (self.root / "sdk" / "schemas").glob("*.json"):
            try:
                json.loads(schema.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                issues.append(AuditIssue("schema", self._relative(schema), f"invalid generated schema: {exc}"))
        return issues

    def _documentation_checks(self) -> list[AuditIssue]:
        issues: list[AuditIssue] = []
        ignored_parts = {".git", ".venv", "venv", "build", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__"}
        documents = sorted(path for path in self.root.rglob("*.md") if not any(part in ignored_parts for part in path.parts))
        for document in documents:
            text = document.read_text(encoding="utf-8")
            for match in _LINK_PATTERN.finditer(text):
                target = match.group(1).strip().split()[0].strip("<>")
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                clean_target = target.split("#", 1)[0].split("?", 1)[0]
                if not clean_target:
                    continue
                target_path = (document.parent / clean_target).resolve()
                if not target_path.exists():
                    category = "README asset" if match.group(0).startswith("!") else "documentation"
                    issues.append(AuditIssue(category, self._relative(document), f"missing link target: {target}"))

        html_pattern = re.compile(r'''(?:href|src)\s*=\s*["']([^"']+)["']''', re.IGNORECASE)
        html_documents = sorted(path for path in self.root.rglob("*.html") if not any(part in ignored_parts for part in path.parts))
        for document in html_documents:
            text = document.read_text(encoding="utf-8")
            for match in html_pattern.finditer(text):
                target = match.group(1).strip()
                if target.startswith(("http://", "https://", "mailto:", "#", "data:", "javascript:")):
                    continue
                clean_target = target.split("#", 1)[0].split("?", 1)[0]
                if not clean_target:
                    continue
                target_path = (document.parent / clean_target).resolve()
                if not target_path.exists():
                    issues.append(AuditIssue("site asset", self._relative(document), f"missing HTML target: {target}"))

        for path in (self.root / "README.md", self.root / "site" / "index.html"):
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8").lower()
            if "1.2.0" not in text:
                issues.append(AuditIssue("documentation", self._relative(path), "release status does not identify Rivet 1.2.0"))
            if "verification-gated" not in text:
                issues.append(AuditIssue("documentation", self._relative(path), "release status is missing verification-gated wording"))
        return issues

    def _example_checks(self) -> list[AuditIssue]:
        issues: list[AuditIssue] = []
        examples = self.root / "examples"
        if not examples.exists():
            return [AuditIssue("examples", "examples", "examples directory is missing")]
        for path in examples.rglob("*"):
            if path.is_file() and path.suffix.lower() == ".json":
                try:
                    json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    issues.append(AuditIssue("examples", self._relative(path), f"invalid JSON example: {exc}"))
            elif path.is_file() and path.suffix.lower() in {".yaml", ".yml"} and not path.read_text(encoding="utf-8").strip():
                issues.append(AuditIssue("examples", self._relative(path), "example is empty"))
        return issues

    def _artifact_checks(self) -> list[AuditIssue]:
        version = self._version()
        normalized_name = "rivet_robot_runtime"
        dist = self.root / "dist"
        issues: list[AuditIssue] = []
        wheel = tuple(dist.glob(f"{normalized_name}-{version}-*.whl"))
        sdist = dist / f"{normalized_name}-{version}.tar.gz"
        if not wheel:
            issues.append(AuditIssue("artifact", self._relative(dist), f"wheel for version {version} was not created"))
        if not sdist.exists():
            issues.append(AuditIssue("artifact", self._relative(dist), f"sdist for version {version} was not created"))
        for artifact in dist.glob(f"{normalized_name}-*"):
            if version not in artifact.name:
                issues.append(AuditIssue("artifact", self._relative(artifact), "stale package artifact remains in dist"))
        return issues

    def _command_check(self, label: str, command: list[str]) -> AuditIssue | None:
        try:
            result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=900)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return AuditIssue("command", label, f"could not run {' '.join(command)}: {exc}")
        if result.returncode:
            output = (result.stdout + "\n" + result.stderr).strip().splitlines()
            detail = output[-1] if output else f"exit code {result.returncode}"
            return AuditIssue("command", label, f"failed ({result.returncode}): {detail}")
        return None

    def _toml(self, path: Path) -> dict[str, Any]:
        return _load_toml(path)

    def _version(self) -> str:
        source = self.root / "src" / "rivet" / "version.py"
        match = re.search(r"__version__\s*=\s*[\"']([^\"']+)", source.read_text(encoding="utf-8"))
        return match.group(1) if match else ""

    def _relative(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()
