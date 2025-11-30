import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time

class BatchProgressGUI(tk.Toplevel):
    def __init__(self, title, items, process_func, on_complete=None):
        """
        Generic Batch Progress Window.
        
        Args:
            title (str): Window title.
            items (list): List of items to process.
            process_func (callable): Function to process each item. 
                                     Signature: process_func(item, update_msg_callback) -> (success: bool, error_msg: str)
            on_complete (callable): Optional callback when done.
        """
        super().__init__()
        self.title(title)
        self.geometry("500x250")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        self.items = items
        self.process_func = process_func
        self.on_complete = on_complete
        
        self.is_cancelled = False
        self.is_running = False
        self.queue = queue.Queue()
        
        self.success_count = 0
        self.errors = []
        
        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Start processing automatically
        self.start_processing()
        
    def _create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status Label
        self.lbl_status = ttk.Label(main_frame, text="Ready...", font=("Segoe UI", 10))
        self.lbl_status.pack(anchor=tk.W, pady=(0, 10))
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=len(self.items))
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Counter Label
        self.lbl_counter = ttk.Label(main_frame, text=f"0 / {len(self.items)}", font=("Segoe UI", 9), foreground="gray")
        self.lbl_counter.pack(anchor=tk.E, pady=(0, 15))
        
        # Log Area (for current item or errors)
        self.log_text = tk.Text(main_frame, height=5, width=60, font=("Consolas", 9), state=tk.DISABLED, bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        self.btn_cancel = ttk.Button(btn_frame, text="Stop", command=self.on_cancel)
        self.btn_cancel.pack(side=tk.RIGHT)
        
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_processing(self):
        self.is_running = True
        self.btn_cancel.config(text="Stop")
        self.lbl_status.config(text="Processing...")
        
        # Start thread
        threading.Thread(target=self._worker, daemon=True).start()
        
        # Start polling queue
        self.after(100, self._poll_queue)
        
    def _worker(self):
        for i, item in enumerate(self.items):
            if self.is_cancelled:
                break
                
            # Update UI: Start of item
            self.queue.put(("start_item", (i, item)))
            
            try:
                # Run processing
                # Pass a lambda to allow the worker to update status message dynamically
                def update_msg(msg):
                    self.queue.put(("msg", msg))
                    
                success, error_msg = self.process_func(item, update_msg)
                
                self.queue.put(("end_item", (success, error_msg)))
                
            except Exception as e:
                self.queue.put(("end_item", (False, str(e))))
                
        self.queue.put(("done", None))
        
    def _poll_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                
                if msg_type == "start_item":
                    idx, item = data
                    name = str(item)
                    if hasattr(item, 'name'): name = item.name
                    self.lbl_status.config(text=f"Processing: {name}")
                    self.progress_var.set(idx)
                    
                elif msg_type == "msg":
                    self.lbl_status.config(text=data)
                    
                elif msg_type == "end_item":
                    success, error_msg = data
                    self.progress_var.set(self.progress_var.get() + 1)
                    self.lbl_counter.config(text=f"{int(self.progress_var.get())} / {len(self.items)}")
                    
                    if success:
                        self.success_count += 1
                    else:
                        self.errors.append(error_msg)
                        self.log(f"Error: {error_msg}")
                        
                elif msg_type == "done":
                    self.is_running = False
                    self._finish()
                    return
                    
        except queue.Empty:
            pass
            
        if self.is_running:
            self.after(100, self._poll_queue)
            
    def on_cancel(self):
        if self.is_running:
            if messagebox.askyesno("Stop", "Are you sure you want to stop the process?"):
                self.is_cancelled = True
                self.lbl_status.config(text="Stopping...")
                self.btn_cancel.config(state=tk.DISABLED)
        else:
            self.destroy()
            
    def _finish(self):
        self.progress_var.set(len(self.items))
        self.btn_cancel.config(text="Close", state=tk.NORMAL, command=self.destroy)
        
        if self.is_cancelled:
            self.lbl_status.config(text="Stopped by user.", foreground="orange")
            self.log("Process stopped by user.")
        else:
            self.lbl_status.config(text="Completed.", foreground="green")
            self.log("Process completed.")
            
        # Show summary
        if self.errors:
            messagebox.showwarning("Completed with Errors", 
                f"Processed: {self.success_count}/{len(self.items)}\n"
                f"Errors: {len(self.errors)}\n\n"
                "Check the log for details.")
        else:
            if not self.is_cancelled:
                messagebox.showinfo("Success", f"Successfully processed {self.success_count} items.")
            
        if self.on_complete:
            self.on_complete(self.success_count, self.errors)

def run_batch_gui(title, items, process_func, parent=None):
    """Helper to run the GUI."""
    if not items: return
    
    # Ensure root exists
    root = parent
    if not root:
        try:
            # Check if root already exists
            if tk._default_root:
                root = tk._default_root
            else:
                root = tk.Tk()
                root.withdraw()
        except:
            root = None
        
    app = BatchProgressGUI(title, items, process_func)
    app.mainloop()
