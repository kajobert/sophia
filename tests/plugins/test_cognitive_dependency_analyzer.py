import pytest
from pathlib import Path

from plugins.cognitive_dependency_analyzer import DependencyAnalyzer


@pytest.fixture
def dep_analyzer_plugin(tmp_path: Path):
    """Fixture to provide a DependencyAnalyzer instance with a temporary project root."""
    # Simulate the project root within a temporary directory
    project_root = tmp_path
    # Create dummy requirement files for testing
    (project_root / "requirements.in").write_text("fastapi\nsqlalchemy\n# a comment\nlitellm\n")
    (project_root / "requirements-dev.in").write_text("pytest\n")

    analyzer = DependencyAnalyzer()
    # To test, we need to "pretend" we are in the temp directory
    analyzer.root_path = project_root
    return analyzer


def test_dep_analyzer_list_dependencies_default(dep_analyzer_plugin: DependencyAnalyzer):
    """Tests listing dependencies from the default requirements.in file."""
    deps = dep_analyzer_plugin.list_dependencies()
    assert len(deps) == 3
    assert "fastapi" in deps
    assert "sqlalchemy" in deps
    assert "litellm" in deps
    assert "# a comment" not in deps


def test_dep_analyzer_list_dependencies_dev(dep_analyzer_plugin: DependencyAnalyzer):
    """Tests listing dependencies from a different file, requirements-dev.in."""
    deps = dep_analyzer_plugin.list_dependencies(file="requirements-dev.in")
    assert len(deps) == 1
    assert "pytest" in deps


def test_dep_analyzer_file_not_found(dep_analyzer_plugin: DependencyAnalyzer):
    """Tests the behavior when the requirement file does not exist."""
    result = dep_analyzer_plugin.list_dependencies(file="non_existent.in")
    assert "Error" in result[0]
    assert "not found" in result[0]
