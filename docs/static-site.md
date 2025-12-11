# Static site

The static site is a very small HTML and JavaScript frontend that talks to the backend HTTP JSON facade and runs from a public Google Cloud Storage bucket. It is intentionally simple and easy to extend.

Use it as a basic UI for the MCP backend, or as a starting point for a richer app.

______________________________________________________________________

## Layout

All frontend files live in `static-site/`

```text
static-site/
  index.html       main page, query form and results
  assets/
    app.js         JavaScript that calls the backend API
    style.css      optional styling
```

You can keep everything in `index.html` at first, then move script and styles into `assets/` when the page grows.

______________________________________________________________________

## Responsibilities

The static site has three simple jobs

- display a form so the user can enter a query
- call the backend JSON endpoint with that query
- render the returned list of results

It does not talk to gRPC directly, that is handled by the backend, so the browser only uses HTTP and JSON.

______________________________________________________________________

## Backend API usage

The JavaScript side talks to the backend JSON facade, typically `POST /mcp/query`, using `fetch`.

Example pattern for `assets/app.js`

```js
const API_BASE = "http://localhost:8000"; // or Cloud Run URL in prod

async function runQuery(text) {
  const response = await fetch(`${API_BASE}/mcp/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: text })
  });

  if (!response.ok) {
    const msg = await response.text();
    throw new Error(`API error ${response.status}: ${msg}`);
  }

  return await response.json();
}
```

`API_BASE` should be

- `http://localhost:8000` for local development
- the Cloud Run service URL for deployed environments

You can later move this into a small `config.js` or derive it from an environment specific placeholder.

______________________________________________________________________

## Basic page structure

A minimal `static-site/index.html` usually looks like this

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>FastMCP demo</title>
  <link rel="stylesheet" href="assets/style.css" />
</head>
<body>
  <main>
    <h1>FastMCP query</h1>

    <form id="query-form">
      <input id="query-input" type="text" placeholder="Enter query" required />
      <button type="submit">Run</button>
    </form>

    <section id="results"></section>
  </main>

  <script src="assets/app.js"></script>
</body>
</html>
```

In `app.js`, attach handlers

```js
const form = document.getElementById("query-form");
const input = document.getElementById("query-input");
const resultsEl = document.getElementById("results");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const q = input.value.trim();
  if (!q) return;

  resultsEl.textContent = "Loading...";

  try {
    const data = await runQuery(q);
    renderResults(data.results || []);
  } catch (err) {
    console.error(err);
    resultsEl.textContent = `Error: ${err.message}`;
  }
});

function renderResults(results) {
  if (!results.length) {
    resultsEl.textContent = "No results";
    return;
  }
  const list = document.createElement("ul");
  results.forEach((row) => {
    const li = document.createElement("li");
    li.textContent = `${row.id}: ${row.content}`;
    list.appendChild(li);
  });
  resultsEl.innerHTML = "";
  resultsEl.appendChild(list);
}
```

______________________________________________________________________

## Local development

For quick frontend only work you can

1. Run the backend locally

   ```bash
   uv venv
   uv pip install -r requirements.txt
   uv run uvicorn app.main:app --reload
   ```

1. Open `static-site/index.html` directly in your browser

1. Set `API_BASE` in `app.js` to `http://localhost:8000`

If you prefer a local static server instead of `file://` URLs

```bash
cd static-site
python -m http.server 8081
```

Then go to [http://localhost:8081](http://localhost:8081) and the page loads from there.

Make sure the backend has CORS enabled if you serve from a different port. You can add FastAPI `CORSMiddleware` for `http://localhost:8081` during development.

______________________________________________________________________

## Deployed behavior

When you have deployed the backend to Cloud Run and created the static bucket

1. Set `API_BASE` in the built assets to the Cloud Run URL, for example

   ```js
   const API_BASE = "https://mcp-api-xyz123-uc.a.run.app";
   ```

1. Sync the static site to the bucket

   ```bash
   gsutil rsync -r static-site/ gs://your-bucket-name
   ```

1. Open the `static_site_url` from Terraform outputs

   The page will call the Cloud Run backend through the JSON facade.

Later, when you add a custom domain or CDN, only the URLs change, the static site code remains the same.

______________________________________________________________________

## Where to look next

- For full architecture context, see `docs/index.md`
- For backend API details and JSON shapes, see `docs/backend.md` and `.vibe/API_SPEC.md`
- For infra and deployment, see `docs/infra.md` and `.vibe/INFRA_NOTES.md`

For deeper design notes aimed at AI assistants or future you, see `.vibe/STATIC_SITE.md`.
