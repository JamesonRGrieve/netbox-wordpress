# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem


def _item(model, label):
    return PluginMenuItem(
        link=f"plugins:netbox_wordpress:{model}_list",
        link_text=label,
        buttons=[
            PluginMenuButton(f"plugins:netbox_wordpress:{model}_add", "Add", "mdi mdi-plus-thick")
        ],
    )


menu = PluginMenu(
    label="WordPress",
    groups=(
        ("Sites", (_item("wordpresssite", "Sites"),)),
        (
            "Content",
            (
                _item("wordpressplugin", "Plugins"),
                _item("wordpresstheme", "Themes"),
                _item("wordpresscontentdirectory", "Content Dirs"),
            ),
        ),
        ("Config", (_item("wordpressconstant", "Constants"),)),
    ),
    icon_class="mdi mdi-wordpress",
)
