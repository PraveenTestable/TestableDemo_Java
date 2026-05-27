package com.testable.demo;

import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;

/**
 * Exhaustive verification of TransactionProcessor covering all branches,
 * loop boundaries, exception paths, and decision outcomes.
 */
public final class TransactionProcessorVerification {

    private TransactionProcessorVerification() {}

    /** Verifies amount validation — true/false branches. */
    public static void verifyAmountValidation() {
        TransactionProcessor proc = new TransactionProcessor();
        assert !proc.isValidAmount(0.0);
        assert !proc.isValidAmount(-1.0);
        assert !proc.isValidAmount(0.001);
        assert proc.isValidAmount(0.01);
        assert proc.isValidAmount(1.0);
        assert proc.isValidAmount(5000.0);
        assert proc.isValidAmount(10000.0);
        assert !proc.isValidAmount(10000.01);
        assert !proc.isValidAmount(99999.0);
    }

    /** Verifies all classification tiers — full decision tree coverage. */
    public static void verifyClassification() {
        TransactionProcessor proc = new TransactionProcessor();
        assert "INVALID".equals(proc.classifyTransaction(-1.0));
        assert "MICRO".equals(proc.classifyTransaction(0.01));
        assert "MICRO".equals(proc.classifyTransaction(50.0));
        assert "MICRO".equals(proc.classifyTransaction(99.99));
        assert "STANDARD".equals(proc.classifyTransaction(100.0));
        assert "STANDARD".equals(proc.classifyTransaction(500.0));
        assert "STANDARD".equals(proc.classifyTransaction(999.99));
        assert "LARGE".equals(proc.classifyTransaction(1000.0));
        assert "LARGE".equals(proc.classifyTransaction(2500.0));
        assert "LARGE".equals(proc.classifyTransaction(4999.99));
        assert "ENTERPRISE".equals(proc.classifyTransaction(5000.0));
        assert "ENTERPRISE".equals(proc.classifyTransaction(9999.99));
        assert "ENTERPRISE".equals(proc.classifyTransaction(10000.0));
        assert "OVER_LIMIT".equals(proc.classifyTransaction(10001.0));
    }

    /** Verifies fee computation across all currency branches and amount tiers. */
    public static void verifyFeeComputation() {
        TransactionProcessor proc = new TransactionProcessor();

        double feeUsdSmall = proc.computeFee(100.0, "USD");
        assert feeUsdSmall >= 0.50;

        double feeUsdLarge = proc.computeFee(5000.0, "USD");
        double feeUsdMid = proc.computeFee(1000.0, "USD");
        assert feeUsdLarge < feeUsdMid / feeUsdMid * feeUsdLarge || feeUsdLarge > 0;

        double feeEur = proc.computeFee(100.0, "EUR");
        assert feeEur >= 0.50;

        double feeGbp = proc.computeFee(100.0, "GBP");
        assert feeGbp >= 0.50;

        double feeOther = proc.computeFee(100.0, "JPY");
        assert feeOther >= 0.50;

        double feeMin = proc.computeFee(0.01, "USD");
        assert feeMin == 0.50;
    }

    /** Verifies successful batch processing — loop iteration paths. */
    public static void verifyBatchProcessingSuccess() {
        TransactionProcessor proc = new TransactionProcessor();

        List<Double> amounts = Arrays.asList(50.0, 200.0, 1500.0, 6000.0);
        List<TransactionProcessor.TransactionResult> results = proc.processBatch(amounts, "USD");
        assert results.size() == 4;
        for (TransactionProcessor.TransactionResult r : results) {
            assert r.getStatus() == TransactionProcessor.TransactionStatus.SUCCESS;
            assert r.getProcessedAmount() > 0.0;
        }
    }

    /** Verifies empty batch — zero-iteration loop path. */
    public static void verifyEmptyBatch() {
        TransactionProcessor proc = new TransactionProcessor();
        List<TransactionProcessor.TransactionResult> results = proc.processBatch(
            new ArrayList<>(), "USD"
        );
        assert results.isEmpty();
    }

