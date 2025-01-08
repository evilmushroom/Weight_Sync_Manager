import bpy
import json
import os
from bpy.props import StringProperty, BoolProperty
from bpy.app.handlers import persistent

bl_info = {
    "name": "Weight Sync Manager",
    "author": "Assistant",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "category": "Rigging",
}

class WeightSyncSettings(bpy.types.PropertyGroup):
    weight_file: StringProperty(
        name="Weight File",
        description="Path to the weight file",
        default="",
        subtype='FILE_PATH'
    )
    is_active: BoolProperty(
        name="Active",
        description="Whether weight syncing is active",
        default=False
    )

def save_weights(obj, filepath):
    """Save weights for an object to specified file with validation"""
    if not obj or obj.type != 'MESH':
        return "No valid mesh selected"
        
    try:
        weight_data = {
            "object_name": obj.name,
            "vertex_count": len(obj.data.vertices),
            "group_names": [g.name for g in obj.vertex_groups],
            "vertex_groups": {},
        }
        
        # Store vertex group data with validation
        for v in obj.data.vertices:
            v_weights = {}
            # Get all weights for this vertex
            for g in obj.vertex_groups:
                try:
                    weight = g.weight(v.index)
                    if weight > 0.0:  # Only store non-zero weights
                        v_weights[g.name] = weight
                except RuntimeError:
                    # Vertex not in group, skip
                    continue
                    
            # Only store vertices that have weights
            if v_weights:
                weight_data["vertex_groups"][str(v.index)] = v_weights
        
        # Validation step
        validation = {
            "total_vertices_with_weights": len(weight_data["vertex_groups"]),
            "groups_with_weights": set(),
            "max_weight": 0.0,
            "min_weight": 1.0
        }
        
        for v_weights in weight_data["vertex_groups"].values():
            for group, weight in v_weights.items():
                validation["groups_with_weights"].add(group)
                validation["max_weight"] = max(validation["max_weight"], weight)
                validation["min_weight"] = min(validation["min_weight"], weight)
        
        weight_data["validation"] = {
            "vertices_with_weights": validation["total_vertices_with_weights"],
            "groups_with_weights": list(validation["groups_with_weights"]),
            "weight_range": [validation["min_weight"], validation["max_weight"]]
        }
        
        # Save to file with pretty printing for debugging
        with open(filepath, 'w') as f:
            json.dump(weight_data, f, indent=2)
            
        print(f"Weight validation data:")
        print(f"- Vertices with weights: {validation['total_vertices_with_weights']}")
        print(f"- Groups with weights: {validation['groups_with_weights']}")
        print(f"- Weight range: {validation['min_weight']} to {validation['max_weight']}")
        
        return None
    except Exception as e:
        return f"Error saving weights: {str(e)}"

def load_weights(obj, filepath):
    """Load weights for an object from specified file with validation"""
    if not obj or obj.type != 'MESH':
        return "No valid mesh selected"
        
    if not os.path.exists(filepath):
        return f"Weight file not found: {filepath}"
    
    try:
        with open(filepath, 'r') as f:
            weight_data = json.load(f)
        
        # Validation checks
        if len(obj.data.vertices) != weight_data.get("vertex_count"):
            return f"Vertex count mismatch: file has {weight_data['vertex_count']}, mesh has {len(obj.data.vertices)}"
            
        # Clear existing weights
        for vg in obj.vertex_groups:
            obj.vertex_groups.remove(vg)
            
        # Create all vertex groups first
        for group_name in weight_data["group_names"]:
            if group_name not in obj.vertex_groups:
                obj.vertex_groups.new(name=group_name)
        
        # Apply weights with validation
        vertices_affected = 0
        for vertex_idx_str, groups in weight_data["vertex_groups"].items():
            vertex_idx = int(vertex_idx_str)
            if vertex_idx < len(obj.data.vertices):
                for group_name, weight in groups.items():
                    if weight > 0.0:  # Only apply non-zero weights
                        vgroup = obj.vertex_groups[group_name]
                        vgroup.add([vertex_idx], weight, 'REPLACE')
                        vertices_affected += 1
                        
        print(f"Load validation:")
        print(f"- Vertices affected: {vertices_affected}")
        print(f"- Groups created: {len(weight_data['group_names'])}")
                
        return None
    except Exception as e:
        return f"Error loading weights: {str(e)}"

@persistent
def load_post_handler(dummy):
    """Handler to automatically load weights after file load"""
    if not bpy.data.filepath:  # Skip if file hasn't been saved
        return
        
    # Wait for context to be ready
    def do_resync():
        if bpy.context.scene is None:
            return 0.1  # Try again in 0.1 seconds
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.library is not None:
                settings = bpy.context.scene.weight_sync_settings
                if settings.is_active and settings.weight_file:
                    load_weights(obj, settings.weight_file)
        return None
        
    bpy.app.timers.register(do_resync)

