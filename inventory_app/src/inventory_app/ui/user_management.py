"""User management screen for admin."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from inventory_app.db.session import get_db_session
from inventory_app.services.user_management_service import (
    get_all_users,
    create_new_user,
    update_user,
    reset_password,
    deactivate_user,
    activate_user,
    delete_user,
)
from inventory_app.models.user import User
from inventory_app.config import ROLE_ADMIN, ROLE_MANAGER, ROLE_STAFF
from inventory_app.utils.logging import logger


class UserManagementWindow:
    """Admin user management screen."""
    
    def __init__(self, parent, user: User, on_navigate_callback=None):
        self.parent = parent
        self.user = user
        self.on_navigate = on_navigate_callback
        
        # Main frame
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.pack(fill=BOTH, expand=TRUE)
        
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(header_frame, text="User Management", font=("Helvetica", 18, "bold")).pack(side=LEFT)
        
        # Buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=X, pady=10)
        
        ttk.Button(
            btn_frame,
            text="Add User",
            command=self.add_user_dialog,
            bootstyle=SUCCESS
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Edit Selected",
            command=self.edit_selected,
            bootstyle=INFO
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Delete Selected",
            command=self.delete_selected,
            bootstyle=DANGER
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Refresh",
            command=self.refresh_users,
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=5)
        
        # Users table: simplified (excluding Admin user)
        columns = ("ID", "Username", "Role", "Active", "Created")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110)
        
        scrollbar = ttk.Scrollbar(self.frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=TRUE)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Bind right-click for context menu
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        self.refresh_users()
    
    def refresh_users(self):
        """Refresh users list."""
        db = get_db_session()
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            users = get_all_users(db)
            for user in users:
                # Hide Admin from list
                if user.role == ROLE_ADMIN:
                    continue
                self.tree.insert(
                    "",
                    END,
                    iid=user.id,
                    values=(
                        user.id,
                        user.username,
                        user.role,
                        "Yes" if user.is_active else "No",
                        user.created_at.strftime("%Y-%m-%d %H:%M") if getattr(user, "created_at", None) else "N/A"
                    )
                )
        finally:
            db.close()
    
    def add_user_dialog(self):
        """Open dialog to add a new user."""
        dialog = UserAddDialog(self.frame, on_save=self.refresh_users)
    
    def show_context_menu(self, event):
        """Show context menu on right-click."""
        item = self.tree.selection()
        if not item:
            return
        
        item_id = item[0]
        
        menu = ttk.Menu(self.tree, tearoff=False)
        menu.add_command(label="Edit", command=lambda: self.edit_user(item_id))
        menu.add_command(label="Reset Password", command=lambda: self.reset_password_dialog(item_id))
        menu.add_separator()
        
        # Get current active status
        values = self.tree.item(item_id, 'values')
        is_active = values[5] == "Yes" if len(values) > 5 else True
        
        if is_active:
            menu.add_command(label="Deactivate", command=lambda: self.toggle_active(item_id, False))
        else:
            menu.add_command(label="Activate", command=lambda: self.toggle_active(item_id, True))
        menu.add_separator()
        menu.add_command(label="Delete", command=lambda: self.delete_user_confirm(item_id))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def edit_user(self, user_id):
        """Edit user details."""
        db = get_db_session()
        try:
            from inventory_app.services.user_management_service import get_user_by_id
            user = get_user_by_id(db, user_id)
            if not user:
                messagebox.showerror("Error", "User not found")
                return
            
            dialog = UserEditDialog(self.frame, user, on_save=self.refresh_users)
        finally:
            db.close()

    def edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Edit User", "Please select a user to edit.")
            return
        self.edit_user(sel[0])
    
    def reset_password_dialog(self, user_id):
        """Reset user password."""
        db = get_db_session()
        try:
            from inventory_app.services.user_management_service import get_user_by_id
            user = get_user_by_id(db, user_id)
            if not user:
                messagebox.showerror("Error", "User not found")
                return
            
            new_password = simpledialog.askstring(
                "Reset Password",
                f"Enter new password for {user.username}:",
                show="*"
            )
            
            if new_password:
                reset_password(db, user_id, new_password)
                messagebox.showinfo("Success", f"Password reset for {user.username}")
                self.refresh_users()
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            messagebox.showerror("Error", f"Failed to reset password: {e}")
        finally:
            db.close()
    
    def toggle_active(self, user_id, activate: bool):
        """Activate or deactivate a user."""
        db = get_db_session()
        try:
            if activate:
                activate_user(db, user_id)
                messagebox.showinfo("Success", "User activated")
            else:
                deactivate_user(db, user_id)
                messagebox.showinfo("Success", "User deactivated")
            self.refresh_users()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            logger.error(f"Error toggling user active status: {e}")
            messagebox.showerror("Error", f"Failed to update user: {e}")
        finally:
            db.close()

    def delete_user_confirm(self, user_id):
        try:
            values = self.tree.item(user_id, 'values')
            username = values[1] if len(values) > 1 else str(user_id)
        except Exception:
            username = str(user_id)
        if not messagebox.askyesno("Confirm Action", f"User '{username}' has activity history. Deactivate instead of delete?"):
            return
        db = get_db_session()
        try:
            # Prefer soft deactivation to avoid FK integrity issues on activity_log
            deactivate_user(db, int(user_id))
            messagebox.showinfo("Deactivated", f"User '{username}' deactivated")
            self.refresh_users()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            messagebox.showerror("Error", f"Failed to deactivate user: {e}")
        finally:
            db.close()

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Delete User", "Please select a user to delete.")
            return
        self.delete_user_confirm(sel[0])
    
    def destroy(self):
        """Clean up."""
        self.frame.destroy()


class UserAddDialog:
    """Dialog to add a new user."""
    
    def __init__(self, parent, on_save=None):
        self.on_save = on_save
        
        self.window = ttk.Toplevel(parent)
        self.window.title("Add New User")
        self.window.geometry("700x520")
        self.window.minsize(600, 450)
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill=BOTH, expand=TRUE)
        
        # Form fields (username + password only)
        ttk.Label(main_frame, text="Username:").grid(row=0, column=0, sticky=W, pady=5)
        self.username_entry = ttk.Entry(main_frame, width=25)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(main_frame, text="Password:").grid(row=1, column=0, sticky=W, pady=5)
        self.password_entry = ttk.Entry(main_frame, width=25, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(main_frame, text="Confirm Password:").grid(row=2, column=0, sticky=W, pady=5)
        self.confirm_entry = ttk.Entry(main_frame, width=25, show="*")
        self.confirm_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(main_frame, text="Role:").grid(row=3, column=0, sticky=W, pady=5)
        self.role_var = ttk.StringVar(value=ROLE_STAFF)
        self.role_combo = ttk.Combobox(
            main_frame,
            textvariable=self.role_var,
            values=[ROLE_STAFF, ROLE_MANAGER],
            state="readonly",
            width=22
        )
        self.role_combo.grid(row=3, column=1, padx=10, pady=5)
        
        # Error label
        self.error_label = ttk.Label(main_frame, text="", foreground="red")
        self.error_label.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            btn_frame,
            text="Create User",
            command=self.create_user,
            bootstyle=SUCCESS
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.window.destroy,
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=5)
    
    def create_user(self):
        """Create the user."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        role = self.role_var.get()
        
        # Validation
        if not all([username, password]):
            self.error_label.config(text="All fields are required")
            return
        
        if password != confirm:
            self.error_label.config(text="Passwords do not match")
            return
        
        if len(password) < 6:
            self.error_label.config(text="Password must be at least 6 characters")
            return
        
        db = get_db_session()
        try:
            create_new_user(db, username, password, role)
            messagebox.showinfo("Success", f"User '{username}' created successfully")
            self.window.destroy()
            if self.on_save:
                self.on_save()
        except ValueError as e:
            self.error_label.config(text=str(e))
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            messagebox.showerror("Error", f"Failed to create user: {e}")
        finally:
            db.close()


