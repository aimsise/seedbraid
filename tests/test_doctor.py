from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from helix.cli import app
from helix.diagnostics import DoctorCheck, DoctorReport, run_doctor


def test_doctor_cli_exit_zero_with_only_warn(monkeypatch) -> None:
    monkeypatch.setattr(
        "helix.cli.run_doctor",
        lambda _genome: DoctorReport(
            checks=[
                DoctorCheck(check="python", status="ok", detail="python=3.12"),
                DoctorCheck(
                    check="compression_zstd",
                    status="warn",
                    detail="zstandard missing",
                    next_action="install zstandard",
                ),
            ]
        ),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "[ok] python: python=3.12" in result.output
    assert "[warn] compression_zstd: zstandard missing" in result.output
    assert "doctor summary ok=1 warn=1 fail=0" in result.output


def test_doctor_cli_exit_one_on_fail(monkeypatch) -> None:
    monkeypatch.setattr(
        "helix.cli.run_doctor",
        lambda _genome: DoctorReport(
            checks=[
                DoctorCheck(
                    check="ipfs_cli",
                    status="fail",
                    detail="ipfs missing",
                    next_action="install kubo",
                )
            ]
        ),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "[fail] ipfs_cli: ipfs missing" in result.output
    assert "next_action: install kubo" in result.output


def test_run_doctor_flags_missing_ipfs(tmp_path: Path, monkeypatch) -> None:
    genome = tmp_path / "genome"
    monkeypatch.setattr("helix.diagnostics.shutil.which", lambda _name: None)
    monkeypatch.delenv("IPFS_PATH", raising=False)

    report = run_doctor(genome)
    ipfs = next(c for c in report.checks if c.check == "ipfs_cli")

    assert ipfs.status == "fail"
    assert report.fail_count >= 1


def test_error_output_includes_code_and_next_action(tmp_path: Path, monkeypatch) -> None:
    src = tmp_path / "input.bin"
    src.write_bytes(b"x")
    monkeypatch.delenv("HELIX_ENCRYPTION_KEY", raising=False)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "encode",
            str(src),
            "--genome",
            str(tmp_path / "genome"),
            "--out",
            str(tmp_path / "seed.hlx"),
            "--encrypt",
        ],
    )

    assert result.exit_code == 1
    assert "error[HELIX_E_ENCRYPTION_KEY_MISSING]" in result.output
    assert "next_action:" in result.output
