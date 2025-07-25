# Lighting setup functions for Blender scenes
# Provides various lighting setups for different moods and scenarios

SETUP_THREE_POINT_LIGHTING_FUNCTION = '''
def setup_three_point_lighting(target_object, key_strength=5.0, fill_strength=2.0, 
                              rim_strength=3.0, key_angle=45, fill_angle=-30, rim_angle=135):
    """Setup classic three-point lighting system.
    
    Args:
        target_object (bpy.types.Object): Object to light
        key_strength (float): Key light intensity
        fill_strength (float): Fill light intensity  
        rim_strength (float): Rim light intensity
        key_angle (float): Key light angle in degrees
        fill_angle (float): Fill light angle in degrees
        rim_angle (float): Rim light angle in degrees
        
    Returns:
        dict: Dictionary containing the three lights
    """
    import bpy
    import math
    from mathutils import Vector
    
    if target_object is None:
        raise ValueError("Target object cannot be None")
    
    lights = {}
    target_loc = Vector(target_object.location)
    
    # Key Light (main light)
    bpy.ops.object.light_add(type='SUN', location=(
        target_loc.x + 5 * math.cos(math.radians(key_angle)),
        target_loc.y + 5 * math.sin(math.radians(key_angle)),
        target_loc.z + 3
    ))
    key_light = bpy.context.active_object
    key_light.name = "Key_Light"
    key_light.data.energy = key_strength
    key_light.data.color = (1.0, 0.95, 0.8)  # Warm white
    lights['key'] = key_light
    
    # Fill Light (softer, opposite side)
    bpy.ops.object.light_add(type='AREA', location=(
        target_loc.x + 4 * math.cos(math.radians(fill_angle)),
        target_loc.y + 4 * math.sin(math.radians(fill_angle)),
        target_loc.z + 2
    ))
    fill_light = bpy.context.active_object
    fill_light.name = "Fill_Light"
    fill_light.data.energy = fill_strength
    fill_light.data.size = 2.0
    fill_light.data.color = (0.8, 0.9, 1.0)  # Cool white
    lights['fill'] = fill_light
    
    # Rim Light (back light for edge definition)
    bpy.ops.object.light_add(type='SPOT', location=(
        target_loc.x + 6 * math.cos(math.radians(rim_angle)),
        target_loc.y + 6 * math.sin(math.radians(rim_angle)),
        target_loc.z + 4
    ))
    rim_light = bpy.context.active_object
    rim_light.name = "Rim_Light"
    rim_light.data.energy = rim_strength
    rim_light.data.spot_size = math.radians(60)
    rim_light.data.color = (1.0, 0.9, 0.7)  # Warm rim
    lights['rim'] = rim_light
    
    # Point all lights at target
    for light in lights.values():
        direction = target_loc - Vector(light.location)
        light.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    return lights
'''

SETUP_NATURAL_LIGHTING_FUNCTION = '''
def setup_natural_lighting(sun_strength=3.0, sun_angle=30, ambient_strength=0.3,
                          sky_texture=True, time_of_day="midday"):
    """Setup natural outdoor lighting with sun and sky.
    
    Args:
        sun_strength (float): Sun light intensity
        sun_angle (float): Sun elevation angle in degrees
        ambient_strength (float): Ambient light strength
        sky_texture (bool): Whether to use sky texture for environment
        time_of_day (str): Time of day (dawn, midday, sunset, night)
        
    Returns:
        dict: Dictionary containing lighting setup
    """
    import bpy
    import math
    
    lights = {}
    
    # Time of day settings
    time_settings = {
        "dawn": {"color": (1.0, 0.7, 0.5), "strength_mult": 0.8, "angle": 15},
        "midday": {"color": (1.0, 0.95, 0.9), "strength_mult": 1.0, "angle": 60},
        "sunset": {"color": (1.0, 0.6, 0.3), "strength_mult": 0.7, "angle": 10},
        "night": {"color": (0.3, 0.4, 0.8), "strength_mult": 0.1, "angle": -10}
    }
    
    settings = time_settings.get(time_of_day, time_settings["midday"])
    
    # Sun light
    sun_rad = math.radians(sun_angle + settings["angle"])
    bpy.ops.object.light_add(type='SUN', location=(
        10 * math.cos(sun_rad),
        -10 * math.sin(sun_rad),
        10 * math.sin(sun_rad)
    ))
    sun_light = bpy.context.active_object
    sun_light.name = "Sun_Light"
    sun_light.data.energy = sun_strength * settings["strength_mult"]
    sun_light.data.color = settings["color"]
    sun_light.rotation_euler = (sun_rad, 0, math.radians(45))
    lights['sun'] = sun_light
    
    # Sky light (ambient)
    if sky_texture:
        # Setup world shader for sky
        world = bpy.context.scene.world
        if world.use_nodes:
            nodes = world.node_tree.nodes
            links = world.node_tree.links
            
            # Clear existing nodes
            nodes.clear()
            
            # Add Sky Texture
            sky_node = nodes.new(type="ShaderNodeTexSky")
            sky_node.sky_type = 'PREETHAM'
            sky_node.sun_elevation = math.radians(sun_angle)
            
            # Add Background shader
            bg_node = nodes.new(type="ShaderNodeBackground")
            bg_node.inputs['Strength'].default_value = ambient_strength
            
            # Add Output
            output_node = nodes.new(type="ShaderNodeOutputWorld")
            
            # Link nodes
            links.new(sky_node.outputs['Color'], bg_node.inputs['Color'])
            links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])
    
    return lights
'''

