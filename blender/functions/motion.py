SET_MOTION_FUNCTION = '''
def set_motion(obj, motion_type, start_frame=1, end_frame=120, **kwargs):
    """Set character motion using keyframes
    
    Args:
        obj: The object to animate
        motion_type: Type of motion (walk, run, jump, fly, custom)
        start_frame: Starting frame
        end_frame: Ending frame
        **kwargs: Motion-specific parameters
    
    Returns:
        The animated object
    """
    import bpy
    import math
    from mathutils import Vector
    
    if obj is None:
        raise ValueError("Object cannot be None")
    
    # Clear existing animation data
    obj.animation_data_clear()
    
    # Set frame range
    scene = bpy.context.scene
    scene.frame_start = start_frame
    scene.frame_end = end_frame
    
    if motion_type == "walk":
        # Walking motion
        start_pos = Vector(kwargs.get('start_pos', obj.location))
        end_pos = Vector(kwargs.get('end_pos', (10, 0, 0)))
        speed = kwargs.get('speed', 1.0)
        
        # Set keyframes
        obj.location = start_pos
        obj.keyframe_insert(data_path="location", frame=start_frame)
        
        obj.location = end_pos
        obj.keyframe_insert(data_path="location", frame=end_frame)
        
        # Add slight bobbing motion
        if kwargs.get('add_bobbing', True):
            mid_frame = (start_frame + end_frame) // 2
            obj.location = (start_pos + end_pos) / 2
            obj.location.z += 0.1 * speed
            obj.keyframe_insert(data_path="location", frame=mid_frame)
    
    elif motion_type == "run":
        # Running motion (faster with more bobbing)
        start_pos = Vector(kwargs.get('start_pos', obj.location))
        end_pos = Vector(kwargs.get('end_pos', (15, 0, 0)))
        
        obj.location = start_pos
        obj.keyframe_insert(data_path="location", frame=start_frame)
        
        # Add multiple bobbing keyframes
        num_steps = kwargs.get('num_steps', 8)
        for i in range(1, num_steps):
            progress = i / num_steps
            frame = int(start_frame + progress * (end_frame - start_frame))
            
            obj.location = start_pos.lerp(end_pos, progress)
            # Add bobbing
            if i % 2:
                obj.location.z += 0.2
            obj.keyframe_insert(data_path="location", frame=frame)
        
        obj.location = end_pos
        obj.keyframe_insert(data_path="location", frame=end_frame)
    
    elif motion_type == "jump":
        # Jump motion with arc
        start_pos = Vector(kwargs.get('start_pos', obj.location))
        end_pos = Vector(kwargs.get('end_pos', (5, 0, 0)))
        height = kwargs.get('height', 3.0)
        
        # Start position
        obj.location = start_pos
        obj.keyframe_insert(data_path="location", frame=start_frame)
        
        # Peak of jump
        mid_frame = (start_frame + end_frame) // 2
        mid_pos = start_pos.lerp(end_pos, 0.5)
        mid_pos.z = start_pos.z + height
        obj.location = mid_pos
        obj.keyframe_insert(data_path="location", frame=mid_frame)
        
        # Landing position
        obj.location = end_pos
        obj.keyframe_insert(data_path="location", frame=end_frame)
        
        # Set interpolation to bezier for smooth arc
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'BEZIER'
                    keyframe.handle_left_type = 'AUTO'
                    keyframe.handle_right_type = 'AUTO'
    
    elif motion_type == "fly":
        # Flying motion with curves
        start_pos = Vector(kwargs.get('start_pos', obj.location))
        end_pos = Vector(kwargs.get('end_pos', (10, 0, 5)))
        wave_amplitude = kwargs.get('wave_amplitude', 1.0)
        wave_frequency = kwargs.get('wave_frequency', 2.0)
        
        # Create curved path
        num_points = kwargs.get('num_points', 20)
        for i in range(num_points + 1):
            progress = i / num_points
            frame = int(start_frame + progress * (end_frame - start_frame))
            
            # Interpolate position
            pos = start_pos.lerp(end_pos, progress)
            
            # Add wave motion
            wave_offset = math.sin(progress * math.pi * 2 * wave_frequency) * wave_amplitude
            pos.z += wave_offset
            
            obj.location = pos
            obj.keyframe_insert(data_path="location", frame=frame)
    
    elif motion_type == "custom":
        # Custom motion path
        path_points = kwargs.get('path_points', [])
        if not path_points:
            raise ValueError("Custom motion requires 'path_points' parameter")
        
        # Distribute keyframes along path
        for i, point in enumerate(path_points):
            progress = i / (len(path_points) - 1)
            frame = int(start_frame + progress * (end_frame - start_frame))
            
            obj.location = Vector(point)
            obj.keyframe_insert(data_path="location", frame=frame)
    
    # Update scene
    bpy.context.view_layer.update()
    
    return obj
'''

