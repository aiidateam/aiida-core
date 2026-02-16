"""
Service Daemon - Generic process manager for services with health monitoring.

Directory Structure:
```
daemon/
├── profile-<aiida_profile_name>/<session_timestamp>
│   ├── <worker_service_name>/
│   │   ├── worker_service_config.json     # config how to start the worker service
│   │   ├── 1/
│   │   │   ├── info.json          # PID, state, timestamps, failure count
│   │   │   ├── stdout.log         # Service stdout
│   │   │   └── stderr.log         # Service stderr
│   │   └── 2/   
│   │       ├── info.json  # PID, state, timestamps, failure count
│   │       ├── stdout.log         # Service stdout
│   │       └── stderr.log         # Service stderr
│   └── <service_name>/
│       ├── service_config.json    # config how to start the service
│       ├── info.json      # PID, state, timestamps, failure count
│       ├── stdout.log             # Service stdout
│       └── stderr.log             # Service stderr
├── supervisor_info.json           # Single daemon PID file
├── supervisor_config.json         # Single daemon PID file
└── supervisor.log                 # Daemon output (background mode only)
```

Key Features:
- Generic daemon works with any service type
- Single daemon.pid file
- Health monitor runs as thread (not separate process)
- Services are children of daemon (proper parent-child relationship)
- When daemon terminates, all children are cleaned up automatically
- Foreground mode: daemon runs in terminal, Ctrl+C stops everything
- Background mode: daemon detaches, use stop script to send SIGTERM
"""

# Design choices
# Services need to be able to be started by the command line
# Worker and reglar servivces are conceptual separated

from dataclasses import dataclass, asdict
import os
import re
import sys
import subprocess
import time
import signal
import threading
import json
import psutil
from typing import List, Dict, Type, assert_never, Self, ClassVar
from abc import abstractmethod, ABC
from pathlib import Path
import enum
import logging

# TODO public API

# TODO logger as in aiida
logger = logging.getLogger()

class ServiceState(enum.Enum):
    ALIVE = "ALIVE"
    DEAD = "DEAD"

class FolderIdentifier(ABC):

    def __init__(self, identifier: str):
        if not self.is_valid_identifier(identifier):
            #TODO polish error msg
            raise ValueError(
                f"Invalid service identifier {identifier}. May only contain alphanumeric characters, underscores, hyphens"
                  "Must start with a letter or number"
                  "Length: 1-255 characters"
            )
        self._identifier = identifier

    @property
    def identifier(self) -> str:
        return self._identifier

    def __str__(self) -> str:
        """String representation returns full identifier."""
        return self._identifier

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"ServiceIdentifier('{self._identifier}')"

    def __hash__(self) -> int:
        """Hash based on the full identifier string."""
        return hash(self._identifier)

    def __eq__(self, other) -> bool:
        """Equality based on the full identifier string."""
        if not isinstance(other, ServiceIdentifier):
            return False
        return self._identifier == other._identifier

    @staticmethod
    def is_valid_identifier(name: str) -> bool:
        """
        Check if a string is a valid service identifier name.
        
        Allows: alphanumeric characters, underscores, hyphens
        Must start with a letter or number
        Length: 1-255 characters
        """
        if not name:
            return False

        # Only allow safe characters: letters, numbers, underscore, hyphen
        # Must start with alphanumeric
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,254}$'

        return bool(re.match(pattern, name))

# TODO needed? kind of it checks if it is a folder identifier 
class ServiceIdentifier(FolderIdentifier):
    pass

@dataclass
class JsonSerialization:
    @classmethod
    def from_file(cls, path: Path) -> Self:
        with open(path, 'r') as f:
            return cls(**json.load(f))

    def to_file(self, path: Path):
        with open(path, 'w') as f:
            json.dump(asdict(self), f)

@dataclass
class ProcessInfo:
    pid: int
    create_time: float

# TODO MonitoredProcessInfo -> WorkerInfo

@dataclass
class ServiceInfo(ProcessInfo, JsonSerialization):
    service_name: str
    command: str
    state: str
    last_check: float
    failures: int

# TODO replace with auto-register subclasses
# We need such a pattern because we need to be able to load the the specialized ServiceConfigs from the json file, so we potentially need to be able to create a ServiceConfig just from the service_name

SERVICE_CONFIG_REGISTRY: Dict[str, Type["ServiceConfig"]] = {}

