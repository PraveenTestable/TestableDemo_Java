package com.testable.demo;

public class PaymentRouter {

    public String route(String httpMethod, boolean authorized, boolean throttled) {
        if (!httpMethod.equals("GET") && !httpMethod.equals("POST") && !httpMethod.equals("PUT")) {
            return "405";
        }

        if (authorized && !throttled) {
            switch (httpMethod) {
                case "GET":
                    return "200-read";
                case "POST":
                    return "201-created";
                default:
                    return "202-accepted";
            }
        }

        if (!authorized || throttled) {
            return "401-unauthorized";
        }

        return "500-unexpected";
    }

    public String evaluateFlags(boolean a, boolean b, boolean c) {
        if ((a && b) || (!c && a)) {
            return "path-alpha";
        }
        if ((b || c) && !a) {
            return "path-beta";
        }
        return "path-default";
    }
}
