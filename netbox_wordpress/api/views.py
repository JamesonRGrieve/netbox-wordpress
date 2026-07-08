# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets
from ..models import (
    WordPressConstant, WordPressContentDirectory, WordPressPlugin, WordPressSite, WordPressTheme,
)
from .serializers import (
    WordPressConstantSerializer, WordPressContentDirectorySerializer, WordPressPluginSerializer,
    WordPressSiteSerializer, WordPressThemeSerializer,
)


class WordPressSiteViewSet(NetBoxModelViewSet):
    queryset = WordPressSite.objects.prefetch_related(
        "device", "virtual_machine", "service_instance", "object_cache_instance", "database",
        "db_user", "tags",
    )
    serializer_class = WordPressSiteSerializer
    filterset_class = filtersets.WordPressSiteFilterSet


class WordPressConstantViewSet(NetBoxModelViewSet):
    queryset = WordPressConstant.objects.prefetch_related("site", "tags")
    serializer_class = WordPressConstantSerializer
    filterset_class = filtersets.WordPressConstantFilterSet


class WordPressPluginViewSet(NetBoxModelViewSet):
    queryset = WordPressPlugin.objects.prefetch_related("site", "tags")
    serializer_class = WordPressPluginSerializer
    filterset_class = filtersets.WordPressPluginFilterSet


class WordPressThemeViewSet(NetBoxModelViewSet):
    queryset = WordPressTheme.objects.prefetch_related("site", "tags")
    serializer_class = WordPressThemeSerializer
    filterset_class = filtersets.WordPressThemeFilterSet


class WordPressContentDirectoryViewSet(NetBoxModelViewSet):
    queryset = WordPressContentDirectory.objects.prefetch_related("site", "tags")
    serializer_class = WordPressContentDirectorySerializer
    filterset_class = filtersets.WordPressContentDirectoryFilterSet
