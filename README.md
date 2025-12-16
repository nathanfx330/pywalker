# PyWalker v1.5

**PyWalker** is a hackable Python-based forum scraper that archives threads into clean, paginated HTML files with embedded archive links. Version 1.5 includes important hotfixes for stability and robustness.

The basic workflow is:

1. Identify the forum main page.
2. Determine which links lead to additional pages.
3. Advance page by page (Page N) and collect posts.

---

## Features

- Robust HTTP requests with automatic retries and SSL handling.
- Extracts posts including authors, content, and page numbers.
- Injects Wayback Machine archive links next to external URLs.
- Supports batch scraping and automatic splitting of large threads.
- Saves progress to allow resuming interrupted jobs.
- Generates styled HTML files for easy offline reading.

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/pywalker.git
cd pywalker
```

2. Install dependencies:

```bash
pip install requests beautifulsoup4 urllib3
```

---

## Usage

Run the script:

```bash
python pywalker.py
```

Menu options:

1. **Single Pass** – Scrapes threads once.
2. **Loop Mode** – Continuously checks for new posts.

You can also resume the last used profile if available.

### Creating a New Profile

- **Profile Name** – Name for this scraping configuration.
- **Root URL** – Forum index page to start scraping from.
- **Link Pattern** – Substring in thread URLs to filter threads.
- **Batch Size** – Number of pages to scrape before pausing.
- **Split Size** – Maximum number of pages per output HTML file.

---

## Output

- HTML files are saved in `Archive_<ProfileName>/` with pagination.
- Each post includes:
  - Author
  - Page number
  - Post content
- External links include **(Archived)** links to [Wayback Machine](https://web.archive.org/).

---

## Configuration File

`pywalker_recipes.json` stores saved profiles:

```json
{
    "ProfileName": {
        "root_url": "https://example.com/forum",
        "pattern": "thread",
        "batch_size": 10,
        "split_limit": 50
    },
    "_LATEST_": "ProfileName"
}
```

---

## Hotfix v1.5

- Fixed `NoneType object is not callable` crash by using `soup.new_tag()` instead of `element.new_tag()`.

---

## Notes

- Compatible with Python 3.7+.
- Avoid scraping forums aggressively to prevent IP bans; respect forum rules.
- HTML output is styled for readability with embedded CSS.

---

## License

MIT License
