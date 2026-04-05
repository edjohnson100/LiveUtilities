# LiveUtilities for Autodesk Fusion

**Version:** 1.3.1  
**Author:** Ed Johnson (Making With An EdJ)

LiveUtilities is an all-in-one HTML palette add-in for Autodesk Fusion that supercharges your parametric modeling workflow. It consolidates live parameter management, state-based configuration snapshots, automated changelog tracking, and batch exporting into a single, clean interface.

<img src="LiveUtilitiesAppIcon.png" width="300">

## Introduction: The "Why" and "What"

We’ve all been there:
* You are tweaking a Fusion design for a 3D print. You open `Modify > Change Parameters`. You change a value. You hit Enter. The modal box closes. You check the fit. It’s wrong. You open the box again... **Lather. Rinse. Repeat.**
* You open a Fusion design you haven't touched in six months named `MyWidget_Final_v42`. You stare at the browser tree and wonder: *"Why did I add that chamfer? Is this actually the final version?"*

Fusion’s native dialogs are functional, but they are often modal (blocking your view) and lack the space for saving iterative states or detailed historical context. 

**LiveUtilities** solves this by combining three powerful tools—LiveParameters, LiveConfig, and Changelog Sidecar—into a single, modeless HTML palette that docks right inside Fusion. Instead of constantly opening and closing native dialogs, you have a persistent, tabbed interface to manage your design's math, states, and history in real-time.

---
## ✨ What's New in v1.3.1

* **Expanded Theme Engine:** We ditched the basic Light/Dark switch for a persistent, multi-theme selector. You can now customize your LiveUtilities palette with developer-favorite color profiles including Ocean Blue, Hacker Green, Warm Sepia, Solarized (Light & Dark), and Gruvbox Light.

* **Persistent UI Memory:** Your selected theme is now saved directly to your local Fusion workspace cache, ensuring the add-in automatically loads your preferred layout every time you boot up.

* **Auto-Sorting UI:** Parameters and Configuration Snapshots now automatically sort themselves alphabetically (A-Z) in the palette, making it much easier to quickly navigate and find what you need in complex designs.

---
## ✨ What's New in v1.3.0

* **Config Auto-Detect & "Dirty" States:** The Config tab is now context-aware! The active snapshot highlights in green. If you tweak a parameter, it instantly turns red and flags as "(Modified)". Even better, if you manually adjust parameters to match a different saved state, the add-in automatically detects the match and highlights that configuration.
* **Batch Config Export:** A new "Milestones and Utilities" section in the Changelog tab lets you step through every saved configuration and automatically export them as STEP, STL, and 3MF files to a folder of your choice, complete with a native progress dialog.
* **Rename Snapshots:** Added a quick-edit pencil icon to rename configuration snapshots without having to delete and recreate them.
* **The "Orphaned Parameter" Safety Net:** Have you ever renamed a sketch dimension (e.g., `SlotDepth=15`) on the fly, only to accidentally uncheck its "favorite" star later? Normally, Fusion drops it from the autocomplete index and buries it. LiveUtilities now automatically tracks **any** renamed Model Parameter. Even if you unfavorite it or delete the sketch it was attached to, the parameter stays pinned in your LiveUtilities sidebar under "Model Parameters." You can click the star in the UI to instantly register it back into Fusion's type-ahead index!
* **Bulletproof Data Handling:** Safely use dimensional characters (like `1/4" Birch`) in your parameter comments and snapshot names without breaking the backend database.

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
* **Tabbed Navigation:** Seamlessly switch between Parameters, Config, and Changelog tools.
* **Theme Toggle:** Switch between Light and Dark mode using the toggle in the header to match your Fusion UI.
* **Auto-Sync & Global Refresh:** The palette automatically refreshes whenever you switch to a different active document. You can also manually hit the **↻** button in the header to rescan the model at any time.

---

### Tab 1: Live Parameters
Keep your parameters docked on the side while you design. Tweak dimensions and see your model update instantly without closing windows.

* **Live Editing:** Type a new value or expression into any input box and press **Enter** (or click away) to apply it immediately. The expression fields auto-expand dynamically as you resize the palette for long formulas.
* **Search & Filter:** Instantly filter your parameter list by name using the search bar, or toggle the **★ Favs Only** switch to hide everything except your favorited parameters.
* **Split Categorization:** Clearly separates "User Parameters" from tracked "Model Parameters."
* **Creation:** Expand the "Add Parameter" section to create new ones on the fly. Supports Name, Unit (dropdown + custom), Expression, and Comments. *(Note: Text parameters must be enclosed in single quotes, e.g., `'MyText'`)*.
* **Rename & Edit Comments:** Click the **Pencil (✎)** icon next to a parameter to safely rename it or update its comment.
* **Delete:** Click the **X** icon to remove a parameter. The add-in will prevent deletion if the parameter is currently in use by the model.
* **Safety Interlock:** To prevent data loss, edits are blocked while native Fusion commands (like Extrude, Fillet, or Sketch tools) are actively running. If you get an error, click the Fusion Canvas and press **ESC** to drop the active tool.

---

