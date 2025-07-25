# Base function utilities for Blender operations
# These functions provide fundamental utilities for object manipulation

SCALE_ASSET_FUNCTION = '''
def scale_asset_to_real_world_dimensions(asset, desired_z_dim, desired_x_dim=None, desired_y_dim=None,
                                       apply_trans=False, asset_dims=None):
    """Scale a 3D asset to specific real-world dimensions.
    
    Args:
        asset (bpy.types.Object): The 3D asset to be scaled.
        desired_z_dim (float): The desired z-dimension in real-world units.
        desired_x_dim (float, optional): The desired x-dimension in real-world units.
        desired_y_dim (float, optional): The desired y-dimension in real-world units.
        apply_trans (bool): Whether to apply transformation
        asset_dims (tuple, optional): Override asset dimensions
        
    Returns:
        bpy.types.Object: The scaled 3D asset.
    """
    import bpy
    import mathutils
    
    if asset is None:
        raise ValueError("Asset cannot be None")
    
    if asset_dims is None:
        # Get the current dimensions of the asset
        current_dim = asset.dimensions
    else:
        current_dim = asset_dims
    
    # Prevent division by zero
    if current_dim[2] == 0:
        raise ValueError("Asset has zero Z dimension")
    
    # Calculate the scale factors
    scale_z = desired_z_dim / current_dim[2]
    scale_x = scale_z
    scale_y = scale_z
    
    if desired_x_dim is not None and current_dim[0] != 0:
        scale_x = desired_x_dim / current_dim[0]
    if desired_y_dim is not None and current_dim[1] != 0:
        scale_y = desired_y_dim / current_dim[1]
    
    # Calculate the overall scale factor
    scale_factor = mathutils.Vector((scale_x, scale_y, scale_z))
    
    # Scale the asset
    asset.scale = mathutils.Vector(asset.scale) * scale_factor
    
    if apply_trans:
        bpy.context.view_layer.objects.active = asset
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    return asset
'''

ROTATE_ASSET_FUNCTION = '''
def rotate_asset_to_point(asset, facing_vector, target_point):
    """Rotate a 3D asset to face a specific point.
    
    Args:
        asset (bpy.types.Object): The 3D asset to rotate
        facing_vector (Vector): The current facing direction of the asset
        target_point (Vector): The point the asset should face
        
    Returns:
        bpy.types.Object: The rotated asset
    """
    import bpy
    import mathutils
    from mathutils import Vector
    
    if asset is None:
        raise ValueError("Asset cannot be None")
    
    # Calculate direction vector from asset to target
    direction = Vector(target_point) - Vector(asset.location)
    direction.normalize()
    
    # Calculate rotation quaternion
    facing_vec = Vector(facing_vector).normalized()
    rotation_quat = facing_vec.rotation_difference(direction)
    
    # Apply rotation
    asset.rotation_euler = rotation_quat.to_euler()
    
    return asset
'''

POSITION_ASSET_FUNCTION = '''
def position_asset(asset, location=None, relative_to=None, offset=None):
    """Position an asset at a specific location or relative to another object.
    
    Args:
        asset (bpy.types.Object): The asset to position
        location (tuple): Absolute world coordinates (x, y, z)
        relative_to (bpy.types.Object): Object to position relative to
        offset (tuple): Offset from relative_to object (x, y, z)
        
    Returns:
        bpy.types.Object: The positioned asset
    """
    import bpy
    from mathutils import Vector
    
    if asset is None:
        raise ValueError("Asset cannot be None")
    
    if location is not None:
        asset.location = Vector(location)
    elif relative_to is not None:
        base_location = Vector(relative_to.location)
        if offset is not None:
            base_location += Vector(offset)
        asset.location = base_location
    elif offset is not None:
        asset.location = Vector(asset.location) + Vector(offset)
    
    return asset
'''

CLEAR_SCENE_FUNCTION = '''
def clear_scene(keep_camera=True, keep_light=True):
    """Clear all objects from the scene except optionally camera and lights.
    
    Args:
        keep_camera (bool): Whether to keep camera objects
        keep_light (bool): Whether to keep light objects
        
    Returns:
        None
    """
    import bpy
    
    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')
    
    # Select objects to delete
    for obj in bpy.context.scene.objects:
        should_delete = True
        
        if keep_camera and obj.type == 'CAMERA':
            should_delete = False
        elif keep_light and obj.type == 'LIGHT':
            should_delete = False
            
        if should_delete:
            obj.select_set(True)
    
    # Delete selected objects
    bpy.ops.object.delete()
'''

SETUP_RENDER_SETTINGS_FUNCTION = '''
def setup_render_settings(resolution_x=1920, resolution_y=1080, fps=24, 
                         file_format="FFMPEG", codec="H264", samples=128):
    """Setup basic render settings for video output.
    
    Args:
        resolution_x (int): Horizontal resolution
        resolution_y (int): Vertical resolution
        fps (int): Frames per second
        file_format (str): Output file format
        codec (str): Video codec
        samples (int): Render samples for quality
        
    Returns:
        None
    """
    import bpy
    
    scene = bpy.context.scene
    render = scene.render
    
    # Resolution settings
    render.resolution_x = resolution_x
    render.resolution_y = resolution_y
    render.resolution_percentage = 100
    
    # Frame rate
    scene.frame_set(1)
    render.fps = fps
    
    # Output format
    render.image_settings.file_format = file_format
    if file_format == "FFMPEG":
        render.ffmpeg.format = 'MPEG4'
        render.ffmpeg.codec = codec
        render.ffmpeg.constant_rate_factor = 'HIGH'
    
    # Quality settings
    if hasattr(scene, 'cycles'):
        scene.cycles.samples = samples
    
    # Enable motion blur for realism
    render.motion_blur_shutter = 0.5
'''

DUPLICATE_ASSET_FUNCTION = '''
def duplicate_asset(asset, location_offset=(2, 0, 0), name_suffix="_copy"):
    """Duplicate an asset with optional positioning and naming.
    
    Args:
        asset (bpy.types.Object): The asset to duplicate
        location_offset (tuple): Offset for the duplicate's position
        name_suffix (str): Suffix for the duplicate's name
        
    Returns:
        bpy.types.Object: The duplicated asset
    """
    import bpy
    from mathutils import Vector
    
    if asset is None:
        raise ValueError("Asset cannot be None")
    
    # Select the asset
    bpy.ops.object.select_all(action='DESELECT')
    asset.select_set(True)
    bpy.context.view_layer.objects.active = asset
    
    # Duplicate
    bpy.ops.object.duplicate()
    
    # Get the duplicated object
    duplicate = bpy.context.active_object
    
    # Set new name
    duplicate.name = asset.name + name_suffix
    
    # Apply location offset
    duplicate.location = Vector(asset.location) + Vector(location_offset)
    
    return duplicate
'''

# Collection of all base functions
BASE_FUNCTIONS = {
    "scale_asset_to_real_world_dimensions": SCALE_ASSET_FUNCTION,
    "rotate_asset_to_point": ROTATE_ASSET_FUNCTION,
    "position_asset": POSITION_ASSET_FUNCTION,
    "clear_scene": CLEAR_SCENE_FUNCTION,
    "setup_render_settings": SETUP_RENDER_SETTINGS_FUNCTION,
    "duplicate_asset": DUPLICATE_ASSET_FUNCTION,
} 