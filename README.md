# 🌈 Famly Learning Journey Downloader

A one-file Python script that downloads **every photo, video, and document** from your child's [Famly](https://famly.co) learning journey and builds a beautiful, offline, browsable gallery you can keep forever — even after your child leaves the nursery.

Famly's learning journey is the digital record your nursery keeps of your child's time there: photos, videos, and short written observations from the staff. When your child moves on to big school, you may lose access to that account. This tool saves a complete copy on your own computer before that happens.

## ✨ What it does

1. **Fetches** every observation from your child's learning journey via Famly's API
2. **Downloads** all photos, videos, and attached documents (in parallel — fast)
3. **Saves** the observation text, author, and date alongside each entry as a JSON file
4. **Builds** a gorgeous, offline, single-file `index.html` gallery you open in any browser — organized by month with a lightbox viewer, keyboard navigation, and your child's name in the title
5. **Opens** the gallery for you automatically when it's done

## 📋 Requirements

- **macOS** with Python 3 (already installed on every Mac since 2019 — try `python3 --version` to confirm)
- A web browser (Chrome, Safari, Firefox, or Edge — any will do)
- 5 minutes

> **Windows / Linux users:** The script uses `curl` (pre-installed on macOS and most Linux distros; on Windows 10+ it's included too). If `python3` isn't found, install [Python 3](https://www.python.org/downloads/) (free) or try `python` instead.

## 🚀 Quick start

```bash
python3 famly-download.py --token "YOUR_TOKEN" --installation-id "YOUR_ID" --child-id "CHILD_ID"
```

Don't have those three values yet? Run the script with no arguments and it will print full step-by-step instructions on how to get them in ~3 minutes:

```bash
python3 famly-download.py
```

Or view the instructions right now in the [**USAGE section of the script**](famly-download.py) (the `--help` output / docstring).

### The short version

You need three things, all from your browser while logged in to Famly:

| Value | Where to find it |
|-------|------------------|
| **CHILD ID** | In the Famly URL: `app.famly.co/#/account/childProfile/THIS-PART/childProfileLearningJourney` |
| **TOKEN** | DevTools → Network → any `graphql` request → Request Headers → `x-famly-accesstoken` |
| **INSTALLATION ID** | Same request headers → `x-famly-installationid` |

The script's built-in instructions walk you through every click, including how to enable the Develop menu in Safari, what to look for, and what to copy.

## 📁 What you get

```
famly-archive/
├── index.html              ← open this in your browser 🌐
├── manifest.json           ← full structured record (all observations)
├── 2026/
│   └── 08/
│       ├── 2026-08-25_0eae1e79_img01_91d99934.jpg
│       └── 2026-08-25_0eae1e79_observation.json
│   └── 07/
│       └── ...
├── 2025/
│   └── ...
└── 2023/
    └── ...
```

Each media file is named `<date>_<observationId>_<img|vid|file>_<number>_<mediaId>.<ext>` and sits next to a `<date>_<obsId>_observation.json` sidecar containing the nursery's written observation, the staff member who wrote it, the status, and the creation date.

The `index.html` gallery is a single self-contained file (no internet needed) with:

- A warm, colorful hero showing your totals (photos, videos, years)
- A sticky timeline to jump to any month
- Observation cards grouped by month with date, text, and a responsive photo grid
- Click any photo to open a full-screen **lightbox** with arrow-key navigation
- Videos play inline; PDFs open in a new tab
- Works on phone, tablet, and desktop

## ⚠️ Important notes

### Timing
The download URLs Famly provides **expire after ~24 hours**. Run the script in one sitting. If you stop and come back the next day, you'll need to grab a fresh TOKEN (the Installation ID and Child ID stay the same).

### Your TOKEN is temporary and private
- It's like a temporary password — it only lets this script access **your child's** data.
- It expires on its own within a day.
- Don't share it with anyone. Don't commit it to git. Once the download finishes, you can throw it away — the downloaded files don't need it.

### Re-runs are safe
Running the script again won't re-download files that are already on disk (it checks file size). You can interrupt and resume anytime.

### Refreshing the gallery later (no auth needed)
Once you've run the full download once, you can rebuild the gallery at any time without your token, installation ID, or child ID — useful for picking up script updates or style changes:

```bash
python3 famly-download.py --gallery-only
# or, if your archive lives elsewhere:
python3 famly-download.py --gallery-only --output-dir /path/to/famly-archive
```

This reads the saved `manifest.json` and rebuilds `index.html` in seconds. It won't touch your downloaded files or re-contact Famly.

### Sharing as a single self-contained file
Want to send the whole gallery to a grandparent or partner as **one file** — no folder needed? Add `--embed` and every photo, PDF, and video gets packed inside the HTML as base64 data URIs:

```bash
# Full embed (photos + videos + PDFs) — ~100 MB single file
python3 famly-download.py --gallery-only --embed --child-name "Your Child"

# Lighter embed (photos + PDFs, videos show a placeholder) — ~30 MB
python3 famly-download.py --gallery-only --embed --embed-no-videos --child-name "Your Child"
```

The result is a single `index.html` that works on its own — open it in any browser, no internet or folder needed. The embedded gallery also includes a **"Download all as ZIP"** button so the recipient can extract all the original files for safekeeping.

> **Note:** The embedded HTML uses [fflate](https://github.com/101arrowz/fflate) (MIT License), a tiny zip library inlined directly in the file — no CDN or internet connection needed for the ZIP download either.

## 🔒 Privacy

- This script only talks to `app.famly.co` — it doesn't send your data anywhere else.
- Everything stays on your computer.
- No telemetry, no analytics, no phone-home.
- The script is short and readable — you can read every line before you run it.

## 🛠️ Troubleshooting

<details>
<summary><b>"Not authorized" or empty results</b></summary>

Your TOKEN may have expired (they're temporary). Redo Step 2 from the instructions to get a fresh one. The token usually lasts a few hours to a day.
</details>

<details>
<summary><b>"Child not found" or no observations</b></summary>

Double-check the CHILD ID — it must match exactly, including all dashes. Make sure you copied the full ID from the URL, not just the first part.
</details>

<details>
<summary><b>Can't find "graphql" in the Network tab</b></summary>

Make sure you refreshed the page (⌘+R or F5) **after** opening the Network tab. The requests only appear while the tab is recording.
</details>

<details>
<summary><b>Can't find the x-famly-* headers</b></summary>

You may be looking at "Response Headers" instead of "Request Headers." Scroll to the section labelled "Request Headers" (usually lower down). In some browsers it's under a "Headers" sub-tab within the request panel.
</details>

<details>
<summary><b>"python3: command not found"</b></summary>

On older Macs, try `python` instead of `python3`. Or install Python 3 from [python.org](https://www.python.org/downloads/) (free).
</details>

<details>
<summary><b>Nothing happens / script hangs</b></summary>

The first run can take 30–60 seconds for lots of photos. Wait. If it's truly stuck after a few minutes, press `Ctrl+C` and run again — already-downloaded files are skipped.
</details>

## 🤝 Sharing

Share this script freely with other parents at your nursery or elsewhere. Don't share your TOKEN or CHILD ID — those are yours alone.

## 📜 License

[GNU General Public License v3.0](LICENSE.md)

## 💛 Why

Because these memories matter, and they shouldn't vanish when an account closes.
