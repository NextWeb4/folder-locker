"""Bilingual Tkinter interface for Folder Locker."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from folder_locker.core import (
    FolderLockerError,
    acl_metadata_path,
    decrypt_container_to_folder,
    default_container_for_folder,
    default_folder_for_container,
    encrypt_folder_stream,
    lock_folder_acl,
    open_in_explorer,
    unlock_folder_acl,
)
from utility_suite.meta import APP_VERSION, AUTHOR, EMAIL, GITHUB, HOMEPAGE
from utility_suite.settings import load_language, save_language


TEXT = {
    "zh": {
        "title": "文件夹保险箱",
        "container_tab": "加密容器（推荐）",
        "acl_tab": "Windows 快速锁定（高级）",
        "encrypt_title": "把文件夹复制到 AES-256-GCM 加密容器",
        "source_folder": "源文件夹",
        "container_file": "容器文件",
        "password": "密码",
        "confirm": "确认密码",
        "browse": "浏览…",
        "encrypt": "创建加密容器",
        "decrypt_title": "从 .locked 容器恢复文件夹",
        "locked_file": ".locked 文件",
        "target_folder": "恢复到",
        "decrypt": "解密并恢复",
        "keep_notice": "为避免数据丢失，加密成功后仍保留原文件夹；确认容器可解密后再自行删除原件。",
        "acl_warning": "此模式只修改 NTFS 权限并混淆文件名，不等于加密。管理员或熟悉 ACL 的用户可能绕过；请优先使用加密容器。",
        "acl_folder": "目标文件夹",
        "acl_lock": "应用快速锁定",
        "acl_unlock": "解除快速锁定",
        "language": "English",
        "about": "关于",
        "ready": "就绪",
        "busy": "处理中…",
        "missing": "请填写所有必填路径和密码。",
        "password_mismatch": "两次输入的密码不一致。",
        "success_encrypt": "加密容器已创建：\n{path}\n\n原文件夹仍保留。",
        "success_decrypt": "文件夹已恢复：\n{path}",
        "success_acl_lock": "快速锁定已应用。元数据：\n{path}",
        "success_acl_unlock": "快速锁定已解除。",
        "error": "操作失败",
        "done": "完成",
        "about_text": "文件夹保险箱 v{version}\n\n作者：{author}\n邮箱：{email}\n主页：{home}\nGitHub：{github}\n\n加密容器使用 PBKDF2-HMAC-SHA256 与 AES-256-GCM。\n本发布包未进行数字签名。",
        "phase_scanning": "扫描文件…",
        "phase_locking": "加密数据…",
        "phase_unlocking": "解密数据…",
        "phase_obfuscating_names": "混淆文件名…",
        "phase_restoring_names": "恢复文件名…",
    },
    "en": {
        "title": "Folder Locker",
        "container_tab": "Encrypted container (recommended)",
        "acl_tab": "Windows quick lock (advanced)",
        "encrypt_title": "Copy a folder into an AES-256-GCM encrypted container",
        "source_folder": "Source folder",
        "container_file": "Container file",
        "password": "Password",
        "confirm": "Confirm password",
        "browse": "Browse…",
        "encrypt": "Create encrypted container",
        "decrypt_title": "Restore a folder from a .locked container",
        "locked_file": ".locked file",
        "target_folder": "Restore to",
        "decrypt": "Decrypt and restore",
        "keep_notice": "To prevent data loss, the source folder is retained. Delete it yourself only after verifying that the container decrypts.",
        "acl_warning": "This mode changes NTFS permissions and obfuscates names; it is not encryption. Administrators or ACL-aware users may bypass it. Prefer an encrypted container.",
        "acl_folder": "Target folder",
        "acl_lock": "Apply quick lock",
        "acl_unlock": "Remove quick lock",
        "language": "中文",
        "about": "About",
        "ready": "Ready",
        "busy": "Working…",
        "missing": "Complete every required path and password field.",
        "password_mismatch": "The two passwords do not match.",
        "success_encrypt": "Encrypted container created:\n{path}\n\nThe source folder was retained.",
        "success_decrypt": "Folder restored:\n{path}",
        "success_acl_lock": "Quick lock applied. Metadata:\n{path}",
        "success_acl_unlock": "Quick lock removed.",
        "error": "Operation failed",
        "done": "Completed",
        "about_text": "Folder Locker v{version}\n\nAuthor: {author}\nEmail: {email}\nHomepage: {home}\nGitHub: {github}\n\nEncrypted containers use PBKDF2-HMAC-SHA256 and AES-256-GCM.\nRelease binaries are not digitally signed.",
        "phase_scanning": "Scanning files…",
        "phase_locking": "Encrypting data…",
        "phase_unlocking": "Decrypting data…",
        "phase_obfuscating_names": "Obfuscating names…",
        "phase_restoring_names": "Restoring names…",
    },
}


class FolderLockerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.language = load_language("folder_locker")
        self._busy = False
        self.status_var = tk.StringVar()
        self.geometry("900x700")
        self.minsize(780, 620)
        self.configure(bg="#0b1220")
        self._configure_theme()
        self._build_ui()
        self._apply_language()

    def tr(self, key: str, **values: object) -> str:
        return TEXT[self.language][key].format(**values)

    def _configure_theme(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background="#0b1220", foreground="#e2e8f0")
        style.configure("TFrame", background="#0b1220")
        style.configure("TLabel", background="#0b1220", foreground="#e2e8f0")
        style.configure("TLabelframe", background="#0b1220", foreground="#7dd3fc")
        style.configure("TLabelframe.Label", background="#0b1220", foreground="#7dd3fc")
        style.configure("TNotebook", background="#0b1220", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 8), background="#172033", foreground="#cbd5e1")
        style.map("TNotebook.Tab", background=[("selected", "#075985")], foreground=[("selected", "#ffffff")])
        style.configure("TButton", padding=(11, 7))
        style.configure("Accent.TButton", background="#0284c7", foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#0369a1")])
        style.configure("Horizontal.TProgressbar", background="#38bdf8", troughcolor="#1e293b")

    def _build_ui(self) -> None:
        shell = ttk.Frame(self, padding=16)
        shell.pack(fill=tk.BOTH, expand=True)
        top = ttk.Frame(shell)
        top.pack(fill=tk.X, pady=(0, 10))
        self.heading = ttk.Label(top, font=("Segoe UI Semibold", 19))
        self.heading.pack(side=tk.LEFT)
        self.about_button = ttk.Button(top, command=self.show_about)
        self.about_button.pack(side=tk.RIGHT)
        self.language_button = ttk.Button(top, command=self.toggle_language)
        self.language_button.pack(side=tk.RIGHT, padx=(0, 8))

        self.notebook = ttk.Notebook(shell)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.container_tab = ttk.Frame(self.notebook, padding=14)
        self.acl_tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.container_tab)
        self.notebook.add(self.acl_tab)
        self._build_container_tab()
        self._build_acl_tab()

        self.progress = ttk.Progressbar(shell, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(12, 4))
        self.status_label = ttk.Label(shell, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X)

    def _entry_row(self, parent: ttk.Frame, row: int, variable: tk.StringVar, command: object) -> tuple[ttk.Label, ttk.Button]:
        label = ttk.Label(parent)
        label.grid(row=row, column=0, sticky="w", pady=5)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", padx=8, pady=5)
        button = ttk.Button(parent, command=command)
        button.grid(row=row, column=2, pady=5)
        parent.columnconfigure(1, weight=1)
        return label, button

    def _password_row(self, parent: ttk.Frame, row: int, variable: tk.StringVar) -> ttk.Label:
        label = ttk.Label(parent)
        label.grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(parent, textvariable=variable, show="●").grid(row=row, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=5)
        return label

    def _build_container_tab(self) -> None:
        self.encrypt_frame = ttk.LabelFrame(self.container_tab, padding=12)
        self.encrypt_frame.pack(fill=tk.X)
        self.source_var = tk.StringVar()
        self.encrypt_target_var = tk.StringVar()
        self.encrypt_password_var = tk.StringVar()
        self.encrypt_confirm_var = tk.StringVar()
        self.source_label, self.source_browse = self._entry_row(self.encrypt_frame, 0, self.source_var, self.choose_source_folder)
        self.encrypt_target_label, self.encrypt_target_browse = self._entry_row(self.encrypt_frame, 1, self.encrypt_target_var, self.choose_encrypt_target)
        self.encrypt_password_label = self._password_row(self.encrypt_frame, 2, self.encrypt_password_var)
        self.encrypt_confirm_label = self._password_row(self.encrypt_frame, 3, self.encrypt_confirm_var)
        self.encrypt_button = ttk.Button(self.encrypt_frame, style="Accent.TButton", command=self.start_encrypt)
        self.encrypt_button.grid(row=4, column=1, sticky="e", pady=(10, 4))
        self.keep_notice = ttk.Label(self.encrypt_frame, foreground="#fbbf24", wraplength=760)
        self.keep_notice.grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self.decrypt_frame = ttk.LabelFrame(self.container_tab, padding=12)
        self.decrypt_frame.pack(fill=tk.X, pady=(14, 0))
        self.container_var = tk.StringVar()
        self.decrypt_target_var = tk.StringVar()
        self.decrypt_password_var = tk.StringVar()
        self.container_label, self.container_browse = self._entry_row(self.decrypt_frame, 0, self.container_var, self.choose_container)
        self.decrypt_target_label, self.decrypt_target_browse = self._entry_row(self.decrypt_frame, 1, self.decrypt_target_var, self.choose_decrypt_target)
        self.decrypt_password_label = self._password_row(self.decrypt_frame, 2, self.decrypt_password_var)
        self.decrypt_button = ttk.Button(self.decrypt_frame, style="Accent.TButton", command=self.start_decrypt)
        self.decrypt_button.grid(row=3, column=1, sticky="e", pady=(10, 4))

    def _build_acl_tab(self) -> None:
        self.acl_warning = ttk.Label(self.acl_tab, foreground="#fbbf24", wraplength=780)
        self.acl_warning.pack(fill=tk.X, pady=(0, 14))
        frame = ttk.Frame(self.acl_tab)
        frame.pack(fill=tk.X)
        self.acl_folder_var = tk.StringVar()
        self.acl_password_var = tk.StringVar()
        self.acl_confirm_var = tk.StringVar()
        self.acl_folder_label, self.acl_browse = self._entry_row(frame, 0, self.acl_folder_var, self.choose_acl_folder)
        self.acl_password_label = self._password_row(frame, 1, self.acl_password_var)
        self.acl_confirm_label = self._password_row(frame, 2, self.acl_confirm_var)
        button_row = ttk.Frame(frame)
        button_row.grid(row=3, column=1, columnspan=2, sticky="e", pady=(12, 0))
        self.acl_lock_button = ttk.Button(button_row, style="Accent.TButton", command=self.start_acl_lock)
        self.acl_lock_button.pack(side=tk.LEFT)
        self.acl_unlock_button = ttk.Button(button_row, command=self.start_acl_unlock)
        self.acl_unlock_button.pack(side=tk.LEFT, padx=(8, 0))

    def _apply_language(self) -> None:
        self.title(f"{self.tr('title')} v{APP_VERSION}")
        self.heading.configure(text=f"{self.tr('title')}  v{APP_VERSION}")
        self.language_button.configure(text=self.tr("language"))
        self.about_button.configure(text=self.tr("about"))
        self.notebook.tab(self.container_tab, text=self.tr("container_tab"))
        self.notebook.tab(self.acl_tab, text=self.tr("acl_tab"))
        self.encrypt_frame.configure(text=self.tr("encrypt_title"))
        self.decrypt_frame.configure(text=self.tr("decrypt_title"))
        for label, key in (
            (self.source_label, "source_folder"),
            (self.encrypt_target_label, "container_file"),
            (self.encrypt_password_label, "password"),
            (self.encrypt_confirm_label, "confirm"),
            (self.container_label, "locked_file"),
            (self.decrypt_target_label, "target_folder"),
            (self.decrypt_password_label, "password"),
            (self.acl_folder_label, "acl_folder"),
            (self.acl_password_label, "password"),
            (self.acl_confirm_label, "confirm"),
        ):
            label.configure(text=self.tr(key))
        for button in (self.source_browse, self.encrypt_target_browse, self.container_browse, self.decrypt_target_browse, self.acl_browse):
            button.configure(text=self.tr("browse"))
        self.encrypt_button.configure(text=self.tr("encrypt"))
        self.decrypt_button.configure(text=self.tr("decrypt"))
        self.acl_lock_button.configure(text=self.tr("acl_lock"))
        self.acl_unlock_button.configure(text=self.tr("acl_unlock"))
        self.keep_notice.configure(text=self.tr("keep_notice"))
        self.acl_warning.configure(text=self.tr("acl_warning"))
        if not self._busy:
            self.status_var.set(self.tr("ready"))

    def toggle_language(self) -> None:
        self.language = "en" if self.language == "zh" else "zh"
        save_language("folder_locker", self.language)
        self._apply_language()

    def show_about(self) -> None:
        messagebox.showinfo(
            self.tr("about"),
            self.tr("about_text", version=APP_VERSION, author=AUTHOR, email=EMAIL, home=HOMEPAGE, github=GITHUB),
            parent=self,
        )

    def choose_source_folder(self) -> None:
        selected = filedialog.askdirectory(parent=self)
        if selected:
            source = Path(selected)
            self.source_var.set(str(source))
            self.encrypt_target_var.set(str(default_container_for_folder(source)))

    def choose_encrypt_target(self) -> None:
        selected = filedialog.asksaveasfilename(parent=self, defaultextension=".locked", filetypes=[("Folder Locker", "*.locked")])
        if selected:
            self.encrypt_target_var.set(selected)

    def choose_container(self) -> None:
        selected = filedialog.askopenfilename(parent=self, filetypes=[("Folder Locker", "*.locked"), ("All", "*.*")])
        if selected:
            container = Path(selected)
            self.container_var.set(str(container))
            self.decrypt_target_var.set(str(default_folder_for_container(container)))

    def choose_decrypt_target(self) -> None:
        parent = filedialog.askdirectory(parent=self)
        if parent:
            source = Path(self.container_var.get()) if self.container_var.get() else Path("restored")
            self.decrypt_target_var.set(str(Path(parent) / default_folder_for_container(source).name))

    def choose_acl_folder(self) -> None:
        selected = filedialog.askdirectory(parent=self)
        if selected:
            self.acl_folder_var.set(selected)

    def _run_background(self, operation: object, success_key: str, success_path: Path | None = None) -> None:
        if self._busy:
            return
        self._busy = True
        self.status_var.set(self.tr("busy"))
        self.progress.configure(value=0, maximum=100)

        def worker() -> None:
            try:
                operation()
            except Exception as error:
                self.after(0, self._finish_error, error)
                return
            self.after(0, self._finish_success, success_key, success_path)

        threading.Thread(target=worker, daemon=True).start()

    def _progress_callback(self, phase: str, done: int, total: int) -> None:
        percent = min(100, int(done * 100 / max(total, 1)))
        key = f"phase_{phase}"
        message = self.tr(key) if key in TEXT[self.language] else self.tr("busy")
        self.after(0, self._update_progress, message, percent)

    def _update_progress(self, message: str, percent: int) -> None:
        self.status_var.set(message)
        self.progress.configure(value=percent)

    def _finish_error(self, error: Exception) -> None:
        self._busy = False
        self.status_var.set(self.tr("ready"))
        messagebox.showerror(self.tr("error"), str(error), parent=self)

    def _finish_success(self, key: str, path: Path | None) -> None:
        self._busy = False
        self.progress.configure(value=100)
        self.status_var.set(self.tr("done"))
        values = {"path": path} if path is not None else {}
        messagebox.showinfo(self.tr("done"), self.tr(key, **values), parent=self)

    def start_encrypt(self) -> None:
        source = Path(self.source_var.get()) if self.source_var.get() else None
        target = Path(self.encrypt_target_var.get()) if self.encrypt_target_var.get() else None
        password = self.encrypt_password_var.get()
        if source is None or target is None or not password:
            messagebox.showwarning(self.tr("title"), self.tr("missing"), parent=self)
            return
        if password != self.encrypt_confirm_var.get():
            messagebox.showwarning(self.tr("title"), self.tr("password_mismatch"), parent=self)
            return
        self._run_background(lambda: encrypt_folder_stream(source, target, password, self._progress_callback), "success_encrypt", target)

    def start_decrypt(self) -> None:
        container = Path(self.container_var.get()) if self.container_var.get() else None
        target = Path(self.decrypt_target_var.get()) if self.decrypt_target_var.get() else None
        password = self.decrypt_password_var.get()
        if container is None or target is None or not password:
            messagebox.showwarning(self.tr("title"), self.tr("missing"), parent=self)
            return
        self._run_background(lambda: decrypt_container_to_folder(container, target, password, self._progress_callback), "success_decrypt", target)

    def start_acl_lock(self) -> None:
        folder = Path(self.acl_folder_var.get()) if self.acl_folder_var.get() else None
        password = self.acl_password_var.get()
        if folder is None or not password:
            messagebox.showwarning(self.tr("title"), self.tr("missing"), parent=self)
            return
        if password != self.acl_confirm_var.get():
            messagebox.showwarning(self.tr("title"), self.tr("password_mismatch"), parent=self)
            return
        metadata = acl_metadata_path(folder)
        self._run_background(lambda: lock_folder_acl(folder, password, self._progress_callback), "success_acl_lock", metadata)

    def start_acl_unlock(self) -> None:
        folder = Path(self.acl_folder_var.get()) if self.acl_folder_var.get() else None
        password = self.acl_password_var.get()
        if folder is None or not password:
            messagebox.showwarning(self.tr("title"), self.tr("missing"), parent=self)
            return
        self._run_background(lambda: unlock_folder_acl(folder, password, self._progress_callback), "success_acl_unlock")


def main() -> None:
    app = FolderLockerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
