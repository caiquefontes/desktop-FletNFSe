# Flet Desktop Development Rules

## 1. Core Architecture
- Always use the `flet.app(target=main)` pattern for desktop execution.
- Utilize stateful Flet controls and encapsulate UI components inside Python classes inheriting from `ft.UserControl` for maintainability.
- Manage global state via a separate controller or state class, avoiding direct global variable mutation where possible.

## 2. Flet Desktop API Limits
- You are strictly building a **Desktop Application**. Do not use `page.route` or Flet's URL routing, as Flet's desktop navigation differs from web routing.
- Do not use `page.launch_url()` for deep web integration unless specifically requested.
- For local file access, always use Flet's native `ft.FilePicker`.

## 3. Window & Theme Management
- Explicitly set desktop window bounds using `page.window.width`, `page.window.height`, and `page.window.min_width` (Flet 0.22+ API).
- Set `page.window.resizable = True` (or `False` if designing a fixed-size tool/dialog).
- Always set `page.theme_mode = ft.ThemeMode.DARK` or `LIGHT` explicitly rather than relying on system defaults for consistent look and feel.
- Ensure `page.update()` is only called within state mutation functions, avoiding redundant redraws.

## 4. Packaging and Dependencies
- Assume deployment will occur via PyInstaller or Nuitka.
- Provide a clear `requirements.txt` containing strictly `flet` and necessary extensions.
- Instruct the user to use `flet pack` for generating standalone Windows `.exe` or MacOS `.app` bundles.
