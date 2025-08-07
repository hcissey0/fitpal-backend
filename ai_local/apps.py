from django.apps import AppConfig
import os


class AiLocalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_local'
    verbose_name = 'Local AI Service'

    def ready(self):
        """
        This method is called when Django starts up.
        We'll use it to pre-load the local model.
        """
        # Only load the model if we're not in migration mode
        # This prevents model loading during migrations
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
            
        try:
            print("🤖 Loading local AI model on Django startup...")
            from .services import get_local_model
            
            # This will trigger the model loading
            model = get_local_model()
            if model.model:
                print("✅ Local AI model loaded successfully on startup!")
            else:
                print("⚠️  Local AI model failed to load - will use fallback plan generation")
                
        except Exception as e:
            print(f"⚠️  Error loading local AI model on startup: {e}")
            print("Will use fallback plan generation when needed")
