# LiveUtilities for Autodesk Fusion

**Version:** 1.4.0  
**Author:** Ed Johnson (Making With An EdJ)

LiveUtilities is an all-in-one HTML palette add-in for Autodesk Fusion that supercharges your parametric modeling workflow. It consolidates live parameter management, state-based configuration snapshots, automated changelog tracking, batch exporting, and a global macro script launcher into a single, clean interface.

<img src="LiveUtilitiesAppIcon.png" width="300">

## Introduction: The "Why" and "What"

We’ve all been there:
* You are tweaking a Fusion design for a 3D print. You open `Modify > Change Parameters`. You change a value. You hit Enter. The modal box closes. You check the fit. It’s wrong. You open the box again... **Lather. Rinse. Repeat.**
* You open a Fusion design you haven't touched in six months named `MyWidget_Final_v42`. You stare at the browser tree and wonder: *"Why did I add that chamfer? Is this actually the final version?"*

Fusion’s native dialogs are functional, but they are often modal (blocking your view) and lack the space for saving iterative states or detailed historical context. 

**LiveUtilities** solves this by combining LiveParameters, LiveConfig, a Changelog Sidecar, and a Macro Launcher into a single, modeless HTML palette that docks right inside Fusion. Instead of constantly opening and closing native dialogs, you have a persistent, tabbed interface to manage your design's math, states, and utilities in real-time.

---
## ✨ What's New in v1.4.1

