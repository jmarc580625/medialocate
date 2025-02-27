"""Configuration parameters for the MediaLocate application.

This module defines constants and paths used throughout the MediaLocate application,
including directory structures, file names, and resource locations. It centralizes
all configuration parameters to maintain consistency across the application.
"""

import os

RESSOURCES_ROOT_DIR = "res"

MEDIALOCATION = "medialocate"
MEDIALOCATION_DIR = f".{MEDIALOCATION}"
MEDIALOCATION_STORE_NAME = f"{MEDIALOCATION}.json"
MEDIALOCATION_STORE_PATH = os.path.join(MEDIALOCATION_DIR, MEDIALOCATION_STORE_NAME)
MEDIALOCATION_RES_DIR = os.path.join(RESSOURCES_ROOT_DIR, MEDIALOCATION)
MEDIALOCATION_PAGE = f"{MEDIALOCATION}.html"
MEDIALOCATION_PAGE_DATA = f"{MEDIALOCATION}.js"
MEDIALOCATION_PAGE_PROLOG = f"{MEDIALOCATION}_prolog.html"
MEDIALOCATION_PAGE_EPILOG = f"{MEDIALOCATION}_epilog.html"

MEDIAGROUPS = "mediagroup"
MEDIAGROUPS_STORE_NAME = f"{MEDIAGROUPS}.json"
MEDIAGROUPS_STORE_PATH = os.path.join(MEDIALOCATION_DIR, MEDIAGROUPS_STORE_NAME)
MEDIAGROUPS_RES_DIR = os.path.join(RESSOURCES_ROOT_DIR, MEDIAGROUPS)

MEDIAPROXIES = "mediaproxy"
MEDIAPROXIES_STORE_NAME = f"{MEDIAPROXIES}.json"
MEDIAPROXIES_STORE_PATH = os.path.join(MEDIALOCATION_DIR, MEDIAPROXIES_STORE_NAME)
MEDIAPROXIES_RES_DIR = os.path.join(RESSOURCES_ROOT_DIR, MEDIAPROXIES)