@dataclass
class ServiceConfig(ABC):
    # TODO rename to service_identifier?
    service_name: ClassVar[str] 
    command: ClassVar[str]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Auto-register any subclass that defines service_name
        name = getattr(cls, "service_name", None)
        if name is not None:
            SERVICE_CONFIG_REGISTRY[name] = cls

    @abstractmethod
    def create_unique_env(self) -> dict[str, str]:
        raise NotImplementedError()

    def to_dict(self):
        values = asdict(self)
        # adding class attributes that are not included
        values["service_name"] = self.service_name
        values["command"] = self.command
        return values

@dataclass
class NonWorkerServiceConfig(ServiceConfig):
    pass

@dataclass
class WorkerServiceConfig(ServiceConfig):
    num_workers: int

@dataclass
class AiidaWorkerConfig(WorkerServiceConfig):
    service_name: ClassVar[str] = "aiida_worker"
    command: ClassVar[str] = "verdi daemon worker"

    def create_unique_env(self) -> dict[str, str]:
        aiida_path = os.environ.get("AIIDA_PATH")
        return {} if aiida_path is None else {"AIIDA_PATH": aiida_path}

# TODO make commands tunable, not sure how without complicated interface, maybe just comamnd_base and args
@dataclass
class SleepServiceConfig(NonWorkerServiceConfig):
    service_name: ClassVar[str] = "sleep10"
    command: ClassVar[str] = "sleep 10"

    def create_unique_env(self) -> dict[str, str]:
        return {}

class ServiceConfigFactory:

    @staticmethod
    def from_file(path: Path) -> ServiceConfig:
        with open(path, "r") as f:
            values = json.load(f)
        return ServiceConfigFactory.from_dict(values)

    @staticmethod
    def from_dict(values: dict) -> ServiceConfig:
        if not (service_name := values.pop("service_name")):
            raise ValueError("Missing 'service_name' in config")
        if not (cls := SERVICE_CONFIG_REGISTRY.get(service_name)):
            raise ValueError(f"Unknown service_name {service_name!r}")

        # have to remove class variables before init
        values.pop("command")
        return cls(**values)

class ServiceConfigMap:
    """
    Collection of service configurations with dict-like access.

    This class manages multiple ServiceConfig instances and provides
    methods to query and access them by ServiceIdentifier.

    Supports dict-like access: collection[service_id] returns the ServiceConfig.
    """

    def __init__(self, configs: List[ServiceConfig]):
        # enforce uniqueness
        configs_counts = {}
        configs_counts = {config.service_name: 1 + configs_counts.get(config.service_name, 0) for config in configs}
        duplicate_configs = list(filter(lambda key: configs_counts[key] > 1 , configs_counts.keys()))
        if len(duplicate_configs) > 0:
            raise ValueError(f"Found serivce names {duplicate_configs} multiple times in the list of service configs")
        self._configs = {ServiceIdentifier(config.service_name): config for config in configs}

    def __getitem__(self, identifier: str | ServiceIdentifier) -> ServiceConfig:
        # Convert string to ServiceIdentifier if needed
        if isinstance(identifier, str):
            identifier = ServiceIdentifier(identifier)

        if identifier not in self._configs:
            available = [sid for sid in self._configs.keys()]
            raise KeyError(
                f"Service '{identifier}' not found. "
                f"Available services: {available}"
            )
        return self._configs[identifier]

    def __contains__(self, identifier: str | ServiceIdentifier) -> bool:
        if isinstance(identifier, str):
            identifier = ServiceIdentifier(identifier)
        return identifier in self._configs

    def __len__(self) -> int:
        return len(self._configs)

    def __iter__(self):
        return iter(self._configs)

    def keys(self):
        return self._configs.keys()

    def values(self):
        return self._configs.values()

    def items(self):
        return self._configs.items()

    def to_file(self, path: Path):
        with open(path, "w") as f:
            json.dump({key.identifier: config.to_dict() for key, config in self._configs.items()}, f)

    @classmethod
    def from_file(cls, path: Path) -> Self:
        with open(path, "r") as f:
            values = json.load(f)
        return cls([ServiceConfigFactory.from_dict(value) for value in values.values()])

@dataclass
class SupervisorInfo(ProcessInfo, JsonSerialization):
    pass

