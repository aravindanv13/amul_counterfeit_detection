# Deploy the review app on Render

The Flask frontend and backend run together in one Docker web service. The image
installs Tesseract and includes both `ft_project_images` folders. `render.yaml`
selects the **free** plan, Singapore region, and explicitly enables folder-demo
scoring. No paid databases or disks are created.

[Create the Render deployment](https://render.com/deploy?repo=https://github.com/aravindanv13/amul_counterfeit_detection)

Sign in to Render, authorize repository access if prompted, review the free web
service, and deploy the Blueprint. If configuring a Web Service manually, choose
Docker, branch `main`, the Free instance, and health-check path `/health`. Use the
environment variables in `render.yaml` and generate a random `SECRET_KEY`.

The container binds to Render's `PORT`. Gunicorn uses one worker and a 180-second
timeout for OCR on a small shared CPU. Logs go to standard output/error. The
repository excludes local scan history, uploads, editor settings, and secrets.

## Verify after deployment

1. Wait for the service to report Live; use the actual URL shown by Render.
2. Open `/health` and confirm `status: UP` and `ocr_engine: ACTIVE`.
3. Open `/` and upload each of the three files in `ft_project_images/fake`.
   Confirm the result is labelled DEMO and its counterfeit score is above 25%.
4. Upload an original image and confirm a score of at most 15%.
5. Check JSON export includes `scoring_mode: folder_demo` and `computed_analysis`.

These percentages are a demonstration policy, not measured detection accuracy.
Image matching uses exact file contents against the deployed fixture folders;
renames work, but edited/recompressed images need to be added to the fixtures.

## Free-plan persistence

Free services sleep after idle periods. Uploaded images and SQLite/CSV changes
are temporary and are lost on restart, spin-down, or deployment. The committed
reference images and seed CSV remain part of each built image. Export reports
before closing a review session. Open the site before presenting and test OCR
performance on the deployed instance.

See [Render free-service limits](https://render.com/docs/free) and
[Docker deployment](https://render.com/docs/docker).
