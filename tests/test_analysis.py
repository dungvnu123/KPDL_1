import sys
import unittest
from dataclasses import replace
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
from mlxtend.frequent_patterns import apriori as reference_apriori

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from telco_arm import Settings, apriori, generate_rules, mine_target_rules, run
from telco_arm.analysis import rule_coverage
from telco_arm.config import FeatureSpec
from telco_arm.preprocessing import one_hot_encode, usage_items
from telco_arm.questions import demographic_bundles, recommend_upgrades
from telco_arm.reporting import render_report
from telco_arm.rules import RULE_COLUMNS

matplotlib.use("Agg")


class MiningTests(unittest.TestCase):
    def test_apriori_matches_reference(self):
        generator = np.random.default_rng(42)
        frame = pd.DataFrame(generator.random((150, 7)) < 0.65, columns=list("ABCDEFG"))
        ours = apriori(frame, 0.20, 4)
        reference = reference_apriori(frame, min_support=0.20, max_len=4, use_colnames=True)
        self.assertEqual(dict(zip(ours.itemsets, ours.support)), dict(zip(reference.itemsets, reference.support)))

    def test_support_boundary_and_empty_input(self):
        frame = pd.DataFrame({"A": [True] * 7 + [False] * 93})
        self.assertEqual(len(apriori(frame, 0.07)), 1)
        self.assertTrue(apriori(frame.iloc[:0], 0.1).empty)
        with self.assertRaises(ValueError):
            apriori(frame, 0.1, 0)

    def test_target_metrics_match_exhaustive_counting(self):
        generator = np.random.default_rng(7)
        frame = pd.DataFrame(generator.random((120, 5)) < 0.65, columns=list("ABCDE"))
        frame["Churn=Yes"] = generator.random(120) < 0.4
        frame["Churn=No"] = ~frame["Churn=Yes"]
        rules = mine_target_rules(frame, "Churn=Yes", 0.05, 0, 0, 4,
                                  exclude=("Churn=No",), min_improvement=None)
        actual = {r.antecedents: r for r in rules.itertuples()}
        expected = set()
        for size in range(1, 4):
            for items in combinations(list("ABCDE"), size):
                matched = frame[list(items)].all(axis=1)
                joint = (matched & frame["Churn=Yes"]).mean()
                if joint >= 0.05:
                    key = frozenset(items)
                    expected.add(key)
                    self.assertAlmostEqual(actual[key].support, joint)
                    self.assertAlmostEqual(actual[key].confidence, joint / matched.mean())
                    self.assertAlmostEqual(actual[key].lift, joint / matched.mean() / frame["Churn=Yes"].mean())
        self.assertEqual(set(actual), expected)

    def test_target_below_support_or_absent_has_no_rules(self):
        frame = pd.DataFrame({"A": [True] * 10, "Churn=Yes": [True] * 2 + [False] * 8})
        self.assertTrue(mine_target_rules(frame, "Churn=Yes", 0.3, 0).empty)
        self.assertTrue(mine_target_rules(frame, "Churn=No", 0.1, 0).empty)
        coverage = rule_coverage(pd.DataFrame(columns=RULE_COLUMNS), frame, "Churn=No")
        self.assertIn("cumulative_recall", coverage)

    def test_usage_contains_only_positive_services(self):
        frame = pd.DataFrame(columns=["PhoneService=Yes", "OnlineBackup=Yes", "OnlineBackup=No",
                                      "InternetService=No", "gender=Female", "Contract=Two year", "Churn=Yes"])
        self.assertEqual(list(usage_items(frame, FeatureSpec())), ["PhoneService=Yes", "OnlineBackup=Yes"])

    def test_empty_rules_can_be_sorted_and_plotted(self):
        from telco_arm import visualization
        from matplotlib import pyplot as plt
        rules = generate_rules(apriori(pd.DataFrame({"A": [True, False]}), 0.5), 0.7)
        self.assertTrue(rules.nlargest(10, "lift").empty)
        for plot in (visualization.plot_rules_scatter, visualization.plot_rule_network, visualization.plot_top_rules):
            figure = plot(rules)
            self.assertEqual(len(figure.axes), 1)
            plt.close(figure)

    def test_demographic_denominators_are_group_counts(self):
        baskets = [frozenset(["gender=Female", "StreamingTV=Yes", "StreamingMovies=Yes"])] * 3
        baskets += [frozenset(["gender=Female"])]
        baskets += [frozenset(["gender=Male", "StreamingTV=Yes", "StreamingMovies=Yes"])]
        baskets += [frozenset(["gender=Male"])] * 3
        defaults = Settings()
        settings = replace(defaults, questions=replace(defaults.questions, min_group_customers=1))
        table = demographic_bundles(one_hot_encode(baskets), settings)
        female = table.loc[table.demographics == "gender=Female"].iloc[0]
        self.assertEqual(female.group_customers, 4)
        self.assertEqual(female.bundle_customers, 3)
        self.assertAlmostEqual(female.support, 3 / 8)
        self.assertAlmostEqual(female.confidence, 3 / 4)
        self.assertAlmostEqual(female.lift, 1.5)

    def test_recommendations_require_missing_service_and_access(self):
        frame = pd.DataFrame({
            "PhoneService=Yes": [True] * 4,
            "OnlineBackup=Yes": [False, True, False, False],
        })
        rules = generate_rules(apriori(frame, 0.1), 0, 0)
        customers = pd.DataFrame({
            "customerID": ["eligible", "existing", "no-internet", "left"],
            "Churn": ["No", "No", "No", "Yes"], "PhoneService": ["Yes"] * 4,
            "InternetService": ["DSL", "DSL", "No", "DSL"],
        })
        _, recommendations = recommend_upgrades(rules, frame, customers, Settings())
        self.assertEqual(recommendations.customerID.tolist(), ["eligible"])
        self.assertEqual(recommendations.recommended_service.tolist(), ["OnlineBackup=Yes"])


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_service_itemsets_match_reference(self):
        result = self.result
        reference = reference_apriori(usage_items(result.onehot, result.settings.features),
                                     min_support=0.1, max_len=4, use_colnames=True)
        self.assertEqual(dict(zip(result.itemsets.itemsets, result.itemsets.support)),
                         dict(zip(reference.itemsets, reference.support)))

    def test_each_answer_metric_matches_raw_counts(self):
        result = self.result
        onehot = result.onehot
        for row in result.answers.bundles.itertuples():
            matched = onehot[row.itemsets.split(", ")].all(axis=1)
            self.assertEqual(row.customers, matched.sum())
            self.assertAlmostEqual(row.support, matched.mean())
        for row in result.answers.probabilities.itertuples():
            joint = int((onehot[row.service_a] & onehot[row.service_b]).sum())
            self.assertEqual(row.both_customers, joint)
            self.assertAlmostEqual(row.confidence, joint / onehot[row.service_a].sum())
        for table in [result.answers.churn, result.answers.retention]:
            for row in table.itertuples():
                matched = onehot[row.antecedents.split(", ")].all(axis=1)
                hits = matched & onehot[row.consequents]
                self.assertEqual(row.matched_customers, matched.sum())
                self.assertEqual(row.target_customers, hits.sum())
                self.assertAlmostEqual(row.confidence, hits.sum() / matched.sum())
        for row in result.answers.demographics.itertuples():
            matched = onehot[row.demographics.split(", ")].all(axis=1)
            bundle = onehot[row.bundle.split(", ")].all(axis=1)
            self.assertEqual(row.group_customers, matched.sum())
            self.assertEqual(row.bundle_customers, (matched & bundle).sum())
            self.assertAlmostEqual(row.confidence, (matched & bundle).sum() / matched.sum())
            self.assertAlmostEqual(row.lift, row.confidence / bundle.mean())

    def test_customer_recommendations_are_valid_and_distinct(self):
        result = self.result
        recommendations = result.answers.recommendations
        customers = result.customers.set_index("customerID")
        onehot = result.onehot.set_axis(result.customers.customerID)
        self.assertFalse(recommendations.duplicated(["customerID", "recommended_service"]).any())
        self.assertLessEqual(recommendations.groupby("customerID").size().max(), 3)
        for row in recommendations.itertuples():
            customer = customers.loc[row.customerID]
            self.assertEqual(customer.Churn, "No")
            self.assertFalse(onehot.loc[row.customerID, row.recommended_service])
            self.assertTrue(onehot.loc[row.customerID, row.matched_services.split(", ")].all())
            if row.recommended_service == "MultipleLines=Yes":
                self.assertEqual(customer.PhoneService, "Yes")
            else:
                self.assertIn(customer.InternetService, ["DSL", "Fiber optic"])

    def test_all_six_questions_have_results(self):
        for name, table in self.result.answers.tables().items():
            with self.subTest(table=name):
                self.assertFalse(table.empty)
        report = render_report(self.result, 3)
        for number in range(1, 7):
            self.assertIn(f"## Câu {number}.", report)


if __name__ == "__main__":
    unittest.main()
