class ComplianceAnalyzer:
    def __init__(self):
        self.nlp_model = spacy.load("pt_core_news_lg")
        self.regulation_db = self._load_regulations()  # circular 3.919, Res. 4.658
        
    def analyze_transaction(self, tx_data: dict) -> ComplianceReport:
        """Análise regulatória com NLP em tempo real"""
        # extração de entidades críticas
        doc = self.nlp_model(tx_data['description'])
        entities = {ent.text: ent.label_ for ent in doc.ents}
        
        # verificação contra base regulatória
        violations = []
        for rule in self.regulation_db:
            if self._matches_rule(tx_data, rule, entities):
                violations.append(ComplianceViolation(
                    rule_id=rule.id,
                    severity=rule.severity,
                    suggestion=self._generate_suggestion(rule)
                ))
        
        # classificação de risco regulatório
        risk_level = self._calculate_regulatory_risk(violations)
        
        return ComplianceReport(
            is_compliant=len(violations) == 0,
            violations=violations,
            risk_level=risk_level,
            auto_correction=self._suggest_corrections(tx_data, violations)
        )