import json
import os
import time
from typing import Dict, Tuple, Optional
import logging
from contextlib import contextmanager

COOLDOWN_SECONDS = 210
BASE_DIR = "/Users/chainreachai/selenium_chrome_profiles"
ACCOUNTS = ("account_1", "account_2", "account_3")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _state_path(profile_name: str) -> str:
    """Build absolute path for a profile's state JSON file."""
    return os.path.join(BASE_DIR, f"{profile_name}_state.json")


def _normalize_record(value) -> float:
    """
    Accept int/float unix epoch or dict with key 'last_used'.
    Return float epoch seconds. Missing or invalid -> 0.0
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        v = value.get("last_used")
        if isinstance(v, (int, float)):
            return float(v)
    return 0.0


def _denormalize_record(epoch: float, original):
    """
    Keep original shape. If original was dict with 'last_used', preserve that.
    Otherwise write bare epoch.
    """
    if isinstance(original, dict):
        new_obj = dict(original)
        new_obj["last_used"] = float(epoch)
        return new_obj
    return float(epoch)


def _read_state(path: str) -> Dict[str, object]:
    """
    Read JSON state. If file missing or invalid, initialize with zeros for all accounts.
    """
    if not os.path.exists(path):
        return {a: 0.0 for a in ACCOUNTS}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("State JSON root must be an object")
            # Ensure all accounts exist
            for a in ACCOUNTS:
                if a not in data:
                    data[a] = 0.0
            return data
    except Exception as e:
        logger.warning("Failed to read state %s: %s. Reinitializing.", path, e)
        return {a: 0.0 for a in ACCOUNTS}


def _atomic_write(path: str, data: Dict[str, object]) -> None:
    """Atomically write JSON to path."""
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


@contextmanager
def _file_lock(path: str, timeout: float = 5.0):
    """
    Simple advisory lock using a .lock file to reduce concurrent write hazards.
    Not foolproof across processes, but good enough if called serially per run.
    """
    lock_path = f"{path}.lock"
    start = time.time()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("utf-8"))
            os.close(fd)
            break
        except FileExistsError:
            if time.time() - start > timeout:
                logger.warning("Lock timeout on %s. Proceeding without exclusive lock.", lock_path)
                break
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            os.remove(lock_path)
        except FileNotFoundError:
            pass


def allocation_account(profile_name: str) -> Optional[str]:
    """
    Select an available account for the given profile based on a fixed cooldown.
    Strategy:
      1) Load state.
      2) Compute elapsed = now - last_used for each account.
      3) Pick the available account(s) with elapsed >= COOLDOWN_SECONDS.
         Break ties by choosing the one with the oldest last_used to balance usage.
      4) Return account name or None if all are cooling down.
    """
    path = _state_path(profile_name)
    state = _read_state(path)
    now = time.time()

    # Build list of (account, last_used, elapsed)
    stats: list[Tuple[str, float, float]] = []
    for a in ACCOUNTS:
        last = _normalize_record(state.get(a))
        stats.append((a, last, now - last))

    # Filter available
    available = [s for s in stats if s[2] >= COOLDOWN_SECONDS]

    if not available:
        # Log shortest remaining wait to aid scheduling
        remaining = min(max(0.0, COOLDOWN_SECONDS - s[2]) for s in stats)
        logger.info("No account available for %s. Wait ~%.0f seconds.", profile_name, remaining)
        return None

    # Choose the one with the oldest last_used (i.e., smallest last timestamp)
    selected = min(available, key=lambda t: t[1])[0]
    logger.info("Selected %s for %s", selected, profile_name)
    return selected


def set_local_account_last_join(profile_name: str, account_name: str) -> None:
    """
    Update the target account's last_used to current time.
    Preserves JSON shape per-field.
    """
    if account_name not in ACCOUNTS:
        raise ValueError(f"Unknown account '{account_name}'. Expected one of {ACCOUNTS}")

    path = _state_path(profile_name)
    with _file_lock(path):
        state = _read_state(path)
        original = state.get(account_name, 0.0)
        state[account_name] = _denormalize_record(time.time(), original)
        # Ensure other accounts are at least present
        for a in ACCOUNTS:
            if a not in state:
                state[a] = 0.0
        _atomic_write(path, state)
    logger.info("Updated %s for %s", account_name, profile_name)


# Optional convenience utilities

def next_available_in_seconds(profile_name: str) -> int:
    """
    Return the minimum seconds until any account becomes available.
    0 if at least one account is already available.
    """
    path = _state_path(profile_name)
    state = _read_state(path)
    now = time.time()
    waits = []
    for a in ACCOUNTS:
        last = _normalize_record(state.get(a))
        elapsed = now - last
        waits.append(max(0.0, COOLDOWN_SECONDS - elapsed))
    return int(max(0, round(min(waits)))) if waits else 0


def ensure_state_initialized(profile_name: str) -> None:
    """
    Create the state file if missing with zeroed timestamps for all accounts.
    Safe to call repeatedly.
    """
    path = _state_path(profile_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        _atomic_write(path, {a: 0.0 for a in ACCOUNTS})
