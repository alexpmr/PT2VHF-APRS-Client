from pt2vhf_aprs.tnc_service import KissStreamDecoder, decode_ax25
from pt2vhf_aprs.tnc_simulator import KISSSimulator


def test_kiss_simulator_fragmentation_duplicates_and_multihop():
    sim = KISSSimulator(fragment_size=7, duplicate_every=2)
    decoder = KissStreamDecoder()
    decoded = []
    for chunk in sim.scenario(sim.multi_hop_demo()):
        for command, frame in decoder.feed(chunk):
            if (command & 0x0F) == 0:
                decoded.append(decode_ax25(frame))
    assert len(decoded) == 4
    assert decoded[0]["source"] == "PT2AAA-7"
    assert decoded[1]["source"] == "PT2BBB"
    assert decoded[2]["source"] == "PT2BBB"
    assert decoded[-1]["info_text"].endswith("ack01")
