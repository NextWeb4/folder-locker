"""Folder Locker core recovered from the Python 3.12 PyInstaller package.

The version-2 format streams each path or data record through AES-256-GCM.
Version-1 reading is retained for containers created by the earlier app.
"""

from __future__ import annotations

import base64
import hmac
import json
import math
import os
import secrets
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

MAGIC_V1 = b"FOLDERLOCK1\n"
MAGIC_V2 = b"FOLDERLOCK2\n"
MAGIC = MAGIC_V1
DEFAULT_CHUNK_SIZE = 1024 * 1024
DEFAULT_ITERATIONS = 600_000
LOCKED_SUFFIX = ".locked"
ACL_META_SUFFIX = ".folderlock.json"

RECORD_DIR = 1
RECORD_FILE_START = 2
RECORD_FILE_DATA = 3
RECORD_FILE_END = 4
RECORD_FINISH = 5

ProgressCallback = Callable[[str, int, int], None]


class FolderLockerError(Exception):
    """Expected, user-facing folder locker failure."""


def emit_progress(progress: ProgressCallback | None, phase: str, done: int, total: int) -> None:
    if progress is not None:
        progress(phase, done, max(total, 1))


def derive_key(password: str, salt: bytes, iterations: int) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return kdf.derive(password.encode("utf-8"))


def password_digest(password: str, salt: bytes, iterations: int) -> bytes:
    return derive_key(password, salt, iterations)


def verify_password_digest(password: str, salt: bytes, iterations: int, expected: bytes) -> bool:
    return hmac.compare_digest(password_digest(password, salt, iterations), expected)


def default_container_for_folder(folder: Path) -> Path:
    return folder.with_name(folder.name + LOCKED_SUFFIX)


def default_folder_for_container(container: Path) -> Path:
    if container.name.endswith(LOCKED_SUFFIX):
        return container.with_name(container.name[: -len(LOCKED_SUFFIX)])
    return container.with_suffix("")


def acl_metadata_path(folder: Path) -> Path:
    return folder.with_name(folder.name + ACL_META_SUFFIX)


def safe_output_path(root: Path, relative_name: str) -> Path:
    posix_path = PurePosixPath(relative_name)
    if posix_path.is_absolute() or any(part in {"", ".", ".."} for part in posix_path.parts):
        raise FolderLockerError("Container contains an unsafe path.")
    target = (root / Path(*posix_path.parts)).resolve()
    resolved_root = root.resolve()
    if target != resolved_root and resolved_root not in target.parents:
        raise FolderLockerError("Container path escapes the output folder.")
    return target


def collect_folder_entries(folder: Path) -> tuple[list[Path], list[tuple[Path, str, int]], int]:
    root = folder.resolve()
    directories: list[Path] = []
    files_to_pack: list[tuple[Path, str, int]] = []
    total_size = 0
    for current_root, dirs, files in os.walk(root):
        dirs.sort()
        files.sort()
        current = Path(current_root)
        for name in dirs:
            directory = current / name
            if directory.is_symlink():
                raise FolderLockerError(f"Symbolic links are not supported: {directory}")
            directories.append(directory)
        for name in files:
            file_path = current / name
            if file_path.is_symlink():
                raise FolderLockerError(f"Symbolic links are not supported: {file_path}")
            try:
                size = file_path.stat().st_size
            except OSError as error:
                raise FolderLockerError(f"Unable to inspect file: {file_path}") from error
            relative_name = file_path.relative_to(root).as_posix()
            files_to_pack.append((file_path, relative_name, size))
            total_size += size
    return directories, files_to_pack, total_size


def pack_path_record(kind: int, relative_name: str) -> bytes:
    path_bytes = relative_name.encode("utf-8")
    return struct.pack(">BI", kind, len(path_bytes)) + path_bytes


def pack_file_start_record(relative_name: str, file_size: int, mtime_ns: int) -> bytes:
    path_bytes = relative_name.encode("utf-8")
    return struct.pack(">BIQQ", RECORD_FILE_START, len(path_bytes), file_size, mtime_ns) + path_bytes


