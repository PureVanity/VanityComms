# Vanity — portfolio site

## What changed in this pass

**Spotify is gone.** The "now playing" widget was pulling from Spotify's
OAuth (PKCE) flow through a Cloudflare Worker (`workers/spotify-exchange.js`)
and a hardcoded redirect URI. That setup only works if the Worker is deployed
separately from the static site and the domains line up exactly — which is
almost certainly why it broke once this moved to Cloudflare Pages. Rather
than debug that plumbing, it's been replaced with something that can't go
down: a single local audio file playing on loop, no login, no external API,
no server. `wrangler.toml` and the `workers/` folder have been deleted since
nothing on the site needs a Worker anymore — Cloudflare Pages will serve
this as a plain static site.

**Color scheme** is now sky blue on near-black (was gold/amber on
near-black). Every color in `index.html`'s `<style>` block is a CSS variable
at the top (`--accent`, `--accent-bright`, etc.), so nudging the shade later
is a one-line change per variable, not a find-and-replace through the file.

**Visual cleanup.** Removed: the emoji in the feature strip, the grain/noise
texture overlay, the pulsing status dot, the gradient-clipped headline text,
the green checkmark icons on the feature list, and the staggered
fade-in-on-load animations on the hero. The goal was a page that reads as
deliberately designed rather than assembled from a template — same bones,
quieter execution.

**New sections:** Commissions, and an "Elsewhere" section with two self-serve
zones (details below).

## Adding your background music

1. Drop an audio file into `assets/audio/` — `.mp3` or `.ogg` both work.
2. In `index.html`, find the `<audio id="bgAudio">` tag near the top of
   `<body>` and update the `<source src="...">` path to match your filename.
3. Update the two constants near the bottom of the script:
   ```js
   const TRACK_NAME = 'Background track';
   const TRACK_CREDIT = 'Add your track title and credit here';
   ```
   These drive both the Music section and the toast text.

**On Minecraft's soundtrack specifically:** I can't source or embed C418's
or Lena Raine's tracks for you — that's Mojang/Microsoft-licensed music, not
something to pull from a public URL into a site you host. If you own the
game, Minecraft's own music files live in your client install and are meant
for personal use in-game, not redistribution on a public website, so I'd
lean toward either an official soundtrack purchase/license for public use,
or a royalty-free ambient track if this needs to be safe for a public site.
Whatever you use, it just needs to land in `assets/audio/` — the player code
doesn't care what the track is.

**How the player behaves:** it attempts muted autoplay on load (browsers
allow this), then unmutes on the visitor's first click, keypress, or tap
anywhere on the page — at which point the "now playing" toast slides in for
about six seconds. The button in the Music section does the same thing
manually and doubles as an ordinary mute/unmute toggle afterward.

## Editing the commissions section

Look for the `<!-- COMMISSIONS -->` comment in `index.html`. Each service is
one `.commission-card` block — copy one to add a service, delete one to
remove it. Replace the `$__` placeholders, turnaround/revision counts, and
point each "Request this" button's `href` at wherever you actually want
requests to land (a Discord invite, a mailto: link, a form).

## Self-serve zones ("Elsewhere" section)

Two zones are marked with HTML comments so you can edit them directly
without touching anything else on the page:

- **`#custom-links-zone`** — plain `<a class="panel">` cards. Duplicate the
  block for each other site, redirect, or embed you want to link out to.
- **`#custom-image-zone`** — `<figure class="custom-image-card">` blocks.
  Drop your image files into `assets/custom/` and point each `<img src>` at
  them; duplicate the block for more images.

Both zones currently show placeholder content (`assets/custom/placeholder.svg`)
so the layout looks right before you've added anything.

## Running it locally

```bash
cd vanity-site
python3 -m http.server 8000
```
Visit `http://localhost:8000`. (`serve.py` also exists in this folder if you
were using that already — untouched by this pass.)

## Deploying

Since there's no Worker anymore, Cloudflare Pages just needs this folder as
a static site: point it at the repo, no build command, output directory is
the project root (wherever `index.html` lives).
