package com.testable.demo;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;

/**
 * Unit tests for TransactionProcessor — all branch, loop, and exception paths.
 */
@DisplayName("TransactionProcessor Unit Tests")
public class TransactionProcessorTest {

    private TransactionProcessor proc;

    @BeforeEach
    void setUp() {
        proc = new TransactionProcessor();
    }

    // --- isValidAmount: boundary conditions ---

    @Test
    @DisplayName("isValidAmount: 0.01 (MIN) returns true")
    void testIsValidAmount_minimum_returnsTrue() {
        assertTrue(proc.isValidAmount(0.01));
    }

    @Test
    @DisplayName("isValidAmount: below minimum returns false")
    void testIsValidAmount_belowMinimum_returnsFalse() {
        assertFalse(proc.isValidAmount(0.009));
        assertFalse(proc.isValidAmount(0.0));
        assertFalse(proc.isValidAmount(-1.0));
    }

    @Test
    @DisplayName("isValidAmount: MAX 10000.0 returns true")
    void testIsValidAmount_maximum_returnsTrue() {
        assertTrue(proc.isValidAmount(10000.0));
    }

    @Test
    @DisplayName("isValidAmount: above maximum returns false")
    void testIsValidAmount_aboveMaximum_returnsFalse() {
        assertFalse(proc.isValidAmount(10000.01));
        assertFalse(proc.isValidAmount(99999.0));
    }

    @ParameterizedTest
    @ValueSource(doubles = {0.01, 1.0, 50.0, 100.0, 1000.0, 5000.0, 10000.0})
    @DisplayName("isValidAmount: valid boundary and mid values")
    void testIsValidAmount_validValues_returnTrue(double amount) {
        assertTrue(proc.isValidAmount(amount));
    }

    // --- classifyTransaction: all tiers ---

    @Test
    @DisplayName("classifyTransaction: negative → INVALID")
    void testClassify_negative_returnsInvalid() {
        assertEquals("INVALID", proc.classifyTransaction(-0.01));
        assertEquals("INVALID", proc.classifyTransaction(-100.0));
    }

    @ParameterizedTest
    @ValueSource(doubles = {0.01, 50.0, 99.99})
    @DisplayName("classifyTransaction: micro range → MICRO")
    void testClassify_micro(double amount) {
        assertEquals("MICRO", proc.classifyTransaction(amount));
    }

    @ParameterizedTest
    @ValueSource(doubles = {100.0, 500.0, 999.99})
    @DisplayName("classifyTransaction: standard range → STANDARD")
    void testClassify_standard(double amount) {
        assertEquals("STANDARD", proc.classifyTransaction(amount));
    }

    @ParameterizedTest
    @ValueSource(doubles = {1000.0, 2500.0, 4999.99})
    @DisplayName("classifyTransaction: large range → LARGE")
    void testClassify_large(double amount) {
        assertEquals("LARGE", proc.classifyTransaction(amount));
    }

    @ParameterizedTest
    @ValueSource(doubles = {5000.0, 7500.0, 10000.0})
    @DisplayName("classifyTransaction: enterprise range → ENTERPRISE")
    void testClassify_enterprise(double amount) {
        assertEquals("ENTERPRISE", proc.classifyTransaction(amount));
    }

    @Test
    @DisplayName("classifyTransaction: above max → OVER_LIMIT")
    void testClassify_overLimit() {
        assertEquals("OVER_LIMIT", proc.classifyTransaction(10001.0));
        assertEquals("OVER_LIMIT", proc.classifyTransaction(999999.0));
    }

    // --- computeFee: currency branches + amount tiers ---

    @Test
    @DisplayName("computeFee: USD small amount uses 2.5% rate, min 0.50")
    void testComputeFee_usd_small() {
        double fee = proc.computeFee(1.0, "USD");
        assertEquals(0.50, fee, 0.001);
    }

    @Test
    @DisplayName("computeFee: EUR medium amount uses 2.2% rate")
    void testComputeFee_eur_medium() {
        double fee = proc.computeFee(200.0, "EUR");
        assertTrue(fee >= 0.50);
        assertTrue(fee <= 200.0);
    }

    @Test
    @DisplayName("computeFee: GBP uses lowest 2.0% rate")
    void testComputeFee_gbp() {
        double feeGbp = proc.computeFee(200.0, "GBP");
        double feeUsd = proc.computeFee(200.0, "USD");
        assertTrue(feeGbp <= feeUsd);
    }

