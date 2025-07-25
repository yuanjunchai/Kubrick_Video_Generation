# Camera setup and animation functions for Blender scenes
# Provides various camera movements and cinematic shots

SETUP_CAMERA_FUNCTION = '''
def setup_camera(location=(7, -7, 5), target=(0, 0, 0), lens=50, clip_start=0.1, clip_end=100):
    """Setup camera with specified parameters and target.
    
    Args:
        location (tuple): Camera location (x, y, z)
        target (tuple): Point for camera to look at (x, y, z)
        lens (float): Focal length in mm
        clip_start (float): Near clipping distance
        clip_end (float): Far clipping distance
        
    Returns:
        bpy.types.Object: The camera object
    """
    import bpy
    import bmesh
    from mathutils import Vector
    
    # Delete existing camera if present
    if bpy.context.scene.camera:
        bpy.data.objects.remove(bpy.context.scene.camera, do_unlink=True)
    
    # Add new camera
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.active_object
    camera.name = "Main_Camera"
    
    # Set camera as active
    bpy.context.scene.camera = camera
    
    # Configure camera settings
    camera.data.lens = lens
    camera.data.clip_start = clip_start
    camera.data.clip_end = clip_end
    
    # Point camera at target
    direction = Vector(target) - Vector(location)
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    return camera
'''

ANIMATE_ORBIT_CAMERA_FUNCTION = '''
def animate_orbit_camera(target_object, radius=5, height=3, start_frame=1, 
                        end_frame=120, start_angle=0, full_rotation=True):
    """Animate camera orbiting around a target object.
    
    Args:
        target_object (bpy.types.Object): Object to orbit around
        radius (float): Orbit radius
        height (float): Camera height above target
        start_frame (int): Starting frame
        end_frame (int): Ending frame
        start_angle (float): Starting angle in degrees
        full_rotation (bool): Whether to complete full 360-degree rotation
        
    Returns:
        bpy.types.Object: The animated camera
    """
    import bpy
    import math
    from mathutils import Vector
    
    if target_object is None:
        raise ValueError("Target object cannot be None")
    
    # Get or create camera
    camera = bpy.context.scene.camera
    if not camera:
        camera = setup_camera()
    
    # Clear existing animation
    camera.animation_data_clear()
    
    target_loc = Vector(target_object.location)
    frame_count = end_frame - start_frame + 1
    
    # Calculate angle increment
    if full_rotation:
        angle_increment = 360.0 / frame_count
    else:
        angle_increment = 180.0 / frame_count
    
    # Set keyframes for orbit
    for i, frame in enumerate(range(start_frame, end_frame + 1)):
        bpy.context.scene.frame_set(frame)
        
        # Calculate orbit position
        angle = math.radians(start_angle + (i * angle_increment))
        x = target_loc.x + radius * math.cos(angle)
        y = target_loc.y + radius * math.sin(angle)
        z = target_loc.z + height
        
        # Set camera position
        camera.location = (x, y, z)
        camera.keyframe_insert(data_path="location", frame=frame)
        
        # Point camera at target
        direction = target_loc - Vector(camera.location)
        camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    # Set interpolation to linear for smooth motion
    if camera.animation_data and camera.animation_data.action:
        for fcurve in camera.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'LINEAR'
    
    return camera
'''