def unpack_path_record(payload: bytes) -> str:
    if len(payload) < 5:
        raise FolderLockerError("Container path record is incomplete.")
    path_length = struct.unpack(">I", payload[1:5])[0]
    if len(payload) != 5 + path_length:
        raise FolderLockerError("Container path record has an invalid length.")
    try:
        return payload[5:].decode("utf-8")
    except UnicodeDecodeError as error:
        raise FolderLockerError("Container path is not valid UTF-8.") from error


def unpack_file_start_record(payload: bytes) -> tuple[str, int, int]:
    header_length = struct.calcsize(">BIQQ")
    if len(payload) < header_length:
        raise FolderLockerError("Container file record is incomplete.")
    _, path_length, file_size, mtime_ns = struct.unpack(">BIQQ", payload[:header_length])
    if len(payload) != header_length + path_length:
        raise FolderLockerError("Container file path has an invalid length.")
    try:
        name = payload[header_length:].decode("utf-8")
    except UnicodeDecodeError as error:
        raise FolderLockerError("Container file path is not valid UTF-8.") from error
    return name, file_size, mtime_ns


def write_encrypted_record(
    destination: object,
    aesgcm: AESGCM,
    nonce_prefix: bytes,
    header_bytes: bytes,
    counter: int,
    payload: bytes,
) -> None:
    nonce = nonce_prefix + struct.pack(">Q", counter)
    aad = MAGIC_V2 + header_bytes + struct.pack(">Q", counter)
    encrypted = aesgcm.encrypt(nonce, payload, aad)
    destination.write(struct.pack(">I", len(encrypted)))
    destination.write(encrypted)


def read_exact(handle: object, size: int) -> bytes:
    data = handle.read(size)
    if len(data) != size:
        raise FolderLockerError("Encrypted container is incomplete or damaged.")
    return data


def read_encrypted_record(
    source: object,
    aesgcm: AESGCM,
    nonce_prefix: bytes,
    header_bytes: bytes,
    counter: int,
) -> bytes:
    length_data = source.read(4)
    if not length_data:
        raise FolderLockerError("Encrypted container is missing its finish record.")
    if len(length_data) != 4:
        raise FolderLockerError("Encrypted container is incomplete or damaged.")
    record_length = struct.unpack(">I", length_data)[0]
    if record_length < 16 or record_length > DEFAULT_CHUNK_SIZE + 4096:
        raise FolderLockerError("Encrypted record length is invalid.")
    encrypted = read_exact(source, record_length)
    nonce = nonce_prefix + struct.pack(">Q", counter)
    aad = MAGIC_V2 + header_bytes + struct.pack(">Q", counter)
    try:
        return aesgcm.decrypt(nonce, encrypted, aad)
    except InvalidTag as error:
        raise FolderLockerError("Incorrect password, or the encrypted container is damaged.") from error


