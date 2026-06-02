# Distribution build plan — website + downloadable app (in parallel)

Decided 2026-06-01: build BOTH the public marketing website and the
double-clickable app in parallel; publish the site the moment the app is ready,
so a "Download" button never 404s or dumps people into a terminal (the
"screaming into the wind" failure the distribution research warned about).

## Track A — Public marketing website (faster, lower risk)
- **What:** a static public site — the manifesto + the four-tool pitch, in the
  black-and-white editorial style (hearth.css). NOT the app; just the idea + the
  reasoning + (eventually) a real Download button.
- **Where:** GitHub Pages (free, static, real URL). Lives in `site/` (rebuild the
  stale old landing page in the new style). Build-time: hours.
- **The Download button:** points to the app once Track B ships. Until then it
  honestly says "for developers: clone + run" / "one-click app coming."
- **Privacy:** static, no analytics (consistent with the thesis).

## Track B — The double-clickable app (the hard last mile)
- **What:** a signed, notarized macOS `.app` a non-technical person double-clicks.
  It must: bundle the Python runtime + the server, fetch/bundle the model weights
  (~8GB), START THE LOCAL SERVER ITSELF, and open the browser to the Hearth hub —
  no terminal, ever.
- **The hard parts (honest):**
  1. Bundling a Python app + heavy native deps (MLX, etc.) into a self-contained
     .app (PyInstaller / briefcase / py2app — pick after a spike).
  2. The ~8GB model weights: bundle (huge download) vs. fetch-on-first-run (needs
     network once). Likely first-run fetch with a clear progress UI.
  3. Apple code signing + notarization (needs an Apple Developer ID, $99/yr) so
     Gatekeeper doesn't block it. This is a real account/credential step for Sonali.
  4. Auto-start the server on a free port + open the browser; clean shutdown.
- **Smallest viable first step:** a spike — get a trivial PyInstaller build of the
  server that double-click-launches + opens the browser, on this Mac, unsigned.
  Prove the mechanism before tackling weights + signing.

## Sequencing
1. Track A website (now) — publishable quickly; establishes the public presence.
2. Track B spike (parallel) — prove the .app can self-launch.
3. Track B full: weights strategy → signing/notarization → real .app.
4. Publish site's Download button when the .app exists. Site + download land together.

## Open items for Sonali
- Apple Developer account ($99/yr) for notarization — required for a non-scary
  download. (Without it, macOS warns "unidentified developer" / blocks it.)
- Domain name? (GitHub Pages gives tsonali.github.io/... free; a custom domain is optional.)
