# Troubleshooting Guide

## Common Issues and Solutions

### 1. Curl/Gunzip Failed - Exit Code -2

**Symptoms:**
```
[Port 8914] HATA: cc-index/collections/CC-MAIN-2025-05/indexes/cdx-00127.gz - Curl/Gunzip failed. Exit code: -2
```

**Cause:**
- Exit code -2 indicates the process was terminated by a signal (SIGINT)
- This typically happens when:
  - Ctrl+C is pressed
  - System is under heavy load
  - Proxy connection is interrupted
  - Timeout is reached

**Solutions:**

1. **Check Proxy Status:**
   ```bash
   python check_proxies.py
   ```
   This will test all proxies defined in `config.py`

2. **Check for Orphaned Proxy Containers:**
   ```bash
   # List running Docker containers
   docker ps | grep alpine-vpn

   # Stop all alpine-vpn containers
   docker stop $(docker ps -q --filter "name=alpine-vpn")

   # Or stop specific container by port
   docker ps | grep 8914
   docker stop <container_id>
   ```

3. **Verify Config.py Proxy Ports:**
   - The error shows ports: 8914, 8902, 8910, 8917, 8916, 8898, 8912, 8890, 8905, 8900
   - These ports are NOT in your current `config.py`
   - You may have old/stale proxy containers running

   **Check your config:**
   ```bash
   grep -A 20 "PROXY_CONFIGS" config.py
   ```

   **Current working ports in config.py:**
   - 8956, 8955, 8954, 8953, 8946, 8944, 8948, 8943, 8942, 8940, 8939, 8929, 8949, 8945, 8941

4. **Clean Restart:**
   ```bash
   # Stop all containers
   docker stop $(docker ps -q)

   # Restart your proxy containers with the correct ports from config.py
   # (Use your proxy startup script)
   ```

---

### 2. KeyboardInterrupt / Threading Lock Issues

**Symptoms:**
```
Exception ignored in: <module 'threading' from '/usr/lib/python3.12/threading.py'>
Traceback (most recent call last):
  File "/usr/lib/python3.12/threading.py", line 1622, in _shutdown
    lock.acquire()
KeyboardInterrupt:
```

**Cause:**
- Threads were not gracefully shutdown when Ctrl+C was pressed
- Python tried to clean up threads but they were blocked on locks

**Solution:**
✅ **FIXED** - Graceful shutdown handling has been added to `warc_processor.py`

The processor now:
- Catches SIGINT/SIGTERM signals
- Sets a shutdown flag
- Allows current tasks to complete
- Cancels remaining futures
- Exits cleanly

To use:
- Press Ctrl+C once
- Wait for "Initiating graceful shutdown..." message
- Current tasks will finish
- Progress is saved automatically

---

### 3. Proxy Connection Errors

**Symptoms:**
```
[Port 8914] HATA: Connection refused
ProxyError: Cannot connect to proxy
```

**Diagnosis:**
```bash
# Test specific proxy
curl -x http://localhost:8914 https://www.google.com

# Check if port is listening
netstat -tlnp | grep 8914

# Or on macOS:
lsof -i :8914
```

**Solutions:**

1. **Proxy not running:**
   ```bash
   # Start proxy containers (use your startup script)
   # Example:
   docker run -d --name alpine-vpn-8914 -p 8914:3128 your-proxy-image
   ```

2. **Port conflict:**
   ```bash
   # Find what's using the port
   lsof -i :8914

   # Kill the process or change port in config.py
   ```

3. **Firewall blocking:**
   ```bash
   # Ubuntu/Debian
   sudo ufw allow 8914/tcp

   # CentOS/RHEL
   sudo firewall-cmd --add-port=8914/tcp --permanent
   sudo firewall-cmd --reload
   ```

---

### 4. Rate Limiting / Too Many Requests

**Symptoms:**
```
HTTP 429 Too Many Requests
Connection throttled
```

**Solutions:**

1. **Reduce rate limit in config.py:**
   ```python
   REQUESTS_PER_SECOND = 1.0  # Lower value
   ```

2. **Reduce worker count:**
   ```bash
   python process_warcs.py --workers 3  # Instead of 5
   ```

3. **Use more proxies:**
   - Add more proxy configs to `config.py`
   - Each worker gets its own proxy

---

### 5. Out of Memory / Performance Issues