def encrypt_folder_stream(
    folder: Path,
    target: Path,
    password: str,
    progress: ProgressCallback | None = None,
) -> None:
    root = folder.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FolderLockerError(f"Folder does not exist: {root}")
    if root.parent == root:
        raise FolderLockerError("A drive root cannot be encrypted.")
    target = target.expanduser().resolve()
    if target.exists():
        raise FolderLockerError(f"Target already exists: {target}")
    if target.parent != root.parent and root in target.parents:
        raise FolderLockerError("The encrypted container cannot be created inside the source folder.")

    emit_progress(progress, "scanning", 0, 1)
    directories, files_to_pack, total_size = collect_folder_entries(root)
    salt = secrets.token_bytes(16)
    nonce_prefix = secrets.token_bytes(4)
    header = {
        "version": 2,
        "format": "folder-stream",
        "kdf": "PBKDF2-HMAC-SHA256",
        "iterations": DEFAULT_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "cipher": "AES-256-GCM",
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "nonce_prefix": base64.b64encode(nonce_prefix).decode("ascii"),
        "file_count": len(files_to_pack),
        "dir_count": len(directories),
        "plaintext_size": total_size,
    }
    header_bytes = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
    aesgcm = AESGCM(derive_key(password, salt, DEFAULT_ITERATIONS))
    counter = 0
    processed = 0
    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        with target.open("xb") as destination:
            destination.write(MAGIC_V2)
            destination.write(struct.pack(">I", len(header_bytes)))
            destination.write(header_bytes)
            for directory in directories:
                relative = directory.relative_to(root).as_posix()
                write_encrypted_record(destination, aesgcm, nonce_prefix, header_bytes, counter, pack_path_record(RECORD_DIR, relative))
                counter += 1
            emit_progress(progress, "locking", processed, total_size)
            for file_path, relative, expected_size in files_to_pack:
                stat = file_path.stat()
                write_encrypted_record(
                    destination,
                    aesgcm,
                    nonce_prefix,
                    header_bytes,
                    counter,
                    pack_file_start_record(relative, expected_size, stat.st_mtime_ns),
                )
                counter += 1
                file_processed = 0
                try:
                    with file_path.open("rb") as source:
                        while chunk := source.read(DEFAULT_CHUNK_SIZE):
                            write_encrypted_record(
                                destination,
                                aesgcm,
                                nonce_prefix,
                                header_bytes,
                                counter,
                                bytes([RECORD_FILE_DATA]) + chunk,
                            )
                            counter += 1
                            file_processed += len(chunk)
                            processed += len(chunk)
                            emit_progress(progress, "locking", processed, total_size)
                except OSError as error:
                    raise FolderLockerError(f"Unable to read file: {file_path}") from error
                if file_processed != expected_size:
                    raise FolderLockerError(f"File changed while it was being encrypted: {file_path}")
                write_encrypted_record(destination, aesgcm, nonce_prefix, header_bytes, counter, bytes([RECORD_FILE_END]))
                counter += 1
            write_encrypted_record(destination, aesgcm, nonce_prefix, header_bytes, counter, bytes([RECORD_FINISH]))
    except Exception:
        target.unlink(missing_ok=True)
        raise
    emit_progress(progress, "locking", total_size, total_size)