WALK_CYCLE_FUNCTION = '''
def create_walk_cycle(obj, start_pos=(0, 0, 0), end_pos=(10, 0, 0), 
                     duration=2.0, steps_per_second=2):
    """Create a walk cycle animation
    
    Args:
        obj: The character object to animate
        start_pos: Starting position
        end_pos: Ending position
        duration: Duration in seconds
        steps_per_second: Walking pace
    
    Returns:
        The animated object
    """
    import bpy
    import math
    from mathutils import Vector
    
    scene = bpy.context.scene
    fps = scene.render.fps
    
    start_frame = scene.frame_current
    end_frame = start_frame + int(duration * fps)
    
    # Calculate step parameters
    total_steps = int(duration * steps_per_second)
    frames_per_step = (end_frame - start_frame) / total_steps
    
    start_vec = Vector(start_pos)
    end_vec = Vector(end_pos)
    
    # Create walk cycle
    for step in range(total_steps + 1):
        frame = start_frame + int(step * frames_per_step)
        progress = step / total_steps
        
        # Calculate position
        pos = start_vec.lerp(end_vec, progress)
        
        # Add vertical bobbing
        if step % 2:
            pos.z += 0.05  # Slight lift on alternating steps
        
        obj.location = pos
        obj.keyframe_insert(data_path="location", frame=frame)
        
        # Add rotation for steps
        if hasattr(obj, 'pose') and obj.pose:
            # This would be for armature-based characters
            # Add foot rotation logic here
            pass
    
    return obj
'''

JUMP_MOTION_FUNCTION = '''
def create_jump_motion(obj, jump_height=2.0, jump_distance=3.0, 
                      preparation_time=0.3, air_time=0.6, landing_time=0.2):
    """Create a realistic jump animation
    
    Args:
        obj: The object to animate
        jump_height: Maximum height of jump
        jump_distance: Horizontal distance of jump
        preparation_time: Time for crouching before jump
        air_time: Time in the air
        landing_time: Time for landing recovery
    
    Returns:
        The animated object
    """
    import bpy
    import math
    from mathutils import Vector
    
    scene = bpy.context.scene
    fps = scene.render.fps
    
    # Calculate frame numbers
    start_frame = scene.frame_current
    prep_frames = int(preparation_time * fps)
    air_frames = int(air_time * fps)
    land_frames = int(landing_time * fps)
    
    # Get initial position
    start_pos = Vector(obj.location)
    
    # Preparation (crouch)
    obj.location = start_pos
    obj.keyframe_insert(data_path="location", frame=start_frame)
    
    crouch_pos = start_pos.copy()
    crouch_pos.z -= 0.2  # Slight crouch
    obj.location = crouch_pos
    obj.keyframe_insert(data_path="location", frame=start_frame + prep_frames)
    
    # Launch
    launch_frame = start_frame + prep_frames
    
    # Air time - create parabolic motion
    for i in range(air_frames + 1):
        progress = i / air_frames
        frame = launch_frame + i
        
        # Horizontal motion (linear)
        x_offset = jump_distance * progress
        
        # Vertical motion (parabolic)
        # y = -4h(x^2 - x) where h is max height, x is normalized progress
        y_offset = -4 * jump_height * (progress * progress - progress)
        
        pos = start_pos.copy()
        pos.x += x_offset
        pos.z += y_offset
        
        obj.location = pos
        obj.keyframe_insert(data_path="location", frame=frame)
    
    # Landing
    land_start_frame = launch_frame + air_frames
    final_pos = start_pos.copy()
    final_pos.x += jump_distance
    
    # Impact position (slight crouch)
    impact_pos = final_pos.copy()
    impact_pos.z -= 0.1
    obj.location = impact_pos
    obj.keyframe_insert(data_path="location", frame=land_start_frame + land_frames // 2)
    
    # Recovery
    obj.location = final_pos
    obj.keyframe_insert(data_path="location", frame=land_start_frame + land_frames)
    
    return obj
'''

ARMATURE_ACTION_FUNCTION = '''
def apply_armature_action(armature, action_name, start_frame=1, end_frame=120, 
                         blend_in=0, blend_out=0):
    """Apply an action to an armature
    
    Args:
        armature: The armature object
        action_name: Name of the action to apply
        start_frame: Starting frame
        end_frame: Ending frame
        blend_in: Frames to blend in
        blend_out: Frames to blend out
    
    Returns:
        The armature with applied action
    """
    import bpy
    
    if not armature or armature.type != 'ARMATURE':
        raise ValueError("Object must be an armature")
    
    # Get or create action
    if action_name in bpy.data.actions:
        action = bpy.data.actions[action_name]
    else:
        raise ValueError(f"Action '{action_name}' not found")
    
    # Create NLA track if needed
    if not armature.animation_data:
        armature.animation_data_create()
    
    anim_data = armature.animation_data
    
    # Clear existing NLA tracks if requested
    if not anim_data.nla_tracks:
        track = anim_data.nla_tracks.new()
        track.name = "Motion Track"
    else:
        track = anim_data.nla_tracks[0]
    
    # Add action as NLA strip
    strip = track.strips.new(action_name, start_frame, action)
    strip.frame_end = end_frame
    
    # Set blending
    strip.blend_in = blend_in
    strip.blend_out = blend_out
    
    # Update scene
    bpy.context.view_layer.update()
    
    return armature
'''