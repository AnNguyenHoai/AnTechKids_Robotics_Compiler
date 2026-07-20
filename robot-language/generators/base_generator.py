from abc import ABC
from abc import abstractmethod


class BaseGenerator(ABC):

    name = "Generator"

    @abstractmethod
    def generate(self, context):
        pass

