# mongo_app/gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from db_manager import DatabaseManager
from bson.binary import UUID, Binary, UUID_SUBTYPE
import uuid

class NotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Notes Application")
        self.geometry("800x600")
        self.db_manager = DatabaseManager()
        self.current_user = None
        self.current_note_id = None
        self._create_login_frame()

    def _create_login_frame(self):
        self.login_frame = ttk.Frame(self, padding="20")
        self.login_frame.pack(expand=True, fill="both")
        
        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, pady=5, sticky="w")
        self.username_entry = ttk.Entry(self.login_frame, width=30)
        self.username_entry.grid(row=0, column=1, pady=5, sticky="ew")
        
        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, pady=5, sticky="w")
        self.password_entry = ttk.Entry(self.login_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, sticky="ew")
        
        login_buttons_frame = ttk.Frame(self.login_frame)
        login_buttons_frame.grid(row=2, column=1, pady=10, sticky="e")

        ttk.Button(login_buttons_frame, text="Login", command=self._login).pack(side="left", padx=5)
        ttk.Button(login_buttons_frame, text="Register", command=self._handle_registration).pack(side="left", padx=5)

    def _login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        user = self.db_manager.get_user_by_username(username)
        
        if user and user.get("Password") == password:
            self.current_user = user
            messagebox.showinfo("Login Success", f"Welcome, {username}!")
            self.login_frame.destroy()
            self._create_main_app_frame()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def _handle_registration(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Registration", "Ім'я користувача та пароль не можуть бути порожніми.")
            return

        success, message = self.db_manager.add_user(username, password)
        if success:
            messagebox.showinfo("Registration Success", message + "\nТепер ви можете увійти.")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Registration Failed", message)

    def _create_main_app_frame(self):
        self.main_app_frame = ttk.Frame(self, padding="20")
        self.main_app_frame.pack(expand=True, fill="both")
        
        ttk.Label(self.main_app_frame, text=f"Notes for {self.current_user['UserName']}:", 
                 font=("Arial", 12, "bold")).pack(pady=10)

        self.notes_tree = ttk.Treeview(self.main_app_frame, columns=("Title", "Status"), show="headings")
        self.notes_tree.heading("Title", text="Title")
        self.notes_tree.heading("Status", text="Status")
        self.notes_tree.column("Title", width=300)
        self.notes_tree.column("Status", width=100)
        self.notes_tree.pack(expand=True, fill="both")
        self.notes_tree.bind("<<TreeviewSelect>>", self._on_note_select)

        ttk.Label(self.main_app_frame, text="Title:").pack(pady=(10, 0), anchor="w")
        self.note_title_entry = ttk.Entry(self.main_app_frame, width=80)
        self.note_title_entry.pack(fill="x", pady=2)

        ttk.Label(self.main_app_frame, text="Text:").pack(pady=(10, 0), anchor="w")
        self.note_text_entry = tk.Text(self.main_app_frame, height=10, width=80)
        self.note_text_entry.pack(fill="both", pady=2)

        button_frame = ttk.Frame(self.main_app_frame)
        button_frame.pack(fill="x", pady=10)

        ttk.Button(button_frame, text="New Note", command=self._new_note).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save", command=self._save_note).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete", command=self._delete_note).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Logout", command=self._logout).pack(side="right", padx=5)

        ttk.Label(self.main_app_frame, text="Search Notes:", 
                 font=("Arial", 10, "bold")).pack(pady=(10,0), anchor="w")
        search_frame = ttk.Frame(self.main_app_frame)
        search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Keyword:").pack(side="left", padx=5)
        self.search_keyword_entry = ttk.Entry(search_frame, width=30)
        self.search_keyword_entry.pack(side="left", padx=5)
        ttk.Label(search_frame, text="Status (optional):").pack(side="left", padx=5)
        self.search_status_entry = ttk.Entry(search_frame, width=20)
        self.search_status_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="Search", command=self._search_notes).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Reset Search", command=self._refresh_notes_list).pack(side="left", padx=5)

        ttk.Label(self.main_app_frame, text="Notes Count for User:").pack(pady=(10,0), anchor="w")
        self.notes_count_label = ttk.Label(self.main_app_frame, text="")
        self.notes_count_label.pack(anchor="w")

        self._refresh_notes_list()
        self._update_notes_count()

    def _refresh_notes_list(self):
        for item in self.notes_tree.get_children():
            self.notes_tree.delete(item)
        
        if self.current_user:
            notes = self.db_manager.get_notes_by_user(self.current_user["Id"])
            for note in notes:
                uuid_str = uuid.UUID(bytes=note["Id"]).hex
                self.notes_tree.insert("", "end", iid=uuid_str, 
                                     values=(note["Title"], note.get("Status", "Активна")))

    def _update_notes_count(self):
        if self.current_user:
            count = self.db_manager.count_notes_by_user(self.current_user["UserName"])
            self.notes_count_label.config(
                text=f"Користувач '{self.current_user['UserName']}' має {count} заміток.")

    def _on_note_select(self, event):
        selected_item = self.notes_tree.focus()
        if selected_item:
            note_uuid = uuid.UUID(hex=selected_item)
            note_id = Binary(note_uuid.bytes, UUID_SUBTYPE)
            self.current_note_id = note_id
            note = self.db_manager.get_note_by_id(note_id)
            if note:
                self.note_title_entry.delete(0, tk.END)
                self.note_title_entry.insert(0, note["Title"])
                self.note_text_entry.delete("1.0", tk.END)
                self.note_text_entry.insert("1.0", note["Text"])
        else:
            self._new_note()

    def _new_note(self):
        self.current_note_id = None
        self.note_title_entry.delete(0, tk.END)
        self.note_text_entry.delete("1.0", tk.END)
        messagebox.showinfo("New Note", "Поля очищено. Введіть дані для нової замітки.")

    def _save_note(self):
        title = self.note_title_entry.get()
        text = self.note_text_entry.get("1.0", tk.END).strip()

        if not title or not text:
            messagebox.showwarning("Warning", "Title and Text cannot be empty.")
            return

        if self.current_note_id:
            success, msg = self.db_manager.update_note(self.current_note_id, title=title, text=text)
            if success:
                messagebox.showinfo("Success", msg)
                self._new_note()  # <--- Сбросить поля и current_note_id после обновления
            else:
                messagebox.showerror("Error", msg)
        else:
            if self.current_user:
                success, msg = self.db_manager.add_note(title, text, self.current_user["Id"])
                if success:
                    messagebox.showinfo("Success", msg)
                    self._new_note()  # <--- Сбросить поля и current_note_id после добавления
                else:
                    messagebox.showerror("Error", msg)
            else:
                messagebox.showerror("Error", "No user logged in.")

        self._refresh_notes_list()
        self._update_notes_count()

    def _delete_note(self):
        if self.current_note_id:
            if messagebox.askyesno("Confirm Delete", "Ви впевнені, що хочете видалити цю замітку?"):
                success, msg = self.db_manager.delete_note(self.current_note_id)
                if success:
                    messagebox.showinfo("Success", msg)
                    self._new_note()
                else:
                    messagebox.showerror("Error", msg)
                self._refresh_notes_list()
                self._update_notes_count()
        else:
            messagebox.showwarning("Warning", "Виберіть замітку для видалення.")

    def _search_notes(self):
        keyword = self.search_keyword_entry.get()
        status = self.search_status_entry.get()
        if not keyword and not status:
            messagebox.showwarning("Search", "Введіть ключове слово або статус для пошуку.")
            return
        
        for item in self.notes_tree.get_children():
            self.notes_tree.delete(item)

        found_notes = self.db_manager.get_notes_with_keyword_and_status(keyword, status if status else None)
        
        if found_notes:
            for note in found_notes:
                uuid_str = uuid.UUID(bytes=note["Id"]).hex
                self.notes_tree.insert("", "end", iid=uuid_str, 
                                     values=(note["Title"], note.get("Status", "Активна")))
            messagebox.showinfo("Search Result", f"Знайдено {len(found_notes)} заміток.")
        else:
            messagebox.showinfo("Search Result", "Заміток за вашим запитом не знайдено.")
            self._new_note()

    def _logout(self):
        self.current_user = None
        self.current_note_id = None
        self.main_app_frame.destroy()
        self._create_login_frame()
        messagebox.showinfo("Logout", "Ви успішно вийшли.")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Ви хочете вийти з застосунку?"):
            self.db_manager.close_connection()
            self.destroy()