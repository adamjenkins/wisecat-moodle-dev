# Playwright recipes for a walkthrough

Read this when writing the walkthrough's browser script (login, tours, error capture, widths, dark mode,
Firefox) or rendering the report to PDF without a PDF tool named by the project.

All samples are Python (`pip install playwright`, then `playwright install chromium firefox`). Run them from a
directory of their own, outside the plugin and the Moodle tree.

## Demo users: tours and drawers

Run once per walkthrough user, as a Moodle CLI script (`define('CLI_SCRIPT', true); require('config.php');`).
It does for that user what clicking "Got it" on each tour does, and leaves the tours unchanged for everyone else
(`public/admin/tool/usertours/classes/tour.php`, `TOUR_LAST_COMPLETED_BY_USER`, 5.3.0):

```php
$user = core_user::get_user_by_username('walk_student1', '*', null, MUST_EXIST);
foreach ($DB->get_records('tool_usertours_tours', null, '', 'id') as $tour) {
    set_user_preference('tool_usertours_tour_completion_time_' . $tour->id, time(), $user);
}
set_user_preference('drawer-open-block', 0, $user);
set_user_preference('drawer-open-index', 0, $user);
```

Dark colour mode for one user on Moodle 5.3 (Boost and its children): the site setting
`enablecolourmodes` (component `theme_boost`) must be on, then set the user's preference
`theme_boost_colourmode` to `dark` (`public/theme/boost/classes/colour_mode.php`, 5.3.0). If the setting was off,
record that in the settings snapshot and restore it.

## The browser script

```python
import json, pathlib, sys
from playwright.sync_api import sync_playwright

WWW = sys.argv[1]                       # the site's wwwroot, never hard-coded
OUT = pathlib.Path(sys.argv[2])         # <notes>/<plugin>/walkthrough-YYYY-MM-DD
CREDS = json.loads(pathlib.Path(sys.argv[3]).read_text())   # {"teacher": ["user", "pass"], ...}
OUT.mkdir(parents=True, exist_ok=True)
problems = []

def watch(page, role):
    page.on("pageerror", lambda e: problems.append(f"{role} {page.url}: JS error {e}"))
    page.on("console", lambda m: m.type == "error" and problems.append(f"{role} {page.url}: console {m.text}"))
    page.on("response", lambda r: r.status >= 500 and problems.append(f"{role} {r.url}: HTTP {r.status}"))

def login(ctx, role):
    page = ctx.new_page()
    watch(page, role)
    user, password = CREDS[role]
    page.goto(f"{WWW}/login/index.php")
    page.fill("#username", user)
    page.fill("#password", password)
    page.click("#loginbtn")
    page.wait_for_load_state("networkidle")
    if "/login/" in page.url:
        sys.exit(f"login failed for {role}: stop and report it, do not retry with other passwords")
    return page

def shot(page, name, selector=None, full=False):
    page.wait_for_load_state("networkidle")
    target = page.locator(selector).first if selector else page
    target.screenshot(path=str(OUT / f"{name}.png"), **({} if selector else {"full_page": full}))

with sync_playwright() as p:
    browser = p.chromium.launch()
    for role, size in [("teacher", (1280, 900)), ("student", (1280, 900)), ("student", (390, 844))]:
        ctx = browser.new_context(viewport={"width": size[0], "height": size[1]})
        page = login(ctx, role)
        tag = role if size[0] > 500 else f"{role}-phone"
        page.goto(f"{WWW}/course/view.php?name=WALK1")   # look the course up by shortname in the data script
        shot(page, f"01-{tag}-course-page")
        # ... one goto, action and shot per step of the coverage list
        ctx.close()
    browser.close()

(OUT / "problems.txt").write_text("\n".join(problems) or "none\n")
```

- Pass the wwwroot, output directory and a credentials file as arguments. Keep credentials out of the script
  and out of the report.
- Look up ids (course, cm) in the demo-data script and pass them in, or navigate by visible links. Ids change
  when the data is rebuilt.
- **Phone width:** after each phone shot, check there is no horizontal scroll:
  `page.evaluate("document.documentElement.scrollWidth - innerWidth")` must be `0`. Report the number.
- **Firefox:** repeat the key screens with `p.firefox.launch()`; the same script works.
- **Reduced motion:** `browser.new_context(reduced_motion="reduce")`.
- **Is it visible, not just in the viewport:** Boost's fixed navbar and floating buttons cover content that a
  bounding-box check passes. Check with `document.elementFromPoint` at the element's centre.
- **After a cache purge** the first request can still serve the old theme CSS. Fetch the page once and wait
  before the shot that proves a style change.
- **HTTPS with a self-signed certificate:** `browser.new_context(ignore_https_errors=True)`.
- `problems.txt` goes into the report's findings: each error with the page it came from.

## Markdown to PDF without a project tool

Write the HTML next to the `.md` file so the relative image links resolve, print it with Chromium, then delete
the HTML:

```python
import pathlib, sys, markdown                    # pip install markdown
from playwright.sync_api import sync_playwright

md = pathlib.Path(sys.argv[1]).resolve()         # <notes>/<plugin>/WALKTHROUGH-YYYY-MM-DD.md
pdf = md.parent / "pdf" / (md.stem + ".pdf")
pdf.parent.mkdir(exist_ok=True)
css = ("body{font:11pt/1.45 sans-serif;margin:0 1.5cm}img{max-width:100%;border:1px solid #ccc}"
       "table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:3px 6px;vertical-align:top}"
       "h2{page-break-before:auto;margin-top:1.6em}img,table{page-break-inside:avoid}")
html = md.parent / (md.stem + ".print.html")
body = markdown.markdown(md.read_text(), extensions=["extra", "sane_lists"])
html.write_text(f"<!doctype html><meta charset=utf-8><style>{css}</style>{body}")
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto(html.as_uri())
    page.wait_for_load_state("networkidle")
    page.pdf(path=str(pdf), format="A4", print_background=True, margin={"top": "1.5cm", "bottom": "1.5cm"})
    b.close()
html.unlink()
print(pdf)
```

Then check it: `pdfinfo <pdf>` (page count), `pdfimages -list <pdf> | tail -n +3 | wc -l` (should equal the
number of screenshots in the report), and `pdftoppm -f 2 -l 2 -png -r 60 <pdf> /tmp/page` to look at one page.
