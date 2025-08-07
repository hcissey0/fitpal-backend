from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .services import get_local_model
import os
from django.conf import settings


@require_http_methods(["GET"])
def model_status(request):
    """
    Check the status of the local AI model
    """
    try:
        model = get_local_model()
        model_file_exists = os.path.exists(model.model_path)
        
        status = {
            'model_loaded': model.model is not None,
            'model_path': model.model_path,
            'model_file_exists': model_file_exists,
            'llama_cpp_available': hasattr(model, 'model') and model.model is not None,
            'status': 'ready' if model.model else 'fallback_only',
            'expected_model_path': os.path.join(settings.BASE_DIR, 'DeepSeek_R1_Distill_Qwen_1_5B.gguf')
        }
        return JsonResponse(status)
    except Exception as e:
        return JsonResponse({
            'model_loaded': False,
            'error': str(e),
            'status': 'error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def test_generation(request):
    """
    Test the local model generation with a simple prompt
    """
    try:
        model = get_local_model()
        
        # Simple test prompt
        test_prompt = """
        Generate a simple 1-day fitness plan for a 25-year-old male, 70kg, 175cm, goal: weight loss.
        Please respond with valid JSON.
        """
        
        response_text = model.generate_plan(test_prompt)
        
        return JsonResponse({
            'success': True,
            'using_model': model.model is not None,
            'response_preview': response_text[:500] + '...' if len(response_text) > 500 else response_text
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
