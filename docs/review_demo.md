# Project review and image-folder demo

## Project layout

- `app.py`, `config/`: Flask startup, configuration, storage paths.
- `routes/`: upload/scan API, saved products, analytics, rules, web page.
- `services/`: image quality, Tesseract OCR, declaration extraction and normalization,
  compliance checking, reference-based counterfeit risk, and pipeline orchestration.
- `rules/`, `models/`: individual declaration rules and report structures.
- `repositories/`, `data/`: SQLite audit storage, CSV products, reference products.
- `templates/index.html`, `static/`: interface, upload JavaScript, styles, sample labels.
- `ft_project_images/fake/`: 3 supplied demonstration images.
- `ft_project_images/original/`: 11 supplied demonstration images.
- `uploads/`: generated copies of uploaded files; original names are not retained.
- `tests/`, `scripts/`: regression tests and benchmark evaluation.

Flow: image upload -> image quality -> OCR -> declaration extraction -> separate
compliance and counterfeit evaluations -> report -> SQLite audit.
The counterfeit engine uses reference comparisons and rules; the folder demo
does not train a classifier or measure detection accuracy.

## Review-demo behavior

The review build defaults to `DEMO_FOLDER_SCORING=1`. Upload normally; there are
no Original/Fake selector buttons. Only uploaded images receive the demo policy:

| Image content | Displayed demo score |
| --- | --- |
| Exact match in `ft_project_images/fake/` | At least 26% |
| Exact match in `ft_project_images/original/` | At most 15% |
| No exact match in either folder | At most 15% |

The banner, printable scan report, JSON export, and stored audit identify the
demo result. `computed_analysis` retains the full calculated counterfeit result,
including its original score and evidence. Compliance evaluation is independent.
Manual text and built-in presets continue through normal scoring.

Browsers omit the real source folder from ordinary file uploads
([MDN File.name](https://developer.mozilla.org/en-US/docs/Web/API/File/name)).
The server therefore compares SHA-256 hashes with files inside the two local
folders. The client filename and claimed folder are not used as evidence.

- Renaming a file preserves the match. Editing, resizing, or recompressing it
  changes its bytes; place the edited file in the local fake folder if needed.
- New files and moves between the local folders take effect on the next upload.
- An identical copy of a known fake image matches even when uploaded from another
  folder. The browser cannot distinguish those copies by their source location.
- Identical bytes in both fixture folders use the fake label. Avoid duplicates
  across labels when preparing the review dataset.
- A fake folder elsewhere on your PC is not automatically indexed. Add its images
  to this project's fake folder, or configure `DEMO_IMAGE_FOLDER` to a dataset root
  containing both `fake` and `original` subfolders.
- Unmatched low demo scores do not establish authenticity. Missing/unreadable
  fixture folders produce an error instead of silently assigning low scores.

To use only the calculated engine score, set this environment variable before
starting the app in PowerShell:

```powershell
$env:DEMO_FOLDER_SCORING = '0'
python app.py
```

Set it to `'1'` and restart to restore the review demo. If Python is not on PATH,
use your IDE's configured interpreter. `.env.example` documents the settings;
the application does not automatically load `.env` files.
