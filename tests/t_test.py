from tests.statistical_test import StatisticalTest
class T_Test(StatisticalTest):

    def test_samples(self, group_a: list, group_b: list, metadata: dict):
        import scipy.stats as stats

        # check variance
        stat, p_variance = stats.levene(group_a, group_b)
        print(f"Variance: {p_variance}")
        equal_variance = p_variance >= 0.05

        t_stat, p_val = stats.ttest_ind(group_a, group_b, equal_var=equal_variance)
        return {
            "t-stat": t_stat,
            "p-val": p_val
        }