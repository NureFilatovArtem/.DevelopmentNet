// create_collections.js
// Підключення до MongoDB
const db = connect('mongodb://localhost:27017/notes_db');

// Створення колекції Users
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
 Id: { // Додано для забезпечення унікального Id типу UUID
    bsonType: "binData",
    description: "must be a UUID and is unique"
 }
 }
 }
 }
});

// Створення індексів для колекції Users
db.users.createIndex({ "Id": 1 }, { unique: true });
db.users.createIndex({ "UserName": 1 }, { unique: true });

// Створення колекції Notes
db.createCollection("notes", {
 validator: {
 $jsonSchema: {
 bsonType: "object",
 required: ["Title", "Text", "UserId"],
 properties: {
 Title: {
 bsonType: "string",
 description: "must be a string and is required"
 },
 Text: {
 bsonType: "string",
 description: "must be a string and is required"
 },
 UserId: {
 bsonType: "binData", // ЦЕ ВАЖЛИВО: Очікується UUID
 description: "must be a UUID and is required"
 },
 CreatedAt: {
 bsonType: "date",
 description: "date when note was created"
 },
 UpdatedAt: {
 bsonType: "date",
 description: "date when note was last updated"
 },
 Status: { // Додано Status, оскільки він використовується пізніше
     bsonType: "string",
     description: "status of the note (e.g., 'Виконана')"
 }
 }
 }
 }
});

// Створення індексів для колекції Notes
db.notes.createIndex({ "Id": 1 }, { unique: true });
db.notes.createIndex({ "UserId": 1 });

print("Колекції 'users' та 'notes' успішно створені з індексами.");