def decrypt_folder_stream(
    source_path: Path,
    target_folder: Path,
    password: str,
    progress: ProgressCallback | None = None,
) -> None:
    target_root = target_folder.expanduser().resolve()
    if target_root.exists():
        raise FolderLockerError(f"Target folder already exists: {target_root}")
    target_root.mkdir(parents=True)
    current_file = None
    current_path: Path | None = None
    current_size = 0
    current_written = 0
    current_mtime_ns = 0
    finished = False

    try:
        with source_path.expanduser().resolve().open("rb") as source:
            if read_exact(source, len(MAGIC_V2)) != MAGIC_V2:
                raise FolderLockerError("This is not a version-2 encrypted container.")
            header_length = struct.unpack(">I", read_exact(source, 4))[0]
            if header_length <= 0 or header_length > 65_536:
                raise FolderLockerError("Encrypted container header is invalid.")
            header_bytes = read_exact(source, header_length)
            try:
                header = json.loads(header_bytes.decode("utf-8"))
                salt = base64.b64decode(header["salt"])
                nonce_prefix = base64.b64decode(header["nonce_prefix"])
                iterations = int(header["iterations"])
                chunk_size = int(header["chunk_size"])
                total_size = int(header.get("plaintext_size", 0))
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as error:
                raise FolderLockerError("Encrypted container header cannot be parsed.") from error
            if header.get("version") != 2 or header.get("format") != "folder-stream" or len(nonce_prefix) != 4:
                raise FolderLockerError("Unsupported encrypted container version.")
            if chunk_size <= 0 or chunk_size > 16 * 1024 * 1024:
                raise FolderLockerError("Encrypted container chunk size is invalid.")
            aesgcm = AESGCM(derive_key(password, salt, iterations))
            counter = 0
            restored = 0
            emit_progress(progress, "unlocking", 0, total_size)
            while not finished:
                payload = read_encrypted_record(source, aesgcm, nonce_prefix, header_bytes, counter)
                counter += 1
                if not payload:
                    raise FolderLockerError("Encrypted container contains an empty record.")
                kind = payload[0]
                if kind == RECORD_DIR:
                    safe_output_path(target_root, unpack_path_record(payload)).mkdir(parents=True, exist_ok=True)
                elif kind == RECORD_FILE_START:
                    if current_file is not None:
                        raise FolderLockerError("Container file records are out of order.")
                    relative_name, current_size, current_mtime_ns = unpack_file_start_record(payload)
                    current_path = safe_output_path(target_root, relative_name)
                    current_path.parent.mkdir(parents=True, exist_ok=True)
                    current_file = current_path.open("xb")
                    current_written = 0
                elif kind == RECORD_FILE_DATA:
                    if current_file is None:
                        raise FolderLockerError("Container data record is missing its file header.")
                    data = payload[1:]
                    current_file.write(data)
                    current_written += len(data)
                    restored += len(data)
                    emit_progress(progress, "unlocking", restored, total_size)
                elif kind == RECORD_FILE_END:
                    if current_file is None or current_path is None:
                        raise FolderLockerError("Container file end record is invalid.")
                    current_file.close()
                    current_file = None
                    if current_written != current_size:
                        raise FolderLockerError("Restored file size does not match its record.")
                    os.utime(current_path, ns=(current_mtime_ns, current_mtime_ns))
                    current_path = None
                elif kind == RECORD_FINISH:
                    if current_file is not None:
                        raise FolderLockerError("Final container record occurred before the current file ended.")
                    finished = True
                else:
                    raise FolderLockerError("Encrypted container contains an unknown record type.")
            if source.read(1):
                raise FolderLockerError("Encrypted container has unexpected trailing data.")
    except Exception:
        if current_file is not None:
            current_file.close()
        shutil.rmtree(target_root, ignore_errors=True)
        raise
    emit_progress(progress, "unlocking", 1, 1)


def encrypt_file(source: Path, target: Path, password: str, progress: ProgressCallback | None = None) -> None:
    source_size = source.stat().st_size
    chunk_count = math.ceil(source_size / DEFAULT_CHUNK_SIZE) if source_size else 0
    salt = secrets.token_bytes(16)
    nonce_prefix = secrets.token_bytes(4)
    header = {
        "version": 1,
        "kdf": "PBKDF2-HMAC-SHA256",
        "iterations": DEFAULT_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "cipher": "AES-256-GCM",
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "chunk_count": chunk_count,
        "plaintext_size": source_size,
        "nonce_prefix": base64.b64encode(nonce_prefix).decode("ascii"),
    }
    header_bytes = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
    aesgcm = AESGCM(derive_key(password, salt, DEFAULT_ITERATIONS))
    aad = MAGIC_V1 + header_bytes
    with source.open("rb") as src, target.open("xb") as dst:
        dst.write(MAGIC_V1)
        dst.write(struct.pack(">I", len(header_bytes)))
        dst.write(header_bytes)
        processed = 0
        for counter in range(chunk_count):
            plain = src.read(DEFAULT_CHUNK_SIZE)
            nonce = nonce_prefix + struct.pack(">Q", counter)
            encrypted = aesgcm.encrypt(nonce, plain, aad)
            dst.write(struct.pack(">I", len(encrypted)))
            dst.write(encrypted)
            processed += len(plain)
            emit_progress(progress, "encrypting", processed, source_size)


