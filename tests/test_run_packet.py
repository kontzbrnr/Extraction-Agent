from infra.orchestration.runtime.run_packet import RunPacket


def test_run_packet_roundtrip_serialization():
    packet = RunPacket(
        run_id="run_3fa85f64",
        stage="narrative",
        agent_name="narrative",
        payload={"k": "v", "n": 1},
        metadata={"profile": "default"},
        context={"x": "y"},
    )

    packet_dict = packet.to_dict()
    packet2 = RunPacket.from_dict(packet_dict)

    assert packet == packet2