class ServiceSupervisorCommon:
    SUPERVISOR_INFO_FILE = "supervisor_info.json"
    SUPERVISOR_CONFIG_FILE = "supervisor_config.json"
    # TODO split log
    SUPERVISOR_LOG_FILE = "supervisor.log"
    PROCESS_INFO_FILE = "info.json"
    KILL_TIMEOUT = 10.0

    @staticmethod
    def _start_service_process(service_dir: Path, config: ServiceConfig, info: ServiceInfo | None = None):
        ServiceSupervisorCommon._start_process(service_dir / config.service_name, config, info)
        
    @staticmethod
    def _start_worker_service_process(service_dir: Path, config: ServiceConfig, worker_num: int, info: ServiceInfo | None = None):
        ServiceSupervisorCommon._start_process(service_dir / config.service_name / str(worker_num), config, info)

    @staticmethod
    def _start_process(process_dir: Path, config: ServiceConfig, info: ServiceInfo | None = None):
        process_dir.mkdir(parents=True, exist_ok=True)

        # Open log files in service directory
        stdout_log = process_dir / "stdout.log"
        stderr_log = process_dir / "stderr.log"

        stdout_file = open(stdout_log, 'a', buffering=1)
        stderr_file = open(stderr_log, 'a', buffering=1)

        # Get unique environment for this service
        service_env = config.create_unique_env()

        process = subprocess.Popen(
            config.command.split(),
            stdout=stdout_file,
            stderr=stderr_file,
            env=os.environ | service_env,
            start_new_session=True  # Create new process group
        )
        create_time = psutil.Process(process.pid).create_time()

        service_info = ServiceInfo(
            service_name=config.service_name,
            command=config.command,
            pid=process.pid,
            state=ServiceState.ALIVE.value,
            create_time=create_time,
            last_check=create_time,
            failures=0 if info is None else info.failures+1
        )
        service_info.to_file(process_dir / ServiceSupervisorCommon.PROCESS_INFO_FILE)

    # TODO consider adding the create_time, then we maybe don't need do check if is alive but directly send _kill_service
    @staticmethod
    def _kill_service(pid: int) -> bool:
        # TODO add create_time
        # Kill the process with timeout of 5 seconds, force kill if it doesn't stop
        logger.debug(f"Stopping process with PID {pid}")
        kill_successful = True
        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)

            # Wait up to 5 seconds for the process to terminate
            start_time = time.time()
            while time.time() - start_time < ServiceSupervisorCommon.KILL_TIMEOUT:
                os.kill(pid, 0)
                time.sleep(0.1)
            else:
                # Timeout - force kill
                print(f"⚠ Process {pid} did not stop gracefully, force killing...")
                os.kill(pid, signal.SIGKILL)
                start_time = time.time()
                while time.time() - start_time < ServiceSupervisorCommon.KILL_TIMEOUT:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                kill_successful = False
                logger.info(f"Force killing process {pid} failed.")
        except ProcessLookupError:
            # Process already gone
            logger.debug(f"Process {pid} stopped.")
            pass
        except PermissionError:
            kill_successful = False
            logger.debug(f"No permission to kill process {pid}")
        except Exception as e:
            kill_successful = False
            logger.warning(f"Error stopping process {pid}: {e}") 
        return kill_successful

    @staticmethod
    def _is_alive(pid: int, create_time: float) -> bool:
        """
        Check if process is alive with PID reuse protection.

        This function verifies:
        1. Process with the PID exists
        2. Process creation time matches what we stored

        This prevents accidentally treating a different process
        (that reused the PID) as our service.

        Args:
            service_info: Service information from state file

        Returns:
            True if process exists and is confirmed to be our service
        """
        try:
            process = psutil.Process(pid)

            # Get actual process creation time
            actual_create_time = process.create_time()

            # Compare with stored creation time
            # Allow 1 second tolerance for timing differences
            time_diff = abs(actual_create_time - create_time)

            if time_diff > 1.0:
                # PID has been reused by a different process!
                print(f"WARNING: PID {pid} reused by different process!")
                print(f"  Expected create time: {create_time}")
                print(f"  Actual create time: {actual_create_time}")
                print(f"  Difference: {time_diff} seconds")
                return False

            # Process exists and creation time matches
            return True

        except psutil.NoSuchProcess:
            # Process doesn't exist
            return False
        except psutil.AccessDenied:
            # Process exists but we don't have permission to access it
            # This could mean:
            # 1. It's running as a different user
            # 2. System restrictions prevent access
            # Conservative approach: assume it's alive
            print(f"WARNING: Cannot access PID {pid} (permission denied)")
            return True

    # TODO add for _cleanup_last_session a boolean return value so we can say it worked
    @staticmethod
    def stop(session_dir: Path):
        service_configs = ServiceConfigMap.from_file(session_dir / ServiceSupervisorCommon.SUPERVISOR_CONFIG_FILE)

        supervisor_info_file = session_dir / ServiceSupervisorCommon.SUPERVISOR_INFO_FILE
        if (supervisor_info_file := supervisor_info_file).exists():
            service_info = None
            try:
                service_info = SupervisorInfo.from_file(supervisor_info_file)
            except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Skipping invalid or corrupted supervisor info file {supervisor_info_file}: {e}. ")

            if (service_info is not None and
                ServiceSupervisorCommon._is_alive(service_info.pid, service_info.create_time) and
                not ServiceSupervisorCommon._kill_service(service_info.pid)):
                    pass
                    # TODO but need to include state to ServiceInfo   
                    #service_info.state = ServiceState.DEAD.value
                    #service_info.to_file(supervisor_info_file)

        for config in service_configs.values():
            if isinstance(config, NonWorkerServiceConfig):
                process_dir = session_dir / config.service_name
                if (info_file := process_dir / ServiceSupervisorCommon.PROCESS_INFO_FILE).exists():
                    try:
                        info = ServiceInfo.from_file(info_file)
                    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as e:
                        logger.warning(f"Skipping invalid or corrupted info file {info_file}: {e}.")
                        continue

                    # TODO should I consider here info.state? _is_alive is safer
                    if ServiceSupervisorCommon._is_alive(info.pid, info.create_time):
                        logger.info(f"Terminating service {info.service_name} process with pid {info.pid}")
                        if ServiceSupervisorCommon._kill_service(info.pid):
                            info.state = ServiceState.DEAD.value
                            info.to_file(process_dir / ServiceSupervisorCommon.PROCESS_INFO_FILE)
                    else:
                        info.state = ServiceState.DEAD.value
                        info.to_file(process_dir / ServiceSupervisorCommon.PROCESS_INFO_FILE)

            elif isinstance(config, WorkerServiceConfig):
                for i in range(config.num_workers): 
                    process_dir = session_dir / config.service_name / str(i)
                    if (info_file := process_dir / ServiceSupervisorCommon.PROCESS_INFO_FILE).exists():
                        try:
                            info = ServiceInfo.from_file(info_file)
                        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as e:
                            logger.warning(f"Skipping invalid or corrupted info file {info_file}: {e}. ")
                            continue

                        if ServiceSupervisorCommon._is_alive(info.pid, info.create_time):
                            logger.info(f"Terminating service {info.service_name} worker {i} with process with pid {info.pid}")
                            if ServiceSupervisorCommon._kill_service(info.pid):
                                info.state = ServiceState.DEAD.value
                                info.to_file(process_dir / ServiceSupervisorCommon.PROCESS_INFO_FILE)
                        else:
                            info.state = ServiceState.DEAD.value
                            info.to_file(process_dir / ServiceSupervisorCommon.PROCESS_INFO_FILE)
            else:
                assert_never(config)


