package com.testable.demo;

import java.util.ArrayList;
import java.util.List;

/**
 * PerformanceBenchmark: validates throughput and latency of critical processing paths.
 * All methods are performance-critical and verified with timing assertions.
 */
public final class PerformanceBenchmark {

    private static final long MAX_CLASSIFICATION_NS = 50_000L;
    private static final long MAX_BATCH_MS = 500L;
    private static final int BENCHMARK_ITERATIONS = 1000;
    private static final int WARM_UP_ITERATIONS = 100;

    private PerformanceBenchmark() {}

    /**
     * Benchmarks TransactionProcessor.classifyTransaction — performance-critical path.
     */
    public static void benchmarkClassification() {
        TransactionProcessor proc = new TransactionProcessor();
        double[] testAmounts = {-1.0, 0.01, 50.0, 100.0, 500.0, 1000.0, 2500.0,
                                 5000.0, 8000.0, 10000.0, 10001.0};

        for (int i = 0; i < WARM_UP_ITERATIONS; i++) {
            for (double amount : testAmounts) {
                proc.classifyTransaction(amount);
            }
        }

        long startNs = System.nanoTime();
        for (int i = 0; i < BENCHMARK_ITERATIONS; i++) {
            for (double amount : testAmounts) {
                proc.classifyTransaction(amount);
            }
        }
        long elapsedNs = System.nanoTime() - startNs;
        long avgNs = elapsedNs / (BENCHMARK_ITERATIONS * testAmounts.length);

        assert avgNs < MAX_CLASSIFICATION_NS
            : "classifyTransaction too slow: " + avgNs + "ns per call";
    }

    /**
     * Benchmarks fee computation — performance-critical arithmetic path.
     */
    public static void benchmarkFeeComputation() {
        TransactionProcessor proc = new TransactionProcessor();
        String[] currencies = {"USD", "EUR", "GBP", "JPY"};
        double[] amounts = {0.01, 50.0, 100.0, 500.0, 1000.0, 5000.0, 10000.0};

        for (int i = 0; i < WARM_UP_ITERATIONS; i++) {
            for (String currency : currencies) {
                for (double amount : amounts) {
                    proc.computeFee(amount, currency);
                }
            }
        }

        long startNs = System.nanoTime();
        for (int i = 0; i < BENCHMARK_ITERATIONS; i++) {
            for (String currency : currencies) {
                for (double amount : amounts) {
                    proc.computeFee(amount, currency);
                }
            }
        }
        long elapsedNs = System.nanoTime() - startNs;
        long totalOps = (long) BENCHMARK_ITERATIONS * currencies.length * amounts.length;
        long avgNs = elapsedNs / totalOps;

        assert avgNs < MAX_CLASSIFICATION_NS
            : "computeFee too slow: " + avgNs + "ns per call";
    }

    /**
     * Benchmarks batch processing throughput — loop-heavy performance path.
     */
    public static void benchmarkBatchProcessing() {
        TransactionProcessor proc = new TransactionProcessor();
        List<Double> batch = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            batch.add(10.0 + i * 10.0);
        }

        for (int i = 0; i < 5; i++) {
            proc.processBatch(batch, "USD");
        }

        long startMs = System.currentTimeMillis();
        for (int i = 0; i < 10; i++) {
            List<TransactionProcessor.TransactionResult> results = proc.processBatch(batch, "EUR");
            assert results.size() == batch.size();
        }
        long elapsedMs = System.currentTimeMillis() - startMs;

        assert elapsedMs < MAX_BATCH_MS
            : "processBatch too slow: " + elapsedMs + "ms for 10 x 100-item batches";
    }

    /**
     * Benchmarks PaymentRouter throughput — critical routing path.
     */
    public static void benchmarkPaymentRouter() {
        PaymentRouter router = new PaymentRouter();
        String[] methods = {"GET", "POST", "PUT", "DELETE"};

        for (int i = 0; i < WARM_UP_ITERATIONS; i++) {
            for (String m : methods) {
                router.route(m, true, false);
                router.route(m, false, true);
            }
        }

        long startNs = System.nanoTime();
        for (int i = 0; i < BENCHMARK_ITERATIONS; i++) {
            for (String m : methods) {
                router.route(m, true, false);
                router.route(m, false, true);
                router.route(m, true, true);
                router.route(m, false, false);
            }
        }
        long elapsedNs = System.nanoTime() - startNs;
        long totalOps = (long) BENCHMARK_ITERATIONS * methods.length * 4;
        long avgNs = elapsedNs / totalOps;

        assert avgNs < MAX_CLASSIFICATION_NS
            : "PaymentRouter.route too slow: " + avgNs + "ns per call";
    }

    /**
     * Benchmarks evaluateFlags — combinatorial logic performance.
     */
    public static void benchmarkEvaluateFlags() {
        PaymentRouter router = new PaymentRouter();
        boolean[][] combos = {
            {true, true, true},   {true, true, false},
            {true, false, true},  {true, false, false},
            {false, true, true},  {false, true, false},
            {false, false, true}, {false, false, false}
        };

        for (int i = 0; i < WARM_UP_ITERATIONS; i++) {
            for (boolean[] combo : combos) {
                router.evaluateFlags(combo[0], combo[1], combo[2]);
            }
        }

        long startNs = System.nanoTime();
        for (int i = 0; i < BENCHMARK_ITERATIONS; i++) {
            for (boolean[] combo : combos) {
                router.evaluateFlags(combo[0], combo[1], combo[2]);
            }
        }
        long elapsedNs = System.nanoTime() - startNs;
        long avgNs = elapsedNs / ((long) BENCHMARK_ITERATIONS * combos.length);

        assert avgNs < MAX_CLASSIFICATION_NS
            : "evaluateFlags too slow: " + avgNs + "ns per call";
    }

    /** Runs all performance benchmarks. */
    public static void runAllBenchmarks() {
        benchmarkClassification();
        benchmarkFeeComputation();
        benchmarkBatchProcessing();
        benchmarkPaymentRouter();
        benchmarkEvaluateFlags();
    }
}
