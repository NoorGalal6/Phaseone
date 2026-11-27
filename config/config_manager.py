import json
class ConfigManager:

    def __init__(self, file_path="config/settings.json"):
        self.file_path = file_path
        self.settings = self.load_settings()

    def load_settings(self):

        with open(self.file_path, "r") as file:
            return json.load(file)

    def get_active_profile(self):

        profile_name = self.settings["active_profile"]
        return self.settings["profiles"][profile_name]

    def save_settings(self):

        with open(self.file_path, "w") as file:
            json.dump(self.settings, file, indent=4)

    def switch_profile(self, profile_name):

        if profile_name in self.settings["profiles"]:
            self.settings["active_profile"] = profile_name
            self.save_settings()
            return True

        return False

    def get_input_settings(self):

        return self.settings["input"]

    def load_controller_profile(self, controller_name):

        controller_profiles = self.settings.get("controller_profiles", {})

        profile_name = controller_profiles.get(controller_name)

        if profile_name in self.settings["profiles"]:
            return self.switch_profile(profile_name)

        return False
