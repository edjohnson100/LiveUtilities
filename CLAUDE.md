# LiveUtilities

A Fusion 360 add-in: a persistent HTML palette (`resources/liveutils_index.html`)
for managing User Parameters, Configuration Snapshots, Design Changelogs, Macro
Scripts, and UI Themes. Entry point is `LiveUtilities.py`; most host-side logic
lives in `core_logic.py`. Version lives in `LiveUtilities.manifest`.

## Multi-monitor palette positioning

`display_utils.py` fixes a real Fusion bug: a floating palette restored to a
saved `left`/`top` can be a valid point on a *connected* display and still
never be drawn, because Fusion won't show a floating palette outside the
display its own main window occupies. This happens whenever Fusion opens on
one monitor after the palette was last parked on another.

The fix validates the saved position against the display Fusion's main window
is actually on (not just "is this point on any screen"), and remaps to the
same relative spot on Fusion's display when it isn't.

- `display_utils.get_displays()` — screen rects in virtual-desktop space, via
  ctypes: `CGGetActiveDisplayList`/`CGDisplayBounds` on macOS,
  `EnumDisplayMonitors` on Windows.
- `display_utils.get_app_window_rect()` — Fusion's main window frame, via
  ctypes: `CGWindowListCopyWindowInfo` filtered to our PID on macOS,
  `EnumWindows`/`GetWindowRect`/`GetWindowThreadProcessId` on Windows. No
  third-party modules on either platform.
- `display_utils.resolve_palette_position(...)` — the core decision: `ok` /
  `remapped` / `clamped` / `unverified`. Called from
  `core_logic._restore_palette_geometry()`.
- `display_utils.describe(...)` — human-readable diagnostic dump used by both
  `core_logic.palette_display_report()` and the standalone script below.

**Standalone diagnostic**: `tools/PaletteDisplayCheck/PaletteDisplayCheck.py`
is a separate Fusion script (Scripts and Add-Ins > Scripts, not the add-in
itself) that reports monitor layout, Fusion's window, the saved palette
position, and the verdict — works whether or not the palette is currently
loaded. Useful for reproducing/confirming the bug without touching the add-in.

### Windows testing status

The macOS path (`_displays_macos` / `_app_window_rect_macos`) is verified
against real hardware (4K + HD side-by-side monitors) — both the diagnostic
verdicts and actual palette open/close behavior confirmed correct.

The Windows path (`_displays_windows` / `_app_window_rect_windows`) compiles
but has **not been run against real Fusion + multi-monitor hardware yet**.
Known-likely failure points to check first if it misbehaves:
- DPI scaling mismatches across monitors with different scale factors (the
  Windows code calls `SetProcessDpiAwareness(2)` to get raw pixel rects, but
  verify Fusion's own `palette.left`/`top` values are also raw pixels, not
  scaled).
- `EnumWindows` picking the wrong top-level window if Fusion has multiple
  visible top-level windows of similar size (the "largest owned window" tie-
  break may need tightening).

To test: run `PaletteDisplayCheck` with Fusion's window on each monitor in
turn and confirm the verdict (`ok` on Fusion's own display, `remapped` when
the saved position is on the other display) matches reality, then do a real
close/reopen of the palette and confirm it lands on the correct screen.

## Working conventions

- No comments explaining *what* code does — only *why*, for non-obvious
  constraints (see the header comment in `display_utils.py` for the pattern).
- `resources/preferences.json` and `imported_themes.json` are gitignored,
  per-machine state — don't commit them, and expect them to differ between
  your Mac and Windows checkouts.