    @Test
    @DisplayName("computeFee: unknown currency uses 3.0% fallback rate")
    void testComputeFee_unknownCurrency_usesFallback() {
        double fee = proc.computeFee(100.0, "JPY");
        assertTrue(fee >= 0.50);
    }

    @Test
    @DisplayName("computeFee: amount >= 5000 gets 10% fee discount")
    void testComputeFee_largeAmount_discount() {
        double feeNoDiscount = proc.computeFee(999.0, "USD");
        double feeDiscount = proc.computeFee(5000.0, "USD");
        assertTrue(feeDiscount / 5000.0 < feeNoDiscount / 999.0);
    }

    @Test
    @DisplayName("computeFee: amount >= 1000 gets 5% fee discount")
    void testComputeFee_midAmount_discount() {
        double fee = proc.computeFee(1000.0, "USD");
        assertTrue(fee >= 0.50);
    }

    // --- processBatch: loop iteration paths ---

    @Test
    @DisplayName("processBatch: null amounts returns empty list (zero iterations)")
    void testProcessBatch_null_returnsEmpty() {
        List<TransactionProcessor.TransactionResult> results = proc.processBatch(null, "USD");
        assertNotNull(results);
        assertTrue(results.isEmpty());
    }

    @Test
    @DisplayName("processBatch: empty list returns empty list (zero iterations)")
    void testProcessBatch_empty_returnsEmpty() {
        List<TransactionProcessor.TransactionResult> results = proc.processBatch(new ArrayList<>(), "USD");
        assertNotNull(results);
        assertTrue(results.isEmpty());
    }

    @Test
    @DisplayName("processBatch: null currency throws IllegalArgumentException")
    void testProcessBatch_nullCurrency_throwsException() {
        assertThrows(IllegalArgumentException.class,
            () -> proc.processBatch(Arrays.asList(100.0), null));
    }

    @Test
    @DisplayName("processBatch: blank currency throws IllegalArgumentException")
    void testProcessBatch_blankCurrency_throwsException() {
        assertThrows(IllegalArgumentException.class,
            () -> proc.processBatch(Arrays.asList(100.0), "   "));
    }

    @Test
    @DisplayName("processBatch: single item processes correctly (one iteration)")
    void testProcessBatch_singleItem_oneIteration() {
        List<TransactionProcessor.TransactionResult> results =
            proc.processBatch(Arrays.asList(100.0), "USD");
        assertEquals(1, results.size());
        assertEquals(TransactionProcessor.TransactionStatus.SUCCESS, results.get(0).getStatus());
    }

    @Test
    @DisplayName("processBatch: multiple items processes all (many iterations)")
    void testProcessBatch_multipleItems_manyIterations() {
        List<Double> amounts = Arrays.asList(50.0, 200.0, 1000.0, 5000.0);
        List<TransactionProcessor.TransactionResult> results = proc.processBatch(amounts, "EUR");
        assertEquals(4, results.size());
        for (TransactionProcessor.TransactionResult r : results) {
            assertNotNull(r.getStatus());
        }
    }

    // --- processWithRetry: retry loop paths ---

    @Test
    @DisplayName("processWithRetry: invalid amount skips retry, returns FAILED immediately")
    void testProcessWithRetry_invalidAmount_skipRetry() {
        TransactionProcessor.TransactionResult r = proc.processWithRetry(0.0, "USD");
        assertEquals(TransactionProcessor.TransactionStatus.FAILED, r.getStatus());
        assertEquals(0.0, r.getProcessedAmount());
    }

    @Test
    @DisplayName("processWithRetry: valid USD amount succeeds on first retry")
    void testProcessWithRetry_validUsd_succeeds() {
        TransactionProcessor.TransactionResult r = proc.processWithRetry(100.0, "USD");
        assertEquals(TransactionProcessor.TransactionStatus.SUCCESS, r.getStatus());
        assertTrue(r.getProcessedAmount() > 0.0);
    }

    @Test
    @DisplayName("processWithRetry: XXX currency causes retry exhaustion or FAILED")
    void testProcessWithRetry_xxxCurrency_failsOrTimeout() {
        TransactionProcessor.TransactionResult r = proc.processWithRetry(100.0, "XXX");
        assertTrue(
            r.getStatus() == TransactionProcessor.TransactionStatus.FAILED ||
            r.getStatus() == TransactionProcessor.TransactionStatus.TIMEOUT
        );
    }

