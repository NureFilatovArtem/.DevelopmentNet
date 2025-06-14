# FILE: db_manager.py
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

    # MODIFY THIS METHOD: Add location_coords parameter for new notes
    def add_note(self, title, text, user_id, location_coords=None): # New: location_coords
        """Create a new note, optionally with geolocation"""
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
            # Add location if provided
            if location_coords and len(location_coords) == 2:
                # Ensure coordinates are [longitude, latitude] as required by GeoJSON Point
                note["location"] = {"type": "Point", "coordinates": [float(location_coords[0]), float(location_coords[1])]}

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

    # MODIFY THIS METHOD: Allow updating location
    def update_note(self, note_id, title=None, text=None, status=None, location_coords=None): # New: location_coords
        """Update an existing note, optionally including geolocation"""
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
            
            # Handle location updates:
            # If location_coords is a tuple/list, set it.
            # If location_coords is an explicit False, unset (remove) the field.
            # Otherwise (None), leave unchanged.
            if location_coords is not None: # Changed to 'is not None' for boolean False check
                if location_coords is False: # To remove location: pass False
                    # Use $unset operator to remove a field
                    self.notes.update_one({"Id": note_id}, {"$unset": {"location": ""}})
                    # Ensure it's not set below if already unset
                    if "location" in update_fields: del update_fields["location"]
                elif len(location_coords) == 2:
                    update_fields["location"] = {"type": "Point", "coordinates": [float(location_coords[0]), float(location_coords[1])]}
                else:
                     raise ValueError("Invalid location_coords: must be (lon, lat) tuple or False to unset.")


            result = self.notes.update_one(
                {"Id": note_id},
                {"$set": update_fields} # Ensure update_fields doesn't contain conflicting operations (like $set for $unset)
            )
            # If update was split (e.g. $unset for location)
            # You might need to check multiple result objects or handle $unset outside of the main $set call.
            # For simplicity, if we remove it, the $set won't apply to it.
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
    
    # ADD NEW METHOD: Geospatial search
    def find_notes_near_point(self, longitude, latitude, max_distance_meters):
        """
        Finds notes near a given point within a specified maximum distance.
        :param longitude: The longitude of the center point.
        :param latitude: The latitude of the center point.
        :param max_distance_meters: The maximum distance from the center point in meters.
        :return: A list of notes found near the point.
        """
        try:
            query = {
                "location": {
                    "$nearSphere": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [longitude, latitude]
                        },
                        "$maxDistance": max_distance_meters
                    }
                }
            }
            # Returning all found notes; GUI will filter by current user if needed.
            return list(self.notes.find(query))
        except Exception as e:
            print(f"Error during geospatial search: {e}")
            return []