* **The Macro Sandbox (Protected Execution):** Complex native scripts (like Fusion's sample `SpurGear`) often contain `adsk.terminate()` commands that accidentally kill the entire LiveUtilities dashboard when they finish. v1.4.1 introduces a system-level sandbox that intercepts and neutralizes these commands, keeping your palette alive.
* **Package Spoofing:** We added dynamic namespace spoofing to the `importlib` executor. This allows you to link complex scripts that rely on relative imports (`from . import`) without throwing package errors.
* **UI Polish & Auto-Sorting:** Your linked macros now automatically sort themselves alphabetically (A-Z) in both the launcher and the script manager. The launcher buttons have also been tightened up for a sleeker profile.
* **Cleaner Version History:** The `C-log:` prefix has been removed from standard design saves to free up screen real estate in Fusion's Data Panel. Milestones are now cleanly marked with a `🚩` emoji so you can visually spot them instantly when scrolling through dozens of saved versions.

---
## ✨ What's New in v1.4.0

* **The Macro Board (Scripts Tab):** LiveUtilities is now a true command center. You can link your favorite standalone Python scripts (like Gridfinity generators or Canvas Greyscale tools) and launch them directly from the new "Scripts" tab. 
* **Smart Directory Picker:** When linking a new script, the add-in automatically resolves Fusion's deeply hidden system paths. With one click, you can jump directly to your personal Scripts folder, Add-ins folder, or even the dynamically hashed native Fusion Sample Scripts folder.
* **Global Plugin Registry:** Your linked scripts are saved globally, meaning your favorite macros are always available in the palette regardless of which Fusion file you have open.

---
## ✨ What's New in v1.3.1

* **Expanded Theme Engine:** We ditched the basic Light/Dark switch for a persistent, multi-theme selector. Customizations include Ocean Blue, Hacker Green, Warm Sepia, Solarized (Light & Dark), and Gruvbox Light.
* **Persistent UI Memory:** Your selected theme and active tab are now saved locally.
* **Auto-Sorting UI:** Parameters and Configuration Snapshots now automatically sort themselves alphabetically (A-Z).

---

## Installation

### Manual Installation Options

This script requires a quick manual installation. You can choose to install it in Fusion's default scripts directory or a custom folder of your choice.

#### Option 1: Install in the Default Fusion Directory
1. **Download:** Download the source code as a ZIP file and extract the `LiveUtilities` folder.
2. **Move the Folder:** Move the entire `LiveUtilities` folder into your native Fusion Scripts directory:
   * **Windows:** `%appdata%\Autodesk\Autodesk Fusion 360\API\Addins`
   * **Mac:** `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Addins`
3. **Open Fusion:** Press `Shift + S` to open the **Scripts and Add-Ins** dialog.
4. **Run the Script:** Make sure the **Add-ins** filter checkbox is checked. You should see **LiveUtilities** in the list of add-ins. You may want to check the 'Run on startup' option so it automatically runs when Fusion starts. Click the **Run** icon to execute the add-in.

#### Option 2: Install in a Custom Directory
1. **Download:** Download the source code as a ZIP file and extract the `LiveUtilities` folder.
2. **Organize:** Create a dedicated folder on your computer for your Fusion tools (e.g., `Documents\Fusion_Tools`) and move the `LiveUtilities` folder inside it.
3. **Open Fusion:** Press `Shift + S` to open the **Scripts and Add-Ins** dialog.
4. **Add the Add-in:** Click the grey **"+"** icon next to the search box at the top of the dialog and select **Script or add-in from device**.
5. **Locate:** Navigate to your custom folder, select the `LiveUtilities` folder, and click **Select Folder**.
6. **Run the Add-in:** Make sure the **Add-ins** filter checkbox is checked. You should now see **LiveUtilities** listed. You may want to check the 'Run on startup' option so it automatically runs when Fusion starts. Click the **Run** icon to execute the add-in.

## Using LiveUtilities

### The Global Interface

Clicking the Live Utilities button opens a persistent palette docked to the right side of your Fusion workspace. 
* **Tabbed Navigation:** Seamlessly switch between Parameters, Config, Changelog, and Scripts.
* **Theme Toggle:** Switch between multiple developer-friendly themes using the dropdown in the header.
* **Auto-Sync & Global Refresh:** The palette automatically refreshes whenever you switch to a different active document. You can also manually hit the **↻** button in the header to rescan the model at any time.

---

### Tab 1: Live Parameters
Keep your parameters docked on the side while you design. Tweak dimensions and see your model update instantly without closing windows.

* **Live Editing:** Type a new value or expression into any input box and press **Enter** (or click away) to apply it immediately. The expression fields auto-expand dynamically.
* **Search & Filter:** Instantly filter your parameter list by name using the search bar, or toggle the **★ Favs Only** switch.
* **Split Categorization:** Clearly separates "User Parameters" from tracked "Model Parameters."
* **Creation:** Expand the "Add Parameter" section to create new ones on the fly. *(Note: Text parameters must be enclosed in single quotes, e.g., `'MyText'`)*.
* **Rename & Edit Comments:** Click the **Pencil (✎)** icon next to a parameter to safely rename it or update its comment.
* **The "Orphaned Parameter" Safety Net:** LiveUtilities automatically tracks any renamed Model Parameter. Even if you unfavorite it, it stays pinned in your LiveUtilities sidebar under "Model Parameters."

---

### Tab 2: Live Config
The missing "Configuration Manager" for Fusion. Save specific combinations of parameters and feature states (Suppressed/Unsuppressed) as named Snapshots.

* **Snapshots:** Once you have your parameters and toggles set exactly how you like them, type a name and click **Save State**. Switch between snapshots with a single click.
* **Auto-Detect & Dirty Tracking:** The active configuration glows green, turns red if modified, and automatically recognizes if you've manually matched a different saved snapshot.
* **Tracked Features (The `CFG_` Magic):** Want to toggle timeline features on and off? Rename a timeline feature or group to start with `CFG_` (e.g., `CFG_Holes`). Click Global Refresh (**↻**). It will appear in the palette!
* **Data Locality:** Snapshots are stored as attributes *inside* the Fusion design file. If you share the file, the configurations travel with it.

---

### Tab 3: Changelog & Utilities
A dedicated space to log your thoughts, decisions, and milestones. Because the logs are stored inside the Fusion file's attributes, the history travels with the design.

* **The Input Palette:** Type your notes here. Checking "Autosave Design" will force a new Fusion version when saving the entry.
* **Milestones and Utilities:**
    * **Batch Export Configs:** Export every saved configuration state as STEP, STL, and 3MF files in one batch.
    * **Create Milestone:** Archives the current active log into a history block and starts a fresh active log.
* **The Sidecar Dashboard:** Click **📂 OPEN LOG DASHBOARD** to launch a "Live View" of your history in your web browser. Drag it out as a floating window! It auto-refreshes as you type in Fusion.

---

### Tab 4: Scripts (Macro Board)
A global launcher for your favorite standalone Python scripts. 

* **Link Scripts:** Open the collapsible "Script Manager" and click **➕ Link New Script**. The Smart Directory Picker will offer to jump you directly to your personal Scripts folder, Add-ins folder, or Fusion's native Sample Scripts folder.
* **Launch:** Click any linked script in the main list to instantly execute it without having to open Fusion's "Scripts and Add-Ins" dialog. 
* **Persistence:** Your linked macros are saved to a global registry, so they are always available no matter what design you are working on.

---

## 🧰 Companion Tool: AttributeNukerPlus
If you ever need to surgically clean up hidden legacy JSON attributes from your Fusion files, check out my standalone companion utility, **AttributeNukerPlus**.
👉 **[Download AttributeNukerPlus Here](https://github.com/edjohnson100/AttributeNukerPlus)**

---

## Tech Stack

For the fellow coders and makers out there, here is how LiveUtilities was built:
* **Language:** Python (Fusion API)
* **Interface:** HTML5 / CSS3 / Vanilla JavaScript (running in a Fusion Palette)
* **Data Storage:** Custom JSON payloads stored in `Design.attributes`. The Macro registry is stored locally via standard Python `json` handlers.
* **Communication:** Asynchronous JSON payload routing via `adsk.core.HTMLEventHandler`.
* **Dynamic Import:** `importlib.util` is utilized to safely load and execute external Python modules dynamically.

## Acknowledgements & Credits

* **Developer:** Ed Johnson ([Making With An EdJ](https://www.youtube.com/@makingwithanedj))
* **AI Assistance:** Developed with coding assistance from Google's Gemini 3.1 Pro model.
* **Icons:** "Lucy in the Sidecar" artwork generated via [Artistly](https://artistly.ai/) and enhanced with Nano Banana 2.
* **Lucy (The Cavachon Puppy):**
  ***Chief Wellness Officer & Director of Mandatory Breaks***
* **License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.

---

## Support the Maker (and Lucy!)

I develop these tools to improve my own parametric workflows and love sharing them with the community. If you find LiveUtilities useful and want to say thanks, feel free to **[buy Lucy a dog treat on Ko-fi](https://ko-fi.com/makingwithanedj)**! 

***

*Happy Making!*
*— EdJ*