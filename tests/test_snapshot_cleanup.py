import pytest
import os
import shutil

def test_snapshot_archive_on_approval(tmp_path):
    # Simulace schválení snapshotu a archivace starého received
    import sys
    sys.path.insert(0, str((__file__)))
    from conftest import ensure_snapshot_path
    snapshots_dir = tmp_path / "snapshots"
    archive_dir = snapshots_dir / "archive"
    snapshots_dir.mkdir()
    archive_dir.mkdir()
    approved = ensure_snapshot_path(snapshots_dir / "test.approved.txt")
    received = ensure_snapshot_path(snapshots_dir / "test.received.txt")
    approved.write_text("ok")
    received.write_text("fail")
    # Simulace schválení (přepsání approved)
    shutil.copy(received, approved)
    # Simulace archivace starého received
    archived = archive_dir / f"test_{os.getpid()}.received.txt"
    shutil.move(received, archived)
    assert approved.exists()
    assert archived.exists()
