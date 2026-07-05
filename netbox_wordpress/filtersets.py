# SPDX-License-Identifier: AGPL-3.0-or-later
import django_filters
from dcim.models import Device
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from netbox_database.models import Database, DatabaseUser
from netbox_services.models import ServiceInstance
from virtualization.models import VirtualMachine

from .choices import FPMProfileChoices, PluginSourceChoices, RelocationStateChoices, WPConstantTypeChoices
from .models import (
    WordPressConstant, WordPressContentDirectory, WordPressPlugin, WordPressSite, WordPressTheme,
)

# Explicit FK filters: django-filter does NOT derive `<fk>_id` from a bare FK in Meta.fields,
# so `?site_id=` would be silently ignored. NetBox convention is `<fk>_id` (by PK).


class _SiteFilterMixin(NetBoxModelFilterSet):
    site_id = django_filters.ModelMultipleChoiceFilter(
        field_name="site", queryset=WordPressSite.objects.all(), label="Site (ID)"
    )
    site = django_filters.ModelMultipleChoiceFilter(
        field_name="site__name", to_field_name="name", queryset=WordPressSite.objects.all(),
        label="Site (name)",
    )

    class Meta:
        abstract = True


class WordPressSiteFilterSet(NetBoxModelFilterSet):
    fpm_profile = django_filters.MultipleChoiceFilter(choices=FPMProfileChoices)
    # Explicit FK-by-PK filters (django-filter does not derive `<fk>_id` from a bare FK).
    device_id = django_filters.ModelMultipleChoiceFilter(field_name="device", queryset=Device.objects.all(), label="Device (ID)")
    virtual_machine_id = django_filters.ModelMultipleChoiceFilter(field_name="virtual_machine", queryset=VirtualMachine.objects.all(), label="Virtual Machine (ID)")
    service_instance_id = django_filters.ModelMultipleChoiceFilter(field_name="service_instance", queryset=ServiceInstance.objects.all(), label="Service Instance (ID)")
    database_id = django_filters.ModelMultipleChoiceFilter(field_name="database", queryset=Database.objects.all(), label="Database (ID)")
    db_user_id = django_filters.ModelMultipleChoiceFilter(field_name="db_user", queryset=DatabaseUser.objects.all(), label="DB User (ID)")

    class Meta:
        model = WordPressSite
        fields = [
            "id", "name", "site_url", "wp_version", "table_prefix", "is_multisite",
            "wp_memory_limit", "prod_hardening", "salt_ref",
        ]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(site_url__icontains=value) | Q(wp_version__icontains=value)
        )


class WordPressConstantFilterSet(_SiteFilterMixin):
    value_type = django_filters.MultipleChoiceFilter(choices=WPConstantTypeChoices)

    class Meta:
        model = WordPressConstant
        fields = ["id", "name", "value"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(value__icontains=value))


class WordPressPluginFilterSet(_SiteFilterMixin):
    source = django_filters.MultipleChoiceFilter(choices=PluginSourceChoices)

    class Meta:
        model = WordPressPlugin
        fields = ["id", "slug", "version", "is_active", "source_url"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(slug__icontains=value) | Q(version__icontains=value))


class WordPressThemeFilterSet(_SiteFilterMixin):
    source = django_filters.MultipleChoiceFilter(choices=PluginSourceChoices)

    class Meta:
        model = WordPressTheme
        fields = ["id", "slug", "version", "is_active", "source_url"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(slug__icontains=value) | Q(version__icontains=value))


class WordPressContentDirectoryFilterSet(_SiteFilterMixin):
    relocation_state = django_filters.MultipleChoiceFilter(choices=RelocationStateChoices)

    class Meta:
        model = WordPressContentDirectory
        fields = ["id", "content_dir", "uploads_dir", "target_content_dir", "content_url"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(content_dir__icontains=value) | Q(target_content_dir__icontains=value)
        )
