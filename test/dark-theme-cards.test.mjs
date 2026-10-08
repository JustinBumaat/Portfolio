import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const page = new URL('../index.html', import.meta.url);

test('dark theme gives project cards a dark surface', async () => {
  const html = await readFile(page, 'utf8');

  assert.match(
    html,
    /\.portfolio-home--dark\s+\.project-card\s*\{[^}]*background:\s*var\(--paper-strong\)/,
  );
});

test('dark theme uses #040406 for its shared surfaces', async () => {
  const html = await readFile(page, 'utf8');

  assert.match(
    html,
    /html\s+\.portfolio-home--dark\s*\{[^}]*--site-background:\s*#040406[^}]*--paper:\s*#040406[^}]*--paper-strong:\s*#040406/,
  );
});

test('dark project cards have light borders and readable text', async () => {
  const html = await readFile(page, 'utf8');

  assert.match(
    html,
    /\.portfolio-home--dark\s+\.project-card\s*\{[^}]*border:\s*1px solid #f4f4f0/,
  );
  assert.match(
    html,
    /\.portfolio-home--dark\s+\.project-card__topline[\s\S]*?color:\s*#f4f4f0/,
  );
});

test('dark navigation surfaces use #040406', async () => {
  const html = await readFile(page, 'utf8');

  assert.match(
    html,
    /html\s+\.menu-overlay--dark\s+\.menu-overlay__panel\s*\{[^}]*background:\s*#040406/,
  );
  assert.match(
    html,
    /html\s+\.menu-toggle--persistent\.menu-toggle--dark\s*\{[^}]*background:\s*#040406/,
  );
  assert.match(
    html,
    /html\s+\.menu-overlay--dark\s+\.menu-overlay__panel\s*\{[^}]*color:\s*#f4f4f0/,
  );
});

test('page loads provide an accessible staggered entrance animation', async () => {
  const html = await readFile(page, 'utf8');

  assert.match(html, /\.page-stagger-item\s*\{[^}]*animation:\s*page-stagger-in/);
  assert.match(html, /@media\s*\(prefers-reduced-motion:\s*reduce\)[\s\S]*?\.page-stagger-item\s*\{[^}]*animation:\s*none/);
  assert.match(html, /const replayPageStagger = \(\) =>/);
  assert.match(html, /window\.addEventListener\("hashchange", schedulePageStagger\)/);
});

test('navigation panel name links back to the home section', async () => {
  const html = await readFile(page, 'utf8');

  assert.match(
    html,
    /const makeMenuNameHomeLink = \(\) =>[\s\S]*?\.menu-overlay__header h2[\s\S]*?heading\.setAttribute\("role", "link"\)[\s\S]*?showHashRoute\("#home", "\/", true\)/,
  );
});
