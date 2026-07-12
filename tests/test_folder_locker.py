from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from folder_locker import core


class FolderLockerCoreTests(unittest.TestCase):
    def test_version_two_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(core, "DEFAULT_ITERATIONS", 2_000):
            root = Path(directory)
            source = root / "source"
            (source / "nested" / "empty").mkdir(parents=True)
            (source / "hello.txt").write_text("hello", encoding="utf-8")
            (source / "nested" / "字幕.txt").write_text("第一行\n第二行", encoding="utf-8")
            (source / "binary.bin").write_bytes(bytes(range(256)) * 20)
            container = root / "source.locked"
            restored = root / "restored"

            core.encrypt_folder_stream(source, container, "correct horse battery staple")
            core.decrypt_container_to_folder(container, restored, "correct horse battery staple")

            self.assertEqual((restored / "hello.txt").read_text(encoding="utf-8"), "hello")
            self.assertEqual((restored / "nested" / "字幕.txt").read_text(encoding="utf-8"), "第一行\n第二行")
            self.assertEqual((restored / "binary.bin").read_bytes(), bytes(range(256)) * 20)
            self.assertTrue((restored / "nested" / "empty").is_dir())

    def test_wrong_password_leaves_no_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(core, "DEFAULT_ITERATIONS", 2_000):
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "file.txt").write_text("secret", encoding="utf-8")
            container = root / "source.locked"
            target = root / "wrong"
            core.encrypt_folder_stream(source, container, "right-password")
            with self.assertRaises(core.FolderLockerError):
                core.decrypt_container_to_folder(container, target, "wrong-password")
            self.assertFalse(target.exists())

    def test_version_one_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(core, "DEFAULT_ITERATIONS", 2_000):
            root = Path(directory)
            source = root / "legacy"
            source.mkdir()
            (source / "legacy.txt").write_text("legacy payload", encoding="utf-8")
            archive = root / "payload.zip"
            container = root / "legacy.locked"
            restored = root / "legacy-restored"
            core.pack_folder(source, archive)
            core.encrypt_file(archive, container, "legacy-password")
            core.decrypt_container_to_folder(container, restored, "legacy-password")
            self.assertEqual((restored / "legacy.txt").read_text(encoding="utf-8"), "legacy payload")

    def test_safe_output_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for unsafe in ("../outside.txt", "/absolute.txt", "a/../../outside.txt"):
                with self.subTest(unsafe=unsafe), self.assertRaises(core.FolderLockerError):
                    core.safe_output_path(root, unsafe)

    def test_name_mapping_round_trip_without_acl_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(core, "DEFAULT_ITERATIONS", 2_000):
            root = Path(directory) / "folder"
            (root / "nested").mkdir(parents=True)
            (root / "nested" / "file.txt").write_text("data", encoding="utf-8")
            mapping = core.collect_name_obfuscation_map(root)
            encrypted = core.encode_acl_mapping("password", mapping)
            self.assertEqual(core.decode_acl_mapping("password", encrypted), mapping)
            core.obfuscate_folder_names(root, mapping)
            self.assertFalse((root / "nested" / "file.txt").exists())
            core.restore_folder_names(root, mapping)
            self.assertEqual((root / "nested" / "file.txt").read_text(encoding="utf-8"), "data")


if __name__ == "__main__":
    unittest.main()
