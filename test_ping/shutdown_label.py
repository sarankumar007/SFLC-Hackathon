
from datetime import datetime
from . import schemas

PACKET_LOSS_THRESHOLD = 50.0  # %
RTT_SPIKE_THRESHOLD = 200.0  # ms


def calculate_confidence(packet_loss: float, rtt_max: float) -> int:
    """
    Calculate a confidence score based on network probe metrics.
    """
    score = 0
    if packet_loss > PACKET_LOSS_THRESHOLD:
        score += 50
    if rtt_max > RTT_SPIKE_THRESHOLD:
        score += 30
    return score

def get_shutdown_status(probe: schemas.PingProbeBase) -> str:
    """
    Determine shutdown status for a PingProbeBase record.
    Returns:
        "not confirmed", "suspected", or "confirmed"
    """
    confidence = calculate_confidence(probe.packet_loss, probe.rtt_max_ms)

    if confidence >= 80:
        return "confirmed"
    elif confidence >= 50:
        return "suspected"
    else:
        return "not confirmed"

if __name__ == "__main__":
    # Create a dummy PingProbeBase object for testing
    probe_instance = schemas.PingProbeBase(
        host="host1",
        packets_sent=5,
        packets_received=3,
        packet_loss=40.0,
        rtt_min_ms=20,
        rtt_max_ms=250,
        rtt_avg_ms=150
    )

    status = get_shutdown_status(probe_instance)
    print(f"Shutdown status for {probe_instance.host}: {status}")
