# subscriber

### `[CmdSubscriber]`

subscriber for servicing text based commands

#### Configuration

- `escape` the sting that denotes the start of a command
- `max_channel_utilization` channel utilization threshold for disabling the servicing of commands
- `blacklist`* List of nodeId that does not have access to any commands

- `whitelist`* List of nodeId that have access to any commands

- \* `blacklist` and `whitelist` are mutually exclusive configurations and cannot be defined at the same time

### [MqttSubscriber]

subscriber for forwarding telemetry data to home assistant via mqtt

#### Configuration

- `node_ids` List of nodeIds that the subscriber will forward telemetry data