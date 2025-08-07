# Local AI Service Setup

## Instructions

1. **Install Dependencies**:
   Ensure all required dependencies for the local AI service are installed by running:
   
   ```bash
   pip install -r rest/ai_service_local/requirements.txt
   ```

2. **Update Django Settings**:
   Add `'rest.ai_service_local.apps.LocalAiServiceConfig'` to the `INSTALLED_APPS` in your Django `settings.py` to ensure the local model loads at startup:

   ```python
   INSTALLED_APPS = [
       ...
       'rest.ai_service_local.apps.LocalAiServiceConfig',
   ]
   ```

3. **Place Model File**:
   Make sure your model file `DeepSeek_R1_Distill_Qwen_1_5B.gguf` is located in the `BASE_DIR` of your Django project.

4. **Run Django**:
   Start your Django server:
   
   ```bash
   python manage.py runserver
   ```

   On Django startup, you'll see logs indicating the local model loading status.

5. **Switch Service**:
   To use the local AI service, change the import in your `views.py` to switch from the existing AI service:
   
   ```python
   # from rest.ai_service import generate_and_save_plan_for_user
   from rest.ai_service_local.ai_service_local import generate_and_save_local_plan_for_user
   ```

   **Note**: Make sure to replace usages in your code as needed.

6. **Verify**:
   Ensure everything functions correctly by generating plans, and checking outputs.
   Report any errors encountered during loading or plan generation for troubleshooting further.
