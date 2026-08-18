# =========================================================
# FILE: tests/test_login.py
# =========================================================

import pytest
import allure

from base.base_test import BaseTest

from testdata.test_data import (
    VALID_LOGIN,
    INVALID_OTP_USERS,
    SHORT_OTP_USERS,
)


# =========================================================
# TEST DATA (built from testdata/test_data.py so there is
# a single source of truth for mobile numbers / OTPs)
#
# ROOT CAUSE FIX: invalid_otp/short_otp cases require the app to
# start logged OUT so the OTP sheet is actually reached — otherwise
# noReset=true's preserved session makes login() take the
# already-logged-in fast path and the test can never validate
# anything. These parameter sets are marked `requires_logout`,
# which the `driver` fixture (conftest.py) uses to automatically
# clear app data ONLY for these specific test runs — reset happens
# automatically where it's genuinely required, and nowhere else.
# This replaces the previous unconditional pytest.skip().
# =========================================================

TEST_USERS = (
        [(VALID_LOGIN["mobile"], VALID_LOGIN["otp"], "valid_login")]
        + [
            pytest.param(mobile, otp, "invalid_otp", marks=pytest.mark.requires_logout)
            for mobile, otp in INVALID_OTP_USERS
        ]
        + [
            pytest.param(mobile, otp, "short_otp", marks=pytest.mark.requires_logout)
            for mobile, otp in SHORT_OTP_USERS
        ]
)


# =========================================================
# LOGIN TEST CLASS
# =========================================================

@allure.feature("Login Flow")
class TestLogin(BaseTest):

    # =====================================================
    # LOGIN WITH MULTIPLE USERS
    # =====================================================

    @pytest.mark.login
    @pytest.mark.regression
    @pytest.mark.parametrize(
        "mobile_number,otp,test_type",
        TEST_USERS
    )
    @allure.title("Login Validation Test")
    def test_login_with_multiple_users(
            self,
            mobile_number,
            otp,
            test_type
    ):

        self.logger.info(
            "========== LOGIN TEST START =========="
        )

        self.logger.info(
            f"TEST TYPE: {test_type}"
        )

        # invalid_otp/short_otp parameter sets are marked
        # @pytest.mark.requires_logout — the driver fixture already
        # cleared app data before this test's session started, so the
        # login sheet is guaranteed to open for real instead of taking
        # the already-logged-in fast path. No skip needed.

        # =================================================
        # VALID LOGIN
        # =================================================

        if test_type == "valid_login":

            result = self.login_page.login(
                mobile_number=mobile_number,
                otp=otp
            )

            assert result is True

            self.logger.info(
                "VALID LOGIN SUCCESS"
            )

        # =================================================
        # INVALID OTP
        # =================================================

        elif test_type == "invalid_otp":

            with pytest.raises(Exception):

                self.login_page.login(
                    mobile_number=mobile_number,
                    otp=otp
                )

            self.logger.info(
                "INVALID OTP VALIDATION SUCCESS"
            )

        # =================================================
        # SHORT OTP
        # =================================================

        elif test_type == "short_otp":

            with pytest.raises(Exception):

                self.login_page.login(
                    mobile_number=mobile_number,
                    otp=otp
                )

            self.logger.info(
                "SHORT OTP VALIDATION SUCCESS"
            )

        self.logger.info(
            "========== LOGIN TEST END =========="
        )

    # =====================================================
    # ONLY VALID LOGIN
    # =====================================================

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.login
    @allure.title("Valid Login Smoke Test")
    def test_valid_login_smoke(self):

        self.logger.info(
            "========== SMOKE LOGIN START =========="
        )

        result = self.login_default_user()

        assert result is True

        self.logger.info(
            "========== SMOKE LOGIN SUCCESS =========="
        )

    # =====================================================
    # INVALID OTP TEST
    # =====================================================

    @pytest.mark.login
    @pytest.mark.requires_logout
    @allure.title("Invalid OTP Validation")
    def test_invalid_otp(self):

        self.logger.info(
            "========== INVALID OTP TEST =========="
        )

        # requires_logout marker (see conftest.py `driver` fixture)
        # clears app data before this test's session, guaranteeing a
        # logged-out start regardless of the global NO_RESET setting.

        mobile, otp = INVALID_OTP_USERS[0]

        with pytest.raises(Exception):

            self.login_page.login(
                mobile_number=mobile,
                otp=otp
            )

        self.logger.info(
            "========== INVALID OTP PASSED =========="
        )