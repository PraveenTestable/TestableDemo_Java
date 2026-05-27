package com.testable.demo;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Whitebox verification harness — full path, loop, exception, and logic coverage. */
public final class CoverageVerification {

    private CoverageVerification() {}

    public static void verifyRouteRequestPaths() {
        PaymentRouter router = new PaymentRouter();
        assert "405".equals(router.route("INVALID", true, false));
        assert "401-unauthorized".equals(router.route("GET", false, false));
        assert "429-rate-limited".equals(router.route("GET", true, true));
        assert "200-read".equals(router.route("GET", true, false));
        assert "201-created".equals(router.route("POST", true, false));
        assert "200-updated".equals(router.route("PUT", true, false));
        assert "200-patched".equals(router.route("PATCH", true, false));
        assert "204-deleted".equals(router.route("DELETE", true, false));
    }

    public static void verifyEvaluateFlagsCombinations() {
        PaymentRouter router = new PaymentRouter();
        assert "path-alpha".equals(router.evaluateFlags(true,  true,  true));
        assert "path-alpha".equals(router.evaluateFlags(true,  true,  false));
        assert "path-default".equals(router.evaluateFlags(true,  false, true));
        assert "path-alpha".equals(router.evaluateFlags(true,  false, false));
        assert "path-beta".equals(router.evaluateFlags(false, true,  true));
        assert "path-beta".equals(router.evaluateFlags(false, true,  false));
        assert "path-beta".equals(router.evaluateFlags(false, false, true));
        assert "path-default".equals(router.evaluateFlags(false, false, false));
    }

    public static void verifyCompoundConditions() {
        PaymentRouter router = new PaymentRouter();
        assert "429-rate-limited".equals(router.route("GET", true,  true));
        assert "200-read".equals(router.route("GET",  true,  false));
        assert "path-alpha".equals(router.evaluateFlags(true, true, false));
        assert "path-beta".equals(router.evaluateFlags(false, true, true));
    }

    public static void verifyNestedConditionPaths() {
        PaymentRouter router = new PaymentRouter();
        assert "invalid-method".equals(router.classifyRequest("INVALID", "admin", 0));
        assert "admin-read".equals(router.classifyRequest("GET", "admin", 0));
        assert "admin-write".equals(router.classifyRequest("POST", "admin", 500));
        assert "admin-write".equals(router.classifyRequest("DELETE", "admin", 500));
        assert "admin-payload-too-large".equals(router.classifyRequest("POST", "admin", 2_000_000));
        assert "user-read".equals(router.classifyRequest("GET", "user", 0));
        assert "user-write".equals(router.classifyRequest("POST", "user", 500));
        assert "user-payload-too-large".equals(router.classifyRequest("POST", "user", 50_000));
        assert "user-forbidden".equals(router.classifyRequest("DELETE", "user", 0));
        assert "unknown-role".equals(router.classifyRequest("GET", "unknown", 0));
    }

    public static void verifyExceptionPaths() {
        PaymentRouter router = new PaymentRouter();
        assert router.parseRateLimitHeader("0")       == true;
        assert router.parseRateLimitHeader("10")      == false;
        assert router.parseRateLimitHeader("invalid") == true;
        assert router.parseRateLimitHeader(null)      == true;
        assert router.safeLoadConfig(null).isEmpty();
        Map<String, String> cfg = new HashMap<>();
        cfg.put("timeout", "10");
        cfg.put("retries", "2");
        Map<String, Object> result = router.safeLoadConfig(cfg);
        assert Integer.valueOf(10).equals(result.get("timeout"));
        assert Integer.valueOf(2).equals(result.get("retries"));
    }

    public static void verifyLoopPaths() {
        PaymentRouter router = new PaymentRouter();
        assert router.waitForRetryWindow(3) == 3;
        assert router.waitForRetryWindow(1) == 1;
        List<String> methods = Arrays.asList("GET", "POST", "DELETE", "INVALID");
        Map<String, String> outcomes = router.collectRouteOutcomes(methods, true, false);
        assert "200-read".equals(outcomes.get("GET"));
        assert "201-created".equals(outcomes.get("POST"));
        assert "204-deleted".equals(outcomes.get("DELETE"));
        assert "405".equals(outcomes.get("INVALID"));
        List<String> search = Arrays.asList("INVALID", "GET", "POST");
        assert "GET".equals(router.findFirstAllowed(search, true));
        assert null == router.findFirstAllowed(Arrays.asList("INVALID"), true);
        List<String[]> requests = Arrays.asList(
            new String[]{"POST", "admin", "100"},
            new String[]{"DELETE", "user", "0"},
            new String[]{"GET", "unknown", "0"}
        );
        List<String> results = router.batchClassify(requests);
        assert "admin-write".equals(results.get(0));
        assert "user-forbidden".equals(results.get(1));
        assert "unknown-role".equals(results.get(2));
    }

    public static void runAllVerifications() {
        verifyRouteRequestPaths();
        verifyEvaluateFlagsCombinations();
        verifyCompoundConditions();
        verifyNestedConditionPaths();
        verifyExceptionPaths();
        verifyLoopPaths();
    }
}
