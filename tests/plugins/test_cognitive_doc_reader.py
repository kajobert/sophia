import pytest
from pathlib import Path
import shutil
from plugins.cognitive_doc_reader import DocReader

@pytest.fixture
def doc_reader_plugin(tmp_path: Path):
    """Fixture to provide a DocReader instance with a temporary docs directory."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    # Create some dummy doc files for testing
    (docs_dir / "en").mkdir()
    (docs_dir / "en" / "01_VISION.md").write_text("This is the vision.")
    (docs_dir / "cs" / "roadmap").mkdir(parents=True)
    (docs_dir / "cs" / "roadmap" / "01_MVP.md").write_text("Toto je MVP.")
    reader = DocReader()
    reader.setup({"docs_dir": str(docs_dir)})
    return reader

def test_doc_reader_list_documents(doc_reader_plugin: DocReader):
    """Tests that the plugin can list all documents."""
    doc_list = doc_reader_plugin.list_all_documents()
    assert len(doc_list) == 2
    # Use Path to handle OS-specific separators
    assert str(Path("en") / "01_VISION.md") in doc_list
    assert str(Path("cs") / "roadmap" / "01_MVP.md") in doc_list

def test_doc_reader_read_document_success(doc_reader_plugin: DocReader):
    """Tests reading a valid document."""
    content = doc_reader_plugin.read_document("en/01_VISION.md")
    assert content == "This is the vision."

def test_doc_reader_read_document_not_found(doc_reader_plugin: DocReader):
    """Tests reading a non-existent document."""
    result = doc_reader_plugin.read_document("en/non_existent.md")
    assert "Error" in result
    assert "No such file or directory" in result

def test_doc_reader_security_prevents_traversal(doc_reader_plugin: DocReader):
    """Tests that the plugin prevents reading files outside the docs directory."""
    result = doc_reader_plugin.read_document("../some_other_file.txt")
    assert "Error" in result
    assert "Accessing files outside the docs directory is forbidden" in result
