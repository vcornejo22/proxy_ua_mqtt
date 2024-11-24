import asyncio
from influxdb_client import Point
from influxdb_client.rest import ApiException
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from asyncua import Client, ua
from asyncua.crypto import security_policies
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from aiomqtt import TLSParameters
from aiomqtt import Client as MQTTClient

load_dotenv()

nodes_dict = {
        "Constant": "ns=3;i=1001",
        "Counter": "ns=3;i=1002",
        "Random": "ns=3;i=1003",
        "Sawtooth": "ns=3;i=1004",
        "Sinusoid": "ns=3;i=1005",
        "Square": "ns=3;i=1006",
        "Triangle": "ns=3;i=1007",
    }

class Config:
    """
    Singleton class to load environment configuration
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self) -> None:
        """
        Loads configuration from environment variables.
        """
        self.influx_token: str = os.getenv("INFLUXDB_TOKEN")
        self.influx_org: str = os.getenv("INFLUXDB_ORG")
        self.influx_url: str = os.getenv("INFLUXDB_URL")
        self.influx_bucket: str = os.getenv("INFLUXDB_BUCKET")

        self.mqtt_broker: str = os.getenv("MQTT_BROKER")
        self.mqtt_port: int = int(os.getenv("MQTT_PORT"))
        self.mqtt_cafile: str = os.getenv("MQTT_CAFILE")
        self.mqtt_cert: str = os.getenv("MQTT_CERT")
        self.mqtt_key: str = os.getenv("MQTT_KEY")
        self.mqtt_user: str = os.getenv("MQTT_USER")
        self.mqtt_password: str = os.getenv("MQTT_PASSWORD")

        self.ua_user: str = os.getenv("UA_USER")
        self.ua_password: str = os.getenv("UA_PASSWORD")
        self.ua_url: str = os.getenv("UA_URL")
        self.ua_uri: str = os.getenv("UA_URI")
        self.ua_cert: str = os.getenv("UA_CERT")
        self.ua_key: str = os.getenv("UA_KEY")
        self.ua_server_cert: str = os.getenv("UA_SERVER_CERT")

class MQTTHandler:
    """
    Singleton class to handle MQTT connections and publishing
    """
    _instance = None

    def __new__(cls, config: Config):
        if cls._instance is None:
            cls._instance = super(MQTTHandler, cls).__new__(cls)
            cls._instance._init_instance(config)
        return cls._instance

    def _init_instance(self, config: Config) -> None:
        """
        Initializes the MQTT handler instance with the given configuration.
        """
        self.config: Config = config
        self.client: MQTTClient = None

    async def connect(self) -> None:
        """
        Establishes a connection to the MQTT broker.
        """
        tls_params = TLSParameters(
            ca_certs=self.config.mqtt_cafile,
            certfile=self.config.mqtt_cert,
            keyfile=self.config.mqtt_key
        )
        self.client = MQTTClient(
            hostname=self.config.mqtt_broker,
            port=self.config.mqtt_port,
            username=self.config.mqtt_user,
            password=self.config.mqtt_password,
            tls_params=tls_params,
            tls_insecure=False
        )
        await self.client.__aenter__()

    async def publish(self, topic: str, payload: str) -> None:
        """
        Publishes a message to the specified MQTT topic.
        
        :param topic: The topic to publish to.
        :param payload: The message payload.
        """
        await self.client.publish(topic, str(payload), qos=1)

class InfluxDBHandler:
    """
    Singleton class to handle InfluxDB connections and data writing
    """
    _instance = None

    def __new__(cls, config: Config):
        if cls._instance is None:
            cls._instance = super(InfluxDBHandler, cls).__new__(cls)
            cls._instance._init_instance(config)
        return cls._instance

    def _init_instance(self, config: Config) -> None:
        """
        Initializes the InfluxDB handler instance with the given configuration.
        """
        self.config: Config = config
        self.client: InfluxDBClientAsync = None
        self.write_api = None

    async def connect(self) -> None:
        """
        Establishes a connection to the InfluxDB server.
        """
        self.client = InfluxDBClientAsync(
            url=self.config.influx_url,
            token=self.config.influx_token,
            org=self.config.influx_org
        )
        self.write_api = self.client.write_api()

    async def write_point(self, point: Point) -> None:
        """
        Writes a data point to the InfluxDB database.
        
        :param point: The data point to be written.
        """
        await self.write_api.write(
            bucket=self.config.influx_bucket,
            org=self.config.influx_org,
            record=point
        )

class OPCUAHandler:
    """
    Singleton class to handle OPC UA client connection and subscription
    """
    _instance = None

    def __new__(cls, config: Config, influx_handler: InfluxDBHandler, mqtt_handler: MQTTHandler, nodes_dict: dict):
        if cls._instance is None:
            cls._instance = super(OPCUAHandler, cls).__new__(cls)
            cls._instance._init_instance(config, influx_handler, mqtt_handler, nodes_dict)
        return cls._instance

    def _init_instance(self, config: Config, influx_handler: InfluxDBHandler, mqtt_handler: MQTTHandler, nodes_dict: dict) -> None:
        """
        Initializes the OPC UA handler instance with the given configuration.
        """
        self.config: Config = config
        self.client: Client = None
        self.influx_handler: InfluxDBHandler = influx_handler
        self.mqtt_handler: MQTTHandler = mqtt_handler
        self.nodes_dict: dict = nodes_dict

    async def connect(self) -> None:
        """
        Establishes a connection to the OPC UA server.
        """
        self.client = Client(url=self.config.ua_url, timeout=60 * 10)
        self.client.set_user(self.config.ua_user)
        self.client.set_password(self.config.ua_password)
        await self.client.set_security(
            security_policies.SecurityPolicyBasic256Sha256,
            certificate=self.config.ua_cert,
            private_key=self.config.ua_key,
            mode=ua.MessageSecurityMode.SignAndEncrypt
        )
        self.client.application_uri = self.config.ua_uri
        await self.client.connect()

    async def subscribe(self) -> None:
        """
        Subscribes to data changes from the OPC UA server.
        """
        handler = SubscriptionHandler(self.influx_handler, self.mqtt_handler, self.nodes_dict)
        subscription = await self.client.create_subscription(1000, handler)
        nodes = [self.client.get_node(node) for node in self.nodes_dict.values()]
        await subscription.subscribe_data_change(nodes)

class SubscriptionHandler:
    """
    Handles data change notifications from OPC UA server
    """
    def __init__(self, influx_handler: InfluxDBHandler, mqtt_handler: MQTTHandler, nodes_dict: dict, timeout: int = 60):
        """
        Initializes the SubscriptionHandler instance.
        
        :param influx_handler: The InfluxDB handler instance.
        :param mqtt_handler: The MQTT handler instance.
        :param nodes_dict: Dictionary of OPC UA nodes to subscribe to.
        :param timeout: Timeout for writing the last value, in seconds.
        """
        self.influx_handler: InfluxDBHandler = influx_handler
        self.mqtt_handler: MQTTHandler = mqtt_handler
        self.nodes_dict: dict = nodes_dict
        self.last_val: dict = {}
        self.timer_task: dict = {}
        self.timeout: int = timeout
        self.value_changed: bool = False

    async def reset_timer(self, key: str, node: str) -> None:
        """
        Resets the timer for inserting the last value after a timeout.
        
        :param key: The key of the node.
        :param node: The node identifier.
        """
        self.value_changed = True
        if key in self.timer_task:
            self.timer_task[key].cancel()
        self.value_changed = False
        self.timer_task[key] = asyncio.create_task(
            self.insert_last_value_after_timeout(key, node)
        )

    async def insert_last_value_after_timeout(self, key: str, node: str) -> None:
        """
        Inserts the last value of the node after a timeout period.
        
        :param key: The key of the node.
        :param node: The node identifier.
        """
        while not self.value_changed:
            await asyncio.sleep(self.timeout)
            if key in self.last_val:
                last_val = self.last_val[key]
                point = Point("UA").tag("Prosys", key).field(node, last_val)
                await self.influx_handler.write_point(point)

    async def datachange_notification(self, node: ua.NodeId, val: float, data: ua.DataValue) -> None:
        """
        Handles data change notifications from the OPC UA server.
        
        :param node: The node that triggered the data change.
        :param val: The new value of the node.
        :param data: Additional data about the change.
        """
        key = self.get_key_by_value(str(node))
        val = float(val)

        if key in self.last_val and val != self.last_val[key] and key == "Constant":
            last_val = self.last_val[key]
            point = (
                Point("UA")
                .tag("Prosys", key)
                .field(node, last_val)
                .time(datetime.now(timezone.utc) - timedelta(seconds=1))
            )
            await self.influx_handler.write_point(point)

        self.last_val[key] = val
        await self.reset_timer(key, node)
        point = Point("UA").tag("Prosys", key).field(node, val)
        await self.influx_handler.write_point(point)
        await self.mqtt_handler.publish(f"prosys/{key}/{node}", val)

    def get_key_by_value(self, search_value: str) -> str:
        """
        Gets the key corresponding to the specified value from the nodes dictionary.
        
        :param search_value: The value to search for.
        :return: The corresponding key, or None if not found.
        """
        for key, value in self.nodes_dict.items():
            if value == search_value:
                return key
        return None

async def main() -> None:
    """
    Main entry point for the program.
    """
    config = Config()
    influx_handler = InfluxDBHandler(config)
    mqtt_handler = MQTTHandler(config)
    opc_ua_handler = OPCUAHandler(config, influx_handler, mqtt_handler, nodes_dict)

    await influx_handler.connect()
    await mqtt_handler.connect()
    await opc_ua_handler.connect()
    await opc_ua_handler.subscribe()

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())