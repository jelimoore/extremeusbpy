# Extreme USB Python

This is an implementation of Icron's Extreme USB control protocol in Python. Any Icron-based USB over Ethernet extender should work (many different vendors white-label their products) - though it is important to note that there are versions that go over a CAT cable (i.e. is not Ethernet) and versions that can travel over a network - only network versions can be controlled by this tool. Theoretically supported devices include:

 - Icron 2301GE-LAN
 - Icron 2304GE-LAN
 - Icron 2304S
 - Icron 2304PoE
 - Crestron USB-EXT-DM (Local and Remote)
 - Possibly others!

It is also important to note that your computer and every USB extender you want to work together should be on the same subnet - no routing or layer 3 transport.

## Example
A minimal example use of this library is as follows:

        from extremeusb import ExtremeUSB

        xusb = ExtremeUSB()
        xusb.getInfo("FF:FF:FF:FF:FF:FF")

## Library API
Specific endpoints are targeted by MAC addresses, rather than IP addresses. All MAC addresses should be formatted with colons, and include the full MAC of the device. For example:

        00:1b:13:12:34:56

To target every device on a network (valid for get info and unpair all), use the broadcast MAC address:
        
        FF:FF:FF:FF:FF:FF

### Instantiation
No parameters are required for instantiating the class.

### Get Info
Returns info about the targeted device, or every device on the network (using broadcast MAC).

        xusb.getInfo("FF:FF:FF:FF:FF:FF")

Will return a List with each device it got a reply from, its MAC address, side (local or remote), and current pairing status. For example:

        [
            {'mac': '00:1b:13:11:11:11', 'side': 'local', 'paired': False},
            {'mac': '00:1b:13:22:22:22', 'side': 'remote', 'paired': False}
        ]

Or:

        [
            {'mac': '00:1b:13:11:11:11', 'side': 'local', 'paired': True, remoteMac: '00:1b:13:22:22:22'},
            {'mac': '00:1b:13:22:22:22', 'side': 'remote', 'paired': True, remoteMac: '00:1b:13:11:11:11'}
        ]

### Pair
Pairs a specific combination of local and remote ends. Requires MAC of both ends.

        xusb.pair("00:1b:13:11:11:11", "00:1b:13:22:22:22")

### Unpair
Unpairs a specific combination of local and remote ends. Requires MAC of both ends.

        xusb.unpair("00:1b:13:11:11:11", "00:1b:13:22:22:22")

### Unpair All
Removes all pairings from a specific device (not sure how this differs from a general unpair), or every device on the network (using broadcast MAC).

        xusb.unpairAll("00:1b:13:11:11:11")

### Ping
Much like ICMP ping, tests availability of the specified endpoint.

        xusb.ping("00:1b:13:12:34:56")

## Protocol Nitty-Gritty

The control protocol is fairly simple, relying on UDP broadcast packets on port 6137. Packets are formatted as such:

        (MAGIC BYTES) + (OPCODE) + (LOCAL MAC ADDRESS) [+ (DESTINATION MAC)]

### Magic Bytes
Required at the start of every transmission. The magic bytes are `A9 C4 D8 F4`.

### Opcode
Identifies the operation to be performed. Valid opcodes are:

        0x00: Info Request (Broadcast Capable)
        0x01: Info Reply
        0x02: Ping
        0x03: Ack
        0x04: Pair Request
        0x05: Unpair Request
        0x06: Topology Request
        0x07: Topology Reply
        0x08: Unhandled Command
        0x09: NACK
        0x0A: Remove All Pairing (Broadcast Capable)

### Local MAC Address
Identifies the target device. Can be the MAC of the target or broadcast for certain commands.

### Remote MAC Address
Identifies the remote device. Only required for certain commands.