def decrypt_file(source: Path, target: Path, password: str, progress: ProgressCallback | None = None) -> None:
    with source.open("rb") as src:
        if read_exact(src, len(MAGIC_V1)) != MAGIC_V1:
            raise FolderLockerError("This is not a Folder Locker container.")
        header_length = struct.unpack(">I", read_exact(src, 4))[0]
        if header_length <= 0 or header_length > 65_536:
            raise FolderLockerError("Encrypted container header is invalid.")
        header_bytes = read_exact(src, header_length)
        try:
            header = json.loads(header_bytes.decode("utf-8"))
            salt = base64.b64decode(header["salt"])
            nonce_prefix = base64.b64decode(header["nonce_prefix"])
            iterations = int(header["iterations"])
            chunk_size = int(header["chunk_size"])
            chunk_count = int(header["chunk_count"])
            plaintext_size = int(header["plaintext_size"])
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as error:
            raise FolderLockerError("Encrypted container header cannot be parsed.") from error
        if header.get("version") != 1 or len(nonce_prefix) != 4:
            raise FolderLockerError("Unsupported encrypted container version.")
        if chunk_size <= 0 or chunk_size > 16 * 1024 * 1024:
            raise FolderLockerError("Encrypted container chunk size is invalid.")
        aesgcm = AESGCM(derive_key(password, salt, iterations))
        aad = MAGIC_V1 + header_bytes
        written = 0
        try:
            with target.open("xb") as dst:
                for counter in range(chunk_count):
                    record_length = struct.unpack(">I", read_exact(src, 4))[0]
                    if record_length < 16 or record_length > chunk_size + 16:
                        raise FolderLockerError("Encrypted record length is invalid.")
                    encrypted = read_exact(src, record_length)
                    nonce = nonce_prefix + struct.pack(">Q", counter)
                    plain = aesgcm.decrypt(nonce, encrypted, aad)
                    dst.write(plain)
                    written += len(plain)
                    emit_progress(progress, "decrypting", written, plaintext_size)
        except InvalidTag as error:
            target.unlink(missing_ok=True)
            raise FolderLockerError("Incorrect password, or the encrypted container is damaged.") from error
        if src.read(1):
            target.unlink(missing_ok=True)
            raise FolderLockerError("Encrypted container has unexpected trailing data.")
        if written != plaintext_size:
            target.unlink(missing_ok=True)
            raise FolderLockerError("Restored data size does not match the container header.")


def pack_folder(folder: Path, archive: Path, progress: ProgressCallback | None = None) -> None:
    root = folder.resolve()
    directories, files_to_pack, total_size = collect_folder_entries(root)
    packed = 0
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as bundle:
        for directory in directories:
            relative = directory.relative_to(root).as_posix() + "/"
            bundle.writestr(relative, b"")
        for file_path, relative, _ in files_to_pack:
            with file_path.open("rb") as src, bundle.open(relative, "w", force_zip64=True) as dst:
                while chunk := src.read(DEFAULT_CHUNK_SIZE):
                    dst.write(chunk)
                    packed += len(chunk)
                    emit_progress(progress, "packing", packed, total_size)


def safe_extract_zip(archive: Path, target_folder: Path, progress: ProgressCallback | None = None) -> None:
    target_root = target_folder.resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "r", allowZip64=True) as bundle:
        members = bundle.infolist()
        total_size = sum(item.file_size for item in members)
        extracted = 0
        for member in members:
            destination = safe_output_path(target_root, member.filename.rstrip("/"))
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as src, destination.open("xb") as dst:
                while chunk := src.read(DEFAULT_CHUNK_SIZE):
                    dst.write(chunk)
                    extracted += len(chunk)
                    emit_progress(progress, "extracting", extracted, total_size)


def decrypt_container_to_folder(
    container: Path,
    target_folder: Path,
    password: str,
    progress: ProgressCallback | None = None,
) -> None:
    container = container.expanduser().resolve()
    if not container.exists() or not container.is_file():
        raise FolderLockerError(f"Encrypted container does not exist: {container}")
    with container.open("rb") as source:
        magic = source.read(max(len(MAGIC_V1), len(MAGIC_V2)))
    if magic.startswith(MAGIC_V2):
        decrypt_folder_stream(container, target_folder, password, progress)
        return
    if magic.startswith(MAGIC_V1):
        if target_folder.exists():
            raise FolderLockerError(f"Target folder already exists: {target_folder}")
        with tempfile.TemporaryDirectory(prefix="folder-unlock-v1-") as temp_dir:
            archive = Path(temp_dir) / "payload.zip"
            decrypt_file(container, archive, password, progress)
            try:
                safe_extract_zip(archive, target_folder, progress)
            except Exception:
                shutil.rmtree(target_folder, ignore_errors=True)
                raise
        return
    raise FolderLockerError("This is not a container generated by Folder Locker.")


