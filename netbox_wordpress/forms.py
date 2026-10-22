# SPDX-License-Identifier: AGPL-3.0-or-later
from dcim.models import Device
from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from netbox_services.models import ServiceInstance
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet
from virtualization.models import VirtualMachine

from .choices import (
    FPMProfileChoices, PluginSourceChoices, PluginStateChoices, RelocationStateChoices,
    WPConstantTypeChoices, WPOptionFormatChoices,
)
from .models import (
    WordPressConstant, WordPressContentDirectory, WordPressMuPlugin, WordPressOption, WordPressPlugin,
    WordPressSite, WordPressTheme,
)


class WordPressSiteForm(NetBoxModelForm):
    device = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)
    virtual_machine = DynamicModelChoiceField(queryset=VirtualMachine.objects.all(), required=False)
    object_cache_instance = DynamicModelChoiceField(queryset=ServiceInstance.objects.all(), required=False)

    fieldsets = (
        FieldSet("name", "site_url", "wp_version", "table_prefix", "is_multisite", "install_path", "site_icon_url", name="Site"),
        FieldSet("device", "virtual_machine", "service_instance", "object_cache_instance", name="Host"),
        FieldSet("database", "db_user", name="Database"),
        FieldSet("fpm_profile", "wp_memory_limit", "prod_hardening", "safe_opt", name="Tuning"),
        FieldSet("login_slug", "trusted_proxies", "enable_hsts", "salt_ref", name="Security"),
    )

    class Meta:
        model = WordPressSite
        fields = [
            "name", "device", "virtual_machine", "service_instance", "object_cache_instance",
            "site_url", "wp_version", "table_prefix", "is_multisite", "install_path", "database",
            "db_user", "fpm_profile", "wp_memory_limit", "prod_hardening", "safe_opt", "login_slug",
            "trusted_proxies", "enable_hsts", "salt_ref", "site_icon_url", "tags",
        ]


class WordPressOptionForm(NetBoxModelForm):
    site = DynamicModelChoiceField(queryset=WordPressSite.objects.all())

    fieldsets = (FieldSet("site", "name", "key_path", "value", "value_format", name="Option"),)

    class Meta:
        model = WordPressOption
        fields = ["site", "name", "key_path", "value", "value_format", "tags"]


class WordPressConstantForm(NetBoxModelForm):
    site = DynamicModelChoiceField(queryset=WordPressSite.objects.all())

    fieldsets = (FieldSet("site", "name", "value", "value_type", name="Constant"),)

    class Meta:
        model = WordPressConstant
        fields = ["site", "name", "value", "value_type", "tags"]


class WordPressPluginForm(NetBoxModelForm):
    site = DynamicModelChoiceField(queryset=WordPressSite.objects.all())

    fieldsets = (FieldSet("site", "slug", "version", "state", "source", "source_url", name="Plugin"),)

    class Meta:
        model = WordPressPlugin
        fields = ["site", "slug", "version", "state", "source", "source_url", "tags"]


class WordPressMuPluginForm(NetBoxModelForm):
    site = DynamicModelChoiceField(queryset=WordPressSite.objects.all())

    fieldsets = (FieldSet("site", "name", "repository", "commit", "source_path", "sha256", "description", name="Must-Use Plugin"),)

    class Meta:
        model = WordPressMuPlugin
        fields = ["site", "name", "repository", "commit", "source_path", "sha256", "description", "tags"]


class WordPressThemeForm(NetBoxModelForm):
    site = DynamicModelChoiceField(queryset=WordPressSite.objects.all())

    fieldsets = (FieldSet("site", "slug", "version", "state", "source", "source_url", name="Theme"),)

    class Meta:
        model = WordPressTheme
        fields = ["site", "slug", "version", "state", "source", "source_url", "tags"]


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
    safe_opt = forms.NullBooleanField(required=False)
    enable_hsts = forms.NullBooleanField(required=False)
    tag = TagFilterField(WordPressSite)


class WordPressConstantFilterForm(NetBoxModelFilterSetForm):
    model = WordPressConstant
    site_id = DynamicModelMultipleChoiceField(queryset=WordPressSite.objects.all(), required=False, label="Site")
    value_type = forms.MultipleChoiceField(choices=WPConstantTypeChoices, required=False)
    tag = TagFilterField(WordPressConstant)


class WordPressOptionFilterForm(NetBoxModelFilterSetForm):
    model = WordPressOption
    site_id = DynamicModelMultipleChoiceField(queryset=WordPressSite.objects.all(), required=False, label="Site")
    value_format = forms.MultipleChoiceField(choices=WPOptionFormatChoices, required=False)
    tag = TagFilterField(WordPressOption)


class WordPressPluginFilterForm(NetBoxModelFilterSetForm):
    model = WordPressPlugin
    site_id = DynamicModelMultipleChoiceField(queryset=WordPressSite.objects.all(), required=False, label="Site")
    source = forms.MultipleChoiceField(choices=PluginSourceChoices, required=False)
    state = forms.MultipleChoiceField(choices=PluginStateChoices, required=False)
    tag = TagFilterField(WordPressPlugin)


class WordPressMuPluginFilterForm(NetBoxModelFilterSetForm):
    model = WordPressMuPlugin
    site_id = DynamicModelMultipleChoiceField(queryset=WordPressSite.objects.all(), required=False, label="Site")
    tag = TagFilterField(WordPressMuPlugin)


class WordPressThemeFilterForm(NetBoxModelFilterSetForm):
    model = WordPressTheme
    site_id = DynamicModelMultipleChoiceField(queryset=WordPressSite.objects.all(), required=False, label="Site")
    source = forms.MultipleChoiceField(choices=PluginSourceChoices, required=False)
    state = forms.MultipleChoiceField(choices=PluginStateChoices, required=False)
    tag = TagFilterField(WordPressTheme)


class WordPressContentDirectoryFilterForm(NetBoxModelFilterSetForm):
    model = WordPressContentDirectory
    site_id = DynamicModelMultipleChoiceField(queryset=WordPressSite.objects.all(), required=False, label="Site")
    relocation_state = forms.MultipleChoiceField(choices=RelocationStateChoices, required=False)
    tag = TagFilterField(WordPressContentDirectory)
