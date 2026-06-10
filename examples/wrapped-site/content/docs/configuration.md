# Configuration

Acme Widget reads a small config table:

| Setting | Default | Description |
| --- | --- | --- |
| `retries` | `3` | How many times to retry on failure |
| `timeout` | `30s` | Per-request timeout |
| `cache` | `true` | Enable the in-memory response cache |

A minimal config file:

```yaml
retries: 5
timeout: 10s
cache: false
```

Tables, syntax highlighting, and inline `code` are rendered by KPress; the surrounding
navigation and chrome come from the wrapper.
