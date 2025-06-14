from pymongo import MongoClient
from bson.binary import UUID, Binary, UUID_SUBTYPE
from datetime import datetime
import uuid

class DatabaseManager:
    def __init__(self, connection_string="mongodb://localhost:27017/"):
        self.client = MongoClient(connection_string)
        self.db = self.client.notes_db
        self.users = self.db.users
        self.notes = self.db.notes

    def close_connection(self):
        self.client.close()

    def add_user(self, username, password):
        """Create a new user"""
        try:
            # Check if user already exists
            if self.users.find_one({"UserName": username}):
                return False, "Користувач з таким ім'ям вже існує."

            user_id = Binary(uuid.uuid4().bytes, UUID_SUBTYPE)
            user = {
                "Id": user_id,
                "UserName": username,
                "Password": password
            }
            self.users.insert_one(user)
            return True, "Користувача успішно зареєстровано!"
        except Exception as e:
            return False, f"Помилка при реєстрації користувача: {e}"

    def get_user_by_username(self, username):
        """Get user by username"""
        return self.users.find_one({"UserName": username})

    def add_note(self, title, text, user_id):
        """Create a new note"""
        try:
            if not isinstance(user_id, Binary):
                if isinstance(user_id, uuid.UUID):
                    user_id = Binary(user_id.bytes, UUID_SUBTYPE)
                elif isinstance(user_id, str):
                    user_id = Binary(uuid.UUID(user_id).bytes, UUID_SUBTYPE)

            note_id = Binary(uuid.uuid4().bytes, UUID_SUBTYPE)
            note = {
                "Id": note_id,
                "Title": title,
                "Text": text,
                "UserId": user_id,
                "CreatedAt": datetime.utcnow(),
                "UpdatedAt": datetime.utcnow(),
                "Status": "Активна"
            }
            self.notes.insert_one(note)
            return True, "Замітку успішно додано."
        except Exception as e:
            return False, f"Помилка при додаванні замітки: {e}"

    def get_notes_by_user(self, user_id):
        """Get all notes for a user"""
        if not isinstance(user_id, Binary):
            if isinstance(user_id, uuid.UUID):
                user_id = Binary(user_id.bytes, UUID_SUBTYPE)
            elif isinstance(user_id, str):
                user_id = Binary(uuid.UUID(user_id).bytes, UUID_SUBTYPE)
        return list(self.notes.find({"UserId": user_id}))

    def get_note_by_id(self, note_id):
        """Get note by ID"""
        if not isinstance(note_id, Binary):
            if isinstance(note_id, uuid.UUID):
                note_id = Binary(note_id.bytes, UUID_SUBTYPE)
            elif isinstance(note_id, str):
                note_id = Binary(uuid.UUID(note_id).bytes, UUID_SUBTYPE)
        return self.notes.find_one({"Id": note_id})

    def update_note(self, note_id, title=None, text=None, status=None):
        """Update an existing note"""
        try:
            if not isinstance(note_id, Binary):
                if isinstance(note_id, uuid.UUID):
                    note_id = Binary(note_id.bytes, UUID_SUBTYPE)
                elif isinstance(note_id, str):
                    note_id = Binary(uuid.UUID(note_id).bytes, UUID_SUBTYPE)

            update_fields = {"UpdatedAt": datetime.utcnow()}
            if title is not None:
                update_fields["Title"] = title
            if text is not None:
                update_fields["Text"] = text
            if status is not None:
                update_fields["Status"] = status

            result = self.notes.update_one(
                {"Id": note_id},
                {"$set": update_fields}
            )
            if result.matched_count > 0:
                return True, "Замітку успішно оновлено."
            return False, "Замітку не знайдено."
        except Exception as e:
            return False, f"Помилка при оновленні замітки: {e}"

    def delete_note(self, note_id):
        """Delete a note"""
        try:
            if not isinstance(note_id, Binary):
                if isinstance(note_id, uuid.UUID):
                    note_id = Binary(note_id.bytes, UUID_SUBTYPE)
                elif isinstance(note_id, str):
                    note_id = Binary(uuid.UUID(note_id).bytes, UUID_SUBTYPE)
            result = self.notes.delete_one({"Id": note_id})
            if result.deleted_count > 0:
                return True, "Замітку успішно видалено."
            return False, "Замітку не знайдено."
        except Exception as e:
            return False, f"Помилка при видаленні замітки: {e}"

    def count_notes_by_user(self, username):
        """Count notes for a user"""
        pipeline = [
            {"$match": {"UserName": username}},
            {"$lookup": {
                "from": "notes",
                "localField": "Id",
                "foreignField": "UserId",
                "as": "user_notes"
            }},
            {"$project": {
                "UserName": 1,
                "notes_count": {"$size": "$user_notes"},
                "_id": 0
            }}
        ]
        result = list(self.users.aggregate(pipeline))
        if result:
            return result[0].get("notes_count", 0)
        return 0

    def get_notes_with_keyword_and_status(self, keyword, status=None):
        """Search notes by keyword and status"""
        query = {
            "$or": [
                {"Title": {"$regex": keyword, "$options": "i"}},
                {"Text": {"$regex": keyword, "$options": "i"}}
            ]
        }
        if status:
            query["Status"] = status
        return list(self.notes.find(query))