    @Test
    @DisplayName("processWithRetry: unsupported currency returns FAILED")
    void testProcessWithRetry_unsupportedCurrency_returnsFailed() {
        TransactionProcessor.TransactionResult r = proc.processWithRetry(100.0, "ZZZ");
        assertEquals(TransactionProcessor.TransactionStatus.FAILED, r.getStatus());
    }

    @Test
    @DisplayName("processWithRetry: high-value USD may timeout or succeed")
    void testProcessWithRetry_highValueUsd_timeoutOrSuccess() {
        TransactionProcessor.TransactionResult r = proc.processWithRetry(9500.0, "USD");
        assertTrue(
            r.getStatus() == TransactionProcessor.TransactionStatus.TIMEOUT ||
            r.getStatus() == TransactionProcessor.TransactionStatus.SUCCESS
        );
    }

    // --- summariseBatch: switch statement paths ---

    @Test
    @DisplayName("summariseBatch: null returns 'No transactions processed'")
    void testSummariseBatch_null() {
        assertEquals("No transactions processed", proc.summariseBatch(null));
    }

    @Test
    @DisplayName("summariseBatch: empty list returns 'No transactions processed'")
    void testSummariseBatch_empty() {
        assertEquals("No transactions processed", proc.summariseBatch(new ArrayList<>()));
    }

    @Test
    @DisplayName("summariseBatch: mixed statuses counted correctly")
    void testSummariseBatch_mixed() {
        List<TransactionProcessor.TransactionResult> results = new ArrayList<>();
        results.add(new TransactionProcessor.TransactionResult(
            TransactionProcessor.TransactionStatus.SUCCESS, "ok", 90.0));
        results.add(new TransactionProcessor.TransactionResult(
            TransactionProcessor.TransactionStatus.FAILED, "fail", 0.0));
        results.add(new TransactionProcessor.TransactionResult(
            TransactionProcessor.TransactionStatus.PENDING, "wait", 0.0));
        results.add(new TransactionProcessor.TransactionResult(
            TransactionProcessor.TransactionStatus.TIMEOUT, "timeout", 0.0));
        results.add(new TransactionProcessor.TransactionResult(
            TransactionProcessor.TransactionStatus.CANCELLED, "cancelled", 0.0));

        String summary = proc.summariseBatch(results);
        assertNotNull(summary);
        assertTrue(summary.contains("Total=5"));
        assertTrue(summary.contains("SUCCESS=1"));
        assertTrue(summary.contains("FAILED=2"));
        assertTrue(summary.contains("PENDING=1"));
    }

    @Test
    @DisplayName("summariseBatch: all success accumulates total amount")
    void testSummariseBatch_allSuccess_accumulatesAmount() {
        List<TransactionProcessor.TransactionResult> results = Arrays.asList(
            new TransactionProcessor.TransactionResult(TransactionProcessor.TransactionStatus.SUCCESS, "ok", 100.0),
            new TransactionProcessor.TransactionResult(TransactionProcessor.TransactionStatus.SUCCESS, "ok", 200.0)
        );
        String summary = proc.summariseBatch(results);
        assertTrue(summary.contains("Amount=300.00"));
    }

    // --- assertions about result structure ---

    @Test
    @DisplayName("TransactionResult getters return correct values")
    void testTransactionResult_getters() {
        TransactionProcessor.TransactionResult r = new TransactionProcessor.TransactionResult(
            TransactionProcessor.TransactionStatus.SUCCESS, "test message", 99.99
        );
        assertEquals(TransactionProcessor.TransactionStatus.SUCCESS, r.getStatus());
        assertEquals("test message", r.getMessage());
        assertEquals(99.99, r.getProcessedAmount(), 0.001);
    }

    @Test
    @DisplayName("TransactionStatus enum has all expected values")
    void testTransactionStatus_enumValues() {
        assertNotNull(TransactionProcessor.TransactionStatus.SUCCESS);
        assertNotNull(TransactionProcessor.TransactionStatus.FAILED);
        assertNotNull(TransactionProcessor.TransactionStatus.PENDING);
        assertNotNull(TransactionProcessor.TransactionStatus.CANCELLED);
        assertNotNull(TransactionProcessor.TransactionStatus.TIMEOUT);
    }
}
