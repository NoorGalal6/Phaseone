from Core.event_bus import EventBus


def test_event_bus():
    bus = EventBus()
    received_data = []

    def my_function(data):
        received_data.append(data)

    bus.subscribe("test_event", my_function)
    bus.publish("test_event", "Hello")

    assert received_data == ["Hello"]