"""Reports screen."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
from datetime import datetime, timedelta
from pathlib import Path
from inventory_app.db.session import get_db_session
from inventory_app.services.report_service import (
    stock_availability_report,
    sales_vs_stock_report,
    slow_fast_movers_report,
    supplier_performance_report,
    export_reports_to_excel
)
from inventory_app.utils.logging import logger


class ReportsWindow:
    """Reports window."""
    
    def __init__(self, parent, user, on_navigate_callback):
        self.parent = parent
        self.user = user
        self.on_navigate = on_navigate_callback
        
        # Main frame
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.pack(fill=BOTH, expand=TRUE)
        
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Reports", font=("Helvetica", 18, "bold")).pack(side=LEFT)
        
        # Date range frame
        date_frame = ttk.LabelFrame(self.frame, text="Date Range (for time-based reports)", padding=10)
        date_frame.pack(fill=X, pady=10)
        
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, padx=5)
        self.start_date_entry = ttk.Entry(date_frame, width=15)
        self.start_date_entry.grid(row=0, column=1, padx=5)
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        
        ttk.Label(date_frame, text="End Date:").grid(row=0, column=2, padx=5)
        self.end_date_entry = ttk.Entry(date_frame, width=15)
        self.end_date_entry.grid(row=0, column=3, padx=5)
        self.end_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Report buttons
        reports_frame = ttk.LabelFrame(self.frame, text="Available Reports", padding=10)
        reports_frame.pack(fill=X, pady=10)
        
        ttk.Button(
            reports_frame,
            text="Stock Availability",
            command=self.view_stock_availability,
            bootstyle=PRIMARY,
            width=25
        ).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(
            reports_frame,
            text="Sales vs Stock",
            command=self.view_sales_vs_stock,
            bootstyle=PRIMARY,
            width=25
        ).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(
            reports_frame,
            text="Slow/Fast Movers",
            command=self.view_movers,
            bootstyle=PRIMARY,
            width=25
        ).grid(row=1, column=0, padx=5, pady=5)
        
        ttk.Button(
            reports_frame,
            text="Supplier Performance",
            command=self.view_supplier_performance,
            bootstyle=PRIMARY,
            width=25
        ).grid(row=1, column=1, padx=5, pady=5)
        
        # Export button
        export_frame = ttk.Frame(self.frame)
        export_frame.pack(fill=X, pady=20)
        
        ttk.Button(
            export_frame,
            text="Export All Reports to Excel",
            command=self.export_all_reports,
            bootstyle=SUCCESS,
            width=30
        ).pack()
        
        # Results frame
        results_frame = ttk.LabelFrame(self.frame, text="Report Results", padding=10)
        results_frame.pack(fill=BOTH, expand=TRUE, pady=10)
        
        # Treeview for results
        self.results_tree = ttk.Treeview(results_frame, show="headings")
        results_scrollbar = ttk.Scrollbar(results_frame, orient=VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.pack(side=LEFT, fill=BOTH, expand=TRUE)
        results_scrollbar.pack(side=RIGHT, fill=Y)
    
    def get_date_range(self):
        """Get start and end dates from entries."""
        try:
            start_str = self.start_date_entry.get().strip()
            end_str = self.end_date_entry.get().strip()
            
            start_date = datetime.strptime(start_str, "%Y-%m-%d") if start_str else None
            end_date = datetime.strptime(end_str, "%Y-%m-%d") if end_str else None
            
            if end_date:
                end_date = end_date.replace(hour=23, minute=59, second=59)
            
            return start_date, end_date
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return None, None
    
    def display_dataframe(self, df, title=""):
        """Display pandas DataFrame in treeview."""
        # Clear tree
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        if df.empty:
            return
        
        # Configure columns
        columns = list(df.columns)
        self.results_tree["columns"] = columns
        self.results_tree["show"] = "headings"
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120)
        
        # Insert rows
        for _, row in df.iterrows():
            values = [str(val) for val in row.values]
            self.results_tree.insert("", END, values=values)
    
    def view_stock_availability(self):
        """View stock availability report."""
        db = next(get_db_session())
        try:
            df = stock_availability_report(db)
            self.display_dataframe(df, "Stock Availability")
        except Exception as e:
            logger.error(f"Error generating stock availability report: {e}")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
        finally:
            db.close()
    
    def view_sales_vs_stock(self):
        """View sales vs stock report."""
        start_date, end_date = self.get_date_range()
        if start_date is None and end_date is None:
            return
        
        db = next(get_db_session())
        try:
            df = sales_vs_stock_report(db, start_date, end_date)
            self.display_dataframe(df, "Sales vs Stock")
        except Exception as e:
            logger.error(f"Error generating sales vs stock report: {e}")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
        finally:
            db.close()
    
    def view_movers(self):
        """View slow/fast movers report."""
        start_date, end_date = self.get_date_range()
        if start_date is None and end_date is None:
            return
        
        db = next(get_db_session())
        try:
            df = slow_fast_movers_report(db, start_date, end_date)
            self.display_dataframe(df, "Slow/Fast Movers")
        except Exception as e:
            logger.error(f"Error generating movers report: {e}")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
        finally:
            db.close()
    
    def view_supplier_performance(self):
        """View supplier performance report."""
        start_date, end_date = self.get_date_range()
        if start_date is None and end_date is None:
            return
        
        db = next(get_db_session())
        try:
            df = supplier_performance_report(db, start_date, end_date)
            self.display_dataframe(df, "Supplier Performance")
        except Exception as e:
            logger.error(f"Error generating supplier performance report: {e}")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
        finally:
            db.close()
    
    def export_all_reports(self):
        """Export all reports to Excel."""
        start_date, end_date = self.get_date_range()
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"inventory_reports_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        
        if not filename:
            return
        
        db = next(get_db_session())
        try:
            export_reports_to_excel(db, Path(filename), start_date, end_date)
            messagebox.showinfo("Success", f"Reports exported successfully to {filename}")
        except Exception as e:
            logger.error(f"Error exporting reports: {e}")
            messagebox.showerror("Error", f"Failed to export reports: {str(e)}")
        finally:
            db.close()
    
    def destroy(self):
        """Clean up."""
        self.frame.destroy()

