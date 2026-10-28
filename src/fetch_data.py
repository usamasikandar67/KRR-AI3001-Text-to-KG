import requests
import pathlib

HEADERS = {"User-Agent": "KRR-coursework/1.0 (23p0032@nu.edu.pk)"}

PEOPLE = [
    "Peter Higgs",
    "Sheldon Glashow",
    "Abdus Salam",
    "Hans Bethe",
    "Kip Thorne"
]

def fetch(title):
    print(f"Fetching {title}...")
    r = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "prop": "extracts",
            "explaintext": 1,
            "redirects": 1,
            "titles": title,
            "format": "json"
        },
        headers=HEADERS,
        timeout=30
    )
    r.raise_for_status()
    page = next(iter(r.json()["query"]["pages"].values()))
    return page["extract"]

def main():
    raw_dir = pathlib.Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    for person in PEOPLE:
        filename = person.replace(" ", "_") + ".txt"
        filepath = raw_dir / filename
        text = fetch(person)
        filepath.write_text(text, encoding="utf-8")
        print(f"Saved {filepath} ({len(text)} characters)")

if __name__ == "__main__":
    main()