class ServiceSupervisorProcess:
    """
    The supervisor process that manages service processes.

    This class runs as the main daemon process and:
    - Monitors child service processes via a health monitor thread
    - Restarts failed services automatically
    - Handles graceful shutdown on SIGTERM/SIGINT
    """

    def __init__(self, session_dir: Path, foreground: bool):
        self._session_dir = session_dir
        self._log_fd = None

        if not foreground:
            self._daemonize()

        # Configure logger to write to supervisor log file
        self._setup_logging()

        # TODO remove prints
        print(f"[{time.ctime()}] Supervisor started (PID: {os.getpid()})")
        self._save_supervisor_info()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Setup zombie reaper BEFORE starting any child processes
        self._setup_child_reaper()

        # Start health monitor thread
        self.monitor_thread = threading.Thread(target=self._health_monitor, daemon=False, name="HealthMonitor")
        self.monitor_thread.start()
        print("✓ Health monitor started")

    def _daemonize(self):
        # TODO add stackoverflow why double fork needed to decouple from terminal session
        """Double fork to become a daemon process."""
        # First fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"Fork #1 failed: {e}\n")
            sys.exit(1)

        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"Fork #2 failed: {e}\n")
            sys.exit(1)

        print(f"[{time.ctime()}] Daemon started (PID: {os.getpid()})")

    def _save_supervisor_info(self):
        """Save the supervisor's PID and create time to a file for later reference."""
        pid = os.getpid()
        supervisor_info = SupervisorInfo(pid, psutil.Process(pid).create_time())
        supervisor_info.to_file(self._session_dir / ServiceSupervisorCommon.SUPERVISOR_INFO_FILE)

    def _setup_logging(self):
        """
        Configure logging to write to the supervisor log file.

        This redirects both:
        1. stdout/stderr (for print() statements)
        2. Python logging (for logger.* calls)

        to the supervisor log file.
        """
        log_file = self._session_dir / ServiceSupervisorCommon.SUPERVISOR_LOG_FILE

        # Redirect stdout and stderr to log file
        sys.stdout.flush()
        sys.stderr.flush()
        self._log_fd = open(log_file, 'a')
        os.dup2(self._log_fd.fileno(), sys.stdout.fileno())
        os.dup2(self._log_fd.fileno(), sys.stderr.fileno())

        # Configure Python logging to also write to the same file
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)

        # Create formatter with timestamp
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # Add handler to the logger
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)

        logger.info("Logger configured to write to supervisor log file")

    def _setup_child_reaper(self):
        """
        Setup SIGCHLD handler to automatically reap zombie processes.

        When child processes terminate, they become zombies until the parent
        calls wait(). This handler automatically reaps terminated children
        to prevent zombie accumulation.
        """
        def handle_sigchld(signum, frame):
            """Non-blocking reaper for terminated child processes."""
            while True:
                try:
                    # Reap any terminated children (non-blocking with WNOHANG)
                    pid, status = os.waitpid(-1, os.WNOHANG)
                    if pid == 0:  # No more children to reap
                        break
                    logger.debug(f"Reaped child process {pid} with exit status {status}")
                except ChildProcessError:
                    # No more children exist
                    break
                except Exception as e:
                    # Log unexpected errors but don't crash
                    logger.warning(f"Error in SIGCHLD handler: {e}")
                    break

        # Register the handler
        signal.signal(signal.SIGCHLD, handle_sigchld)
        logger.debug("SIGCHLD handler installed for zombie reaping")

    def _check_service_process_health(self, config: ServiceConfig):
        process_dir = self._session_dir / config.service_name
        self._check_process_health(process_dir, config)

    def _check_worker_process_health(self, config: ServiceConfig, worker_num: int):
        process_dir = self._session_dir / config.service_name / str(worker_num)
        self._check_process_health(process_dir, config)

    @staticmethod
    def _check_process_health(process_dir, config: ServiceConfig):
        info_path = process_dir / ServiceSupervisorCommon.PROCESS_INFO_FILE
        try:
            info = ServiceInfo.from_file(info_path)
        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Skipping invalid or corrupted info file {info_path}: {e}. ")
            return 

        is_alive = ServiceSupervisorCommon._is_alive(info.pid, info.create_time)
        info.last_check = time.time()
        if is_alive:
            info.last_check = time.time()
            info.state = ServiceState.ALIVE.value
            try:
                info.to_file(info_path)
            except:
                logger.error(f"Unable to update service {info.service_name} info with PID {info.pid} after restart. Continueing.")
        else:
            # TODO add traceback into logger errors
            logger.info(f"[{time.ctime(info.last_check)}] Service {info.service_name!r} died with PID {info.pid} died")
            info.state = ServiceState.DEAD.value
            try:
                info.to_file(info_path)
            except:
                logger.error(f"Unable to update service {info.service_name} info with PID {info.pid} after it died. Continueing.")

            logger.info(f"Restarting service {info.service_name!r}...")
            try:
                ServiceSupervisorCommon._start_process(process_dir, config)
            except:
                logger.error(f"Unable to restart service {info.service_name}. Continueing.")
                return
            else:
                logger.info(f"Restarting service {info.service_name!r} was successful.")

    # TODO rename to keep_alive_monitor
    def _health_monitor(self):
        """Health monitor thread - checks child processes every 5s."""
        logger.info(f"[{time.ctime()}] Health monitor thread started")
        self.running = True
        while self.running:
            # TODO global config
            time.sleep(5)
            
            service_configs = ServiceConfigMap.from_file(self._session_dir / ServiceSupervisorCommon.SUPERVISOR_CONFIG_FILE)
            for config in service_configs.values():
                if isinstance(config, WorkerServiceConfig):
                    for i in range(config.num_workers):
                        self._check_worker_process_health(config, i)
                elif isinstance(config, NonWorkerServiceConfig):
                    self._check_service_process_health(config)
                else:
                    assert_never(config)
        print(f"[{time.ctime()}] Health monitor thread shutting down...")
        self._shutdown()

    def _shutdown(self):
        ServiceSupervisorCommon.stop(self._session_dir)

        # Close log file descriptor before exiting
        if self._log_fd is not None:
            try:
                self._log_fd.close()
            except Exception as e:
                # Best effort - don't fail shutdown
                print(f"Warning: Failed to close log file descriptor: {e}")


    def _signal_handler(self, signum, frame):
        """Handle SIGTERM/SIGINT."""
        print(f"\n[{time.ctime()}] Received signal {signum}, shutting down...")
        self._shutdown()
        sys.exit(0)

