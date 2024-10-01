# CMD

text based commands for interacting with meshEcho

## Common Configuration

- `blacklist`* List of nodeId that does not have access to the command

- `whitelist`* List of nodeId that have access to the command

- \* `blacklist` and `whitelist` are mutually exclusive configurations and cannot be defined at the same time

### `[EchoCmd]` (`echo`)

display a line of text.

input

```
{escape}echo text to echo back
```

### `[ManCmd]` (`man`)

list available cmd or specific cmd help message.

input

```
{escape}man
```

```
{escape}man {escape}echo
```

### `[NoaaCmd]` (`noaa`)

reports NOAA alerts around your QTH

- calling node much be sharing position data of any precision.

input

```
{escape}noaa
```

### `[PingCmd]` (`ping`)

reports packet received time

input

```
{escape}ping
```

### `[RollCmd]` (`roll`)

generates random (N)umbers X where X in [1,M]

#### Configuration

- `default_rolls` (optional) default roll count
- `default_sides` (optional)  default die size
- `max_rolls` (optional) maximum requestable number of rolls
- `max_sides` (optional) maximum requestable die size

input

```
{escape}roll
```

```
{escape}roll 10
```

```
{escape}roll 6d100
```

### `[TopCmd]` (`top`)

reports host status

input

```
{escape}top
```