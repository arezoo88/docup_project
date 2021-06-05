from django.apps import AppConfig


class AuthConfig(AppConfig):
    name = 'authentication'
    def ready(self):
        print("reset all users online status...")
        self.get_model('User').objects.all().update(online=0)#TODO ask about this