class ServiceSupervisorController:
        
    # TODO move to common
    class SessionDirUtils:
        SESSION_DIR_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
        SESSION_DIR_PATTERN = r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d{6}$'

        @staticmethod
        def generate_dirname() -> str:
            from datetime import datetime

            now = datetime.now()
            dirname = now.strftime(ServiceSupervisorController.SessionDirUtils.SESSION_DIR_TIMESTAMP_FORMAT) + f"-{now.microsecond:06d}"
            # NOTE: raise value for internal consistency
            if not ServiceSupervisorController.SessionDirUtils.match_dirname(dirname):
                raise RuntimeError(f"The created timestamp {dirname} does not match pattern {ServiceSupervisorController.SessionDirUtils.SESSION_DIR_PATTERN}. Please contact a developer.")
            return dirname

        @staticmethod
        def match_dirname(dirname: str) -> bool:
            import re
            # NOTE: The regex expression has to match the timestamp format
            return bool(re.compile(ServiceSupervisorController.SessionDirUtils.SESSION_DIR_PATTERN).match(dirname))
    
    
    @staticmethod
    def _is_running(session_dir: Path) -> bool:
        """
        Check if daemon is running by checking PID file.

        Returns:
            True if daemon is running, False otherwise
        """
        if not session_dir.exists() or not session_dir.is_dir():
            return False

        supervisor_info_file = session_dir / ServiceSupervisorCommon.SUPERVISOR_INFO_FILE
        if not supervisor_info_file.exists():
            return False

        try:
            info = SupervisorInfo.from_file(supervisor_info_file)
        except:
            logger.warning(f"Could not read supervisor info file {supervisor_info_file}. Assuming it is not running.")
            return False
        else:
            return ServiceSupervisorCommon._is_alive(info.pid, info.create_time)

    @staticmethod
    def _create_new_session_dir(supervisor_dir: Path) -> Path:
        timestamp = ServiceSupervisorController.SessionDirUtils.generate_dirname()
        daemon_current_session_dir = supervisor_dir / timestamp
        daemon_current_session_dir.mkdir(parents=False, exist_ok=False)

        return daemon_current_session_dir

    @staticmethod
    def _get_latest_session_dir(supervisor_dir: Path) -> Path | None:
        """
        Get the most recent daemon session directory based on timestamp.

        Scans the daemon base directory for session directories with
        timestamp format YYYY-MM-DD_HH-MM-SS-mmmmmm and returns the most recent one.

        Returns:
            Path to the latest session directory, or None if no sessions exist
        """
        ServiceSupervisorController._validate_supervisor_dir(supervisor_dir)

        # Pattern to match timestamp directories: YYYY-MM-DD_HH-MM-SS-mmmmmm
        # Example: 2025-11-30_16-46-25-324746

        session_dirs = []

        # Find all directories matching the timestamp pattern
        for path in supervisor_dir.iterdir():
            if path.is_dir() and ServiceSupervisorController.SessionDirUtils.match_dirname(path.name):
                session_dirs.append(path)

        # No session directories found
        if not session_dirs:
            return None

        # Sort by directory name (timestamp) - latest will be last
        # Because YYYY-MM-DD_HH-MM-SS-mmmmmm is lexicographically sortable
        session_dirs.sort(key=lambda p: p.name)

        return session_dirs[-1]  # Return most recent

    @staticmethod
    def _validate_supervisor_dir(supervisor_dir: Path):
        # Check if base directory exists
        if not supervisor_dir.exists():
            # TODO error msg
            raise ValueError()
        elif not supervisor_dir.is_dir(): 
            # TODO error msg
            raise ValueError()

    @staticmethod
    def start(supervisor_dir: Path, service_configs: ServiceConfigMap, foreground: bool = False):
        """
        Start the daemon.

        Args:
            service_configs: Configuration for all services to manage
            foreground: If True, run in foreground. If False, detach to run in background.

        Raises:
            RuntimeError: If daemon is already running
        """
        ServiceSupervisorController._validate_supervisor_dir(supervisor_dir)
        latest_session_dir = ServiceSupervisorController._get_latest_session_dir(supervisor_dir)
        # TODO check if service_configs have changed
        if latest_session_dir is not None and ServiceSupervisorController._is_running(latest_session_dir):
            logger.info("Daemon is already running, continue with last session. If you want to start with new settings please stop and start daemon.")
            return

        session_dir = ServiceSupervisorController._create_new_session_dir(supervisor_dir)

        # Start all configured services
        for config in service_configs.values():
            ServiceSupervisorController._start_service(session_dir, config)

        service_configs.to_file(session_dir / ServiceSupervisorCommon.SUPERVISOR_CONFIG_FILE)
        ServiceSupervisorProcess(session_dir, foreground)

    @staticmethod
    def _start_service(session_dir: Path, config: ServiceConfig):
        if session_dir is None:
            # TODO error message, should not happen so dev error
            raise RuntimeError()
        # Get config using base identifier
        if isinstance(config, NonWorkerServiceConfig):
            ServiceSupervisorCommon._start_service_process(session_dir, config)
        elif isinstance(config, WorkerServiceConfig):
            for i in range(config.num_workers):
                ServiceSupervisorCommon._start_worker_service_process(session_dir, config, i)

        else:
            assert_never(config)

    @staticmethod
    def stop(supervisor_dir: Path):
        ServiceSupervisorController._validate_supervisor_dir(supervisor_dir)

        session_dir = ServiceSupervisorController._get_latest_session_dir(supervisor_dir)
        if session_dir is None:
            raise ValueError(f"No session found in {supervisor_dir}")

        ServiceSupervisorCommon.stop(session_dir)

    @staticmethod
    def status(supervisor_dir: Path):
        # TODO this is completey generated, need to revise and move formatting to dedicated class
        """
        Print status of all services by reading supervisor config and service info files.

        Reads the supervisor config file to discover all configured services,
        then reads each service's info file to display current status information.
        """
        ServiceSupervisorController._validate_supervisor_dir(supervisor_dir)

        session_dir = ServiceSupervisorController._get_latest_session_dir(supervisor_dir)
        if session_dir is None:
            raise ValueError(f"No session found in {supervisor_dir}")

        # Load supervisor config to get all services
        config_file = session_dir / ServiceSupervisorCommon.SUPERVISOR_CONFIG_FILE
        if not config_file.exists():
            print(f"No supervisor config file found at {config_file}")
            return

        try:
            service_configs = ServiceConfigMap.from_file(config_file)
        except Exception as e:
            print(f"Error reading supervisor config: {e}")
            return

        print("\n" + "="*80)
        print(f"Daemon Status - Session: {session_dir.name}")
        print("="*80)

        # Check supervisor status
        supervisor_info_file = session_dir / ServiceSupervisorCommon.SUPERVISOR_INFO_FILE
        if supervisor_info_file.exists():
            try:
                supervisor_info = SupervisorInfo.from_file(supervisor_info_file)
                is_alive = ServiceSupervisorCommon._is_alive(supervisor_info.pid, supervisor_info.create_time)
                log_dir = session_dir / ServiceSupervisorCommon.SUPERVISOR_LOG_FILE
                print(f"\nSupervisor Process:")
                print(f"  PID: {supervisor_info.pid}")
                print(f"  Status: {'RUNNING' if is_alive else 'STOPPED'}")
                print(f"  Started: {time.ctime(supervisor_info.create_time)}")
                print(f"  Log: {log_dir}")
            except Exception as e:
                print(f"\nSupervisor Process: Error reading info - {e}")
        else:
            print("\nSupervisor Process: No info file found")

        print("\n" + "-"*80)
        print("Services:")
        print("-"*80)

        # Iterate through all configured services
        for service_identifier, config in service_configs.items():
            if isinstance(config, NonWorkerServiceConfig):
                # Non-worker service (single instance)
                service_dir = session_dir / config.service_name
                info_file = service_dir / ServiceSupervisorCommon.PROCESS_INFO_FILE

                print(f"\n[{config.service_name}]")
                print(f"  Type: Service")
                print(f"  Command: {config.command}")

                if info_file.exists():
                    try:
                        info = ServiceInfo.from_file(info_file)
                        is_alive = ServiceSupervisorCommon._is_alive(info.pid, info.create_time)
                        print(f"  PID: {info.pid}")
                        # TODO 
                        print(f"  State: {info.state} ({'ALIVE' if is_alive else 'DEAD'})")
                        print(f"  Started: {time.ctime(info.create_time)}")
                        print(f"  Last Check: {time.ctime(info.last_check)}")
                        print(f"  Failures: {info.failures}")
                        print(f"  Logs:")
                        print(f"    stdout: {service_dir / 'stdout.log'}")
                        print(f"    stderr: {service_dir / 'stderr.log'}")
                    except Exception as e:
                        print(f"  Error: Could not read info file - {e}")
                else:
                    print(f"  Status: No info file found")

            elif isinstance(config, WorkerServiceConfig):
                # Worker service (multiple instances)
                print(f"\n[{config.service_name}]")
                print(f"  Type: Worker Service")
                print(f"  Command: {config.command}")
                print(f"  Workers: {config.num_workers}")

                for worker_num in range(config.num_workers):
                    worker_dir = session_dir / config.service_name / str(worker_num)
                    info_file = worker_dir / ServiceSupervisorCommon.PROCESS_INFO_FILE

                    print(f"\n  Worker {worker_num}:")

                    if info_file.exists():
                        try:
                            info = ServiceInfo.from_file(info_file)
                            is_alive = ServiceSupervisorCommon._is_alive(info.pid, info.create_time)
                            print(f"    PID: {info.pid}")
                            print(f"    State: {info.state} ({'ALIVE' if is_alive else 'DEAD'})")
                            print(f"    Started: {time.ctime(info.create_time)}")
                            print(f"    Last Check: {time.ctime(info.last_check)}")
                            print(f"    Failures: {info.failures}")
                            print(f"    Logs:")
                            print(f"      stdout: {worker_dir / 'stdout.log'}")
                            print(f"      stderr: {worker_dir / 'stderr.log'}")
                        except Exception as e:
                            print(f"    Error: Could not read info file - {e}")
                    else:
                        print(f"    Status: No info file found")
            else:
                assert_never(config)

        print("\n" + "="*80 + "\n")


