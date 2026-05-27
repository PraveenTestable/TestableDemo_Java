package com.testable.demo;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

/**
 * Unit tests for PaymentRouter — exhaustive branch and decision coverage.
 */
@DisplayName("PaymentRouter Unit Tests")
public class PaymentRouterTest {

    private PaymentRouter router;

    @BeforeEach
    void setUp() {
        router = new PaymentRouter();
    }

    // --- route(): HTTP method validation branch ---

    @Test
    @DisplayName("route: unsupported method DELETE returns 405")
    void testRoute_unsupportedMethod_delete_returns405() {
        assertEquals("405", router.route("DELETE", true, false));
    }

    @Test
    @DisplayName("route: unsupported method PATCH returns 405")
    void testRoute_unsupportedMethod_patch_returns405() {
        assertEquals("405", router.route("PATCH", false, false));
    }

    @Test
    @DisplayName("route: unsupported method HEAD returns 405")
    void testRoute_unsupportedMethod_head_returns405() {
        assertEquals("405", router.route("HEAD", true, false));
    }

    @ParameterizedTest
    @ValueSource(strings = {"OPTIONS", "TRACE", "CONNECT", "PUT_INVALID"})
    @DisplayName("route: various unsupported methods return 405")
    void testRoute_unsupportedMethods_return405(String method) {
        assertEquals("405", router.route(method, true, false));
    }

    // --- route(): authorized + not throttled branch ---

    @Test
    @DisplayName("route: GET authorized not-throttled returns 200-read")
    void testRoute_get_authorized_notThrottled_returns200Read() {
        assertEquals("200-read", router.route("GET", true, false));
    }

    @Test
    @DisplayName("route: POST authorized not-throttled returns 201-created")
    void testRoute_post_authorized_notThrottled_returns201Created() {
        assertEquals("201-created", router.route("POST", true, false));
    }

    @Test
    @DisplayName("route: PUT authorized not-throttled returns 202-accepted")
    void testRoute_put_authorized_notThrottled_returns202Accepted() {
        assertEquals("202-accepted", router.route("PUT", true, false));
    }

    // --- route(): unauthorized or throttled branch ---

    @Test
    @DisplayName("route: GET not-authorized returns 401")
    void testRoute_get_notAuthorized_returns401() {
        assertEquals("401-unauthorized", router.route("GET", false, false));
    }

    @Test
    @DisplayName("route: POST authorized but throttled returns 401")
    void testRoute_post_authorized_throttled_returns401() {
        assertEquals("401-unauthorized", router.route("POST", true, true));
    }

    @Test
    @DisplayName("route: PUT not-authorized and throttled returns 401")
    void testRoute_put_notAuthorized_throttled_returns401() {
        assertEquals("401-unauthorized", router.route("PUT", false, true));
    }

    @ParameterizedTest
    @CsvSource({
        "GET,  false, false",
        "GET,  true,  true",
        "POST, false, true",
        "PUT,  false, false",
    })
    @DisplayName("route: unauthorized paths all return 401")
    void testRoute_unauthorizedPaths_return401(String method, boolean authorized, boolean throttled) {
        assertEquals("401-unauthorized", router.route(method, authorized, throttled));
    }

    // --- evaluateFlags(): path-alpha conditions ---

    @Test
    @DisplayName("evaluateFlags: a=T b=T c=F → path-alpha (a&&b true)")
    void testEvaluateFlags_aTrue_bTrue_cFalse_pathAlpha() {
        assertEquals("path-alpha", router.evaluateFlags(true, true, false));
    }

    @Test
    @DisplayName("evaluateFlags: a=T b=F c=F → path-alpha (!c&&a true)")
    void testEvaluateFlags_aTrue_bFalse_cFalse_pathAlpha() {
        assertEquals("path-alpha", router.evaluateFlags(true, false, false));
    }

    @Test
    @DisplayName("evaluateFlags: a=T b=F c=T → path-default")
    void testEvaluateFlags_aTrue_bFalse_cTrue_pathAlpha() {
        // a=T, b=F, c=T: (a&&b)=F, (!c&&a)=(F&&T)=F → first condition false
        // (b||c)&&!a = (T)&&F = F → second condition false
        // → path-default
        assertEquals("path-default", router.evaluateFlags(true, false, true));
    }

    @Test
    @DisplayName("evaluateFlags: a=T b=T c=T → path-alpha (a&&b true)")
    void testEvaluateFlags_aTrue_bTrue_cTrue_pathAlpha() {
        assertEquals("path-alpha", router.evaluateFlags(true, true, true));
    }

    // --- evaluateFlags(): path-beta conditions ---

    @Test
    @DisplayName("evaluateFlags: a=F b=T c=F → path-beta ((b||c)&&!a true)")
    void testEvaluateFlags_aFalse_bTrue_cFalse_pathBeta() {
        assertEquals("path-beta", router.evaluateFlags(false, true, false));
    }

    @Test
    @DisplayName("evaluateFlags: a=F b=F c=T → path-beta ((b||c)&&!a true)")
    void testEvaluateFlags_aFalse_bFalse_cTrue_pathBeta() {
        assertEquals("path-beta", router.evaluateFlags(false, false, true));
    }

    @Test
    @DisplayName("evaluateFlags: a=F b=T c=T → path-beta ((b||c)&&!a true)")
    void testEvaluateFlags_aFalse_bTrue_cTrue_pathBeta() {
        assertEquals("path-beta", router.evaluateFlags(false, true, true));
    }

    // --- evaluateFlags(): path-default ---

    @Test
    @DisplayName("evaluateFlags: a=F b=F c=F → path-default (all conditions false)")
    void testEvaluateFlags_allFalse_pathDefault() {
        assertEquals("path-default", router.evaluateFlags(false, false, false));
    }

    // --- Truth table: all 8 combinations ---

    @ParameterizedTest
    @CsvSource({
        "true,  true,  true,  path-alpha",
        "true,  true,  false, path-alpha",
        "true,  false, false, path-alpha",
        "false, true,  false, path-beta",
        "false, true,  true,  path-beta",
        "false, false, true,  path-beta",
        "false, false, false, path-default",
    })
    @DisplayName("evaluateFlags: truth table coverage")
    void testEvaluateFlags_truthTable(boolean a, boolean b, boolean c, String expected) {
        assertEquals(expected, router.evaluateFlags(a, b, c));
    }

    // --- assertNotNull sanity ---

    @Test
    @DisplayName("router instance is not null")
    void testRouterNotNull() {
        assertNotNull(router);
    }

    @Test
    @DisplayName("route always returns non-null, non-empty string")
    void testRoute_alwaysReturnsNonNull() {
        String result = router.route("GET", true, false);
        assertNotNull(result);
        assertFalse(result.isEmpty());
    }
}
