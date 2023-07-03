from setuptools import setup


setup(
    entry_points="""
[pretix.plugin]
pretix_manualseats=pretix_manualseats:PretixPluginMeta
"""
)
