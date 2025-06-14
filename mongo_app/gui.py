
import tkinter as tk
from tkinter import ttk, messagebox
from db_manager import DatabaseManager
from bson.binary import UUID, Binary, UUID_SUBTYPE
import uuid

class NotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Notes Application")
        self.geometry("1000x800") # INCREASE WINDOW SIZE
        self.db_manager = DatabaseManager()
        self.current_user = None
        self.current_note_id = None # Store Binary UUID here
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
        # RENAMED from _register to _handle_registration to avoid TypeError
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

    # RENAMED from _register to _handle_registration to avoid TypeError
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
        self.main_app_frame = ttk.Frame(self, padding="20"); self.main_app_frame.pack(expand=True, fill="both")
        
        notes_section = ttk.Frame(self.main_app_frame); notes_section.pack(expand=True, fill="both", pady=5)
        ttk.Label(notes_section, text=f"Notes for {self.current_user['UserName']}:", 
                 font=("Arial", 12, "bold")).pack(pady=10)

        # ADD Latitude and Longitude columns to Treeview
        self.notes_tree = ttk.Treeview(notes_section, columns=("Title", "Status", "Lon", "Lat"), show="headings")
        self.notes_tree.heading("Title", text="Title")
        self.notes_tree.heading("Status", text="Status")
        self.notes_tree.heading("Lon", text="Lon") # New column
        self.notes_tree.heading("Lat", text="Lat") # New column
        self.notes_tree.column("Title", width=250)
        self.notes_tree.column("Status", width=80)
        self.notes_tree.column("Lon", width=70) # Set width for new column
        self.notes_tree.column("Lat", width=70) # Set width for new column
        self.notes_tree.pack(expand=True, fill="both")
        self.notes_tree.bind("<<TreeviewSelect>>", self._on_note_select)

        # Section for editing/creating notes
        edit_note_section = ttk.LabelFrame(self.main_app_frame, text="Note Details", padding="10")
        edit_note_section.pack(fill="x", pady=10)

        ttk.Label(edit_note_section, text="Title:").grid(row=0, column=0, pady=2, sticky="w")
        self.note_title_entry = ttk.Entry(edit_note_section, width=50)
        self.note_title_entry.grid(row=0, column=1, pady=2, sticky="ew")

        ttk.Label(edit_note_section, text="Text:").grid(row=1, column=0, pady=2, sticky="w")
        self.note_text_entry = tk.Text(edit_note_section, height=5, width=50)
        self.note_text_entry.grid(row=1, column=1, pady=2, sticky="ew")
        
        # ADD NEW FIELDS FOR LOCATION (Lon, Lat)
        location_frame = ttk.Frame(edit_note_section)
        location_frame.grid(row=2, column=1, pady=2, sticky="w")
        ttk.Label(edit_note_section, text="Location:").grid(row=2, column=0, pady=2, sticky="w")
        
        ttk.Label(location_frame, text="Lon:").pack(side="left", padx=2)
        self.note_lon_entry = ttk.Entry(location_frame, width=15)
        self.note_lon_entry.pack(side="left", padx=2)

        ttk.Label(location_frame, text="Lat:").pack(side="left", padx=2)
        self.note_lat_entry = ttk.Entry(location_frame, width=15)
        self.note_lat_entry.pack(side="left", padx=2)

        edit_note_section.grid_columnconfigure(1, weight=1) # Allow column 1 to expand

        button_frame = ttk.Frame(edit_note_section); button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="New Note", command=self._new_note).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save", command=self._save_note).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete", command=self._delete_note).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Logout", command=self._logout).pack(side="right", padx=5)

        # Existing Search section
        search_section = ttk.LabelFrame(self.main_app_frame, text="Search & Aggregation", padding="10")
        search_section.pack(fill="x", pady=10)

        search_basic_frame = ttk.Frame(search_section)
        search_basic_frame.pack(fill="x", pady=5)
        ttk.Label(search_basic_frame, text="Keyword:").pack(side="left", padx=5)
        self.search_keyword_entry = ttk.Entry(search_basic_frame, width=20)
        self.search_keyword_entry.pack(side="left", padx=5)
        ttk.Label(search_basic_frame, text="Status (optional):").pack(side="left", padx=5)
        self.search_status_entry = ttk.Entry(search_basic_frame, width=15)
        self.search_status_entry.pack(side="left", padx=5)
        ttk.Button(search_basic_frame, text="Search", command=self._search_notes).pack(side="left", padx=5)
        ttk.Button(search_basic_frame, text="Reset Search", command=self._refresh_notes_list).pack(side="left", padx=5)

        self.notes_count_label = ttk.Label(search_section, text=""); self.notes_count_label.pack(anchor="w", pady=5)
        
        # ADD NEW GEOSPATIAL SEARCH SECTION
        geo_search_frame = ttk.LabelFrame(search_section, text="Geospatial Search", padding="10")
        geo_search_frame.pack(fill="x", pady=5)

        ttk.Label(geo_search_frame, text="Center Lon:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.geo_lon_entry = ttk.Entry(geo_search_frame, width=15); self.geo_lon_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(geo_search_frame, text="Center Lat:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.geo_lat_entry = ttk.Entry(geo_search_frame, width=15); self.geo_lat_entry.grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        ttk.Label(geo_search_frame, text="Max Distance (km):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.geo_dist_entry = ttk.Entry(geo_search_frame, width=15); self.geo_dist_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ttk.Button(geo_search_frame, text="Find Near", command=self._find_notes_near).grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky="ew")
        geo_search_frame.grid_columnconfigure(1, weight=1); geo_search_frame.grid_columnconfigure(3, weight=1) # Allow expansion

        self._refresh_notes_list(); self._update_notes_count()


    def _refresh_notes_list(self):
        for item in self.notes_tree.get_children(): self.notes_tree.delete(item)
        
        if self.current_user:
            notes = self.db_manager.get_notes_by_user(self.current_user["Id"])
            for note in notes:
                uuid_str = uuid.UUID(bytes=bytes(note["Id"])).hex if isinstance(note["Id"], Binary) else str(note["Id"])
                loc = note.get("location")
                lat_val = round(loc["coordinates"][1], 4) if loc else ""
                lon_val = round(loc["coordinates"][0], 4) if loc else ""
                self.notes_tree.insert("", "end", iid=uuid_str, 
                                     values=(note["Title"], note.get("Status", "Активна"), lon_val, lat_val)) # Display Lon, Lat
        
        # After refreshing, clear general search fields
        self.search_keyword_entry.delete(0, tk.END)
        self.search_status_entry.delete(0, tk.END)
        self.geo_lon_entry.delete(0, tk.END) # Clear geo fields
        self.geo_lat_entry.delete(0, tk.END)
        self.geo_dist_entry.delete(0, tk.END)


    def _update_notes_count(self):
        if self.current_user:
            count = self.db_manager.count_notes_by_user(self.current_user["UserName"])
            self.notes_count_label.config(
                text=f"Користувач '{self.current_user['UserName']}' має {count} заміток.")

    def _on_note_select(self, event):
        selected_item = self.notes_tree.focus()
        if selected_item:
            # The iid is now a hex string. Convert back to UUID, then to Binary.
            note_uuid = uuid.UUID(selected_item)
            note_id_binary = Binary(note_uuid.bytes, UUID_SUBTYPE)
            self.current_note_id = note_id_binary # Store as Binary

            note = self.db_manager.get_note_by_id(note_id_binary)
            if note:
                self.note_title_entry.delete(0, tk.END)
                self.note_title_entry.insert(0, note["Title"])
                self.note_text_entry.delete("1.0", tk.END)
                self.note_text_entry.insert("1.0", note["Text"])
                
                # Populate location fields
                location_data = note.get("location")
                self.note_lon_entry.delete(0, tk.END); self.note_lat_entry.delete(0, tk.END)
                if location_data and "coordinates" in location_data:
                    self.note_lon_entry.insert(0, str(location_data["coordinates"][0]))
                    self.note_lat_entry.insert(0, str(location_data["coordinates"][1]))
        else:
            self._new_note()

    def _new_note(self):
        self.current_note_id = None
        self.note_title_entry.delete(0, tk.END); self.note_text_entry.delete("1.0", tk.END)
        self.note_lon_entry.delete(0, tk.END); self.note_lat_entry.delete(0, tk.END) # Clear location fields
        messagebox.showinfo("New Note", "Поля очищено. Введіть дані для нової замітки.")

    def _save_note(self):
        title = self.note_title_entry.get()
        text = self.note_text_entry.get("1.0", tk.END).strip()
        lon_str = self.note_lon_entry.get().strip()
        lat_str = self.note_lat_entry.get().strip()

        location_coords = None
        if lon_str and lat_str:
            try:
                lon = float(lon_str)
                lat = float(lat_str)
                location_coords = (lon, lat)
            except ValueError:
                messagebox.showwarning("Location Error", "Координати Longitude та Latitude мають бути числами.")
                return
        elif lon_str or lat_str: # If one is filled and other isn't
            messagebox.showwarning("Location Error", "Введіть обидві координати (Longitude та Latitude) або залиште обидві порожніми.")
            return

        if not title or not text:
            messagebox.showwarning("Warning", "Title and Text cannot be empty.")
            return

        if self.current_note_id: # Update existing note
            success, msg = self.db_manager.update_note(self.current_note_id, title=title, text=text, location_coords=location_coords)
            if success:
                messagebox.showinfo("Success", msg)
                self._new_note()  # Reset fields and current_note_id after update
            else:
                messagebox.showerror("Error", msg)
        else: # Add new note
            if self.current_user:
                success, msg = self.db_manager.add_note(title, text, self.current_user["Id"], location_coords=location_coords) # Pass coordinates
                if success:
                    messagebox.showinfo("Success", msg)
                    self._new_note()  # Reset fields and current_note_id after add
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
        
        for item in self.notes_tree.get_children(): self.notes_tree.delete(item)

        found_notes = self.db_manager.get_notes_with_keyword_and_status(keyword, status if status else None)
        
        if found_notes:
            for note in found_notes:
                uuid_str = uuid.UUID(bytes=bytes(note["Id"])).hex if isinstance(note["Id"], Binary) else str(note["Id"])
                loc = note.get("location")
                lat_val = round(loc["coordinates"][1], 4) if loc else ""
                lon_val = round(loc["coordinates"][0], 4) if loc else ""
                self.notes_tree.insert("", "end", iid=uuid_str, 
                                     values=(note["Title"], note.get("Status", "Активна"), lon_val, lat_val))
            messagebox.showinfo("Search Result", f"Знайдено {len(found_notes)} заміток.")
        else:
            messagebox.showinfo("Search Result", "Заміток за вашим запитом не знайдено.")
            self._new_note()

    # ADD NEW FUNCTION: Geospatial search
    def _find_notes_near(self):
        try:
            center_lon = float(self.geo_lon_entry.get())
            center_lat = float(self.geo_lat_entry.get())
            max_distance_km = float(self.geo_dist_entry.get()) # User inputs in kilometers
            max_distance_meters = max_distance_km * 1000 # Convert to meters for MongoDB

            # Clear Treeview before displaying geospatial search results
            for item in self.notes_tree.get_children(): self.notes_tree.delete(item)

            found_notes = self.db_manager.find_notes_near_point(center_lon, center_lat, max_distance_meters)
            
            # Filter to show only notes of the current user (if current_user is set)
            current_user_id_binary = self.current_user["Id"] if self.current_user and isinstance(self.current_user["Id"], Binary) else None
            
            # Convert _data back to uuid.UUID for comparison as 'current_user["Id"]' is Binary.
            # Comparison needs to be correct (Binary == Binary or convert both to hex string)
            # Python comparison `Binary == Binary` works if their raw bytes are identical.
            
            filtered_notes = [
                note for note in found_notes if self.current_user and note["UserId"] == current_user_id_binary
            ]
            
            if filtered_notes:
                for note in filtered_notes:
                    uuid_str = uuid.UUID(bytes=bytes(note["Id"])).hex if isinstance(note["Id"], Binary) else str(note["Id"])
                    loc = note.get("location")
                    lat_val = round(loc["coordinates"][1], 4) if loc else ""
                    lon_val = round(loc["coordinates"][0], 4) if loc else ""
                    self.notes_tree.insert("", "end", iid=uuid_str, 
                                         values=(note["Title"], note.get("Status", "Активна"), lon_val, lat_val))
                messagebox.showinfo("Geospatial Search Result", f"Знайдено {len(filtered_notes)} заміток поруч для поточного користувача.")
            else:
                messagebox.showinfo("Geospatial Search Result", "Заміток поруч не знайдено для поточного користувача.")
            
            self._new_note() # Clear note detail fields
            # _update_notes_count is not called as this is a specific search result, not all user's notes.

        except ValueError:
            messagebox.showerror("Input Error", "Будь ласка, введіть дійсні числа для координат та дистанції.")
        except Exception as e:
            messagebox.showerror("Search Error", f"Виникла помилка під час геопошуку: {e}")

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