class UserEditDialog:
    """Dialog to edit user details."""
    
    def __init__(self, parent, user: User, on_save=None):
        self.user = user
        self.on_save = on_save
        
        self.window = ttk.Toplevel(parent)
        self.window.title(f"Edit User: {user.username}")
        self.window.geometry("700x460")
        self.window.minsize(580, 380)
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill=BOTH, expand=TRUE)
        
        # Form fields
        ttk.Label(main_frame, text="Username:").grid(row=0, column=0, sticky=W, pady=5)
        self.username_entry = ttk.Entry(main_frame, width=25)
        self.username_entry.insert(0, user.username)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)
        


        # Role
        ttk.Label(main_frame, text="Role:").grid(row=1, column=0, sticky=W, pady=5)
        self.role_var = ttk.StringVar(value=user.role if user.role in (ROLE_STAFF, ROLE_MANAGER) else ROLE_MANAGER)
        self.role_combo = ttk.Combobox(
            main_frame,
            textvariable=self.role_var,
            values=[ROLE_STAFF, ROLE_MANAGER],
            state="readonly",
            width=22
        )
        self.role_combo.grid(row=1, column=1, padx=10, pady=5)

        # New Password (optional)
        ttk.Label(main_frame, text="New Password:").grid(row=2, column=0, sticky=W, pady=5)
        self.new_password_entry = ttk.Entry(main_frame, width=25, show="*")
        self.new_password_entry.grid(row=2, column=1, padx=10, pady=5)
        
        # Error label
        self.error_label = ttk.Label(main_frame, text="", foreground="red")
        self.error_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            btn_frame,
            text="Save Changes",
            command=self.save_changes,
            bootstyle=SUCCESS
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.window.destroy,
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=5)
    
    def save_changes(self):
        """Save user changes."""
        username = self.username_entry.get().strip()
        role = self.role_var.get()
        new_password = self.new_password_entry.get()

        db = get_db_session()
        try:
            # Update username/role only
            update_user(db, self.user.id, username=username or None, role=role)
            # Optionally reset password if provided
            if new_password:
                reset_password(db, self.user.id, new_password)
            messagebox.showinfo("Success", "User updated successfully")
            self.window.destroy()
            if self.on_save:
                self.on_save()
        except ValueError as e:
            self.error_label.config(text=str(e))
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            messagebox.showerror("Error", f"Failed to update user: {e}")
        finally:
            db.close()