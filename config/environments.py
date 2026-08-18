# =========================================================
# FILE: config/environments.py
#
# CHANGES (iOS support / driver-management improvement):
#   - Each environment now carries a nested "android" and
#     "ios" block instead of flat appPackage/appActivity
#     keys. driver_factory.py picks the right block based
#     on the selected device's "platform" (from
#     device_config.py), so QA/Staging/Prod each know both
#     their Android apkPath AND their iOS bundleId/appPath
#     without needing separate env dictionaries per platform.
#   - featureFlags stay top-level (shared across platforms —
#     a feature flag is a backend/product concept, not an
#     OS concept).
#   - get_env() signature/behaviour is unchanged, so any
#     existing caller of get_env(name) keeps working; only
#     the shape of the returned dict's app-identity fields
#     changed (nested under "android"/"ios" instead of flat).
# =========================================================

import os

ENVIRONMENTS = {

    # =====================================================
    # QA — Debug builds, internal test servers
    # =====================================================

    "qa": {
        "android": {
            "appPackage":  "com.zee5.hipi",
            "appActivity": "com.creatoreconomy.MainActivity",
            "apkPath":     os.getenv("QA_APK_PATH", "resources/apps/hipi_qa.apk"),
            "buildType":   "debug",
        },
        "ios": {
            "bundleId": os.getenv("QA_IOS_BUNDLE_ID", "com.zee5.hipi.qa"),
            "appPath":  os.getenv("QA_IPA_PATH", "resources/apps/hipi_qa.app"),
        },
        "featureFlags": {
            "casting_enabled":   True,
            "rewards_enabled":   True,
            "brand_marketplace": False,   # Not live on QA yet
        },
    },

    # =====================================================
    # STAGING — Release builds, staging servers
    # =====================================================

    "staging": {
        "android": {
            "appPackage":  "com.zee5.hipi",
            "appActivity": "com.creatoreconomy.MainActivity",
            "apkPath":     os.getenv("STAGING_APK_PATH", "resources/apps/hipi_staging.apk"),
            "buildType":   "release",
        },
        "ios": {
            "bundleId": os.getenv("STAGING_IOS_BUNDLE_ID", "com.zee5.hipi.staging"),
            "appPath":  os.getenv("STAGING_IPA_PATH", "resources/apps/hipi_staging.app"),
        },
        "featureFlags": {
            "casting_enabled":   True,
            "rewards_enabled":   True,
            "brand_marketplace": True,
        },
    },

    # =====================================================
    # PRODUCTION — Release builds, production servers
    # Run ONLY smoke tests against production.
    # =====================================================

    "production": {
        "android": {
            "appPackage":  "com.zee5.hipi",
            "appActivity": "com.creatoreconomy.MainActivity",
            "apkPath":     os.getenv("PROD_APK_PATH", "resources/apps/hipi_prod.apk"),
            "buildType":   "release",
        },
        "ios": {
            "bundleId": os.getenv("PROD_IOS_BUNDLE_ID", "com.zee5.hipi"),
            "appPath":  os.getenv("PROD_IPA_PATH", "resources/apps/hipi_prod.app"),
        },
        "featureFlags": {
            "casting_enabled":   True,
            "rewards_enabled":   True,
            "brand_marketplace": True,
        },
    },
}

# Active environment — read from ENV var so CI/CD sets it
# without touching code. Defaults to "qa".
ACTIVE_ENV = os.getenv("TEST_ENV", "qa")


def get_env(env_name: str = None) -> dict:
    """
    Returns the config dict for the given environment name.
    Falls back to ACTIVE_ENV if no name is provided.
    Raises ValueError for unknown environment names.
    """
    name = env_name or ACTIVE_ENV
    if name not in ENVIRONMENTS:
        raise ValueError(
            f"Unknown environment '{name}'. "
            f"Valid options: {list(ENVIRONMENTS.keys())}"
        )
    return ENVIRONMENTS[name]
