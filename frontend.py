import tkinter as tk
from tkinter import messagebox, ttk
import requests
import threading

API_URL = "http://127.0.0.1:5000"

class BookstoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Online Bookstore")
        self.geometry("800x600")
        self.current_user_id = None
        self.current_role = None
        self.cart = []
        
        self.show_login_screen()
        
    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()
    
    #login screen
    def show_login_screen(self):
        self.clear_screen()
        tk.Label(self, text="Bookstore Login", font=("Arial", 24)).pack(pady=20)
        
        tk.Label(self, text="Username").pack()
        username_entry = tk.Entry(self)
        username_entry.pack()
        
        tk.Label(self, text="Password").pack()
        password_entry = tk.Entry(self, show="*")
        password_entry.pack()
    
        def perform_login():
            user = username_entry.get()
            pwd = password_entry.get()
            try:
                response = requests.post(f"{API_URL}/login", json={"username": user, "password": pwd})
                if response.status_code == 200:
                    data = response.json()
                    self.current_user_id = data['user_id']
                    self.current_role = data['role']
                    if self.current_role == 'manager':
                        self.show_manager_dashboard()
                    else:
                        self.show_customer_dashboard()
                else:
                    messagebox.showerror("Error", "Invalid login credentials")
            except:
                messagebox.showerror("Error", "Cannot connect to server")
            
        tk.Button(self, text="Login", command=perform_login).pack(pady=10)
        tk.Button(self, text="Register", command=self.show_register_screen).pack()
    
    def show_register_screen(self):
        self.clear_screen()
        tk.Label(self, text="Register New User", font=("Arial", 16)).pack(pady=10)
        
        tk.Label(self, text="Username").pack()
        u_entry = tk.Entry(self)
        u_entry.pack()
        
        tk.Label(self, text="Email").pack()
        e_entry = tk.Entry(self)
        e_entry.pack()
        
        tk.Label(self, text="Password").pack()
        p_entry = tk.Entry(self, show="*")
        p_entry.pack()
        
        def register():
            data = {
                "username": u_entry.get(),
                "email": e_entry.get(),
                "password": p_entry.get()
            }
            requests.post(f"{API_URL}/register", json=data)
            messagebox.showinfo("Success", "Account created successfully")
            self.show_login_screen()
            
        tk.Button(self, text="Submit", command=register).pack(pady=10)
        tk.Button(self, text="Back", command=self.show_login_screen).pack()
        
    def show_customer_dashboard(self):
        self.clear_screen()
        tk.Label(self, text="Book Catalog", font=("Arial", 16)).pack(pady=10)
        
        # Search Bar 
        frame_search = tk.Frame(self)
        frame_search.pack()
        search_entry = tk.Entry(frame_search, width=30)
        search_entry.pack(side=tk.LEFT)
        
        # Results List
        columns = ("ID", "Title", "Author", "Buy Price", "Rent Price")
        tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
        tree.pack(pady=10, fill=tk.BOTH, expand=True)

        def search_books():
            # Threading to prevent freezing 
            def run_search():
                q = search_entry.get()
                resp = requests.get(f"{API_URL}/books", params={"q": q})
                books = resp.json()
                
                # Update UI in main thread
                for i in tree.get_children():
                    tree.delete(i)
                for b in books:
                    tree.insert("", tk.END, values=(b['id'], b['title'], b['author'], b['buy_price'], b['rent_price']))
            
            threading.Thread(target=run_search).start()

        tk.Button(frame_search, text="Search", command=search_books).pack(side=tk.LEFT, padx=5)

        # Actions
        def add_to_cart(action_type):
            selected = tree.selection()
            if not selected: return
            item = tree.item(selected[0])['values']
            price = item[3] if action_type == 'buy' else item[4]
            self.cart.append({"book_id": item[0], "type": action_type, "price": price})
            messagebox.showinfo("Cart", f"Added {item[1]} to {action_type} list.")

        def checkout():
            if not self.cart: return
            payload = {"user_id": self.current_user_id, "items": self.cart}
            requests.post(f"{API_URL}/orders", json=payload)
            messagebox.showinfo("Success", "Order Placed! Bill sent to email.")
            self.cart = []

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Buy Selected", command=lambda: add_to_cart('buy')).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Rent Selected", command=lambda: add_to_cart('rent')).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Checkout", command=checkout, bg="green", fg="white").pack(side=tk.LEFT, padx=20)
        tk.Button(self, text="Logout", command=self.show_login_screen).pack(pady=5)

    #Manager Dashboard
    def show_manager_dashboard(self):
        self.clear_screen()
        tk.Label(self, text="Manager Dashboard", font=("Arial", 16)).pack(pady=10)
        
        #  Create Tabs
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill="both")

        # Orders tab
        order_frame = tk.Frame(notebook)
        notebook.add(order_frame, text="Manage Orders")
        
        columns = ("ID", "User", "Total", "Status")
        order_tree = ttk.Treeview(order_frame, columns=columns, show="headings")
        for col in columns:
            order_tree.heading(col, text=col)
        order_tree.pack(fill=tk.BOTH, expand=True)

        def load_orders():
            resp = requests.get(f"{API_URL}/orders")
            orders = resp.json()
            for i in order_tree.get_children():
                order_tree.delete(i)
            for o in orders:
                order_tree.insert("", tk.END, values=(o['id'], o['username'], o['total_amount'], o['status']))

        def mark_paid():
            selected = order_tree.selection()
            if not selected: return
            oid = order_tree.item(selected[0])['values'][0]
            requests.put(f"{API_URL}/orders/{oid}/pay")
            load_orders()

        tk.Button(order_frame, text="Refresh List", command=load_orders).pack(pady=5)
        tk.Button(order_frame, text="Mark as Paid", command=mark_paid).pack(pady=5)

        # Add Book tab
        book_frame = tk.Frame(notebook)
        notebook.add(book_frame, text="Add Book")
        
        tk.Label(book_frame, text="Title").pack()
        title_e = tk.Entry(book_frame)
        title_e.pack()
        
        tk.Label(book_frame, text="Author").pack()
        auth_e = tk.Entry(book_frame)
        auth_e.pack()

        tk.Label(book_frame, text="Buy Price").pack()
        buy_e = tk.Entry(book_frame)
        buy_e.pack()

        tk.Label(book_frame, text="Rent Price").pack()
        rent_e = tk.Entry(book_frame)
        rent_e.pack()

        def add_book():
            data = {
                "title": title_e.get(), "author": auth_e.get(),
                "buy_price": float(buy_e.get()), "rent_price": float(rent_e.get())
            }
            requests.post(f"{API_URL}/books", json=data)
            messagebox.showinfo("Success", "Book Added")
            title_e.delete(0, tk.END)

        tk.Button(book_frame, text="Add Book", command=add_book).pack(pady=20)
        
        # Logout
        tk.Button(self, text="Logout", command=self.show_login_screen).pack(pady=5)

if __name__ == "__main__":
    app = BookstoreApp()
    app.mainloop()