# ai_local App Setup

## Instructions

1. **Install Dependencies**:
   Ensure all required dependencies for the ai_local app are installed by running:
   
   ```bash
   pip install -r ai_local/requirements.txt
   ```

2. **Update Django Settings**:
   Add `'ai_local.apps.AiLocalConfig'` to the `INSTALLED_APPS` in your Django `settings.py` to ensure the local model loads at startup:

   ```python
   INSTALLED_APPS = [
       ...
       'ai_local.apps.AiLocalConfig',
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
   To use the ai_local service, change the import in your `views.py` to switch from the existing AI service:
   
   ```python
   # from rest.ai_service import generate_and_save_plan_for_user
   from ai_local.services import generate_and_save_local_plan_for_user
   ```

   **Note**: Make sure to replace usages in your code as needed.

6. **Verify**:
   Verify that the model is loaded correctly by accessing:
   - Model status: [http://localhost:8000/ai_local/status/](http://localhost:8000/ai_local/status/)
   - Test Generation: [http://localhost:8000/ai_local/test/](http://localhost:8000/ai_local/test/)

7. **Testing**:
   Run the tests to verify everything is functioning:

   ```bash
   python manage.py test ai_local
   ```