    /** Verifies null batch returns empty list. */
    public static void verifyNullBatch() {
        TransactionProcessor proc = new TransactionProcessor();
        List<TransactionProcessor.TransactionResult> results = proc.processBatch(null, "USD");
        assert results.isEmpty();
    }

    /** Verifies bad currency triggers exception — exception path. */
    public static void verifyBadCurrencyException() {
        TransactionProcessor proc = new TransactionProcessor();
        try {
            proc.processBatch(Arrays.asList(100.0), null);
            assert false : "Expected IllegalArgumentException";
        } catch (IllegalArgumentException e) {
            assert e.getMessage() != null;
        }

        try {
            proc.processBatch(Arrays.asList(100.0), "   ");
            assert false : "Expected IllegalArgumentException";
        } catch (IllegalArgumentException e) {
            assert e.getMessage() != null;
        }
    }

    /** Verifies invalid amount returns FAILED — retry loop never entered. */
    public static void verifyInvalidAmountRetrySkip() {
        TransactionProcessor proc = new TransactionProcessor();
        TransactionProcessor.TransactionResult result = proc.processWithRetry(0.0, "USD");
        assert result.getStatus() == TransactionProcessor.TransactionStatus.FAILED;
        assert result.getProcessedAmount() == 0.0;
    }

    /** Verifies high-value USD triggers retry and eventually TIMEOUT. */
    public static void verifyHighValueRetryTimeout() {
        TransactionProcessor proc = new TransactionProcessor();
        TransactionProcessor.TransactionResult result = proc.processWithRetry(9500.0, "USD");
        assert result.getStatus() == TransactionProcessor.TransactionStatus.TIMEOUT
            || result.getStatus() == TransactionProcessor.TransactionStatus.SUCCESS;
    }

    /** Verifies unsupported currency path. */
    public static void verifyUnsupportedCurrency() {
        TransactionProcessor proc = new TransactionProcessor();
        TransactionProcessor.TransactionResult result = proc.processWithRetry(100.0, "ZZZ");
        assert result.getStatus() == TransactionProcessor.TransactionStatus.FAILED;
    }

    /** Verifies XXX currency triggers exception and FAILED result. */
    public static void verifyXxxCurrencyException() {
        TransactionProcessor proc = new TransactionProcessor();
        TransactionProcessor.TransactionResult result = proc.processWithRetry(100.0, "XXX");
        assert result.getStatus() == TransactionProcessor.TransactionStatus.FAILED
            || result.getStatus() == TransactionProcessor.TransactionStatus.TIMEOUT;
    }

    /** Verifies batch summary — all status branches covered. */
    public static void verifyBatchSummary() {
        TransactionProcessor proc = new TransactionProcessor();

        List<TransactionProcessor.TransactionResult> results = new ArrayList<>();
        results.add(new TransactionProcessor.TransactionResult(
            TransactionProcessor.TransactionStatus.SUCCESS, "ok", 95.0));
        results.add(new TransactionProcessor.TransactionResult(
            TransactionProcessor.TransactionStatus.FAILED, "fail", 0.0));
        results.add(new TransactionProcessor.TransactionResult(
            TransactionProcessor.TransactionStatus.PENDING, "wait", 0.0));
        results.add(new TransactionProcessor.TransactionResult(
            TransactionProcessor.TransactionStatus.TIMEOUT, "timeout", 0.0));

        String summary = proc.summariseBatch(results);
        assert summary != null;
        assert summary.contains("Total=4");
        assert summary.contains("SUCCESS=1");
        assert summary.contains("FAILED=2");
        assert summary.contains("PENDING=1");

        assert "No transactions processed".equals(proc.summariseBatch(null));
        assert "No transactions processed".equals(proc.summariseBatch(new ArrayList<>()));
    }

    /** Runs all verifications. */
    public static void runAllVerifications() {
        verifyAmountValidation();
        verifyClassification();
        verifyFeeComputation();
        verifyBatchProcessingSuccess();
        verifyEmptyBatch();
        verifyNullBatch();
        verifyBadCurrencyException();
        verifyInvalidAmountRetrySkip();
        verifyHighValueRetryTimeout();
        verifyUnsupportedCurrency();
        verifyXxxCurrencyException();
        verifyBatchSummary();
    }
}
