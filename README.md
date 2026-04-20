# MyST CV Template

A reusable template for building academic CV websites with [MyST Markdown](https://mystmd.org/), automatic CV PDF generation via [Typst](https://typst.app/), blog support with RSS feeds, and automated deployment via GitHub Actions.

## Features

- **MyST Markdown** source format with Jupyter notebook integration
- **Automatic CV PDF generation** from website content using Typst and [modern-cv](https://typst.app/universe/package/modern-cv/)
- **Blog** with RSS and Atom feed generation
- **Giscus comments** (GitHub-backed) for blog posts
- **GitHub Pages** deployment on push to `main`
- **Netlify PR previews** for pull request review
- **Pre-commit hooks**: Black, codespell, nbstripout for code quality

## Quick Start

1. Click **Use this template** on GitHub to create a new repository
2. Update `myst.yml` with your site title, description, and table of contents
3. Replace placeholder content in `pages/` with your own
4. Update `generate_cv.py` preamble with your author information
5. Update `generate_rss.py` with your site URL and metadata
6. Push to GitHub to trigger automated builds

## Project Structure

```
.
├── myst.yml                    # MyST configuration
├── index.md                    # Landing page (bio, highlights, news)
├── custom.css                  # Custom CSS styling
├── requirements.txt            # Python dependencies
├── generate_cv.py              # CV PDF generation script
├── generate_rss.py             # RSS/Atom feed generation script
├── inject_comments.py          # Giscus comment injection script
├── Dockerfile                  # Docker build for full site
├── logo.png                    # Site logo
├── fav.ico                     # Favicon
├── CNAME                       # Custom domain (optional)
├── pages/                      # Site content
│   ├── about.md                # Biography, education, appointments
│   ├── research.md             # Publications, grants, patents
│   ├── software.md             # Open-source software projects
│   ├── teaching.md             # Courses, mentoring
│   ├── talks.md                # Workshops, invited talks, presentations
│   ├── awards.md               # Awards & honors
│   ├── services.md             # Professional & institutional services
│   ├── contact.md              # Contact information
│   ├── news.md                 # News log by year
│   ├── blog.md                 # Blog landing page
│   └── images/                 # Shared images
├── blog/                       # Blog posts
│   └── sample-post.md          # Sample blog post
├── .pre-commit-config.yaml     # Pre-commit hook configuration
├── CONTRIBUTING.md              # Contribution guidelines
├── CONDUCT.md                   # Code of conduct
└── .github/workflows/
    ├── build.yml               # PR preview builds (Netlify)
    └── deploy.yml              # Production deployment (GitHub Pages)
```

## Customization

### Site Metadata

Edit `myst.yml`:

- `project.title`: your name
- `project.description`: site description
- `project.keywords`: your research keywords
- `site.parts.footer`: footer links (CV PDF, social profiles)

### Author Information for CV

Edit the `gen_preamble()` function in `generate_cv.py`:

- `firstname`, `lastname`: your name
- `email`, `phone`, `homepage`: contact details
- `github`: GitHub username
- `address`: office address
- `positions`: job titles
- `custom`: social media and academic profile links

### Adding Pages

1. Create a new `.md` file in `pages/`
2. Add the file to `project.toc` in `myst.yml`

### Adding Blog Posts

1. Create a new `.md` file in `blog/` with frontmatter (title, date, authors, description, tags)
2. Add a card entry in `pages/blog.md` linking to the new post

## Building Locally

### Build HTML

```bash
pip install -r requirements.txt
npm install -g mystmd
myst build --html
```

The built site will be in `_build/html/`.

### Build Local HTML + PDF

For this customized resume site, the simplest local build command is:

```bash
python build_local.py
```

Or on Windows PowerShell:

```powershell
.\build_local.ps1
```

This script will:

1. Generate `cv.typ`
2. Compile `cv.pdf` when `typst` and `fonts/` are available
3. Build the HTML site into `_build/html/`
4. Copy `cv.pdf` into `_build/html/cv.pdf` when PDF generation succeeds

If `typst` or `fonts/` are missing, the script will still build the HTML site and clearly tell you why the PDF was skipped.

### Build CV PDF

Prerequisites: Python 3.10+, [Typst](https://typst.app/) CLI, and the required CV fonts in a `fonts/` directory.

```bash
# Generate Typst source from website markdown files
python generate_cv.py

# Compile to PDF (with custom fonts and icons)
typst compile cv.typ cv.pdf --font-path ./fonts --ignore-system-fonts
```

The script reads content from `pages/about.md`, `pages/research.md`, `pages/software.md`, `pages/teaching.md`, `pages/talks.md`, `pages/awards.md`, and `pages/services.md`, then generates a `cv.typ` file with all CV sections.

### Font Setup (for CV)

The current `modern-cv` setup expects Source Sans 3, Roboto, a CJK fallback font for Chinese text, and Font Awesome 6 icons. Download them into a `fonts/` directory:

```bash
mkdir -p fonts

# Source Sans 3 (modern-cv body font)
curl -sL "https://github.com/adobe-fonts/source-sans/releases/download/3.052R/OTF-source-sans-3.052R.zip" -o source-sans.zip
unzip -j -o source-sans.zip "*.otf" -d fonts/

# Roboto (modern-cv heading font)
curl -sL "https://github.com/googlefonts/roboto-2/releases/download/v2.138/roboto-unhinted.zip" -o roboto.zip
unzip -j -o roboto.zip "*.ttf" -d fonts/

# Source Han Sans SC (Chinese fallback)
curl -sL "https://github.com/adobe-fonts/source-han-sans/releases/latest/download/SourceHanSansSC.zip" -o source-han-sans-sc.zip
unzip -j -o source-han-sans-sc.zip "*.otf" -d fonts/

# Font Awesome 6 (icons)
curl -sL "https://use.fontawesome.com/releases/v6.7.2/fontawesome-free-6.7.2-desktop.zip" -o fa.zip
unzip -j -o fa.zip "*.otf" -d fonts/
```

The `--ignore-system-fonts` flag in the compile command ensures Typst uses only these fonts, which keeps rendering consistent across environments and avoids CI-only font fallback differences.

### Generate RSS/Atom Feeds

```bash
pip install feedgen pyyaml
python generate_rss.py
```

Reads frontmatter from `blog/*.md` and writes `rss.xml` and `atom.xml`.

### Building with Docker

Build and serve the site without installing any dependencies locally:

```bash
docker build -t myst-cv-template .
docker run --rm -p 3000:3000 -p 3100:3100 myst-cv-template
```

Then open http://localhost:3000 in your browser. If port 3000 is already in use, map to different ports (e.g., `-p 3001:3000 -p 3101:3100` and open http://localhost:3001). The Docker image includes Node.js, Python, Typst, and all required fonts.

## Deployment

### GitHub Pages (production)

Pushes to `main` trigger the `deploy.yml` workflow, which:

1. Builds the HTML site with MyST
2. Generates `rss.xml` and `atom.xml` from blog posts
3. Generates `cv.typ` from markdown content
4. Compiles `cv.pdf` with Typst
5. Injects Giscus comments into blog posts
6. Deploys everything to GitHub Pages

The CV PDF will be available at `https://your-site.com/cv.pdf`.

### Recommended workflow for this resume site

If you are using this repository as your personal CV website, the simplest workflow is:

1. Edit the Markdown files locally, such as `index.md` and files in `pages/`
2. Commit and push your changes to the `main` branch on GitHub
3. Let GitHub Actions automatically build and deploy the website
4. Share the GitHub Pages URL instead of the repository URL

If you do not configure a custom domain, the public site URL will normally be:

```text
https://<your-github-username>.github.io/<your-repository-name>/
```

After each push to `main`, the deployed site will also regenerate and publish `cv.pdf`, so the web resume and PDF resume stay in sync.

### Netlify (PR previews)

Pull requests trigger the `build.yml` workflow for preview deployments. Requires `NETLIFY_AUTH_TOKEN` and `NETLIFY_SITE_ID` secrets.

## GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `NETLIFY_AUTH_TOKEN` | Netlify authentication for PR previews |
| `NETLIFY_SITE_ID` | Netlify site ID for PR previews |

## License

[MIT](LICENSE)