def run_checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise FolderLockerError(f"Command failed ({' '.join(command)}): {details}")
    return result


def current_windows_user() -> str:
    if not sys.platform.startswith("win"):
        raise FolderLockerError("ACL mode is supported only on Windows/NTFS.")
    return run_checked(["whoami"]).stdout.strip()


def random_locked_name(used_names: set[str]) -> str:
    while True:
        name = "~fl_" + secrets.token_hex(12)
        if name not in used_names:
            used_names.add(name)
            return name


def collect_name_obfuscation_map(folder: Path) -> dict:
    root = folder.resolve()
    entries: list[dict[str, str]] = []
    for current_root, dirs, files in os.walk(root):
        current = Path(current_root)
        used = set(dirs) | set(files)
        parent = current.relative_to(root).as_posix()
        for name in sorted(files):
            path = current / name
            if path.is_symlink():
                raise FolderLockerError(f"Symbolic links are not supported: {path}")
            entries.append({"kind": "file", "parent": parent, "original": name, "locked": random_locked_name(used)})
        for name in sorted(dirs):
            path = current / name
            if path.is_symlink():
                raise FolderLockerError(f"Symbolic links are not supported: {path}")
            entries.append({"kind": "dir", "parent": parent, "original": name, "locked": random_locked_name(used)})
    return {"version": 1, "entries": entries}


