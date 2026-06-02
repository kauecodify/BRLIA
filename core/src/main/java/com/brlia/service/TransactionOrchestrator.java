@Service
@RequiredArgsConstructor
@Slf4j
public class TransactionOrchestrator {

    private final FraudDetectionClient mlClient; // chamada gRPC para ml-engine
    private final SettlementStrategyFactory settlementFactory;
    private final TransactionRepository txRepo;
    private final KafkaTemplate<String, String> kafkaTemplate;

    @Transactional
    public SettlementResponse processTransaction(TransactionRequest request) {
        // 1. validação inicial
        validateRequest(request);

        // 2. análise de risco com IA (timeout de 200ms)
        FraudAnalysisResult riskResult = mlClient.analyzeWithTimeout(
                buildFraudFeatures(request),
                Duration.ofMillis(200));

        if (riskResult.isFraud() && riskResult.getConfidence() > 0.85) {
            logFraudAttempt(request, riskResult);
            return SettlementResponse.rejected("ALTO_RISCO_FRAUDE", riskResult.getExplanation());
        }

        // 3. estratégia de liquidação inteligente
        SettlementStrategy strategy = settlementFactory.getStrategy(
                request.getSettlementMethod(),
                riskResult.getRiskScore(),
                request.getAmount());

        // 4. execução com circuit breaker
        try {
            SettlementResult settlement = ResilienceDecorator.decorateSupplier(
                    circuitBreaker,
                    () -> strategy.execute(request)).get();

            // 5. feedback para reforço do modelo
            publishTrainingEvent(request, settlement.isSuccess());

            return buildResponse(settlement, riskResult);
        } catch (Exception e) {
            handleSettlementFailure(request, e);
            return SettlementResponse.error("FALHA_LIQUIDACAO");
        }
    }

    private void publishTrainingEvent(TransactionRequest tx, boolean success) {
        TrainingEvent event = TrainingEvent.builder()
                .transactionId(tx.getId())
                .features(extractFeatures(tx))
                .label(success ? 0 : 1) // 0=legítima, 1=falha
                .timestamp(Instant.now())
                .build();

        kafkaTemplate.send("ml-training-events",
                tx.getId(),
                toJson(event));
    }
}