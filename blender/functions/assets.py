IMPORT_ASSET_FUNCTION = '''
def import_asset(filepath, name=None, location=(0, 0, 0), collection_name=None):
    """Import 3D asset into the scene
    
    Args:
        filepath: Path to the 3D asset file
        name: Optional name for the imported object
        location: Initial location (x, y, z)
        collection_name: Optional collection to add object to
    
    Returns:
        The imported object
    """
    import bpy
    import os
    
    # Check if file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Asset file not found: {filepath}")
    
    # Store current selection
    previous_selection = list(bpy.context.selected_objects)
    
    # Determine file type and import accordingly
    file_ext = filepath.lower().split('.')[-1]
    
    try:
        if file_ext == 'fbx':
            bpy.ops.import_scene.fbx(filepath=filepath)
        elif file_ext == 'obj':
            bpy.ops.import_scene.obj(filepath=filepath)
        elif file_ext in ['glb', 'gltf']:
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif file_ext == 'dae':
            bpy.ops.wm.collada_import(filepath=filepath)
        elif file_ext == 'abc':
            bpy.ops.wm.alembic_import(filepath=filepath)
        else:
            raise ValueError(f"Unsupported file format: .{file_ext}")
    except Exception as e:
        raise RuntimeError(f"Failed to import asset: {str(e)}")
    
    # Get newly imported objects
    imported_objects = [obj for obj in bpy.context.selected_objects 
                       if obj not in previous_selection]
    
    if not imported_objects:
        raise RuntimeError("No objects were imported")
    
    # Get the main imported object (usually the parent)
    imported_obj = imported_objects[0]
    if len(imported_objects) > 1:
        # Find root object (one without parent in the imported set)
        for obj in imported_objects:
            if obj.parent not in imported_objects:
                imported_obj = obj
                break
    
    # Rename if specified
    if name:
        imported_obj.name = name
    
    # Set location
    imported_obj.location = location
    
    # Add to collection if specified
    if collection_name:
        # Create collection if it doesn't exist
        if collection_name not in bpy.data.collections:
            new_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(new_collection)
        
        # Move to collection
        collection = bpy.data.collections[collection_name]
        for obj in imported_objects:
            for coll in obj.users_collection:
                coll.objects.unlink(obj)
            collection.objects.link(obj)
    
    return imported_obj
'''

SCALE_ASSET_FUNCTION = '''
def scale_asset(obj, target_size=None, target_height=None, uniform=True):
    """Scale asset to target dimensions
    
    Args:
        obj: The object to scale
        target_size: Target size as (x, y, z) tuple
        target_height: Target height (z dimension)
        uniform: Whether to maintain aspect ratio
    
    Returns:
        The scaled object
    """
    import bpy
    from mathutils import Vector
    
    if obj is None:
        raise ValueError("Object cannot be None")
    
    # Update mesh data
    if hasattr(obj, 'data') and hasattr(obj.data, 'update'):
        obj.data.update()
    
    # Get current dimensions
    current_dims = obj.dimensions.copy()
    
    if all(d == 0 for d in current_dims):
        raise ValueError("Object has zero dimensions")
    
    # Calculate scale factor
    if target_size:
        if uniform:
            # Use the largest scale factor to maintain proportions
            scale_factors = [target_size[i] / current_dims[i] 
                           for i in range(3) if current_dims[i] > 0]
            scale_factor = min(scale_factors) if scale_factors else 1.0
            obj.scale = (scale_factor, scale_factor, scale_factor)
        else:
            # Non-uniform scaling
            obj.scale = tuple(target_size[i] / current_dims[i] 
                            if current_dims[i] > 0 else 1.0 
                            for i in range(3))
    
    elif target_height:
        if current_dims.z > 0:
            scale_factor = target_height / current_dims.z
            if uniform:
                obj.scale = (scale_factor, scale_factor, scale_factor)
            else:
                obj.scale.z = scale_factor
    
    # Apply scale
    bpy.context.view_layer.update()
    
    return obj
'''

