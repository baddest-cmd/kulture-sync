import csv
import os

def generate_mock_catalog():
    catalog_data = [
        {"track_id": "T001", "title": "Sgudi Snyc", "artist": "De Mthuda", "genre": "Amapiano", "is_local": "True", "popularity": "0.85"},
        {"track_id": "T002", "title": "Imali", "artist": "Phuzekhemisi", "genre": "Maskandi", "is_local": "True", "popularity": "0.40"},
        {"track_id": "T003", "title": "Bula Boot", "artist": "Vetro", "genre": "Lekompo", "is_local": "True", "popularity": "0.30"},
        {"track_id": "T004", "title": "Gqom Wave", "artist": "DJ Lag", "genre": "Gqom", "is_local": "True", "popularity": "0.75"},
        {"track_id": "T005", "title": "Tshwara", "artist": "Muzi", "genre": "Electronic", "is_local": "True", "popularity": "0.55"},
        {"track_id": "T006", "title": "Future Free", "artist": "Frank Ocean", "genre": "R&B", "is_local": "False", "popularity": "0.90"},
        {"track_id": "T007", "title": "As It Was", "artist": "Harry Styles", "genre": "Pop", "is_local": "False", "popularity": "0.95"},
        {"track_id": "T008", "title": "Yano Grooves", "artist": "Kabza De Small", "genre": "Amapiano", "is_local": "True", "popularity": "0.88"},
        {"track_id": "T009", "title": "Motswako Heights", "artist": "Khuli Chana", "genre": "Motswako", "is_local": "True", "popularity": "0.65"},
        {"track_id": "T010", "title": "Bacardi Dance", "artist": "Mujava", "genre": "Bacardi", "is_local": "True", "popularity": "0.50"},
    ]
    os.makedirs("data", exist_ok=True)
    with open("data/mock_migrated_library.csv", mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["track_id", "title", "artist", "genre", "is_local", "popularity"])
        writer.writeheader()
        writer.writerows(catalog_data)
    print("Mock catalog generated at data/mock_migrated_library.csv")

if __name__ == "__main__":
    generate_mock_catalog()
