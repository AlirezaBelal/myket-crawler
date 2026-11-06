import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'site');
const html = await readFile(path.join(root, 'index.html'), 'utf8');
const css = await readFile(path.join(root, 'styles.css'), 'utf8');
const mark = await readFile(path.join(root, 'assets', 'myket-mark.svg'), 'utf8');
const illustration = await readFile(path.join(root, 'assets', 'crawler-workflow.svg'), 'utf8');

test('product site positions the local crawler accurately', () => {
  assert.match(html, /<title>Myket Crawler — Local Android app research<\/title>/);
  assert.match(html, /rel="canonical" href="https:\/\/alirezabelal\.github\.io\/myket-crawler\/"/);
  assert.match(html, /Python and Selenium crawler/);
  assert.match(html, /does not crawl Myket or process datasets/);
  assert.match(html, /workflow illustration · not a live crawl or product screenshot/i);
  assert.doesNotMatch(html, /browser-based CSV\/JSON import|hosted crawler|live marketplace data/i);
});

test('primary tasks, installation, safeguards, and documentation links exist', () => {
  assert.match(html, /Get started on GitHub/);
  assert.match(html, /href="#install"/);
  assert.match(html, /href="#workflow"/);
  assert.match(html, /py -3 -m venv \.venv/);
  assert.match(html, /python3 -m venv \.venv/);
  assert.match(html, /--max-apps 3 --max-navigations 20/);
  assert.match(html, /CAPTCHA, rate limits, or anti-bot controls/);
  assert.match(html, /QUICKSTART\.fa\.md/);
});

test('local assets and the page security boundaries are present', () => {
  assert.match(html, /connect-src 'none'/);
  assert.match(html, /script-src 'none'/);
  assert.match(html, /<link rel="stylesheet" href="\.\/styles\.css">/);
  assert.match(html, /\.\/assets\/myket-mark\.svg/);
  assert.match(html, /\.\/assets\/crawler-workflow\.svg/);
  assert.match(mark, /<svg[\s\S]*<title id="title">Myket Crawler mark<\/title>/);
  assert.match(illustration, /ILLUSTRATIVE FLOW · NO LIVE DATA/);
  assert.doesNotMatch(html, /<script\b|<form\b|<iframe\b|https:\/\/fonts\./i);
  assert.doesNotMatch(html, /<(?:img|script)\b[^>]+src="https?:\/\//i);
  assert.doesNotMatch(html, /<link\b(?=[^>]*rel="stylesheet")[^>]+href="https?:\/\//i);
});

test('responsive styles define the full mobile-to-wide layout and keyboard focus', () => {
  assert.match(css, /\.skip-link:focus/);
  assert.match(css, /:focus-visible/);
  assert.match(css, /@media \(max-width: 900px\)/);
  assert.match(css, /@media \(max-width: 650px\)/);
  assert.match(css, /@media \(max-width: 380px\)/);
  assert.match(css, /prefers-reduced-motion: reduce/);
  assert.match(css, /overflow-x: auto/);
});
