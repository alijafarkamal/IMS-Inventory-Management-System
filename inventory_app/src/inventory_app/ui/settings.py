"""Settings window for notification/email configuration."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Toplevel

from inventory_app.services.notifier_config import load_notification_config, save_notification_config
from inventory_app.utils.logging import logger


class SettingsWindow:
    """Toplevel window to configure notification email settings.

    Provides two fields:
    - Sender email
    - Recipients (comma-separated)
    """

    def __init__(self, parent):
        self.parent = parent
        self.top = Toplevel(parent)
        self.top.title("Notification Settings")
        self.top.geometry("420x200")
        self.top.transient(parent)
        self.top.grab_set()

        cfg = load_notification_config()

        body = ttk.Frame(self.top, padding=12)
        body.pack(fill=BOTH, expand=TRUE)

        ttk.Label(body, text="Sender Email:").pack(anchor=W, pady=(0, 4))
        self.sender_var = ttk.StringVar(value=cfg.get("sender", ""))
        ttk.Entry(body, textvariable=self.sender_var).pack(fill=X)

        ttk.Label(body, text="Recipients (comma-separated):").pack(anchor=W, pady=(12, 4))
        self.recipients_var = ttk.StringVar(value=", ".join(cfg.get("recipients", [])))
        ttk.Entry(body, textvariable=self.recipients_var).pack(fill=X)

        btn_frame = ttk.Frame(body)
        btn_frame.pack(fill=X, pady=(16, 0))

        ttk.Button(btn_frame, text="Save", command=self.save, bootstyle=SUCCESS).pack(side=RIGHT, padx=6)
        ttk.Button(btn_frame, text="Close", command=self.close, bootstyle=SECONDARY).pack(side=RIGHT)

    def save(self):
        sender = self.sender_var.get().strip()
        recipients_raw = self.recipients_var.get().strip()
        recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
        try:
            save_notification_config(sender=sender, recipients=recipients)
            logger.info("Notification settings saved")
        except Exception as e:
            logger.error(f"Failed to save notification settings: {e}")
        finally:
            self.close()

    def close(self):
        try:
            self.top.grab_release()
        except Exception:
            pass
        self.top.destroy()