# Backwards compatibility alias
class AiidaDaemon:
    """Adddd-specific supervisor that automatically uses the AiiDA profile daemon directory."""

    def __init__(self, profile_identifier: str| None = None):
        """
        Initialize AiiDA supervisor with automatic profile directory.

        Args:
            service_configs: ServiceConfigMap with all service configurations
        """
        from aiida.manage import get_manager 
        manager = get_manager()
        profile = manager.load_profile() if profile_identifier is None else manager.load_profile(profile_identifier)
        config = manager.get_config()
        self._daemon_dir = config.get_new_daemon_dir(profile)
        # TODO check if this is fixed by auto-register subclass

    def start(self, num_workers: int, foreground: bool):
        num_workers = config.get_option("daemon.default_workers", 1) if num_workers is None else num_workers
        #service_configs = ServiceConfigMap([AiidaWorkerConfig(num_workers=num_workers)])
        # TODO this is just for showcasing
        service_configs = ServiceConfigMap([AiidaWorkerConfig(num_workers=num_workers), SleepServiceConfig()])
        ServiceSupervisorController.start(self._daemon_dir, service_configs, foreground)

    def stop(self):
        ServiceSupervisorController.stop(self._daemon_dir)

    def status(self):
        ServiceSupervisorController.status(self._daemon_dir)
