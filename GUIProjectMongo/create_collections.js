const db = connect('mongodb://localhost:27017/notes_db');

// Створення колекції Users (БЕЗ ЗМІН в User Schema/Validator)
db.createCollection("users", {
 validator: {
 $jsonSchema: {
 bsonType: "object",
 required: ["UserName", "Password"],
 properties: {
 UserName: {
 bsonType: "string",
 description: "must be a string and is required"
 },
 Password: {
 bsonType: "string",
 description: "must be a string and is required"
 },
 Id: { // Забезпечуємо унікальний Id типу UUID
    bsonType: "binData", // Id буде зберігатися як BSON Binary (subtype 0x04)
    description: "must be a UUID (Binary subtype 0x04) and is unique"
 }
 }
 }
 }
});

// Створення індексів для колекції Users (БЕЗ ЗМІН)
db.users.createIndex({ "Id": 1 }, { unique: true });
db.users.createIndex({ "UserName": 1 }, { unique: true });

// Створення колекції Notes (ДОДАНО LOCATION ТА ВІДПОВІДНІ ПОЛЯ)
db.createCollection("notes", {
 validator: {
 $jsonSchema: {
 bsonType: "object",
 required: ["Id", "Title", "Text", "UserId", "CreatedAt", "UpdatedAt"], // Додав Id, CreatedAt, UpdatedAt як required для повної консистентності
 properties: {
 Id: {
 bsonType: "binData", // Id буде зберігатися як BSON Binary (subtype 0x04)
 description: "must be a UUID (Binary subtype 0x04) and is unique"
 },
 Title: {
 bsonType: "string",
 description: "must be a string and is required"
 },
 Text: {
 bsonType: "string",
 description: "must be a string and is required"
 },
 UserId: {
 bsonType: "binData", // ЦЕ ВАЖЛИВО: Очікується UUID (Binary subtype 0x04)
 description: "must be a UUID (Binary subtype 0x04) and is required"
 },
 CreatedAt: {
 bsonType: "date",
 description: "date when note was created"
 },
 UpdatedAt: {
 bsonType: "date",
 description: "date when note was last updated"
 },
 Status: {
     bsonType: "string",
     description: "status of the note (e.g., 'Активна', 'Виконана')"
 },
 location: { // <<< НОВЕ ПОЛЕ ДЛЯ ГЕОДАНИХ >>>
     bsonType: "object",
     required: ["type", "coordinates"],
     properties: {
         type: {
             bsonType: "string",
             enum: ["Point"],
             description: "must be 'Point' for GeoJSON"
         },
         coordinates: {
             bsonType: "array",
             items: [
                 { bsonType: "number" }, // Longitude
                 { bsonType: "number" }  // Latitude
             ],
             description: "must be an array of [longitude, latitude] for a Point"
         }
     },
     description: "GeoJSON Point location for the note (optional)"
 }
 }
 }
 }
});

// Створення індексів для колекції Notes (ДОДАНО ГЕОСПАТІАЛЬНИЙ ІНДЕКС)
db.notes.createIndex({ "Id": 1 }, { unique: true });
db.notes.createIndex({ "UserId": 1 });
db.notes.createIndex({ "Status": 1 }); // Додав індекс для Status, він корисний
// <<< НОВИЙ ГЕОСПАТІАЛЬНИЙ ІНДЕКС >>>
db.notes.createIndex({ "location": "2dsphere" }); 


print("Колекції 'users' та 'notes' успішно створені з індексами.");