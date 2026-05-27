package com.testable.demo;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Control flow sample: routing, nested conditions, loops, exception handling,
 * and compound logical sub-expressions.
 */
public class PaymentRouter {

    public static final java.util.Set<String> VALID_METHODS =
        new java.util.HashSet<>(java.util.Arrays.asList("GET", "POST", "PUT", "PATCH", "DELETE"));

    // -----------------------------------------------------------------------
    // Core routing — branch + condition coverage (8 distinct paths)
    // -----------------------------------------------------------------------

    public String route(String method, boolean authenticated, boolean rateLimited) {
        if (!VALID_METHODS.contains(method)) {
            return "405";
        }
        if (!authenticated) {
            return "401-unauthorized";
        }
        if (rateLimited) {
            return "429-rate-limited";
        }
        switch (method) {
            case "GET":    return "200-read";
            case "POST":   return "201-created";
            case "PUT":    return "200-updated";
            case "PATCH":  return "200-patched";
            default:       return "204-deleted";
        }
    }

    // -----------------------------------------------------------------------
    // Compound logical sub-expression coverage
    // -----------------------------------------------------------------------

    public String evaluateFlags(boolean a, boolean b, boolean c) {
        if ((a && b) || (!c && a)) {
            return "path-alpha";
        }
        if ((b || c) && !a) {
            return "path-beta";
        }
        return "path-default";
    }

    // -----------------------------------------------------------------------
    // Nested condition path testing
    // -----------------------------------------------------------------------

    public String classifyRequest(String method, String role, int payloadSize) {
        if (!VALID_METHODS.contains(method)) {
            return "invalid-method";
        }
        if ("admin".equals(role)) {
            if (java.util.Arrays.asList("POST", "PUT", "PATCH", "DELETE").contains(method)) {
                if (payloadSize > 1_000_000) {
                    return "admin-payload-too-large";
                }
                return "admin-write";
            }
            return "admin-read";
        }
        if ("user".equals(role)) {
            if (java.util.Arrays.asList("POST", "PUT", "PATCH").contains(method)) {
                if (payloadSize > 10_000) {
                    return "user-payload-too-large";
                }
                return "user-write";
            }
            if ("DELETE".equals(method)) {
                return "user-forbidden";
            }
            return "user-read";
        }
        return "unknown-role";
    }

    // -----------------------------------------------------------------------
    // Exception path handling
    // -----------------------------------------------------------------------

    public boolean parseRateLimitHeader(String value) {
        if (value == null) {
            return true;
        }
        try {
            int limit = Integer.parseInt(value.trim());
            if (limit < 0) {
                throw new IllegalArgumentException("Rate limit cannot be negative: " + limit);
            }
            return limit == 0;
        } catch (NumberFormatException e) {
            return true;
        }
    }

    public Map<String, Object> safeLoadConfig(Map<String, String> data) {
        if (data == null) {
            return new HashMap<>();
        }
        try {
            int timeout  = Integer.parseInt(data.getOrDefault("timeout",  "30"));
            int retries  = Integer.parseInt(data.getOrDefault("retries",  "3"));
            if (timeout <= 0 || retries < 0) {
                throw new IllegalArgumentException("timeout must be > 0 and retries >= 0");
            }
            Map<String, Object> result = new HashMap<>();
            result.put("timeout", timeout);
            result.put("retries", retries);
            return result;
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid config value: " + e.getMessage(), e);
        }
    }

    // -----------------------------------------------------------------------
    // Loop condition testing
    // -----------------------------------------------------------------------

    public Map<String, String> collectRouteOutcomes(
            List<String> methods, boolean authenticated, boolean rateLimited) {
        Map<String, String> outcomes = new HashMap<>();
        for (String method : methods) {
            outcomes.put(method, route(method, authenticated, rateLimited));
        }
        return outcomes;
    }

    public int waitForRetryWindow(int maxAttempts) {
        int attempt = 0;
        while (attempt < maxAttempts) {
            attempt++;
            if (attempt == maxAttempts) {
                break;
            }
        }
        return attempt;
    }

    public String findFirstAllowed(List<String> methods, boolean authenticated) {
        for (String method : methods) {
            String result = route(method, authenticated, false);
            if (!result.startsWith("4") && !result.startsWith("5")) {
                return method;
            }
        }
        return null;
    }

    public List<String> batchClassify(List<String[]> requests) {
        List<String> results = new ArrayList<>();
        for (String[] req : requests) {
            String method = req[0];
            String role   = req[1];
            int size      = Integer.parseInt(req[2]);
            results.add(classifyRequest(method, role, size));
        }
        return results;
    }
}
