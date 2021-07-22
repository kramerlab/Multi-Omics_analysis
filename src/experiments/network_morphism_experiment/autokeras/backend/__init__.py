from experiments.network_morphism_experiment.autokeras.backend import torch


class Backend:
    backend = torch

    def __init__(self):
        pass

    @classmethod
    def produce_model(cls, graph):
        return cls.backend.produce_model(graph)

    @classmethod
    def get_model_trainer(cls, **kwargs):
        return cls.backend.ModelTrainer(**kwargs)

    @classmethod
    def classification_loss(cls, prediction, target):
        return cls.backend.classification_loss(prediction, target)

    @classmethod
    def regression_loss(cls, prediction, target):
        return cls.backend.regression_loss(prediction, target)

    @classmethod
    def binary_classification_loss(cls, prediction, target):
        return cls.backend.binary_classification_loss(prediction, target)

    @classmethod
    def classification_metric(cls, prediction, target):
        return cls.backend.classification_metric(prediction, target)

    @classmethod
    def regression_metric(cls, prediction, target):
        return cls.backend.regression_metric(prediction, target)

    @classmethod
    def binary_classification_metric(cls, prediction, target):
        return cls.backend.binary_classification_metric(prediction, target)

    @classmethod
    def predict(cls, model, loader):
        return cls.backend.predict(model, loader)

    @classmethod
    def get_device(cls):
        return cls.backend.get_device()
