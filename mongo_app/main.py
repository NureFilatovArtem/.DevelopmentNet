from gui import NotesApp

if __name__ == "__main__":
    app = NotesApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()