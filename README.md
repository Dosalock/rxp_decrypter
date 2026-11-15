# rxp_decrypter
Encrypted RXPGuides addon data — auto-updated guide packs for World of Warcraft
# RXP Guides Data

Encrypted guide files for the **RXPGuides** WoW addon.

This repository hosts the latest encrypted guide data used by the standalone
guide tools built with BuildTool. The end-user exes automatically download
the file from this repo on startup, so updating guides here updates them
for everyone — no reinstall needed.

## How it works

- `guide.txt` is an RC4+zlib encrypted blob keyed to a BattleTag.
- The standalone tool downloads this file, decrypts it with the user's
  BattleTag, and copies the resulting guide text to their clipboard.
- To update guides for all users, simply replace `guide.txt` in this repo.

## File format


- **count** — number of guides in the pack
- **check_value** — integrity check (last 4 bytes of decrypted data)
- **base64_payload** — base64(RC4(zlib(guide_text)))
- **trailing** — preserved metadata (e.g. `|40000`)

## Updating guides

1. Re-encrypt your new guide text with the original BattleTag key.
2. All users get the update next time they open their tool.

---
DISCLAIMER: THE TOOL IS NOT DISTRIBUTED HERE


*Made by slcker*
