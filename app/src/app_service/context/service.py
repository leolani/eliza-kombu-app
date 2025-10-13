import logging

from cltl.combot.event.emissor import ScenarioStopped, Agent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.event.util import extract_scenario_id
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.infra.topic_worker import TopicWorker
from emissor.representation.scenario import Scenario

logger = logging.getLogger(__name__)

AGENT = Agent("Leolani", "http://cltl.nl/leolani/world/leolani")


class ContextService:
    @classmethod
    def from_config(cls, event_bus: EventBus, resource_manager: ResourceManager, config_manager: ConfigurationManager):
        config = config_manager.get_config("eliza.context")
        scenario_topic = config.get("topic_scenario")
        intention_topic = config.get("topic_intention")
        desire_topic = config.get("topic_desire")

        return cls(scenario_topic, intention_topic, desire_topic,
                   event_bus, resource_manager)

    def __init__(self, scenario_topic: str, intention_topic: str, desire_topic: str,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._scenario_topic = scenario_topic
        self._intention_topic = intention_topic
        self._desire_topic = desire_topic

        self._topic_worker = None

        self.AGENT = AGENT

    @property
    def app(self):
        return None

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._desire_topic],
                                         self._event_bus,
                                         buffer_size=32, processor=self._process,
                                         resource_manager=self._resource_manager,
                                         name=self.__class__.__name__)
        self._topic_worker.start().wait()

    def stop(self):
        if not self._topic_worker:
            pass

        self._topic_worker.stop()
        self._topic_worker.await_stop()
        self._topic_worker = None

    def _process(self, event: Event):
        if event.metadata.topic == self._desire_topic:
            achieved = event.payload.achieved
            if "quit" in achieved:
                self._stop_scenario(event)
        else:
            logger.warning("Unhandled event: %s", event)

    def _stop_scenario(self, event: Event):
        scenario_id = extract_scenario_id(event)
        if not scenario_id:
            logger.warning("No scenario_id found in event, cannot stop scenario")
            return

        scenario = Scenario.new_instance(scenario_id, 0, timestamp_now(), None, {})
        self._event_bus.publish(self._scenario_topic,
                                Event.for_payload(ScenarioStopped.create(scenario)))
        logger.info("Stopped scenario %s", scenario_id)
