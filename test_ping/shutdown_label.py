
from datetime import datetime
from test_ping import schemas

# Threshold constants
PACKET_LOSS_THRESHOLD = 50.0  # %
RTT_SPIKE_THRESHOLD = 200.0  # ms
SIGNAL_STRENGTH_LOW = 2       # out of 5
POOR_SIGNAL_QUALITIES = {"POOR", "NONE"}


def calculate_confidence(packet_loss: float, rtt_max: float, signal_strength: int = None, signal_quality: str = None) -> int:
    """
    Calculate a confidence score based on packet loss, RTT, and signal quality.
    """
    score = 0

    # Packet loss contribution
    if packet_loss > PACKET_LOSS_THRESHOLD:
        score += 50

    # RTT spike contribution
    if rtt_max > RTT_SPIKE_THRESHOLD:
        score += 30

    # Signal-based contribution
    if signal_strength is not None and signal_strength <= SIGNAL_STRENGTH_LOW:
        score += 10
    if signal_quality and signal_quality.upper() in POOR_SIGNAL_QUALITIES:
        score += 10

    return min(score, 100)


def get_shutdown_status(probe) -> str:
    """
    Determine shutdown status for either:
    - PingProbeBase (Pydantic)
    - PingProbe (SQLAlchemy ORM)
    - Full mobile payload with nested pingResults/deviceInfo

    Returns:
        "not confirmed", "suspected", or "confirmed"
    """

    # ---  Extract core network metrics ---
    packet_loss = getattr(probe, "packet_loss", None)
    rtt_max = getattr(probe, "rtt_max_ms", None)
    signal_quality = getattr(probe, "signalQuality", None)
    signal_strength = None

    # --- If pingResults exist, prefer them ---
    ping_results = getattr(probe, "pingResults", None)
    if ping_results and isinstance(ping_results, list) and len(ping_results) > 0:
        first_ping = ping_results[0]
        packet_loss = first_ping.packetLoss * 100 if first_ping.packetLoss is not None else packet_loss
        rtt_max = first_ping.maxResponseTime or rtt_max

    # --- If deviceInfo exists, get signal info ---
    device_info = getattr(probe, "deviceInfo", None)
    if device_info:
        signal_strength = device_info.signalStrength or signal_strength

    # --- Compute confidence ---
    confidence = calculate_confidence(packet_loss or 0, rtt_max or 0, signal_strength, signal_quality)

    # --- Return status ---
    if confidence >= 80:
        return "confirmed"
    elif confidence >= 50:
        return "suspected"
    else:
        return "not confirmed"

if __name__ == "__main__":
    from types import SimpleNamespace

    print("\n=== 🔍 TEST 1: Basic PingProbeBase (Pydantic) ===")
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
    print(f"Host: {probe_instance.host}")
    print(f"→ Status: {status}\n")

    print("=== 🔍 TEST 2: Full Mobile Payload (JSON-like) ===")
    mobile_payload = SimpleNamespace(
        pingResults=[
            SimpleNamespace(
                packetLoss=1.0,               # 100% packet loss
                maxResponseTime=350.0,        # High latency
                totalPacketsSent=3,
                totalPacketsReceived=0
            )
        ],
        deviceInfo=SimpleNamespace(
            signalStrength=1,                # Weak signal
            carrier="Vodafone"
        ),
        signalQuality="POOR",
        networkType="MOBILE_DATA"
    )
    status = get_shutdown_status(mobile_payload)
    print(f"Network Type: {mobile_payload.networkType}")
    print(f"Signal Strength: {mobile_payload.deviceInfo.signalStrength}")
    print(f"Signal Quality: {mobile_payload.signalQuality}")
    print(f"→ Status: {status}\n")

    print("=== 🔍 TEST 3: Good Connection ===")
    good_payload = SimpleNamespace(
        pingResults=[
            SimpleNamespace(
                packetLoss=0.0,
                maxResponseTime=100.0
            )
        ],
        deviceInfo=SimpleNamespace(
            signalStrength=4
        ),
        signalQuality="GOOD"
    )
    status = get_shutdown_status(good_payload)
    print(f"→ Status: {status}\n")

    print("=== ✅ TEST COMPLETE ===")
