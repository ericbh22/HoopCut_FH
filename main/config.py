import json
import os

# Path to store configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'app_config.json')

# Default configuration
DEFAULT_CONFIG = {
    'auto_ai': True,
    "three_point_adjust": False
}

def load_config():
    """Load configuration from file or create default if doesn't exist"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is corrupted or doesn't exist, use default
            pass
    
    # Create default config file
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_setting(key, default=None):
    """Get a specific setting value"""
    config = load_config()
    return config.get(key, default) 

def set_setting(key, value):
    """Set a specific setting value and save to file"""
    config = load_config()
    config[key] = value
    save_config(config)



# Load initial configuration
_config = load_config()
auto_ai = _config.get('auto_ai', True)
three_point_adjust = _config.get("three_point_adjust",False)