Server Base
===========

`bless.backends.server` provides the abstract server interface used by all
platform backends.

Callbacks are dispatched in priority order: characteristic-specific handlers,
then server-wide handlers, then default handling when no callbacks are defined.

.. automodule:: bless.backends.server
   :members:
   :undoc-members:
   :no-index:

.. autoclass:: bless.backends.server.BaseBlessServer
   :members:
   :undoc-members:
   :show-inheritance:
