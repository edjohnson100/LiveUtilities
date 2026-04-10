# Technical Reference: LiveUtilities
**Generated:** 2026-04-10

## Project Overview and Workflow
The LiveUtilities project is a Fusion add-in designed to streamline and enhance the user's workflow by providing a unified, modeless HTML palette for managing various aspects of a Fusion design. These aspects include user parameters, design configurations (snapshots), design changelogs, and macro scripts. The add-in aims to improve efficiency and organization within the Fusion environment by centralizing these key functionalities into a single, accessible interface.

The core functionality of the add-in is implemented in `core_logic.py`, which handles the heavy lifting of scanning the design, applying configurations, executing external scripts (plugins), and generating reports. This script interacts directly with the Fusion API (`adsk.fusion`) to manipulate the design data. The `LiveUtilities.py` file serves as the entry point for the add-in within Fusion, initializing the UI, managing data updates, and facilitating communication between the add-in and the HTML-based palette. The palette itself is constructed using `liveutils_index.html`, styled with `liveutils_style.css`, and driven by `liveutils_script.js`. This JavaScript code handles UI rendering, user interactions, and communication with Fusion via the `adsk.fusion` API. The `plugins.json` file acts as a configuration file, listing available Fusion plugins and their file paths, allowing the add-in to manage and execute external scripts.

The typical user workflow begins with the user installing the LiveUtilities add-in into Fusion using the `LiveUtilities.manifest` file. Once installed, the user can access the Live Utilities palette within Fusion. From the palette, the user can manage design parameters, create and apply configuration snapshots, view and manage design changelogs, and execute macro scripts. The user interacts with the HTML-based UI within the palette, triggering actions that are then processed by the JavaScript code (`liveutils_script.js`), which in turn communicates with the Fusion application through the `LiveUtilities.py` and `core_logic.py` files. The add-in provides a centralized location for managing and interacting with these key design elements, improving the user's overall workflow and productivity.

---

## File Index and Summaries

### File: `core_logic.py`
**Summary:** This file contains the core logic for a Fusion add-in, providing functionality for managing design configurations, parameters, external plugins, and a changelog system, including scanning the design, applying configurations, executing external scripts, and generating reports.

**Dependencies:**
* adsk.core
* adsk.fusion
* traceback
* json
* re
* datetime
* tempfile
* webbrowser
* time
* os
* sys
* platform
* importlib.util

### File: `LiveUtilities.manifest`
**Summary:** This manifest file describes an Autodesk Fusion add-in called "LiveUtilities" which provides a unified palette for managing user parameters, configuration snapshots, design changelogs, and macro scripts. It specifies metadata like ID, author, version, supported OS, and icon filename.

**Dependencies:**
* None

### File: `LiveUtilities.py`
**Summary:** This file defines a Fusion add-in called "Live Utilities" that provides a persistent palette with tools for managing parameters, configurations, changelogs, and macros, enhancing the user's workflow within Fusion. It handles UI interactions, data updates, and communication between the add-in and the HTML-based palette.

**Dependencies:**
* adsk.core
* adsk.fusion
* traceback
* json
* os
* importlib
* pathlib
* .core_logic

### File: `README.md`
**Summary:** This README.md file describes the LiveUtilities add-in for Autodesk Fusion, which provides a modeless HTML palette for managing parameters, configurations, changelogs, and macro scripts within Fusion. It details the add-in's features, installation instructions, usage guidelines, and acknowledgements.

**Dependencies:**
* None

### File: `resources\liveutils_index.html`
**Summary:** This HTML file defines the structure and content of a web-based interface for managing live parameters, configurations, changelogs, and scripts, likely for a CAD or design application. It provides interactive elements for creating, editing, and exporting data, as well as customizing the user interface.

**Dependencies:**
* liveutils_style.css
* liveutils_script.js

### File: `resources\liveutils_script.js`
**Summary:** This JavaScript file provides the front-end logic for a Fusion add-in, handling UI rendering, data updates, user interactions, and communication with the Fusion application via the `adsk.fusion` API. It manages parameters, configurations, features, and scripts within the add-in's user interface.

**Dependencies:**
* None

### File: `resources\liveutils_style.css`
**Summary:** This CSS file defines styles and color themes for a user interface, including light and dark modes, using CSS variables to manage color palettes and common UI elements. It provides a consistent look and feel with customizable themes.

**Dependencies:**
None

### File: `resources\plugins.json`
**Summary:** This JSON file defines a list of Fusion plugins, specifying their names and file paths. It serves as a configuration file for managing and locating plugin scripts.

**Dependencies:**
* None

