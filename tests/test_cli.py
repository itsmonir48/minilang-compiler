import subprocess
import sys

from minilang import __version__
from minilang.cli import main


def test_main_without_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage: minilang" in capsys.readouterr().out


def test_python_dash_m_version():
    result = subprocess.run(
        [sys.executable, "-m", "minilang", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == f"minilang {__version__}"
