# Preview and publish the landing page

The site is plain HTML, CSS, and JavaScript with no build step.

## Preview locally

From the repository root, run:

```bash
python -m http.server 8000 --directory docs
```

Then open `http://localhost:8000/`.

## Publish with GitHub Pages

After this change is merged:

1. Open **Settings → Pages** in the repository.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select the `main` branch and the `/docs` folder.
4. Save and verify `https://icidade.github.io/miniCISO/` after the deployment completes.

GitHub Pages supports any source branch; `gh-pages` is a common convention, not a required branch. Keeping the source in `main/docs` makes content changes reviewable alongside the project documentation.

All site assets use relative paths so the page works at the `/miniCISO/` project subpath. The canonical and social-preview URLs intentionally use the production URL.