ANIMATE_DOLLY_CAMERA_FUNCTION = '''
def animate_dolly_camera(start_location, end_location, target_object=None,
                        start_frame=1, end_frame=120, smooth_motion=True):
    """Animate camera moving from start to end location (dolly shot).
    
    Args:
        start_location (tuple): Starting camera position
        end_location (tuple): Ending camera position
        target_object (bpy.types.Object, optional): Object to keep in focus
        start_frame (int): Starting frame
        end_frame (int): Ending frame
        smooth_motion (bool): Whether to use smooth interpolation
        
    Returns:
        bpy.types.Object: The animated camera
    """
    import bpy
    from mathutils import Vector
    
    # Get or create camera
    camera = bpy.context.scene.camera
    if not camera:
        camera = setup_camera()
    
    # Clear existing animation
    camera.animation_data_clear()
    
    # Set start position
    bpy.context.scene.frame_set(start_frame)
    camera.location = Vector(start_location)
    camera.keyframe_insert(data_path="location", frame=start_frame)
    
    # Set end position
    bpy.context.scene.frame_set(end_frame)
    camera.location = Vector(end_location)
    camera.keyframe_insert(data_path="location", frame=end_frame)
    
    # If target object specified, animate rotation to keep it in frame
    if target_object:
        target_loc = Vector(target_object.location)
        
        # Start rotation
        bpy.context.scene.frame_set(start_frame)
        direction = target_loc - Vector(start_location)
        camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        camera.keyframe_insert(data_path="rotation_euler", frame=start_frame)
        
        # End rotation
        bpy.context.scene.frame_set(end_frame)
        direction = target_loc - Vector(end_location)
        camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        camera.keyframe_insert(data_path="rotation_euler", frame=end_frame)
    
    # Set interpolation mode
    if camera.animation_data and camera.animation_data.action:
        for fcurve in camera.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'BEZIER' if smooth_motion else 'LINEAR'
    
    return camera
'''

ANIMATE_TRACKING_CAMERA_FUNCTION = '''
def animate_tracking_camera(target_object, camera_path=None, start_frame=1, 
                           end_frame=120, smooth_tracking=True):
    """Animate camera tracking a moving object.
    
    Args:
        target_object (bpy.types.Object): Object to track
        camera_path (list, optional): List of camera positions [(x,y,z), ...]
        start_frame (int): Starting frame
        end_frame (int): Ending frame
        smooth_tracking (bool): Whether to use smooth tracking
        
    Returns:
        bpy.types.Object: The tracking camera
    """
    import bpy
    from mathutils import Vector
    
    if target_object is None:
        raise ValueError("Target object cannot be None")
    
    # Get or create camera
    camera = bpy.context.scene.camera
    if not camera:
        camera = setup_camera()
    
    # Clear existing animation
    camera.animation_data_clear()
    
    frame_count = end_frame - start_frame + 1
    
    # If no camera path provided, use current position
    if camera_path is None:
        camera_path = [camera.location] * frame_count
    elif len(camera_path) < frame_count:
        # Extend path by repeating last position
        last_pos = camera_path[-1] if camera_path else camera.location
        camera_path.extend([last_pos] * (frame_count - len(camera_path)))
    
    # Animate camera tracking
    for i, frame in enumerate(range(start_frame, end_frame + 1)):
        bpy.context.scene.frame_set(frame)
        
        # Set camera position if path provided
        if i < len(camera_path):
            camera.location = Vector(camera_path[i])
            camera.keyframe_insert(data_path="location", frame=frame)
        
        # Point camera at target (get target position at this frame)
        target_loc = Vector(target_object.location)
        direction = target_loc - Vector(camera.location)
        camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    # Set interpolation
    if camera.animation_data and camera.animation_data.action:
        for fcurve in camera.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'BEZIER' if smooth_tracking else 'LINEAR'
    
    return camera
'''

