"""Permission regression tests. Only synthetic configuration is used."""
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cl_control_web_next.app.startup import prepare_private_data, prepare_service_options
from cl_control_web_next.app.studio_llm import read_options, provider_status


class StartupPermissionTests(unittest.TestCase):
    def test_regular_options_are_not_rewritten_or_copied(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "options.json"
            data = b'{"ai_provider":"offline","test_only":"synthetic"}\n'
            path.write_bytes(data)
            path.chmod(0o600)
            with patch("cl_control_web_next.app.startup.os.fchown") as chown:
                self.assertTrue(prepare_service_options(path, 1234))
            chown.assert_called_once()
            self.assertEqual(chown.call_args.args[1:], (0, 1234))
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["options.json"])
            self.assertEqual(provider_status(read_options(path))["provider"], "offline")

    def test_absent_options_remain_absent(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "options.json"
            self.assertFalse(prepare_service_options(path, os.getgid()))
            self.assertFalse(path.exists())

    def test_symlink_is_rejected_without_changing_target(self):
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "target.json"
            target.write_text("{}", encoding="utf-8")
            target.chmod(0o600)
            link = Path(tmp) / "options.json"
            link.symlink_to(target)
            with self.assertRaises(OSError):
                prepare_service_options(link, os.getgid())
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)

    def test_hardlink_is_rejected(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "options.json"
            path.write_text("{}", encoding="utf-8")
            os.link(path, Path(tmp) / "second.json")
            with self.assertRaises(RuntimeError):
                prepare_service_options(path, os.getgid())

    def test_private_directory_does_not_change_other_files(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp) / "data"
            directory.mkdir()
            other = directory / "layout.json"
            other.write_text("{}", encoding="utf-8")
            other.chmod(0o600)
            with patch("cl_control_web_next.app.startup.os.chown") as chown:
                prepare_private_data(directory, 10001, 1234)
            chown.assert_called_once_with(directory, 10001, 1234, follow_symlinks=False)
            self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(other.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
