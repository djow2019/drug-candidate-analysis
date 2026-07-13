from abc import ABC, abstractmethod


class StatisticalTest(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def test_samples(self, group_a: list, group_b: list, metadata: dict):
        pass

