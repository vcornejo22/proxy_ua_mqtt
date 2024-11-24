# Project Description

This project is a data integration system that connects OPC UA (Open Platform Communications Unified Architecture) with MQTT and InfluxDB using Python. The main goal is to acquire data from an industrial control system via OPC UA, process it, and publish it to an MQTT broker, as well as store it in an InfluxDB database for later analysis and visualization.

## Features:
- **OPC UA Client**: Connects to an OPC UA server and subscribes to data changes.
- **MQTT Client**: Publishes the data acquired from OPC UA to a specified MQTT broker for integration with other systems.
- **InfluxDB Integration**: Stores the acquired data in an InfluxDB time-series database for historical analysis.
- **Configurable**: Uses environment variables to configure OPC UA, MQTT, and InfluxDB connections.
- **Asynchronous Processing**: The project is built using `asyncio` to handle multiple tasks concurrently, improving efficiency.

## Technology Stack:
- **Python**: Main programming language.
- **Asyncio**: To handle asynchronous tasks and I/O operations.
- **asyncua**: To interact with OPC UA servers.
- **aiomqtt**: To handle MQTT communications.
- **InfluxDB Client**: To write data to an InfluxDB database.

## Usage:
1. Configure the environment variables in a `.env` file.
2. Run the main script to start data collection and publication.
3. Data from OPC UA will be stored in InfluxDB and published to MQTT for real-time monitoring.
