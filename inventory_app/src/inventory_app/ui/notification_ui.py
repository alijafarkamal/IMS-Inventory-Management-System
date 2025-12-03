"""UI windows for sending and viewing in-app notifications."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Toplevel, END
from inventory_app.services.notifier_config import load_notification_config
from inventory_app.services.notification_store import (
    create_notification,
    get_notifications_for_user,
    mark_notification_read,
)
from inventory_app.db.session import get_db_session
from inventory_app.utils.logging import logger


class SendNotificationWindow:
    """Window for staff to send notifications to Manager and Admin."""

    def __init__(self, parent, sender):
        self.sender = sender
        self.top = Toplevel(parent)
        self.top.title("Send Notification")
        self.top.geometry("480x300")
        self.top.transient(parent)
        self.top.grab_set()

        body = ttk.Frame(self.top, padding=12)
        body.pack(fill=BOTH, expand=TRUE)

        ttk.Label(body, text="Title:").pack(anchor=W)
        self.title_var = ttk.StringVar()
        ttk.Entry(body, textvariable=self.title_var).pack(fill=X)

        ttk.Label(body, text="Message:").pack(anchor=W, pady=(8, 0))
        self.msg = ttk.Text(body, height=8)
        self.msg.pack(fill=BOTH, expand=TRUE)

        # Recipient checkboxes
        recip_frame = ttk.Frame(body)
        recip_frame.pack(fill=X, pady=(8, 0))
        self.to_manager = ttk.BooleanVar(value=True)
        self.to_admin = ttk.BooleanVar(value=True)
        ttk.Checkbutton(recip_frame, text="Manager", variable=self.to_manager).pack(side=LEFT, padx=6)
        ttk.Checkbutton(recip_frame, text="Admin", variable=self.to_admin).pack(side=LEFT, padx=6)

        btn_frame = ttk.Frame(body)
        btn_frame.pack(fill=X, pady=(12, 0))
        ttk.Button(btn_frame, text="Send", bootstyle=SUCCESS, command=self.send).pack(side=RIGHT)
        ttk.Button(btn_frame, text="Close", bootstyle=SECONDARY, command=self.close).pack(side=RIGHT, padx=6)

    def send(self):
        title = self.title_var.get().strip()
        message = self.msg.get("1.0", END).strip()
        recipients = []
        if self.to_manager.get():
            recipients.append("Manager")
        if self.to_admin.get():
            recipients.append("Admin")
        if not title or not message or not recipients:
            logger.error("Title, message and at least one recipient are required")
            return

        db = get_db_session()
        try:
            create_notification(db=db, title=title, message=message, sender=self.sender.username, recipients=recipients)
            logger.info("Notification sent")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
        finally:
            db.close()
            self.close()

    def close(self):
        try:
            self.top.grab_release()
        except Exception:
            pass
        self.top.destroy()


class ViewNotificationsWindow:
    """Window for Manager/Admin to view notifications."""

    def __init__(self, parent, user):
        self.user = user
        self.top = Toplevel(parent)
        self.top.title("Notifications")
        self.top.geometry("640x360")
        self.top.transient(parent)
        self.top.grab_set()

        body = ttk.Frame(self.top, padding=12)
        body.pack(fill=BOTH, expand=TRUE)

        self.tree = ttk.Treeview(body, columns=("Title", "Message", "Sender", "When", "Read"), show="headings")
        for c in ("Title", "Message", "Sender", "When", "Read"):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)
        self.tree.pack(fill=BOTH, expand=TRUE)

        btn_frame = ttk.Frame(body)
        btn_frame.pack(fill=X)
        ttk.Button(btn_frame, text="Mark Read", bootstyle=SUCCESS, command=self.mark_selected_read).pack(side=RIGHT)
        ttk.Button(btn_frame, text="Close", bootstyle=SECONDARY, command=self.close).pack(side=RIGHT, padx=6)

        self.refresh()

    def refresh(self):
        db = get_db_session()
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            notifs = get_notifications_for_user(db=db, user=self.user)
            for n in notifs:
                self.tree.insert("", END, iid=str(n.id), values=(n.title, (n.message[:80] + '...') if len(n.message) > 80 else n.message, n.sender, n.created_at.strftime("%Y-%m-%d %H:%M"), "Yes" if n.is_read else "No"))
        except Exception as e:
            logger.error(f"Failed to load notifications: {e}")
        finally:
            db.close()

    def mark_selected_read(self):
        sel = self.tree.selection()
        if not sel:
            return
        db = get_db_session()
        try:
            for iid in sel:
                mark_notification_read(db=db, notification_id=int(iid))
            db.close()
            self.refresh()
        except Exception as e:
            logger.error(f"Failed to mark read: {e}")

    def close(self):
        try:
            self.top.grab_release()
        except Exception:
            pass
        self.top.destroy()
