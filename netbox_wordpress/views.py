# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.views import generic

from . import filtersets, forms, models, tables


class WordPressSiteView(generic.ObjectView):
    # NetBox auto-discovers templates/netbox_wordpress/wordpresssite.html (extends generic/object.html).
    queryset = models.WordPressSite.objects.all()


class WordPressSiteListView(generic.ObjectListView):
    queryset = models.WordPressSite.objects.all()
    table = tables.WordPressSiteTable
    filterset = filtersets.WordPressSiteFilterSet
    filterset_form = forms.WordPressSiteFilterForm


class WordPressSiteEditView(generic.ObjectEditView):
    queryset = models.WordPressSite.objects.all()
    form = forms.WordPressSiteForm


class WordPressSiteDeleteView(generic.ObjectDeleteView):
    queryset = models.WordPressSite.objects.all()


class WordPressSiteBulkDeleteView(generic.BulkDeleteView):
    queryset = models.WordPressSite.objects.all()
    table = tables.WordPressSiteTable


class WordPressConstantView(generic.ObjectView):
    queryset = models.WordPressConstant.objects.all()


class WordPressConstantListView(generic.ObjectListView):
    queryset = models.WordPressConstant.objects.all()
    table = tables.WordPressConstantTable
    filterset = filtersets.WordPressConstantFilterSet
    filterset_form = forms.WordPressConstantFilterForm


class WordPressConstantEditView(generic.ObjectEditView):
    queryset = models.WordPressConstant.objects.all()
    form = forms.WordPressConstantForm


class WordPressConstantDeleteView(generic.ObjectDeleteView):
    queryset = models.WordPressConstant.objects.all()


class WordPressConstantBulkDeleteView(generic.BulkDeleteView):
    queryset = models.WordPressConstant.objects.all()
    table = tables.WordPressConstantTable


class WordPressOptionView(generic.ObjectView):
    queryset = models.WordPressOption.objects.all()


class WordPressOptionListView(generic.ObjectListView):
    queryset = models.WordPressOption.objects.all()
    table = tables.WordPressOptionTable
    filterset = filtersets.WordPressOptionFilterSet
    filterset_form = forms.WordPressOptionFilterForm


class WordPressOptionEditView(generic.ObjectEditView):
    queryset = models.WordPressOption.objects.all()
    form = forms.WordPressOptionForm


class WordPressOptionDeleteView(generic.ObjectDeleteView):
    queryset = models.WordPressOption.objects.all()


class WordPressOptionBulkDeleteView(generic.BulkDeleteView):
    queryset = models.WordPressOption.objects.all()
    table = tables.WordPressOptionTable


class WordPressPluginView(generic.ObjectView):
    queryset = models.WordPressPlugin.objects.all()


class WordPressPluginListView(generic.ObjectListView):
    queryset = models.WordPressPlugin.objects.all()
    table = tables.WordPressPluginTable
    filterset = filtersets.WordPressPluginFilterSet
    filterset_form = forms.WordPressPluginFilterForm


class WordPressPluginEditView(generic.ObjectEditView):
    queryset = models.WordPressPlugin.objects.all()
    form = forms.WordPressPluginForm


class WordPressPluginDeleteView(generic.ObjectDeleteView):
    queryset = models.WordPressPlugin.objects.all()


class WordPressPluginBulkDeleteView(generic.BulkDeleteView):
    queryset = models.WordPressPlugin.objects.all()
    table = tables.WordPressPluginTable


class WordPressMuPluginView(generic.ObjectView):
    queryset = models.WordPressMuPlugin.objects.all()


class WordPressMuPluginListView(generic.ObjectListView):
    queryset = models.WordPressMuPlugin.objects.all()
    table = tables.WordPressMuPluginTable
    filterset = filtersets.WordPressMuPluginFilterSet
    filterset_form = forms.WordPressMuPluginFilterForm


class WordPressMuPluginEditView(generic.ObjectEditView):
    queryset = models.WordPressMuPlugin.objects.all()
    form = forms.WordPressMuPluginForm


class WordPressMuPluginDeleteView(generic.ObjectDeleteView):
    queryset = models.WordPressMuPlugin.objects.all()


class WordPressMuPluginBulkDeleteView(generic.BulkDeleteView):
    queryset = models.WordPressMuPlugin.objects.all()
    table = tables.WordPressMuPluginTable


class WordPressThemeView(generic.ObjectView):
    queryset = models.WordPressTheme.objects.all()


class WordPressThemeListView(generic.ObjectListView):
    queryset = models.WordPressTheme.objects.all()
    table = tables.WordPressThemeTable
    filterset = filtersets.WordPressThemeFilterSet
    filterset_form = forms.WordPressThemeFilterForm


class WordPressThemeEditView(generic.ObjectEditView):
    queryset = models.WordPressTheme.objects.all()
    form = forms.WordPressThemeForm


class WordPressThemeDeleteView(generic.ObjectDeleteView):
    queryset = models.WordPressTheme.objects.all()


class WordPressThemeBulkDeleteView(generic.BulkDeleteView):
    queryset = models.WordPressTheme.objects.all()
    table = tables.WordPressThemeTable


class WordPressContentDirectoryView(generic.ObjectView):
    queryset = models.WordPressContentDirectory.objects.all()


class WordPressContentDirectoryListView(generic.ObjectListView):
    queryset = models.WordPressContentDirectory.objects.all()
    table = tables.WordPressContentDirectoryTable
    filterset = filtersets.WordPressContentDirectoryFilterSet
    filterset_form = forms.WordPressContentDirectoryFilterForm


class WordPressContentDirectoryEditView(generic.ObjectEditView):
    queryset = models.WordPressContentDirectory.objects.all()
    form = forms.WordPressContentDirectoryForm


class WordPressContentDirectoryDeleteView(generic.ObjectDeleteView):
    queryset = models.WordPressContentDirectory.objects.all()


class WordPressContentDirectoryBulkDeleteView(generic.BulkDeleteView):
    queryset = models.WordPressContentDirectory.objects.all()
    table = tables.WordPressContentDirectoryTable
