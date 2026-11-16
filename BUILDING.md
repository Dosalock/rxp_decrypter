# Building from Source

This repo contains the full source for both executables. No obfuscation, no packed payloads — everything you see is what runs.

## Files

| File | Purpose |
|------|---------|
| user_exe.py | The end-user tool (dark UI, BattleTag input, clipboard copy). This is what gets shipped to players. |
| uild_tool_gui.py | The builder that takes an encrypted guide .txt, embeds it into a fresh user_exe.py, and runs PyInstaller on the result. |
| guide.txt / guide_de.txt | Latest encrypted guide data (EN/DE). Fetched at runtime by the tool via GitHub raw URLs. |

## Requirements

- Windows 10/11 x64
- Python 3.10+ (any recent version works)
- PyInstaller: pip install pyinstaller
- tkinterdnd2 (only needed for BuildTool drag-and-drop): pip install tkinterdnd2

## Rebuild the end-user exe

`at
pyinstaller --onefile --windowed ^
  --name "RXPDecryption.Tool" ^
  --icon icon.ico ^
  --add-data "icon.ico;." ^
  user_exe.py
`

Output: dist\RXPDecryption.Tool.exe (~14 MB, self-contained — end users need nothing but stock Windows).

## Rebuild the BuildTool exe

`at
pyinstaller --onefile --windowed ^
  --name "BuildTool" ^
  --icon icon.ico ^
  --hidden-import tkinterdnd2 ^
  build_tool_gui.py
`

Output: dist\BuildTool.exe (~13 MB).

## Network calls (full list)

The end-user exe makes exactly **two** outbound HTTP requests, both to GitHub:

1. GET https://api.github.com/repos/Inariaa/rxp_decrypter/commits/main
   - Fetches the latest commit SHA on the main branch.
2. GET https://raw.githubusercontent.com/Inariaa/rxp_decrypter/<SHA>/guide.txt (or guide_de.txt)
   - Downloads the encrypted guide file at that exact commit.

No other network calls exist in the codebase. Grep for urllib or http to verify — every request goes through urllib.request and only hits github.com / aw.githubusercontent.com.

## Where data is stored locally

- Guide cache: .rxp_cache_en.dat / .rxp_cache_de.dat next to the exe (hidden files).
- BattleTag history: %USERPROFILE%\Documents\.rxp_guide_tags.txt (last 10 tags, double-click in History menu to reuse).

Delete either file at any time — the tool recreates them on demand.

## Verifying a release binary

Each GitHub release includes the source zip/tarball. To confirm a shipped .exe matches this repo:

1. Download the release exe and note its SHA-256.
2. Rebuild locally with the commands above using the same icon.ico.
3. Compare behavior — the only differences will be PyInstaller's internal layout, not logic.

The source is the contract. If a future release behaves differently from what's in this repo, that's a bug or a supply-chain issue worth reporting.