**Symptoms:**
```
MemoryError
System becomes unresponsive
Python process killed
```

**Solutions:**

1. **Reduce sample size:**
   ```bash
   python process_warcs.py --sample-size 5  # 5MB instead of 10MB
   ```

2. **Reduce workers:**
   ```bash
   python process_warcs.py --workers 3
   ```

3. **Process in batches:**
   ```bash
   # Process 100 at a time
   python process_warcs.py --limit 100

   # Then resume from failures
   python process_warcs.py --resume-from data/failures/failed_warcs_*.json
   ```

4. **Monitor resource usage:**
   ```bash
   # Watch memory usage
   watch -n 1 'ps aux | grep python | grep -v grep'

   # Or use htop
   htop -p $(pgrep -f process_warcs)
   ```

---

### 6. Partial WARC / Decompression Errors

**Symptoms:**
```
Compressed file ended before the end-of-stream marker was reached
gzip.BadGzipFile
```

**Note:**
✅ These are EXPECTED and are now suppressed.

The processor only downloads the first 10MB of each WARC file (they can be 1GB+).
This means we get partial/incomplete gzip files, which cause warnings when parsing.

**This is normal and not an error!**

---

### 7. Resume from Failures

**When to use:**
- Processing was interrupted (Ctrl+C, crash, etc.)
- Some WARCs failed after max retries
- You want to retry only failed WARCs

**How to use:**
```bash
# Find failure files
ls -lh data/failures/

# Resume from JSON
python process_warcs.py --resume-from data/failures/failed_warcs_20250105_123456.json

# Resume from TXT (simpler format)
python process_warcs.py --resume-from data/failures/failed_warcs_20250105_123456.txt
```

**Failure tracking:**
- Failed WARCs are automatically saved to `data/failures/`
- Both JSON (detailed) and TXT (simple paths) formats
- Includes failure reason, attempt count, timestamps

---

## Quick Diagnostic Checklist

Before starting a large job:

```bash
# 1. Check proxies
python check_proxies.py

# 2. Check disk space
df -h

# 3. Check memory
free -h  # Linux
vm_stat  # macOS

# 4. Test with small batch first
python process_warcs.py --limit 10 --workers 2

# 5. If successful, scale up
python process_warcs.py --limit 1000 --workers 5
```

---

## Getting Help

If you encounter issues not covered here:

1. Check the logs in `logs/` directory
2. Look at failure files in `data/failures/`
3. Test proxies with `check_proxies.py`
4. Try with fewer workers and smaller batches

---

## Configuration Tips

**For stable long-running jobs (sample mode):**

```bash
# Sample mode: Fast, download only 5MB per WARC
python process_warcs.py \
  --workers 3 \
  --sample-size 5 \
  --rate-limit 1.5 \
  --max-retries 5 \
  --retry-delay 300
```

**For complete scanning (full WARC mode):**

```bash
# Full mode: Download entire WARC files (1GB+ each, SLOW!)
# Use 0 for sample-size to download full WARCs
python process_warcs.py \
  --workers 2 \
  --sample-size 0 \
  --rate-limit 0.5 \
  --limit 10
```

**For fast exploration:**

```bash
# Fast sample mode: Quick scan with 10MB samples
python process_warcs.py \
  --limit 100 \
  --workers 10 \
  --sample-size 10 \
  --rate-limit 3.0
```

### Sample Size Guide

- `--sample-size 5`: 5MB per WARC (fast, ~50-100 URLs per WARC)
- `--sample-size 10`: 10MB per WARC (default, ~100-200 URLs per WARC)
- `--sample-size 50`: 50MB per WARC (thorough, ~500-1000 URLs per WARC)
- `--sample-size 0`: **Full WARC** (complete, ALL URLs, 1GB+ download, VERY SLOW!)

### Deduplication Behavior

**Changed in latest version:**
- Deduplication is now **per-WARC** instead of global
- Same URL in different WARCs = recorded multiple times
- Example: If `example.com` appears in 10 WARCs, you get 10 results
- Use `sort -u` or post-process to deduplicate results if needed

---

## Exit Codes

- `0` - Success
- `1` - Error (check logs)
- `-2` - Killed by signal (SIGINT/Ctrl+C)
- `-9` - Killed forcefully (SIGKILL, usually OOM)