def encode_acl_mapping(password: str, mapping: dict) -> dict:
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    plain = json.dumps(mapping, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encrypted = AESGCM(derive_key(password, salt, DEFAULT_ITERATIONS)).encrypt(nonce, plain, b"folder-lock-acl-map-v1")
    return {
        "iterations": DEFAULT_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "data": base64.b64encode(encrypted).decode("ascii"),
    }


def decode_acl_mapping(password: str, payload: dict) -> dict:
    try:
        iterations = int(payload["iterations"])
        salt = base64.b64decode(payload["salt"])
        nonce = base64.b64decode(payload["nonce"])
        encrypted = base64.b64decode(payload["data"])
    except (KeyError, ValueError, TypeError) as error:
        raise FolderLockerError("Folder-name metadata is incomplete.") from error
    try:
        plain = AESGCM(derive_key(password, salt, iterations)).decrypt(nonce, encrypted, b"folder-lock-acl-map-v1")
    except InvalidTag as error:
        raise FolderLockerError("Folder-name metadata cannot be decrypted.") from error
    try:
        return json.loads(plain.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FolderLockerError("Folder-name metadata cannot be parsed.") from error


def _entry_path(root: Path, entry: dict[str, str], name_key: str) -> Path:
    parent = entry.get("parent", ".")
    parent_path = root if parent in {"", "."} else safe_output_path(root, parent)
    return parent_path / entry[name_key]


def obfuscate_folder_names(folder: Path, mapping: dict, progress: ProgressCallback | None = None) -> None:
    root = folder.resolve()
    entries = list(mapping.get("entries", []))
    files = [entry for entry in entries if entry.get("kind") == "file"]
    dirs = [entry for entry in entries if entry.get("kind") == "dir"]
    dirs.sort(key=lambda item: item.get("parent", "").count("/"), reverse=True)
    ordered = files + dirs
    emit_progress(progress, "obfuscating_names", 0, len(ordered))
    for index, entry in enumerate(ordered, start=1):
        source = _entry_path(root, entry, "original")
        target = source.with_name(entry["locked"])
        if source.exists():
            source.rename(target)
        emit_progress(progress, "obfuscating_names", index, len(ordered))


def restore_folder_names(folder: Path, mapping: dict, progress: ProgressCallback | None = None) -> None:
    root = folder.resolve()
    entries = list(mapping.get("entries", []))
    dirs = [entry for entry in entries if entry.get("kind") == "dir"]
    files = [entry for entry in entries if entry.get("kind") == "file"]
    dirs.sort(key=lambda item: item.get("parent", "").count("/"))
    ordered = dirs + files
    emit_progress(progress, "restoring_names", 0, len(ordered))
    for index, entry in enumerate(ordered, start=1):
        source = _entry_path(root, entry, "locked")
        target = source.with_name(entry["original"])
        if target.exists():
            raise FolderLockerError(f"Cannot restore name because target exists: {target}")
        if source.exists():
            source.rename(target)
        emit_progress(progress, "restoring_names", index, len(ordered))


def _write_acl_metadata(folder: Path, user: str, password: str, mapping: dict) -> Path:
    metadata_path = acl_metadata_path(folder)
    if metadata_path.exists():
        raise FolderLockerError(f"ACL metadata already exists: {metadata_path}")
    salt = secrets.token_bytes(16)
    payload = {
        "version": 1,
        "mode": "acl-lock",
        "folder_name": folder.name,
        "user": user,
        "iterations": DEFAULT_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "password_digest": base64.b64encode(password_digest(password, salt, DEFAULT_ITERATIONS)).decode("ascii"),
        "created_at": datetime.now(UTC).isoformat(),
        "name_obfuscation": encode_acl_mapping(password, mapping),
    }
    temporary = metadata_path.with_name(metadata_path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(metadata_path)
    subprocess.run(["attrib", "+h", str(metadata_path)], capture_output=True, text=True, check=False)
    return metadata_path


def _read_acl_metadata(folder: Path) -> dict:
    metadata_path = acl_metadata_path(folder)
    if not metadata_path.exists():
        raise FolderLockerError(f"ACL metadata was not found: {metadata_path}")
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise FolderLockerError("ACL metadata cannot be read.") from error
    if payload.get("version") != 1 or payload.get("mode") != "acl-lock":
        raise FolderLockerError("Unsupported ACL metadata version.")
    return payload


def lock_folder_acl(folder: Path, password: str, progress: ProgressCallback | None = None) -> Path:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise FolderLockerError(f"Folder does not exist: {folder}")
    if folder.parent == folder:
        raise FolderLockerError("A drive root cannot be ACL-locked.")
    user = current_windows_user()
    mapping = collect_name_obfuscation_map(folder)
    metadata_path = _write_acl_metadata(folder, user, password, mapping)
    try:
        obfuscate_folder_names(folder, mapping, progress)
        run_checked(["icacls", str(folder), "/deny", f"{user}:(OI)(CI)(F)"])
    except Exception:
        try:
            restore_folder_names(folder, mapping, progress)
        finally:
            subprocess.run(["attrib", "-h", str(metadata_path)], capture_output=True, text=True, check=False)
            metadata_path.unlink(missing_ok=True)
        raise
    return metadata_path


def unlock_folder_acl(folder: Path, password: str, progress: ProgressCallback | None = None) -> None:
    folder = folder.expanduser().resolve()
    payload = _read_acl_metadata(folder)
    try:
        salt = base64.b64decode(payload["salt"])
        expected = base64.b64decode(payload["password_digest"])
        iterations = int(payload["iterations"])
        user = str(payload["user"])
    except (KeyError, ValueError, TypeError) as error:
        raise FolderLockerError("ACL metadata fields are incomplete.") from error
    if not verify_password_digest(password, salt, iterations, expected):
        raise FolderLockerError("Incorrect password.")
    mapping = decode_acl_mapping(password, payload["name_obfuscation"])
    run_checked(["icacls", str(folder), "/remove:d", user])
    restore_folder_names(folder, mapping, progress)
    metadata_path = acl_metadata_path(folder)
    subprocess.run(["attrib", "-h", str(metadata_path)], capture_output=True, text=True, check=False)
    metadata_path.unlink(missing_ok=True)


def open_in_explorer(folder: Path) -> None:
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer", str(folder)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(folder)])
    else:
        subprocess.Popen(["xdg-open", str(folder)])
