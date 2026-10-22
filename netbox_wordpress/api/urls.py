# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.routers import NetBoxRouter

from . import views

app_name = "netbox_wordpress"

router = NetBoxRouter()
router.register("sites", views.WordPressSiteViewSet)
router.register("constants", views.WordPressConstantViewSet)
router.register("options", views.WordPressOptionViewSet)
router.register("plugins", views.WordPressPluginViewSet)
router.register("muplugins", views.WordPressMuPluginViewSet)
router.register("themes", views.WordPressThemeViewSet)
router.register("content-directories", views.WordPressContentDirectoryViewSet)

urlpatterns = router.urls
