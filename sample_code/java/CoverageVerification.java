package com.testable.demo;

public final class CoverageVerification {

    private CoverageVerification() {}

    public static void verifyRouteRequestPaths() {
        PaymentRouter router = new PaymentRouter();
        assert "405".equals(router.route("DELETE", true, false));
        assert "405".equals(router.route("PATCH", false, false));
        assert "200-read".equals(router.route("GET", true, false));
        assert "201-created".equals(router.route("POST", true, false));
        assert "202-accepted".equals(router.route("PUT", true, false));
        assert "401-unauthorized".equals(router.route("GET", false, false));
        assert "401-unauthorized".equals(router.route("GET", true, true));
        assert "401-unauthorized".equals(router.route("POST", false, true));
    }

    public static void verifyEvaluateFlagsCombinations() {
        PaymentRouter router = new PaymentRouter();
        assert "path-alpha".equals(router.evaluateFlags(true, true, false));
        assert "path-alpha".equals(router.evaluateFlags(true, true, true));
        assert "path-alpha".equals(router.evaluateFlags(true, false, true));
        assert "path-alpha".equals(router.evaluateFlags(true, false, false));
        assert "path-beta".equals(router.evaluateFlags(false, true, false));
        assert "path-beta".equals(router.evaluateFlags(false, true, true));
        assert "path-beta".equals(router.evaluateFlags(false, false, true));
        assert "path-default".equals(router.evaluateFlags(false, false, false));
    }

    public static void verifyCompoundConditions() {
        PaymentRouter router = new PaymentRouter();
        assert "401-unauthorized".equals(router.route("GET", true, false == true));
        assert "200-read".equals(router.route("GET", true, false == false));
        assert "path-alpha".equals(router.evaluateFlags(true, true, false == true));
        assert "path-beta".equals(router.evaluateFlags(false, true, false == false));
    }

    public static void runAllVerifications() {
        verifyRouteRequestPaths();
        verifyEvaluateFlagsCombinations();
        verifyCompoundConditions();
    }
}
