# Weight Sync Manager Addon (for Blender 3.0+)

**Weight Sync Manager** is a Blender addon that simplifies vertex weight management. It allows users to save, load, and resync vertex group weights in JSON format, ensuring seamless synchronization across projects and Blender sessions.

---

## Features

- **Save Weights**: Export vertex weights for any mesh to a JSON file.
- **Load Weights**: Import weights from a JSON file, with validation to ensure accuracy.
- **Resync Weights**: Automatically resync weights upon file reload or when required.
- **Validation**: Check for vertex count mismatches, weight range, and affected groups.
- **Clear Weight File**: Remove the active weight file and disable syncing.
- **User-Friendly UI**: A dedicated panel in the 3D View Sidebar for managing weights.
- **Error Handling**: Comprehensive checks to ensure smooth operation.

---

## Installation

1. **Download**  
   Download the `weight_sync_manager.py` file from this repository.

2. **Install in Blender**  
   - Open Blender.  
   - Go to `Edit > Preferences > Add-ons`.  
   - Click `Install...`, select the `weight_sync_manager.py` file, and enable it.

3. **Access the Addon**  
   - The addon will now be available in the **3D Viewport Sidebar** under `Tool > Weight Sync Manager`.

---

## Usage Instructions

1. Select a mesh object in the 3D Viewport.
2. Open the **Weight Sync Manager** panel in the Sidebar under `Tool`.
3. Use the following operations:
   - **Save Weights**: Click "Save Weights," select a file location, and save the weights.
   - **Load Weights**: Click "Load Weights," select the JSON file, and import the weights.
   - **Resync Weights**: Click "Resync Weights" to reload weights from the active file.
   - **Clear Weight File**: Click "Clear Weight File" to disable weight syncing.
4. Status updates and validation info will be displayed in the UI.

---

## Requirements

- **Blender Version**: 3.0.0 or later

---

## Known Limitations

- Vertex count mismatches between the mesh and weight file will prevent weight loading.
- JSON weight files must be manually managed; ensure they are not moved or deleted during a session.

---

## Contribution

Contributions are welcome! If you’d like to suggest improvements, report bugs, or add new features:

1. Fork this repository.
2. Create a new branch for your changes.
3. Submit a pull request.

---

## License

This addon is licensed under the **GNU General Public License v3**.
