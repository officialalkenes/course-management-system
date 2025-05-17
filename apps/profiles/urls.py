# urls.py
from rest_framework.routers import DefaultRouter
from .views import OnboardingViewSet

router = DefaultRouter()
router.register(r"profile-onboarding", OnboardingViewSet, basename="onboarding")

urlpatterns = router.urls
