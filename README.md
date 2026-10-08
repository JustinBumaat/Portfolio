# Justin Buma-at Portfolio

A personal portfolio for Justin Buma-at, highlighting selected projects, engineering experience, creative work, and an everyday gear collection.

![Justin Buma-at portfolio preview](images/hero-portrait-768.jpg)

## Highlights

- Animated, staggered page entrances that replay during portfolio navigation.
- Project, experience, and creative-work sections with responsive layouts.
- Light, dark, and system theme preferences.
- Accessible navigation, including a keyboard-accessible home link in the navigation panel.
- A contact form powered by EmailJS.

## Run locally

This is a static site. From the repository root, run:

```bash
python3 -m http.server 4173
```

Then visit [http://localhost:4173](http://localhost:4173).

## Project structure

```text
├── index.html       # Site entry point and small progressive enhancements
├── assets/          # Optimized JavaScript and stylesheet bundles
├── images/          # Portfolio imagery and project logos
└── test/            # Node-based regression checks
```

## Checks

```bash
node --test test/dark-theme-cards.test.mjs
```

## Runtime notes

The contact form sends messages through EmailJS. Other portfolio content is served from the repository itself.
