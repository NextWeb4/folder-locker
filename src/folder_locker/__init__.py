"""Secure, offline folder container and optional Windows ACL helpers."""

from .core import (
    FolderLockerError,
    decrypt_container_to_folder,
    encrypt_folder_stream,
    lock_folder_acl,
    unlock_folder_acl,
)

__all__ = [
    "FolderLockerError",
    "decrypt_container_to_folder",
    "encrypt_folder_stream",
    "lock_folder_acl",
    "unlock_folder_acl",
]
__version__ = "1.0.0"
