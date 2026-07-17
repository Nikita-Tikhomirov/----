# Kwork RAR/7Z Attachment Design

## Goal

Read relevant files from Kwork `.rar` and `.7z` attachments with the same evidence and safety limits already used for ZIP archives, so the lead judge and reply composer can use their contents.

## Context

`attachments.py` downloads `.rar` and `.7z` files but originally marked them as manual-only. The workstation has `C:\Program Files\WinRAR\UnRAR.exe` and a usable `7z.exe` bundled with NVIDIA App. ZIP behavior must remain unchanged.

## Options Considered

1. Add Python libraries for RAR and 7Z. This would add package weight and `rarfile` still depends on an external extractor for common RAR variants.
2. Drive `WinRAR.exe` directly. It is a GUI executable and can block without a visible console result, so it is not suitable for unattended scanning.
3. Use existing console tools: `UnRAR.exe`/`Rar.exe` for RAR and `7z.exe` for 7Z. No dependency is added. This is the selected approach.

## Behavior

- ZIP continues through the existing in-memory `zipfile` implementation.
- For `.rar` and `.7z`, the app writes the already-downloaded archive to a temporary file, asks the matching console tool for a list of entries, and never extracts the entire archive to disk.
- Entry names are filtered to files only. The existing DeepSeek selector or name/type fallback chooses at most eight relevant entries.
- Archive listings are bounded to 200 entry names and 256 KB of console output before selection, so a deliberately huge archive cannot grow the in-memory report without limit.
- Each selected entry is streamed from the console tool into memory with the existing `max_bytes` cap. If a file exceeds the cap, the child process is stopped and that entry is reported as skipped.
- Selected entry content reuses `inspect_attachment`, so PDF, DOCX, image OCR/OpenRouter vision, text files, and nested archives retain their existing behavior.
- `UnRAR`/`RAR` and `7z` are discovered through explicit environment paths, `PATH`, conventional Program Files locations, and the local NVIDIA App 7-Zip path. If the needed executable is absent, the report says which archive type cannot be opened; it does not crash scanning or send anything.
- A corrupt, password-protected, unsupported, or unreadable archive reports its reason in the attachment summary. A password-protected archive whose selected files cannot be read is marked `архив не открыт`. No Kwork response is sent during attachment processing.

## Scope

Modify `src/app/attachments.py`, `tests/test_attachments.py`, and `README.md`. Do not add a Python dependency, modify Kwork send behavior, or persist extracted archive files beyond the existing downloaded attachment copy.

## Verification

- Tests emulate both console backends, verify RAR/7Z selection, nested parsing, and the `архив открыт` report status.
- A selected entry above `max_bytes` is stopped and reported as skipped.
- Missing archive tooling returns a clear non-fatal summary.
- Password errors, CP866 7-Zip filenames, output limits, and temporary-file cleanup have unit coverage.
- Existing ZIP archive tests pass unchanged.
- Local RAR and 7Z smoke archives are listed and read without opening a Kwork page or sending a response.
