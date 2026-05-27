package com.testable.demo;

import java.util.List;
import java.util.ArrayList;

/**
 * TransactionProcessor: processes financial transactions with retry logic,
 * validation, and comprehensive control-flow paths for whitebox coverage.
 */
public class TransactionProcessor {

    public static final int MAX_RETRIES = 3;
    public static final double MAX_AMOUNT = 10000.0;
    public static final double MIN_AMOUNT = 0.01;

    public enum TransactionStatus {
        SUCCESS, FAILED, PENDING, CANCELLED, TIMEOUT
    }

    public static class TransactionResult {
        private final TransactionStatus status;
        private final String message;
        private final double processedAmount;

        public TransactionResult(TransactionStatus status, String message, double processedAmount) {
            this.status = status;
            this.message = message;
            this.processedAmount = processedAmount;
        }

        public TransactionStatus getStatus() { return status; }
        public String getMessage() { return message; }
        public double getProcessedAmount() { return processedAmount; }
    }

    /**
     * Validates a transaction amount — multiple branch paths.
     */
    public boolean isValidAmount(double amount) {
        if (amount < MIN_AMOUNT) {
            return false;
        }
        if (amount > MAX_AMOUNT) {
            return false;
        }
        return true;
    }

    /**
     * Classifies a transaction by amount tier — decision tree with multiple outcomes.
     */
    public String classifyTransaction(double amount) {
        if (amount < 0) {
            return "INVALID";
        } else if (amount < 100.0) {
            return "MICRO";
        } else if (amount < 1000.0) {
            return "STANDARD";
        } else if (amount < 5000.0) {
            return "LARGE";
        } else if (amount <= MAX_AMOUNT) {
            return "ENTERPRISE";
        } else {
            return "OVER_LIMIT";
        }
    }

    /**
     * Processes a list of transactions with retry logic — loop + exception paths.
     */
    public List<TransactionResult> processBatch(List<Double> amounts, String currency) {
        List<TransactionResult> results = new ArrayList<>();

        if (amounts == null || amounts.isEmpty()) {
            return results;
        }

        if (currency == null || currency.trim().isEmpty()) {
            throw new IllegalArgumentException("Currency must not be null or empty");
        }

        for (double amount : amounts) {
            TransactionResult result = processWithRetry(amount, currency);
            results.add(result);
        }

        return results;
    }

    /**
     * Process a single transaction with retry — while loop + nested conditions.
     */
    public TransactionResult processWithRetry(double amount, String currency) {
        if (!isValidAmount(amount)) {
            return new TransactionResult(
                TransactionStatus.FAILED,
                "Invalid amount: " + amount,
                0.0
            );
        }

        int attempts = 0;
        TransactionResult lastResult = null;

        while (attempts < MAX_RETRIES) {
            attempts++;
            try {
                lastResult = attemptTransaction(amount, currency, attempts);
                if (lastResult.getStatus() == TransactionStatus.SUCCESS) {
                    return lastResult;
                }
            } catch (IllegalStateException e) {
                lastResult = new TransactionResult(
                    TransactionStatus.FAILED,
                    "Attempt " + attempts + " failed: " + e.getMessage(),
                    0.0
                );
            } catch (ArithmeticException e) {
                return new TransactionResult(
                    TransactionStatus.FAILED,
                    "Arithmetic error: " + e.getMessage(),
                    0.0
                );
            }

            if (attempts == MAX_RETRIES && lastResult != null
                    && lastResult.getStatus() != TransactionStatus.SUCCESS) {
                return new TransactionResult(
                    TransactionStatus.TIMEOUT,
                    "Max retries reached after " + attempts + " attempts",
                    0.0
                );
            }
        }

        return lastResult != null ? lastResult :
            new TransactionResult(TransactionStatus.FAILED, "Unknown failure", 0.0);
    }

    /**
     * Simulates a single transaction attempt — deterministic for test coverage.
     */
    private TransactionResult attemptTransaction(double amount, String currency, int attempt) {
        switch (currency) {
            case "USD":
            case "EUR":
            case "GBP":
                if (attempt == 1 && amount > 9000.0) {
                    throw new IllegalStateException("High-value transaction requires review");
                }
                double fee = computeFee(amount, currency);
                return new TransactionResult(
                    TransactionStatus.SUCCESS,
                    "Processed " + amount + " " + currency,
                    amount - fee
                );
            case "XXX":
                throw new IllegalStateException("Currency XXX not accepted");
            default:
                return new TransactionResult(
                    TransactionStatus.FAILED,
                    "Unsupported currency: " + currency,
                    0.0
                );
        }
    }

    /**
     * Computes transaction fee based on currency and tier — multiple nested decisions.
     */
    public double computeFee(double amount, String currency) {
        double baseRate;
        if ("USD".equals(currency)) {
            baseRate = 0.025;
        } else if ("EUR".equals(currency)) {
            baseRate = 0.022;
        } else if ("GBP".equals(currency)) {
            baseRate = 0.020;
        } else {
            baseRate = 0.030;
        }

        double fee = amount * baseRate;

        if (amount >= 5000.0) {
            fee *= 0.90;
        } else if (amount >= 1000.0) {
            fee *= 0.95;
        }

        return Math.max(fee, 0.50);
    }

    /**
     * Summarises batch results — loop with accumulation and conditional aggregation.
     */
    public String summariseBatch(List<TransactionResult> results) {
        if (results == null || results.isEmpty()) {
            return "No transactions processed";
        }

        int succeeded = 0;
        int failed = 0;
        int pending = 0;
        double totalProcessed = 0.0;

        for (TransactionResult r : results) {
            switch (r.getStatus()) {
                case SUCCESS:
                    succeeded++;
                    totalProcessed += r.getProcessedAmount();
                    break;
                case FAILED:
                case TIMEOUT:
                    failed++;
                    break;
                case PENDING:
                    pending++;
                    break;
                default:
                    break;
            }
        }

        return String.format(
            "Total=%d SUCCESS=%d FAILED=%d PENDING=%d Amount=%.2f",
            results.size(), succeeded, failed, pending, totalProcessed
        );
    }
}
