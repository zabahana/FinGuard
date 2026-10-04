# Import-ready GitHub Pages article

Public article URL: `https://zabahana.github.io/FinGuard/`.

The publication build contains only `index.html`, `.nojekyll`, and these seven figures:

1. `assets/model-behavior.png`
2. `assets/safety-outcomes.png`
3. `assets/attack-lab-results.png`
4. `assets/attack-catalogue.png`
5. `assets/model-evaluation.png`
6. `assets/prompt-injection-story.png`
7. `assets/workspace.png`

It publishes the article text, reported evaluation results, figures, and the contact email `zga5029@psu.edu`. The source repository is public, as authorized by its owner. No transaction dataset, raw trial transcripts, model weights, credentials, or application backend is copied into the publication build.

Build with `node scripts/build-github-pages.cjs` with Marked available through Node's module search path. The output is `artifacts/github-pages/`. The article uses absolute HTTPS image URLs, semantic figures/captions, and a canonical URL. Unlike the offline publication HTML, it has no embedded base64 images or publishing toolbar.

Deployment: an article-only `codex/github-pages` branch, with GitHub Pages publishing from its root. The repository owner explicitly authorized publishing the repository, article, figures, evaluation results, and contact email.

After deployment, use the live page URL in Medium's **Stories → Import a story** flow, then inspect all seven images and their captions. Import compatibility is not guaranteed. Medium creates a canonical link to the imported source; publishing the Medium story remains a separate step.

## Update the published article

After editing the Medium template, regenerate the Markdown and offline HTML as described in [visual publication maintenance](VISUALS.md). For a fresh checkout, clone the publication branch into the ignored build directory before building:

```sh
git clone --branch codex/github-pages --single-branch https://github.com/zabahana/FinGuard.git artifacts/github-pages
```

If that directory already contains its publication checkout, use it directly. Build and publish:

```sh
node scripts/build-github-pages.cjs
git -C artifacts/github-pages add index.html .nojekyll assets
git -C artifacts/github-pages commit -m "Update public FinGuard article"
git -C artifacts/github-pages push origin codex/github-pages
```

Pages deploys pushes to that publication branch. A push to `main` alone does not update the live article. Check the public page and each figure after a deployment.