### Tab 2: Live Config
The missing "Configuration Manager" for Fusion. Save specific combinations of parameters and feature states (Suppressed/Unsuppressed) as named Snapshots, acting as a "Poor Man's" configuration tool.

* **Snapshots:** Once you have your parameters and toggles set exactly how you like them, type a name (e.g., "Printer_A_Settings") and click **Save State**. Switch between snapshots with a single click.
* **Auto-Detect & Dirty Tracking:** The add-in actively monitors your design. The active configuration glows green, turns red if modified, and automatically recognizes if you've manually matched a different saved snapshot.
* **Manage:** Use the **✎ (Rename)** icon to quickly update a snapshot's name, the **💾 (Update)** button to overwrite it with the current screen state, or the **🗑️ (Delete)** button to remove it.
* **Tracked Features (The `CFG_` Magic):** Want to toggle timeline features on and off?
    1. In the Fusion timeline, find a feature or group (Extrude, Fillet, Component Group).
    2. Rename it to start with `CFG_` (e.g., `CFG_Holes`).
    3. Click the Global Refresh (**↻**) button.
    4. You will now see a toggle switch for that feature in the palette, and its state will be saved in your Snapshots!
* **Data Locality:** Snapshots are stored as attributes *inside* the Fusion design file. If you share the file, the configurations travel with it.

> **Sample File:** Download `Sink_Strainer_Live_Config_Demo.f3d` from the [Releases > Assets](https://github.com/edjohnson100/LiveConfig/releases) section to test drive pre-configured snapshots and `CFG_` timeline groups.

---

### Tab 3: Changelog & Utilities
A dedicated space to log your thoughts, decisions, and milestones. Because the logs are stored inside the Fusion file's attributes, the history travels with the design.

* **The Input Palette:**
    * **New Entry:** Type your notes here. Be verbose! Explain *why* you are making changes.
    * **Autosave Design:** Checked by default. Adding an entry will automatically save the Fusion design (creating a new version) to ensure the log is permanently attached. Uncheck to log a note for the current session without versioning immediately.
* **Milestones and Utilities:**
    * **Batch Export Configs:** Select a folder and automatically export every saved configuration state as STEP, STL, and 3MF files in one batch (includes a native Fusion progress bar).
    * **Create Milestone:** Reached a major turning point (e.g., "Prototype 1 Complete")? This archives the current active log into a history block and starts a fresh active log.
    * **Export:** Saves your entire history (Active + Milestones) to a `.txt` file on your computer.
* **The Sidecar Dashboard:** Click **📂 OPEN LOG DASHBOARD** to launch a "Live View" of your history in your web browser.
    * *Pro Tip:* Drag the browser tab out to create a separate floating window. Resize it into a narrow "Sidecar" next to your Fusion window or move it to a second monitor.
    * *Auto-Refresh & Smart Scroll:* As you add entries in Fusion, the dashboard updates automatically and remembers your scroll position. Adjust the sync interval via the slider at the top of the dashboard.

---

## 🧰 Companion Tool: AttributeNukerPlus
If you ever need to surgically clean up hidden legacy JSON attributes from your Fusion files (especially useful when uninstalling old add-ins or resetting corrupted metadata), check out my standalone companion utility, **AttributeNukerPlus**. It provides a safe, readable table interface to selectively delete keys or nuke entire attributes.
👉 **[Download AttributeNukerPlus Here](https://github.com/edjohnson100/AttributeNukerPlus)**

---

## Tech Stack

For the fellow coders and makers out there, here is how LiveUtilities was built:
* **Language:** Python (Fusion API)
* **Interface:** HTML5 / CSS3 / Vanilla JavaScript (running in a Fusion Palette)
* **Data Storage:** Custom JSON payloads stored in `Design.attributes` on the Root Component of the active design.
* **Communication:** Asynchronous JSON payload routing via `adsk.core.HTMLEventHandler`.
* **Dashboard Engine:** A custom generator that writes a localized, self-refreshing HTML file to the user's temporary directory, bypassing standard browser security restrictions for a seamless local experience.

## Acknowledgements & Credits

* **Developer:** Ed Johnson ([Making With An EdJ](https://www.youtube.com/@makingwithanedj))
* **AI Assistance:** Developed with coding assistance from Google's Gemini 3.1 Pro model.
* **Icons:** "Lucy in the Sidecar" artwork generated via [Artistly](https://artistly.ai/) and enhanced with Nano Banana 2.
* **Lucy (The Cavachon Puppy):**
  ***Chief Wellness Officer & Director of Mandatory Breaks***
  * Thank you for ensuring I maintained healthy circulation and preventing Repetitive Strain Injury one fetch session at a time by interrupting my deep coding sessions.
* **License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.

---

## Support the Maker (and Lucy!)

I develop these tools to improve my own parametric workflows and love sharing them with the community. If you find LiveUtilities useful and want to say thanks, feel free to **[buy Lucy a dog treat on Ko-fi](https://ko-fi.com/makingwithanedj)**! This is completely optional and supports my Chief Wellness Officer in maintaining mandatory play breaks. Your appreciation and feedback are more than enough.

***

*Happy Making!*
*— EdJ*