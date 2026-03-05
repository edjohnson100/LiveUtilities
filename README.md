# LiveUtilities
**A unified, persistent palette for real-time management of User Parameters, Configuration Snapshots, and Design Changelogs for Autodesk Fusion.**

<img src="LiveUtilitiesAppIcon.png" width="300">

## Introduction: The "Why" and "What"

We’ve all been there:
* You are tweaking a Fusion design for a 3D print. You open `Modify > Change Parameters`. You change a value. You hit Enter. The modal box closes. You check the fit. It’s wrong. You open the box again... **Lather. Rinse. Repeat.**
* You open a Fusion design you haven't touched in six months named `MyWidget_Final_v42`. You stare at the browser tree and wonder: *"Why did I add that chamfer? Is this actually the final version?"*

Fusion’s native dialogs are functional, but they are often modal (blocking your view) and lack the space for saving iterative states or detailed historical context. 

**LiveUtilities** solves this by combining three powerful tools—LiveParameters, LiveConfig, and Changelog Sidecar—into a single, modeless HTML palette that docks right inside Fusion. Instead of constantly opening and closing native dialogs, you have a persistent, tabbed interface to manage your design's math, states, and history in real-time.

## Installation

### Method: Manual Installation (Scripts & Add-Ins)
Currently, this add-in requires a quick manual installation. 

1. Download the source code as a ZIP file and extract the `LiveUtilities` folder.
2. Move the entire `LiveUtilities` folder into your Fusion Add-Ins directory:
   * **Windows:** `%appdata%\Autodesk\Autodesk Fusion 360\API\AddIns`
   * **Mac:** `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns`
3. Open Fusion and press `Shift + S` to open the **Scripts and Add-Ins** dialog.
4. Click the **Add-Ins** tab at the top.
5. Click the green **"+"** icon next to "My Add-Ins" and select the `LiveUtilities` folder you just moved.
6. Select `LiveUtilities` from the list, check **"Run on Startup"** (optional), and click **Run**.
7. You will now find the **Live Utilities** button in the **Solid > Modify** panel.

## Using LiveUtilities

### The Global Interface
Clicking the Live Utilities button opens a persistent palette docked to the right side of your Fusion workspace. 
* **Tabbed Navigation:** Seamlessly switch between Parameters, Config, and Changelog tools.
* **Theme Toggle:** Switch between Light and Dark mode using the toggle in the header to match your Fusion UI.
* **Auto-Sync & Global Refresh:** The palette automatically refreshes whenever you switch to a different active document. You can also manually hit the **↻** button in the header to rescan the model at any time.

---

### Tab 1: Live Parameters
Keep your parameters docked on the side while you design. Tweak dimensions and see your model update instantly without closing windows.

* **Live Editing:** Type a new value or expression into any input box and press **Enter** (or click away) to apply it immediately.
* **Search & Filter:** Instantly filter your parameter list by name using the search bar, or toggle the **★ Favs Only** switch to hide everything except your favorited parameters.
* **Creation:** Expand the "Add Parameter" section to create new ones on the fly. Supports Name, Unit (dropdown + custom), Expression, and Comments. *(Note: Text parameters must be enclosed in single quotes, e.g., `'MyText'`)*.
* **Rename & Edit Comments:** Click the **Pencil (✎)** icon next to a parameter to safely rename it or update its comment.
* **Delete:** Click the **X** icon to remove a parameter. The add-in will prevent deletion if the parameter is currently in use by the model.
* **Safety Interlock:** To prevent data loss, edits are blocked while native Fusion commands (like Extrude, Fillet, or Sketch tools) are actively running. If you get an error, click the Fusion Canvas and press **ESC** to drop the active tool.

---

### Tab 2: Live Config
The missing "Configuration Manager" for Fusion. Save specific combinations of parameters and feature states (Suppressed/Unsuppressed) as named Snapshots, acting as a "Poor Man's" configuration tool.

* **Snapshots:** Once you have your parameters and toggles set exactly how you like them, type a name (e.g., "Printer_A_Settings") and click **Save State**. Switch between snapshots with a single click.
* **Manage:** Use the **💾 (Update)** button to overwrite a snapshot with the current screen state, or the **🗑️ (Delete)** button to remove it.
* **Tracked Features (The `CFG_` Magic):** Want to toggle timeline features on and off?
    1. In the Fusion timeline, find a feature or group (Extrude, Fillet, Component Group).
    2. Rename it to start with `CFG_` (e.g., `CFG_Holes`).
    3. Click the Global Refresh (**↻**) button.
    4. You will now see a toggle switch for that feature in the palette, and its state will be saved in your Snapshots!
* **Data Locality:** Snapshots are stored as attributes *inside* the Fusion design file. If you share the file, the configurations travel with it.

> **Sample File:** Download `Sink_Strainer_Live_Config_Demo.f3d` from the [Releases > Assets](https://github.com/edjohnson100/LiveConfig/releases) section to test drive pre-configured snapshots and `CFG_` timeline groups.

---

### Tab 3: Changelog Sidecar
A dedicated space to log your thoughts, decisions, and milestones. Because the logs are stored inside the Fusion file's attributes, the history travels with the design.

* **The Input Palette:**
    * **New Entry:** Type your notes here. Be verbose! Explain *why* you are making changes.
    * **Autosave Design:** Checked by default. Adding an entry will automatically save the Fusion design (creating a new version) to ensure the log is permanently attached. Uncheck to log a note for the current session without versioning immediately.
* **Utilities:**
    * **Create Milestone:** Reached a major turning point (e.g., "Prototype 1 Complete")? This archives the current active log into a history block and starts a fresh active log.
    * **Export:** Saves your entire history (Active + Milestones) to a `.txt` file on your computer.
* **The Sidecar Dashboard:** Click **📂 OPEN LOG DASHBOARD** to launch a "Live View" of your history in your web browser.
    * *Pro Tip:* Drag the browser tab out to create a separate floating window. Resize it into a narrow "Sidecar" next to your Fusion window or move it to a second monitor.
    * *Auto-Refresh & Smart Scroll:* As you add entries in Fusion, the dashboard updates automatically and remembers your scroll position. Adjust the sync interval via the slider at the top of the dashboard.

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
* **Icons:** "Lucy in the Sidecar" artwork generated via [Artistly](https://artistly.ai/) and enhamced with Gemini Nano Banana.
* **Lucy (The Cavachon Puppy):**
  ***Chief Wellness Officer & Director of Mandatory Breaks***
  * Thank you for ensuring I maintained healthy circulation and preventing Repetitive Strain Injury one fetch session at a time by interrupting my deep coding sessions.
* **License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.

***

*Happy Making!*
*— EdJ*