class WEIGHTSYNC_OT_save(bpy.types.Operator):
    bl_idname = "weightsync.save"
    bl_label = "Save Weights"
    
    filepath: StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        settings = context.scene.weight_sync_settings
        obj = context.active_object
        
        error = save_weights(obj, self.filepath)
        if error:
            self.report({'ERROR'}, error)
        else:
            settings.weight_file = self.filepath
            settings.is_active = True
            self.report({'INFO'}, f"Weights saved to {self.filepath}")
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.filepath = context.scene.weight_sync_settings.weight_file or "weights.json"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class WEIGHTSYNC_OT_load(bpy.types.Operator):
    bl_idname = "weightsync.load"
    bl_label = "Load Weights"
    
    filepath: StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        settings = context.scene.weight_sync_settings
        obj = context.active_object
        
        error = load_weights(obj, self.filepath)
        if error:
            self.report({'ERROR'}, error)
        else:
            settings.weight_file = self.filepath
            settings.is_active = True
            self.report({'INFO'}, f"Weights loaded from {self.filepath}")
            
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.filepath = context.scene.weight_sync_settings.weight_file or "weights.json"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class WEIGHTSYNC_OT_resync(bpy.types.Operator):
    bl_idname = "weightsync.resync"
    bl_label = "Resync Weights"
    
    def execute(self, context):
        settings = context.scene.weight_sync_settings
        if not settings.is_active or not settings.weight_file:
            self.report({'ERROR'}, "No active weight file")
            return {'FINISHED'}
            
        # Simply load weights from the active file
        obj = context.active_object
        error = load_weights(obj, settings.weight_file)
        
        if error:
            self.report({'ERROR'}, error)
        else:
            self.report({'INFO'}, f"Weights resynced from {settings.weight_file}")
            
        return {'FINISHED'}

class WEIGHTSYNC_OT_clear(bpy.types.Operator):
    bl_idname = "weightsync.clear"
    bl_label = "Clear Weight File"
    
    def execute(self, context):
        settings = context.scene.weight_sync_settings
        settings.weight_file = ""
        settings.is_active = False
        self.report({'INFO'}, "Weight file cleared")
        return {'FINISHED'}

class WEIGHTSYNC_PT_panel(bpy.types.Panel):
    bl_label = "Weight Sync Manager"
    bl_idname = "WEIGHTSYNC_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.weight_sync_settings
        obj = context.active_object
        
        # Object Status
        box = layout.box()
        row = box.row()
        if obj and obj.type == 'MESH':
            row.label(text=f"Object: {obj.name}", icon='MESH_DATA')
            
            # Group info
            if obj.vertex_groups:
                box.label(text=f"Vertex Groups: {len(obj.vertex_groups)}", icon='GROUP_VERTEX')
                # Add validation info
                box.label(text=f"Vertices with weights: {sum(1 for v in obj.data.vertices if v.groups)}")
        else:
            row.label(text="No mesh selected", icon='ERROR')
            layout.enabled = False
            return

        # Weight File Status
        box = layout.box()
        row = box.row(align=True)
        if settings.is_active and settings.weight_file:
            row.label(text="Status: Active", icon='CHECKMARK')
            filename = os.path.basename(settings.weight_file)
            box.label(text=f"File: {filename}", icon='FILE')
        else:
            row.label(text="Status: No file", icon='X')

        # Operations
        col = layout.column(align=True)
        row = col.row(align=True)  # Put save/load side by side
        row.operator(WEIGHTSYNC_OT_save.bl_idname, icon='EXPORT')
        row.operator(WEIGHTSYNC_OT_load.bl_idname, icon='IMPORT')
        
        if settings.is_active:
            row = col.row(align=True)  # Put resync/clear side by side
            row.operator(WEIGHTSYNC_OT_resync.bl_idname, icon='FILE_REFRESH')
            row.operator(WEIGHTSYNC_OT_clear.bl_idname, icon='X')

classes = (
    WeightSyncSettings,
    WEIGHTSYNC_OT_save,
    WEIGHTSYNC_OT_load,
    WEIGHTSYNC_OT_resync,
    WEIGHTSYNC_OT_clear,
    WEIGHTSYNC_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.weight_sync_settings = bpy.props.PointerProperty(type=WeightSyncSettings)
    bpy.app.handlers.load_post.append(load_post_handler)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.weight_sync_settings
    if load_post_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post_handler)

if __name__ == "__main__":
    register()