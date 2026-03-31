# avioFlyBackend

Python backend module for the `avioFly` conversation system.

- Typed request and response contracts
- Service abstractions
- Swappable storage and cache layers
- Pagination support
- Streaming-capable chat result shape
- Host-owned configuration through environment variables

## Notes

- Configuration is provided by the host application.
- Provider credentials are not stored in the module.
- Transport, storage, and cache implementations are swappable.
