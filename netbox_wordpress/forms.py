# SPDX-License-Identifier: AGPL-3.0-or-later
from dcim.models import Device
from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet
from virtualization.models import VirtualMachine

from .choices import FPMProfileChoices, PluginSourceChoices, RelocationStateChoices, WPConstantTypeChoices
from .models import (
    WordPressConstant, WordPressContentDirectory, WordPressPlugin, WordPressSite, WordPressTheme,
)


class WordPressSiteForm(NetBoxModelForm):
    device = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)
    virtual_machine = DynamicModelChoiceField(queryset=VirtualMachine.objects.all(), required=False)

    fieldsets = (
        FieldSet("name", "site_url", "wp_version", "table_prefix", "is_multisite", name="Site"),
        FieldSet("device", "virtual_machine", "service_instance", name="Host"),
        FieldSet("database", "db_user", name="Database"),
        FieldSet("fpm_profile", "wp_memory_limit", "prod_hardening", "salt_ref", name="Tuning & secrets"),
    )

    class Meta:
        model = WordPressSite
        fields = [
            "name", "device", "virtual_machine", "service_instance", "site_url", "wp_version",
            "table_prefix", "is_multisite", "database", "db_user", "fpm_profile", "wp_memory_limit",
            "prod_hardening", "salt_ref", "tags",
        ]


class WordPressConstantForm(NetBoxModelForm):
    site = DynamicModelChoiceField(queryset=WordPressSite.objects.all())

    fieldsets = (FieldSet("site", "name", "value", "value_type", name="Constant"),)

    class Meta:
        model = WordPressConstant
        fields = ["site", "name", "value", "value_type", "tags"]


class WordPressPluginForm(NetBoxModelForm):
    site = DynamicModelChoiceField(queryset=WordPressSite.objects.all())

    fieldsets = (FieldSet("site", "slug", "version", "is_active", "source", "source_url", name="Plugin"),)

    class Meta:
        model = WordPressPlugin
        fields = ["site", "slug", "version", "is_active", "source", "source_url", "tags"]


class WordPressThemeForm(NetBoxModelForm):
    site = DynamicModelChoiceField(queryset=WordPressSite.objects.all())

    fieldsets = (FieldSet("site", "slug", "version", "is_active", "source", "source_url", name="Theme"),)

    class Meta:
        model = WordPressTheme
        fields = ["site", "slug", "version", "is_active", "source", "source_url", "tags"]


class WordPressContentDirectoryForm(NetBoxModelForm):
    site = DynamicModelChoiceField(queryset=WordPressSite.objects.all())

    fieldsets = (
        FieldSet("site", "content_dir", "uploads_dir", "content_url", name="Content directory"),
        FieldSet("target_content_dir", "relocation_state", name="Relocation"),
    )

    class Meta:
        model = WordPressContentDirectory
        fields = [
            "site", "content_dir", "uploads_dir", "target_content_dir", "content_url",
            "relocation_state", "tags",
        ]


class WordPressSiteFilterForm(NetBoxModelFilterSetForm):
    model = WordPressSite
    device_id = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), required=False, label="Device")
    virtual_machine_id = DynamicModelMultipleChoiceField(queryset=VirtualMachine.objects.all(), required=False, label="Virtual Machine")
    fpm_profile = forms.MultipleChoiceField(choices=FPMProfileChoices, required=False)
    is_multisite = forms.NullBooleanField(required=False)
    prod_hardening = forms.NullBooleanField(required=False)
    tag = TagFilterField(WordPressSite)


class WordPressConstantFilterForm(NetBoxModelFilterSetForm):
    model = WordPressConstant
    site_id = DynamicModelMultipleChoiceField(queryset=WordPressSite.objects.all(), required=False, label="Site")
    value_type = forms.MultipleChoiceField(choices=WPConstantTypeChoices, required=False)
    tag = TagFilterField(WordPressConstant)


class WordPressPluginFilterForm(NetBoxModelFilterSetForm):
    model = WordPressPlugin
    site_id = DynamicModelMultipleChoiceField(queryset=WordPressSite.objects.all(), required=False, label="Site")
    source = forms.MultipleChoiceField(choices=PluginSourceChoices, required=False)
    is_active = forms.NullBooleanField(required=False)
    tag = TagFilterField(WordPressPlugin)


class WordPressThemeFilterForm(NetBoxModelFilterSetForm):
    model = WordPressTheme
    site_id = DynamicModelMultipleChoiceField(queryset=WordPressSite.objects.all(), required=False, label="Site")
    source = forms.MultipleChoiceField(choices=PluginSourceChoices, required=False)
    is_active = forms.NullBooleanField(required=False)
    tag = TagFilterField(WordPressTheme)


class WordPressContentDirectoryFilterForm(NetBoxModelFilterSetForm):
    model = WordPressContentDirectory
    site_id = DynamicModelMultipleChoiceField(queryset=WordPressSite.objects.all(), required=False, label="Site")
    relocation_state = forms.MultipleChoiceField(choices=RelocationStateChoices, required=False)
    tag = TagFilterField(WordPressContentDirectory)
