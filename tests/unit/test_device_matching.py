from audio_switcher.domain.models import AudioDevice
from audio_switcher.services.device_matching import resolve_device, resolve_devices


def test_resolves_by_id_before_name() -> None:
    configured = AudioDevice("saved-id", "Speakers")
    active = [
        AudioDevice("saved-id", "Renamed speakers"),
        AudioDevice("other-id", "Speakers"),
    ]

    assert resolve_device(configured, active) == active[0]


def test_resolves_changed_id_by_unique_same_name() -> None:
    configured = AudioDevice("old-id", "USB Headphones")
    active = [AudioDevice("new-id", "USB Headphones")]

    assert resolve_device(configured, active) == active[0]


def test_name_fallback_ignores_case_and_repeated_whitespace() -> None:
    configured = AudioDevice("old-id", "USB   Headphones")
    active = [AudioDevice("new-id", "usb headphones")]

    assert resolve_device(configured, active) == active[0]


def test_ambiguous_same_name_is_not_automatically_resolved() -> None:
    configured = AudioDevice("old-id", "Digital Audio")
    active = [
        AudioDevice("new-id-1", "Digital Audio"),
        AudioDevice("new-id-2", "Digital Audio"),
    ]

    assert resolve_device(configured, active) is None


def test_resolve_devices_preserves_order_and_deduplicates_live_endpoint() -> None:
    configured = [
        AudioDevice("old-a", "A"),
        AudioDevice("new-a", "A"),
        AudioDevice("old-b", "B"),
    ]
    active = [AudioDevice("new-a", "A"), AudioDevice("new-b", "B")]

    assert resolve_devices(configured, active) == [active[0], active[1]]
