# Config
Configuration library with JSON based

# Examples

## Base use
  config = Config("settings.json")
  
  config["window.size"] = [1280, 720]
  
  print(config.get("window.size"))          # [1280, 720]
  
  print(config["window.size"])              # [1280, 720]

## With default values
  theme = config.get("ui.theme", "light")

## Check
  if "recent_files" in config:
  
    print(config["recent_files"])

## Direct access
config["audio.volume"] = 0.75

volume = config["audio.volume"]