ANIMATE_HANDHELD_CAMERA_FUNCTION = '''
def animate_handheld_camera(base_location, target_object=None, start_frame=1,
                           end_frame=120, shake_intensity=0.1, shake_frequency=2.0):
    """Animate camera with handheld shake effect.
    
    Args:
        base_location (tuple): Base camera position
        target_object (bpy.types.Object, optional): Object to focus on
        start_frame (int): Starting frame
        end_frame (int): Ending frame
        shake_intensity (float): Intensity of camera shake
        shake_frequency (float): Frequency of shake oscillation
        
    Returns:
        bpy.types.Object: The handheld camera
    """
    import bpy
    import math
    import random
    from mathutils import Vector
    
    # Get or create camera
    camera = bpy.context.scene.camera
    if not camera:
        camera = setup_camera()
    
    # Clear existing animation
    camera.animation_data_clear()
    
    base_loc = Vector(base_location)
    
    # Animate with shake
    for frame in range(start_frame, end_frame + 1):
        bpy.context.scene.frame_set(frame)
        
        # Calculate shake offset
        time = (frame - start_frame) * shake_frequency / 24.0  # Convert to seconds
        shake_x = shake_intensity * math.sin(time * 5 + random.random())
        shake_y = shake_intensity * math.cos(time * 7 + random.random())
        shake_z = shake_intensity * math.sin(time * 3 + random.random()) * 0.5
        
        # Apply shake to position
        shaky_location = base_loc + Vector((shake_x, shake_y, shake_z))
        camera.location = shaky_location
        camera.keyframe_insert(data_path="location", frame=frame)
        
        # Handle rotation (point at target with slight shake)
        if target_object:
            target_loc = Vector(target_object.location)
            direction = target_loc - shaky_location
            base_rotation = direction.to_track_quat('-Z', 'Y').to_euler()
            
            # Add rotational shake
            shake_rot_x = shake_intensity * 0.5 * math.sin(time * 4 + random.random())
            shake_rot_y = shake_intensity * 0.5 * math.cos(time * 6 + random.random())
            shake_rot_z = shake_intensity * 0.3 * math.sin(time * 8 + random.random())
            
            camera.rotation_euler = (
                base_rotation.x + shake_rot_x,
                base_rotation.y + shake_rot_y,
                base_rotation.z + shake_rot_z
            )
        else:
            # Just add rotational shake to current rotation
            shake_rot_x = shake_intensity * 0.5 * math.sin(time * 4)
            shake_rot_y = shake_intensity * 0.5 * math.cos(time * 6)
            
            camera.rotation_euler = (
                camera.rotation_euler.x + shake_rot_x,
                camera.rotation_euler.y + shake_rot_y,
                camera.rotation_euler.z
            )
        
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    return camera
'''

SETUP_SHOT_COMPOSITION_FUNCTION = '''
def setup_shot_composition(target_object, shot_type="medium", angle="eye_level"):
    """Setup camera for specific shot composition.
    
    Args:
        target_object (bpy.types.Object): Subject of the shot
        shot_type (str): Type of shot (close_up, medium, wide, extreme_wide)
        angle (str): Camera angle (low, eye_level, high, birds_eye)
        
    Returns:
        bpy.types.Object: The positioned camera
    """
    import bpy
    from mathutils import Vector
    
    if target_object is None:
        raise ValueError("Target object cannot be None")
    
    target_loc = Vector(target_object.location)
    target_size = max(target_object.dimensions)
    
    # Shot distance based on type
    distance_multipliers = {
        "extreme_close_up": 0.8,
        "close_up": 1.5,
        "medium": 3.0,
        "wide": 6.0,
        "extreme_wide": 12.0
    }
    distance = target_size * distance_multipliers.get(shot_type, 3.0)
    
    # Height based on angle
    height_offsets = {
        "low": -target_size * 0.5,
        "eye_level": target_size * 0.5,
        "high": target_size * 1.5,
        "birds_eye": target_size * 3.0
    }
    height_offset = height_offsets.get(angle, 0)
    
    # Calculate camera position
    camera_location = (
        target_loc.x - distance,
        target_loc.y - distance * 0.5,
        target_loc.z + height_offset
    )
    
    # Setup camera
    camera = setup_camera(location=camera_location, target=target_loc)
    
    # Adjust focal length based on shot type
    focal_lengths = {
        "extreme_close_up": 85,
        "close_up": 85,
        "medium": 50,
        "wide": 35,
        "extreme_wide": 24
    }
    camera.data.lens = focal_lengths.get(shot_type, 50)
    
    return camera
'''

# Collection of all camera functions
CAMERA_FUNCTIONS = {
    "setup_camera": SETUP_CAMERA_FUNCTION,
    "animate_orbit_camera": ANIMATE_ORBIT_CAMERA_FUNCTION,
    "animate_dolly_camera": ANIMATE_DOLLY_CAMERA_FUNCTION,
    "animate_tracking_camera": ANIMATE_TRACKING_CAMERA_FUNCTION,
    "animate_handheld_camera": ANIMATE_HANDHELD_CAMERA_FUNCTION,
    "setup_shot_composition": SETUP_SHOT_COMPOSITION_FUNCTION,
} 