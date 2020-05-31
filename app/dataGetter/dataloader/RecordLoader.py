from app.dataGetter.dataloader.Actor import Actor
from abc import ABC, abstractmethod


class LoadRecordActor(Actor, ABC):
    def __init__(self):
        super().__init__(self, proc=True)

    @abstractmethod
    def run(self):
        ...

