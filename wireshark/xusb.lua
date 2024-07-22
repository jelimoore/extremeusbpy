proto = Proto("ExtremeUSB", "Icron Extreme USB and Crestron USB-EXT-DM")

transactionId = ProtoField.uint32("extremeusb.transaction_id", "transactionId", base.DEC)
opcode = ProtoField.uint8("extremeusb.opcode", "opcode", base.DEC)

proto.fields = {transactionId, opcode}

port = 6137

opcodes = {
    [0] = 'REQ_INFO',
    [1] = 'REP_INFO',
    [2] = 'PING',
    [3] = 'ACK',
    [4] = 'PAIR',
    [5] = 'REMOVE_PAIRING',
    [6] = 'REQ_TOPO',
    [7] = 'REP_TOPO',
    [8] = 'REP_UNHANDLED_CMD',
    [9] = 'NACK',
    [10] = 'REMOVE_PAIRING_ALL',
}

function proto.dissector(buffer, pinfo, tree)
    length = buffer:len()
    if length == 0 then return end
    pinfo.cols.protocol = proto.name
    local subtree = tree:add(proto, buffer(), "Extreme USB Protocol Data")
    subtree:add(transactionId, buffer(4,8):uint())
    subtree:add(opcode, buffer(8,9):uint())
end

local udp_port = DissectorTable.get("udp.port")
udp_port:add(port, proto)