SETUP_DRAMATIC_LIGHTING_FUNCTION = '''
def setup_dramatic_lighting(target_object, mood="dramatic", color_temp="warm"):
    """Setup dramatic lighting for cinematic scenes.
    
    Args:
        target_object (bpy.types.Object): Object to light dramatically
        mood (str): Lighting mood (dramatic, mysterious, heroic, menacing)
        color_temp (str): Color temperature (warm, cool, neutral)
        
    Returns:
        dict: Dictionary containing dramatic lights
    """
    import bpy
    import math
    from mathutils import Vector
    
    if target_object is None:
        raise ValueError("Target object cannot be None")
    
    lights = {}
    target_loc = Vector(target_object.location)
    
    # Color temperature settings
    colors = {
        "warm": (1.0, 0.8, 0.6),
        "cool": (0.6, 0.8, 1.0), 
        "neutral": (1.0, 1.0, 1.0)
    }
    base_color = colors.get(color_temp, colors["warm"])
    
    if mood == "dramatic":
        # Strong key light from low angle
        bpy.ops.object.light_add(type='SPOT', location=(
            target_loc.x - 3,
            target_loc.y - 5,
            target_loc.z + 1
        ))
        key_light = bpy.context.active_object
        key_light.name = "Dramatic_Key"
        key_light.data.energy = 8.0
        key_light.data.spot_size = math.radians(45)
        key_light.data.color = base_color
        lights['key'] = key_light
        
        # Rim light for dramatic edge
        bpy.ops.object.light_add(type='SPOT', location=(
            target_loc.x + 4,
            target_loc.y + 3,
            target_loc.z + 6
        ))
        rim_light = bpy.context.active_object
        rim_light.name = "Dramatic_Rim"
        rim_light.data.energy = 6.0
        rim_light.data.spot_size = math.radians(30)
        rim_light.data.color = (base_color[0], base_color[1] * 0.8, base_color[2] * 1.2)
        lights['rim'] = rim_light
        
    elif mood == "mysterious":
        # Low, colored lighting
        bpy.ops.object.light_add(type='POINT', location=(
            target_loc.x + 2,
            target_loc.y,
            target_loc.z + 0.5
        ))
        mystery_light = bpy.context.active_object
        mystery_light.name = "Mystery_Light"
        mystery_light.data.energy = 4.0
        mystery_light.data.color = (0.7, 0.4, 0.9)  # Purple tint
        lights['mystery'] = mystery_light
        
    # Point lights at target
    for light in lights.values():
        if light.type == 'LIGHT':
            direction = target_loc - Vector(light.location)
            light.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    return lights
'''

SETUP_STUDIO_LIGHTING_FUNCTION = '''
def setup_studio_lighting(target_object, soft_shadows=True, background_light=True):
    """Setup professional studio lighting with soft shadows.
    
    Args:
        target_object (bpy.types.Object): Object to light
        soft_shadows (bool): Whether to use soft shadows
        background_light (bool): Whether to add background lighting
        
    Returns:
        dict: Dictionary containing studio lights
    """
    import bpy
    import math
    from mathutils import Vector
    
    if target_object is None:
        raise ValueError("Target object cannot be None")
    
    lights = {}
    target_loc = Vector(target_object.location)
    
    # Main key light (large area light)
    bpy.ops.object.light_add(type='AREA', location=(
        target_loc.x - 4,
        target_loc.y - 6,
        target_loc.z + 3
    ))
    key_light = bpy.context.active_object
    key_light.name = "Studio_Key"
    key_light.data.energy = 6.0
    key_light.data.size = 3.0 if soft_shadows else 1.0
    key_light.data.color = (1.0, 0.98, 0.95)  # Neutral white
    lights['key'] = key_light
    
    # Fill light (opposite side)
    bpy.ops.object.light_add(type='AREA', location=(
        target_loc.x + 3,
        target_loc.y - 4,
        target_loc.z + 2
    ))
    fill_light = bpy.context.active_object
    fill_light.name = "Studio_Fill"
    fill_light.data.energy = 3.0
    fill_light.data.size = 4.0 if soft_shadows else 1.5
    fill_light.data.color = (0.95, 0.98, 1.0)  # Slightly cool
    lights['fill'] = fill_light
    
    # Hair/Rim light
    bpy.ops.object.light_add(type='SPOT', location=(
        target_loc.x + 2,
        target_loc.y + 5,
        target_loc.z + 5
    ))
    rim_light = bpy.context.active_object
    rim_light.name = "Studio_Rim"
    rim_light.data.energy = 4.0
    rim_light.data.spot_size = math.radians(40)
    rim_light.data.color = (1.0, 0.95, 0.85)
    lights['rim'] = rim_light
    
    # Background light
    if background_light:
        bpy.ops.object.light_add(type='AREA', location=(
            target_loc.x,
            target_loc.y + 8,
            target_loc.z
        ))
        bg_light = bpy.context.active_object
        bg_light.name = "Studio_Background"
        bg_light.data.energy = 2.0
        bg_light.data.size = 6.0
        bg_light.data.color = (0.9, 0.9, 1.0)
        bg_light.rotation_euler = (0, math.radians(180), 0)
        lights['background'] = bg_light
    
    # Point lights at target
    for name, light in lights.items():
        if name != 'background' and light.type == 'LIGHT':
            direction = target_loc - Vector(light.location)
            light.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    return lights
'''

# Collection of all lighting functions
LIGHTING_FUNCTIONS = {
    "setup_three_point_lighting": SETUP_THREE_POINT_LIGHTING_FUNCTION,
    "setup_natural_lighting": SETUP_NATURAL_LIGHTING_FUNCTION, 
    "setup_dramatic_lighting": SETUP_DRAMATIC_LIGHTING_FUNCTION,
    "setup_studio_lighting": SETUP_STUDIO_LIGHTING_FUNCTION,
} 