ROTATE_ASSET_FUNCTION = '''
def rotate_asset(obj, rotation=None, target_point=None, face_direction=None):
    """Rotate asset to specified orientation
    
    Args:
        obj: The object to rotate
        rotation: Rotation as (x, y, z) Euler angles in radians
        target_point: Point to face towards
        face_direction: Direction vector to align with
    
    Returns:
        The rotated object
    """
    import bpy
    import math
    from mathutils import Vector, Matrix
    
    if obj is None:
        raise ValueError("Object cannot be None")
    
    if rotation:
        # Direct rotation
        obj.rotation_euler = rotation
    
    elif target_point:
        # Face towards target point
        obj_loc = Vector(obj.location)
        target_loc = Vector(target_point)
        
        # Calculate direction vector
        direction = target_loc - obj_loc
        
        if direction.length > 0:
            # Calculate rotation to face target
            direction.normalize()
            
            # Default forward is -Y
            rot_quat = direction.to_track_quat('-Y', 'Z')
            obj.rotation_euler = rot_quat.to_euler()
    
    elif face_direction:
        # Align with direction vector
        direction = Vector(face_direction).normalized()
        
        # Calculate rotation quaternion
        rot_quat = direction.to_track_quat('-Y', 'Z')
        obj.rotation_euler = rot_quat.to_euler()
    
    # Update scene
    bpy.context.view_layer.update()
    
    return obj
'''

POSITION_ASSET_FUNCTION = '''
def position_asset(obj, location=None, align_to_ground=False, offset=(0, 0, 0)):
    """Position asset at specified location with options
    
    Args:
        obj: The object to position
        location: Target location (x, y, z)
        align_to_ground: Whether to align bottom to z=0
        offset: Additional offset from target location
    
    Returns:
        The positioned object
    """
    import bpy
    from mathutils import Vector
    
    if obj is None:
        raise ValueError("Object cannot be None")
    
    # Set base location
    if location:
        obj.location = Vector(location)
    
    # Align to ground if requested
    if align_to_ground:
        # Calculate bounding box in world space
        bbox_corners = [obj.matrix_world @ Vector(corner) 
                       for corner in obj.bound_box]
        
        # Find minimum Z value
        min_z = min(corner.z for corner in bbox_corners)
        
        # Adjust location to place object on ground
        obj.location.z -= min_z
    
    # Apply offset
    obj.location += Vector(offset)
    
    # Update scene
    bpy.context.view_layer.update()
    
    return obj
'''

APPLY_MATERIAL_FUNCTION = '''
def apply_material(obj, material_name=None, color=None, metallic=0.0, roughness=0.5):
    """Apply or create material for object
    
    Args:
        obj: The object to apply material to
        material_name: Name of existing material or new material
        color: RGB color tuple (0-1 range) or None
        metallic: Metallic value (0-1)
        roughness: Roughness value (0-1)
    
    Returns:
        The applied material
    """
    import bpy
    
    if obj is None:
        raise ValueError("Object cannot be None")
    
    # Ensure object can have materials
    if not hasattr(obj.data, 'materials'):
        raise ValueError("Object does not support materials")
    
    # Get or create material
    if material_name and material_name in bpy.data.materials:
        mat = bpy.data.materials[material_name]
    else:
        mat = bpy.data.materials.new(name=material_name or f"{obj.name}_Material")
        mat.use_nodes = True
    
    # Set up material nodes
    if mat.use_nodes:
        nodes = mat.node_tree.nodes
        
        # Get principled BSDF
        bsdf = nodes.get("Principled BSDF")
        if not bsdf:
            # Clear default nodes and create new
            nodes.clear()
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            output = nodes.new(type='ShaderNodeOutputMaterial')
            mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        # Set color
        if color:
            if len(color) == 3:
                color = (*color, 1.0)  # Add alpha
            bsdf.inputs['Base Color'].default_value = color
        
        # Set metallic and roughness
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
    
    # Apply material to object
    if obj.data.materials:
        # Replace first material
        obj.data.materials[0] = mat
    else:
        # Add new material
        obj.data.materials.append(mat)
    
    return mat
'''