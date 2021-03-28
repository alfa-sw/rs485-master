import logging
import abc

from enum import Enum, auto

class Event(object):
    source = None
    label = None
    attachment = None
    pass

class Observable(abc.ABC):
    """ The virtual class implementing the event system,
    following the publish-subscribe pattern.
    Any instance of this class publish messages, which are
    sent to receiving objects previously subscribed. 
    Each instance of this class stores a list 
    of callbacks. When an event is fired by the instance,
    each callback is called with event data as argument
    """

    def __init__(self):
        self.callbacks = []
        
    def subscribe(self, callback):
        """
        add the callback defined as argument. 
        :param callback: Callback shall have 1 positional argument:
            def callback(e), where 'e' is an instance of class Event. 
        """

        self.callbacks.append(callback)
        
    def fire(self, event_label, **attrs):
        """
        add the callback defined as argument. 
        :param callback: Callback shall have 1 positional argument:
            def callback(e), where 'e' is an instance of class Event. 
        """
        e = Event()
        e.source = self
        e.label = event_label
        e.attachment = attrs
        for k, v in attrs.items():
            setattr(e, k, v)
        for fn in self.callbacks:
            fn(e)

